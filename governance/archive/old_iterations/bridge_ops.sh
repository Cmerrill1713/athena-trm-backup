#!/usr/bin/env bash
#
# NeuroForge Bridge Ops - Quick operator commands
# Usage: ./scripts/bridge_ops.sh [start|stop|restart|smoke|slo|chaos|real|mock]
#

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

case "${1:-help}" in
    start|up)
        echo "🚀 Starting bridge (mock mode)"
        make bridge-up
        ;;

    stop|down)
        echo "🛑 Stopping bridge"
        make bridge-down
        ;;

    restart)
        echo "🔄 Restarting bridge"
        make bridge-down
        sleep 2
        make bridge-up
        ;;

    smoke)
        echo "🧪 Running smoke tests"
        make bridge-smoke
        ;;

    slo)
        echo "📊 Running SLO checks"
        make bridge-slo
        ;;

    chaos)
        echo "💥 Running chaos test"
        make bridge-chaos
        ;;

    real)
        echo "🔗 Starting bridge (real backends)"
        make bridge-down
        USE_MOCK=0 UAT_BASE=http://127.0.0.1:8080 ATHENA_BASE=http://127.0.0.1:8090 make bridge-up
        make bridge-smoke
        ;;

    mock)
        echo "🎭 Starting bridge (mock mode)"
        make bridge-down
        USE_MOCK=1 make bridge-up
        make bridge-smoke
        ;;

    app)
        echo "📱 Launching app"
        cd NeuroForgeApp
        API_BASE=http://127.0.0.1:8014 QA_MODE=1 EVO_SUGGESTIONS=0 swift run
        ;;

    full)
        echo "🎯 Full stack (bridge + app)"
        make bridge-all
        ;;

    help|*)
        cat <<'EOF'
NeuroForge Bridge Operations
============================

Quick commands:
  ./scripts/bridge_ops.sh start     Start bridge (mock mode)
  ./scripts/bridge_ops.sh stop      Stop bridge
  ./scripts/bridge_ops.sh restart   Restart bridge
  ./scripts/bridge_ops.sh smoke     Run smoke tests
  ./scripts/bridge_ops.sh slo       Check SLO (p95 < 250ms)
  ./scripts/bridge_ops.sh chaos     Run chaos test
  ./scripts/bridge_ops.sh real      Start with real backends
  ./scripts/bridge_ops.sh mock      Start with mock data
  ./scripts/bridge_ops.sh app       Launch NeuroForge app
  ./scripts/bridge_ops.sh full      Start bridge + app

EOF
        ;;
esac
