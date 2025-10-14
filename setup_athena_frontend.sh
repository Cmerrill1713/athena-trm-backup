#!/usr/bin/env zsh
set -euo pipefail

title() { printf "\n\033[1;36m%s\033[0m\n" "$1"; }
ok()    { printf "\033[0;32m✓ %s\033[0m\n" "$1"; }
warn()  { printf "\033[0;33m⚠ %s\033[0m\n" "$1"; }
die()   { printf "\033[0;31m✗ %s\033[0m\n" "$1"; exit 1; }

# --- sanity checks ------------------------------------------------------------
[[ "$OSTYPE" == darwin* ]] || die "This script targets macOS."
command -v xcode-select >/dev/null || true

# --- Xcode CLT / Xcode -------------------------------------------------------
title "1) Ensure Xcode & CLT"
if ! xcode-select -p >/dev/null 2>&1; then
  warn "Installing Xcode Command Line Tools…"
  xcode-select --install || true
  echo "➡ When CLT installer finishes, re-run this script."
  exit 1
fi
if [[ ! -d "/Applications/Xcode.app" ]]; then
  warn "Xcode.app not found. Install from App Store, then re-run."
  exit 1
fi
sudo xcode-select -s /Applications/Xcode.app
xcodebuild -version || die "xcodebuild not available"
ok "Xcode active: $(xcodebuild -version | tr '\n' ' | ')"

# --- Homebrew & dev tools ----------------------------------------------------
title "2) Homebrew + tooling"
if ! command -v brew >/dev/null 2>&1; then
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv)"
fi
eval "$($(brew --prefix)/bin/brew shellenv)"
brew update

if [[ -f Brewfile ]]; then
  brew bundle
else
  brew install swiftlint jq yq || true
  brew install python@3.11 || true
fi
ok "Homebrew tools installed"

# --- Python env for demo script ----------------------------------------------
title "3) Python venv for demo"
PYBIN="$(brew --prefix)/bin/python3" || PYBIN="$(command -v python3)"
$PYBIN -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
if [[ -f requirements.txt ]]; then
  pip install -r requirements.txt
else
  pip install psutil
fi
ok "Python virtualenv ready"

# --- Resolve Swift packages ---------------------------------------------------
title "4) Resolve SwiftPM deps"
if [[ -f "Package.swift" ]]; then
  swift package resolve
  ok "SwiftPM resolved"
fi

# --- Choose project/workspace -------------------------------------------------
title "5) Detect Xcode project"
PROJ="$(ls -1 *.xcodeproj 2>/dev/null | head -n1 || true)"
WSPC="$(ls -1 *.xcworkspace 2>/dev/null | head -n1 || true)"
[[ -n "$WSPC" || -n "$PROJ" ]] || die "No .xcodeproj or .xcworkspace found."

OPENABLE="$WSPC"
[[ -z "$OPENABLE" ]] && OPENABLE="$PROJ"
ok "Using $OPENABLE"

# --- Build (macOS) -----------------------------------------------------------
title "6) Build app (Debug)"
SCHEME="${SCHEME:-NeuroForgeApp}"
DEST="platform=macOS"
set +e
# Use Debug to avoid Release-only compilation of preview/top-level macros
xcodebuild -workspace "$WSPC" -scheme "$SCHEME" -configuration Debug -destination "$DEST" build \
  || xcodebuild -project "$PROJ" -scheme "$SCHEME" -configuration Debug -destination "$DEST" build
XCB_STATUS=$?
set -e
[[ $XCB_STATUS -eq 0 ]] || die "xcodebuild failed. Check scheme name ($SCHEME) and signing."

ok "Build succeeded"

# --- Export env & run app -----------------------------------------------------
title "7) Launch app with dev flags"
APP_NAME="${APP_NAME:-NeuroForgeApp}"
export POPUPS_ENABLED=1
export AUTOEXEC_GUARD=1

# Try to locate built .app
APP_PATH="$(fd -t d "${APP_NAME}\.app" build DerivedData . -H 2>/dev/null | head -n1)"
[[ -z "$APP_PATH" ]] && APP_PATH="$(fd -t d "\.app$" build DerivedData . -H | head -n1)"
[[ -n "$APP_PATH" ]] || die "Could not locate built .app. Check build paths."

ok "Launching: $APP_PATH"
open -n "$APP_PATH"

# --- Trigger pop-outs demo ----------------------------------------------------
title "8) Trigger Athena pop-out windows demo"
if [[ -f "demo_athena_popouts.py" ]]; then
  python demo_athena_popouts.py --smoke || warn "Demo script returned non-zero; check logs."
else
  warn "demo_athena_popouts.py not found; skipping demo trigger."
fi

ok "All done. Pop-out windows should be visible. (Use VO/keyboard to test accessibility)"
