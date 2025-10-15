#!/usr/bin/env bash
# Athena Control Menu - Simple number-driven interface
# No flags, no memory required - just pick a number

set -euo pipefail

ROOT="${ATHENA_ROOT:-$HOME/Documents/GitHub}"
cd "$ROOT" 2>/dev/null || true

banner() {
    printf "\n\033[1;32m╔════════════════════════════════════════╗\n"
    printf "║     ATHENA CONTROL MENU                ║\n"
    printf "╚════════════════════════════════════════╝\033[0m\n"
}

pause() {
    read -r -p $'\n\033[1;33mPress [Enter] to continue...\033[0m'
}

need() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "❌ Missing: $1"
        exit 1
    }
}

run() {
    echo -e "\n\033[1;34m$ $*\033[0m"
    eval "$@"
}

# Option 1: Status (speaks + report)
status() {
    echo "🔍 Running quick health check..."
    run "make green 2>&1 || echo '⚠️ Some services not running'"
    echo ""
    echo "📊 Running daily ops check (90s)..."
    run "make daily-ops 2>&1 || echo '⚠️ Some checks pending'"
}

# Option 2: Use Vision
vision() {
    echo ""
    read -r -p "📸 Image path: " IMG
    read -r -p "💬 Ask Athena: " Q

    if [[ -z "${IMG// }" ]]; then
        echo "❌ No image provided"
        return
    fi

    if [[ -z "${Q// }" ]]; then
        Q="Describe this image"
    fi

    run "python3 scripts/athena_vision.py \"$IMG\" \"$Q\" --report 2>&1 || echo '⚠️ Vision failed'"
}

# Option 3: Start / Go Live
go_live() {
    echo "🚀 Starting full stack (monitoring + FastVLM)..."
    run "make fastvlm-go-live"
}

# Option 4: Enable canary
canary_on() {
    echo ""
    read -r -p "🐤 Canary model name: " M

    if [[ -z "${M// }" ]]; then
        echo "❌ No model provided"
        return
    fi

    echo "Enabling canary at 10%..."
    run "make canary-10 CANARY_MODEL=\"$M\""
    echo ""
    echo "⚠️  Don't forget to activate:"
    echo "   source /tmp/canary.env"
    echo ""
    run "make canary-status || true"
}

# Option 5: Canary evaluate / auto-promote
canary_eval() {
    echo "📊 Evaluating canary vs control (statistical)..."
    run "make canary-eval 2>&1 || echo '⚠️ Evaluation incomplete'"
    echo ""
    echo "🎯 Checking if auto-promotion triggered..."
    run "make canary-auto-promote 2>&1 || echo '⏳ Continue monitoring'"
}

# Option 6: Rollback canary
rollback() {
    echo "🚨 Rolling back canary to control..."
    run "make canary-rollback"
    echo ""
    echo "⚠️  Don't forget to activate:"
    echo "   source /tmp/canary.env"
}

# Option 7: View logs
logs() {
    echo "📋 Latest logs (tail 60 lines each):"

    for f in /tmp/fastvlm_server.log /tmp/fastvlm_watchdog.log logs/auto_promotion.log logs/evolution.log; do
        if [[ -f "$f" ]]; then
            echo -e "\n\033[1;36m--- $f ---\033[0m"
            tail -n 60 "$f"
        fi
    done
}

# Option 8: PANIC button
panic() {
    echo ""
    echo "🔴 PANIC MODE - Stopping everything and rolling back..."
    echo ""

    run "make canary-rollback 2>&1 || echo 'Canary already off'"
    run "make fastvlm-down 2>&1 || echo 'FastVLM already stopped'"
    run "make fastvlm-logrotate 2>&1 || echo 'Logs rotated'"

    echo ""
    echo "✅ System stopped and rolled back"
    echo "   Run option [3] to restart when ready"
}

# Option 9: Lineage
lineage() {
    echo "🌳 Generating model lineage..."
    run "make lineage-tree 2>&1 || echo '⚠️ No lineage data yet'"
}

# Option 0: Advanced menu
advanced_menu() {
    while true; do
        echo ""
        echo "╔════════════════════════════════════════╗"
        echo "║     ADVANCED OPTIONS                   ║"
        echo "╚════════════════════════════════════════╝"
        cat <<'EOF'
[a] Validate green (pre-tag)
[b] Tag as v0.9.1-green
[c] Seed Weaviate
[d] E2E full sweep
[e] Learning stats
[f] Crash recovery test
[g] Smoke tests (6 images)
[h] Circuit breaker status
[i] Promotion status
[0] Back to main menu
EOF
        read -r -p $'\nChoose: ' CH
        case "$CH" in
            a) run "make validate-green"; pause;;
            b) run "make tag-green && git push --tags"; pause;;
            c) run "make weaviate-seed"; pause;;
            d) run "make e2e-sweep"; pause;;
            e) run "make learn-stats"; pause;;
            f) run "make fastvlm-crash-test"; pause;;
            g) run "make fastvlm-smoke"; pause;;
            h) run "make breaker-status"; pause;;
            i) run "make canary-promotion-status"; pause;;
            0) return;;
            *) echo "Invalid."; sleep 0.6;;
        esac
    done
}

# Main menu
menu() {
    while true; do
        banner
        cat <<'EOF'
[1] 🔍 Status (quick health + daily ops)
[2] 🖼️  Use Vision (ask about an image)
[3] 🚀 Start / Go Live
[4] 🐤 Canary: enable 10%
[5] 📊 Canary: evaluate / auto-promote
[6] 🚨 Rollback canary
[7] 📋 View logs
[8] 🔴 PANIC (stop + rollback)
[9] 🌳 Model lineage
[0] ⚙️  Advanced options
[q] Quit
EOF
        read -r -p $'\n\033[1;33mChoose 1-9, 0, or q: \033[0m' CH

        case "$CH" in
            1) status; pause;;
            2) vision; pause;;
            3) go_live; pause;;
            4) canary_on; pause;;
            5) canary_eval; pause;;
            6) rollback; pause;;
            7) logs; pause;;
            8) panic; pause;;
            9) lineage; pause;;
            0) advanced_menu;;
            q|Q) echo -e "\n👋 Goodbye!"; exit 0;;
            *) echo "❌ Invalid choice"; sleep 0.6;;
        esac
    done
}

# Check dependencies
need make

# Launch
menu
