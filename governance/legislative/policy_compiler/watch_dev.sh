#!/usr/bin/env bash
# AI Republic Development Watch Mode
# ================================
#
# Automatically rebuild frontend when files change
# Run tests when backend files change
#
# Usage:
#   ./watch_dev.sh              # Watch all changes
#   ./watch_dev.sh --frontend   # Watch only frontend
#   ./watch_dev.sh --backend    # Watch only backend
#   ./watch_dev.sh --test       # Watch only test files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WATCH_FRONTEND="${WATCH_FRONTEND:-true}"
WATCH_BACKEND="${WATCH_BACKEND:-true}"
WATCH_TESTS="${WATCH_TESTS:-true}"
QUIET="${QUIET:-false}"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --frontend)
      WATCH_FRONTEND=true
      WATCH_BACKEND=false
      WATCH_TESTS=false
      shift
      ;;
    --backend)
      WATCH_FRONTEND=false
      WATCH_BACKEND=true
      WATCH_TESTS=false
      shift
      ;;
    --test)
      WATCH_FRONTEND=false
      WATCH_BACKEND=false
      WATCH_TESTS=true
      shift
      ;;
    --quiet)
      QUIET=true
      shift
      ;;
    -h|--help)
      echo "AI Republic Development Watch Mode"
      echo "=================================="
      echo ""
      echo "Automatically rebuild and test when files change."
      echo ""
      echo "Usage:"
      echo "  $0                    # Watch all changes"
      echo "  $0 --frontend        # Watch only SwiftUI files"
      echo "  $0 --backend         # Watch only Python backend"
      echo "  $0 --test            # Watch only test files"
      echo "  $0 --quiet           # Suppress verbose output"
      echo ""
      echo "Watch patterns:"
      echo "  Frontend: *.swift, *.xcodeproj, Package.swift"
      echo "  Backend:  *.py (excluding tests)"
      echo "  Tests:    burn_in_*.py, spikes.py, triggers.py"
      echo ""
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use -h for help"
      exit 1
      ;;
  esac
done

echo -e "${BLUE}👀 AI Republic Watch Mode Started${NC}"
echo "================================="
echo ""
echo "Watching for changes..."
if [[ "$WATCH_FRONTEND" == "true" ]]; then
  echo "  ✅ Frontend (SwiftUI)"
fi
if [[ "$WATCH_BACKEND" == "true" ]]; then
  echo "  ✅ Backend (Python)"
fi
if [[ "$WATCH_TESTS" == "true" ]]; then
  echo "  ✅ Tests (Burn-in)"
fi
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop watching${NC}"
echo ""

# Create temp files for tracking
LAST_FRONTEND_BUILD="/tmp/ar_watch_frontend_$$"
LAST_BACKEND_CHANGE="/tmp/ar_watch_backend_$$"
LAST_TEST_CHANGE="/tmp/ar_watch_test_$$"

touch "$LAST_FRONTEND_BUILD"
touch "$LAST_BACKEND_CHANGE"
touch "$LAST_TEST_CHANGE"

cleanup() {
  echo ""
  echo -e "${BLUE}🛑 Watch mode stopped${NC}"
  rm -f "$LAST_FRONTEND_BUILD" "$LAST_BACKEND_CHANGE" "$LAST_TEST_CHANGE"
  exit 0
}

trap cleanup SIGINT SIGTERM

# Main watch loop
while true; do
  sleep 2

  # Check frontend changes
  if [[ "$WATCH_FRONTEND" == "true" ]]; then
    if find NeuroForgeApp -name "*.swift" -o -name "*.xcodeproj" -o -name "Package.swift" \
         -newer "$LAST_FRONTEND_BUILD" 2>/dev/null | grep -q .; then
      echo -e "${GREEN}🔄 Frontend changes detected, rebuilding...${NC}"
      if [[ "$QUIET" != "true" ]]; then
        make frontend
      else
        make frontend >/dev/null 2>&1
        echo -e "${GREEN}✅ Frontend rebuilt${NC}"
      fi
      touch "$LAST_FRONTEND_BUILD"
    fi
  fi

  # Check backend changes
  if [[ "$WATCH_BACKEND" == "true" ]]; then
    if find . -name "*.py" -not -path "./test*" -not -path "./tests/*" \
         -not -name "*test*.py" -not -name "burn_in*.py" -not -name "spikes.py" \
         -not -name "triggers.py" -newer "$LAST_BACKEND_CHANGE" 2>/dev/null | grep -q .; then
      echo -e "${BLUE}🔄 Backend changes detected${NC}"
      if [[ "$QUIET" != "true" ]]; then
        echo -e "${BLUE}💡 Consider restarting backend services if needed${NC}"
      fi
      touch "$LAST_BACKEND_CHANGE"
    fi
  fi

  # Check test changes
  if [[ "$WATCH_TESTS" == "true" ]]; then
    if find . -name "burn_in*.py" -o -name "spikes.py" -o -name "triggers.py" \
         -newer "$LAST_TEST_CHANGE" 2>/dev/null | grep -q .; then
      echo -e "${YELLOW}🧪 Test changes detected, running tests...${NC}"
      if [[ "$QUIET" != "true" ]]; then
        make test
      else
        make test >/dev/null 2>&1
        echo -e "${GREEN}✅ Tests completed${NC}"
      fi
      touch "$LAST_TEST_CHANGE"
    fi
  fi
done
