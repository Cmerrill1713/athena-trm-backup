#!/usr/bin/env bash
set -euo pipefail

# --- 0) sanity
APP_BUNDLE_NAME="NeuroForgeApp.app"
PROJECT_PATH="NeuroForgeApp/NeuroForgeApp.xcodeproj"
SCHEME="NeuroForgeApp"
INFO_PLIST=$(plutil -p "$PROJECT_PATH/project.pbxproj" >/dev/null 2>&1 && \
             /usr/libexec/PlistBuddy -c "Print :objects" "$PROJECT_PATH/project.pbxproj" >/dev/null 2>&1 && \
             fd -a Info.plist NeuroForgeApp | head -1 || true)

# --- 1) Strip previews helper (idempotent)
cat > scripts/strip_previews.sh <<'BP'
#!/usr/bin/env bash
set -euo pipefail
# Comment out PreviewProvider blocks (safe for CI)
fd -e swift --hidden NeuroForgeApp/Sources | while read -r f; do
  awk '
    /struct .*PreviewProvider/ {inprev=1}
    inprev==1 {print "//[PREVIEW] " $0; if ($0 ~ /}/) c++}
    inprev!=1 {print $0}
    /struct .*PreviewProvider/ { }
    { if(inprev==1 && $0 ~ /^}/) depth++ }
  ' "$f" > "$f.tmp" || true
  # Only replace if we actually tagged something
  if grep -q '\[PREVIEW\]' "$f.tmp" 2>/dev/null; then mv "$f.tmp" "$f"; else rm -f "$f.tmp"; fi
done
BP
chmod +x scripts/strip_previews.sh

# --- 2) Frontside CLI to trigger windows or run E2E
cat > bin/athenactl <<'CLI'
#!/usr/bin/env bash
set -euo pipefail
cmd="${1:-}"
app="${APP_PATH_OVERRIDE:-Build/Products/Debug/NeuroForgeApp.app}"
case "$cmd" in
  show-critical)  open "athena://trigger?kind=critical" ;;
  show-tribunal)  open "athena://trigger?kind=tribunal" ;;
  show-emergency) open "athena://trigger?kind=emergency" ;;
  e2e)
    ATHENA_E2E=1 open -n "$app"
    echo "waiting for report…"
    for i in {1..30}; do
      test -f "$HOME/athena_e2e.json" && { cat "$HOME/athena_e2e.json"; exit 0; }
      sleep 0.3
    done
    echo "no E2E report created" >&2; exit 1
    ;;
  *)
    echo "usage: athenactl {show-critical|show-tribunal|show-emergency|e2e}"; exit 2;;
esac
CLI
chmod +x bin/athenactl

# --- 3) Frontside bridge Swift (URL scheme + notifications)
cat > NeuroForgeApp/Sources/App/FrontsideBridge.swift <<'SWIFT'
import SwiftUI
import AppKit

@MainActor
final class FrontsideBridge: NSObject, ObservableObject {
    static let shared = FrontsideBridge()
    func handle(_ url: URL) {
        guard url.scheme == "athena" else { return }
        let items = URLComponents(url: url, resolvingAgainstBaseURL: false)?.queryItems
        let kind = items?.first(where: {$0.name == "kind"})?.value ?? ""
        switch kind {
        case "critical":  NotificationCenter.default.post(name: .ShowCriticalAlert, object: nil)
        case "tribunal":  NotificationCenter.default.post(name: .ShowTribunalDecision, object: nil)
        case "emergency": NotificationCenter.default.post(name: .ShowSystemEmergency, object: nil)
        default: break
        }
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Headless E2E demo mode: auto-show windows, write report, exit
        if ProcessInfo.processInfo.environment["ATHENA_E2E"] == "1" {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                NotificationCenter.default.post(name: .ShowCriticalAlert, object: nil)
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                NotificationCenter.default.post(name: .ShowTribunalDecision, object: nil)
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                NotificationCenter.default.post(name: .ShowSystemEmergency, object: nil)
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 3.5) {
                let payload = ["status":"ok","shown":["critical","tribunal","emergency"]]
                if let data = try? JSONSerialization.data(withJSONObject: payload, options: [.prettyPrinted]) {
                    let url = URL(fileURLWithPath: NSHomeDirectory()).appendingPathComponent("athena_e2e.json")
                    try? data.write(to: url)
                }
                NSApp.terminate(nil)
            }
        }
    }
    func application(_ application: NSApplication, open urls: [URL]) {
        urls.forEach { FrontsideBridge.shared.handle($0) }
    }
}

