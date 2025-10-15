#!/bin/bash
# Emergency Rollback Playbook for v0.9.2
# Run this if something goes wrong after shipping

set -euo pipefail

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║           🚨  ROLLBACK PLAYBOOK v0.9.2  🚨                   ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

PS3="Select rollback action: "
options=("Restart Services" "Reset Bandit State" "Restore State Snapshot" "Check Logs" "Exit")

select opt in "${options[@]}"
do
    case $opt in
        "Restart Services")
            echo ""
            echo "🔄 Restarting all services..."
            cd AI-Projects/universal-ai-tools
            docker-compose down
            make green
            echo "✅ Services restarted"
            echo ""
            ;;
        "Reset Bandit State")
            echo ""
            echo "🔄 Resetting bandit state..."
            cd AI-Projects/universal-ai-tools
            if [ -f "state/bandit.json" ]; then
                cp state/bandit.json state/bandit.backup.$(date +%s).json
                echo '{}' > state/bandit.json
                echo "✅ Bandit state reset (backup created)"
            else
                echo "⚠️  No bandit.json found"
            fi
            cd ../..
            echo ""
            ;;
        "Restore State Snapshot")
            echo ""
            echo "🔄 Restoring state from v0.9.2 snapshot..."
            if [ -f "releases/v0.9.2/bandit.launch.json" ]; then
                cp releases/v0.9.2/bandit.launch.json AI-Projects/universal-ai-tools/state/bandit.json
                echo "✅ Bandit state restored"
            fi
            if [ -f "releases/v0.9.2/telemetry.launch.sqlite" ]; then
                cp releases/v0.9.2/telemetry.launch.sqlite AI-Projects/universal-ai-tools/state/telemetry.sqlite
                echo "✅ Telemetry restored"
            fi
            echo ""
            ;;
        "Check Logs")
            echo ""
            echo "📋 Recent service logs:"
            echo ""
            echo "=== RAG Service ==="
            tail -20 /tmp/rag_service.log 2>/dev/null || echo "No logs"
            echo ""
            echo "=== Vision RAG ==="
            tail -20 /tmp/vision_rag.log 2>/dev/null || echo "No logs"
            echo ""
            echo "=== Dashboard ==="
            tail -20 /tmp/dashboard.log 2>/dev/null || echo "No logs"
            echo ""
            echo "=== Eval API ==="
            tail -20 /tmp/eval.log 2>/dev/null || echo "No logs"
            echo ""
            ;;
        "Exit")
            echo ""
            echo "👋 Exiting rollback playbook"
            break
            ;;
        *) echo "Invalid option $REPLY";;
    esac
done

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              📞  ESCALATION CONTACTS  📞                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "GitHub Issues: https://github.com/Cmerrill1713/athena-trm-backup/issues"
echo "Documentation: POST_LAUNCH_7DAY_PLAN.md"
echo ""