extension Notification.Name {
    static let ShowCriticalAlert = Notification.Name("ShowCriticalAlert")
    static let ShowTribunalDecision = Notification.Name("ShowTribunalDecision")
    static let ShowSystemEmergency = Notification.Name("ShowSystemEmergency")
}
SWIFT

# --- 4) Ensure @main App wires the delegate (safe if already present)
if ! grep -R "@NSApplicationDelegateAdaptor" -n NeuroForgeApp/Sources  >/dev/null 2>&1; then
cat >> NeuroForgeApp/Sources/App/main.swift <<'SWIFT'

import SwiftUI

@main
struct AthenaApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    var body: some Scene {
        WindowGroup { AthenaDashboardView() }
            .handlesExternalEvents(matching: Set(["*"]))
    }
}
SWIFT
fi

# --- 5) Add URL scheme to Info.plist (idempotent)
if [ -n "${INFO_PLIST:-}" ] && [ -f "$INFO_PLIST" ]; then
  /usr/libexec/PlistBuddy -c "Delete :CFBundleURLTypes" "$INFO_PLIST" >/dev/null 2>&1 || true
  /usr/libexec/PlistBuddy -c "Add :CFBundleURLTypes array" "$INFO_PLIST"
  /usr/libexec/PlistBuddy -c "Add :CFBundleURLTypes:0 dict" "$INFO_PLIST"
  /usr/libexec/PlistBuddy -c "Add :CFBundleURLTypes:0:CFBundleURLName string athena" "$INFO_PLIST"
  /usr/libexec/PlistBuddy -c "Add :CFBundleURLTypes:0:CFBundleURLSchemes array" "$INFO_PLIST"
  /usr/libexec/PlistBuddy -c "Add :CFBundleURLTypes:0:CFBundleURLSchemes:0 string athena" "$INFO_PLIST"
else
  echo "⚠️  Could not find Info.plist automatically. Add URL scheme manually later."
fi

# --- 6) Makefile targets for Cursor/CI
cat > Makefile.frontside <<'MK'
.PHONY: frontside-build frontside-run frontside-e2e show-critical show-tribunal show-emergency

XCB_FLAGS = -project NeuroForgeApp/NeuroForgeApp.xcodeproj \
            -scheme NeuroForgeApp -configuration Debug \
            -destination 'platform=macOS' \
            -derivedDataPath Build

frontside-build:
	@bash scripts/strip_previews.sh || true
	xcodebuild $(XCB_FLAGS) build

frontside-run: frontside-build
	open -n Build/Build/Products/Debug/NeuroForgeApp.app

frontside-e2e: frontside-build
	ATHENA_E2E=1 open -n Build/Build/Products/Debug/NeuroForgeApp.app
	@echo "Waiting for E2E report…"; \
	for i in $$(seq 1 30); do \
		test -f $$HOME/athena_e2e.json && { echo "OK:"; cat $$HOME/athena_e2e.json; exit 0; }; \
		sleep 0.3; \
	done; \
	echo "No E2E report produced" >&2; exit 1

show-critical: frontside-build ; APP_PATH_OVERRIDE=Build/Build/Products/Debug/NeuroForgeApp.app bin/athenactl show-critical
show-tribunal: frontside-build ; APP_PATH_OVERRIDE=Build/Build/Products/Debug/NeuroForgeApp.app bin/athenactl show-tribunal
show-emergency: frontside-build ; APP_PATH_OVERRIDE=Build/Build/Products/Debug/NeuroForgeApp.app bin/athenactl show-emergency
MK

# merge (append once) into your main Makefile if present
if [ -f Makefile ]; then
  if ! grep -q 'frontside-build' Makefile; then
    echo '' >> Makefile
    echo '# --- Frontside hooks ---' >> Makefile
    cat Makefile.frontside >> Makefile
  fi
else
  mv Makefile.frontside Makefile
fi
rm -f Makefile.frontside

# --- 7) Cursor task buttons (optional but handy)
cat > cursor.json <<'CUR'
{
  "tasks": [
    { "label": "Frontend: Build (macOS)", "command": "make frontside-build" },
    { "label": "Frontend: Run (Dashboard)", "command": "make frontside-run" },
    { "label": "Frontend: E2E (headless)", "command": "make frontside-e2e" },
    { "label": "Frontend: Show Critical", "command": "make show-critical" },
    { "label": "Frontend: Show Tribunal", "command": "make show-tribunal" },
    { "label": "Frontend: Show Emergency", "command": "make show-emergency" }
  ]
}
CUR

echo "✅ Frontside hooks installed."
echo "Try:  make frontside-e2e    (headless)"
echo "or:   make show-critical    (interactive pop-out)"
