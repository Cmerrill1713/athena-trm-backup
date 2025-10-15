#!/usr/bin/env bash
# Notification Handler - Multi-platform webhooks
# Supports: Slack, Discord, Telegram, Generic webhooks

set -euo pipefail

# Configuration
NOTIFY_PLATFORM="${NOTIFY_PLATFORM:-}"
NOTIFY_WEBHOOK="${NOTIFY_WEBHOOK:-}"
NOTIFY_TOKEN="${NOTIFY_TOKEN:-}"       # For Telegram
NOTIFY_CHAT_ID="${NOTIFY_CHAT_ID:-}"   # For Telegram

# Colors for different platforms
STATUS_COLORS() {
    case "$1" in
        success) echo "#00ff00" ;;  # Green
        warning) echo "#ffa500" ;;  # Orange
        error)   echo "#ff0000" ;;  # Red
        info)    echo "#0099ff" ;;  # Blue
        *) echo "#888888" ;;         # Gray
    esac
}

STATUS_EMOJI() {
    case "$1" in
        success) echo "✅" ;;
        warning) echo "⚠️" ;;
        error)   echo "❌" ;;
        info)    echo "ℹ️" ;;
        *) echo "🔔" ;;
    esac
}

# Send to Slack
notify_slack() {
    local message="$1"
    local status="${2:-info}"
    local emoji=$(STATUS_EMOJI "$status")
    local color=$(STATUS_COLORS "$status")

    curl -s -X POST "$NOTIFY_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d @- << EOF > /dev/null
{
    "username": "Stack Watchdog",
    "icon_emoji": ":robot_face:",
    "attachments": [{
        "color": "$color",
        "text": "$emoji $message",
        "footer": "Stack Orchestration",
        "ts": $(date +%s)
    }]
}
EOF
}

# Send to Discord
notify_discord() {
    local message="$1"
    local status="${2:-info}"
    local emoji=$(STATUS_EMOJI "$status")
    local color_dec

    # Convert hex to decimal for Discord
    case "$status" in
        success) color_dec=65280 ;;   # Green
        warning) color_dec=16753920 ;; # Orange
        error)   color_dec=16711680 ;;  # Red
        info)    color_dec=39423 ;;     # Blue
        *) color_dec=8947848 ;;         # Gray
    esac

    curl -s -X POST "$NOTIFY_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d @- << EOF > /dev/null
{
    "username": "Stack Watchdog",
    "avatar_url": "https://cdn-icons-png.flaticon.com/512/4712/4712035.png",
    "embeds": [{
        "title": "🤖 Stack Orchestration",
        "description": "$emoji $message",
        "color": $color_dec,
        "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    }]
}
EOF
}

# Send to Telegram
notify_telegram() {
    local message="$1"
    local status="${2:-info}"
    local emoji=$(STATUS_EMOJI "$status")

    if [[ -z "$NOTIFY_TOKEN" ]] || [[ -z "$NOTIFY_CHAT_ID" ]]; then
        echo "Error: NOTIFY_TOKEN and NOTIFY_CHAT_ID required for Telegram" >&2
        return 1
    fi

    local url="https://api.telegram.org/bot${NOTIFY_TOKEN}/sendMessage"

    curl -s -X POST "$url" \
        -H "Content-Type: application/json" \
        -d @- << EOF > /dev/null
{
    "chat_id": "$NOTIFY_CHAT_ID",
    "text": "🤖 *Stack Watchdog*\n\n$emoji $message",
    "parse_mode": "Markdown"
}
EOF
}

# Send to generic webhook (JSON POST)
notify_generic() {
    local message="$1"
    local status="${2:-info}"
    local emoji=$(STATUS_EMOJI "$status")

    curl -s -X POST "$NOTIFY_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d @- << EOF > /dev/null
{
    "message": "$emoji $message",
    "status": "$status",
    "service": "stack-watchdog",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "hostname": "$(hostname)"
}
EOF
}

# Main notification dispatcher
send_notification() {
    local message="$1"
    local status="${2:-info}"

    # Skip if no webhook configured
    if [[ -z "$NOTIFY_WEBHOOK" ]] && [[ -z "$NOTIFY_TOKEN" ]]; then
        return 0
    fi

    # Auto-detect platform if not specified
    if [[ -z "$NOTIFY_PLATFORM" ]]; then
        if [[ "$NOTIFY_WEBHOOK" == *"slack.com"* ]]; then
            NOTIFY_PLATFORM="slack"
        elif [[ "$NOTIFY_WEBHOOK" == *"discord.com"* ]]; then
            NOTIFY_PLATFORM="discord"
        elif [[ -n "$NOTIFY_TOKEN" ]]; then
            NOTIFY_PLATFORM="telegram"
        else
            NOTIFY_PLATFORM="generic"
        fi
    fi

    # Send to platform
    case "$NOTIFY_PLATFORM" in
        slack)
            notify_slack "$message" "$status"
            ;;
        discord)
            notify_discord "$message" "$status"
            ;;
        telegram)
            notify_telegram "$message" "$status"
            ;;
        generic|*)
            notify_generic "$message" "$status"
            ;;
    esac

    return 0
}

# CLI interface
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ $# -lt 1 ]]; then
        echo "Usage: $0 <message> [status]"
        echo ""
        echo "Status: success, warning, error, info (default: info)"
        echo ""
        echo "Environment variables:"
        echo "  NOTIFY_WEBHOOK   - Webhook URL (Slack/Discord/Generic)"
        echo "  NOTIFY_PLATFORM  - Platform: slack, discord, telegram, generic (auto-detect if not set)"
        echo "  NOTIFY_TOKEN     - Bot token (Telegram only)"
        echo "  NOTIFY_CHAT_ID   - Chat ID (Telegram only)"
        echo ""
        echo "Examples:"
        echo "  # Slack"
        echo "  export NOTIFY_WEBHOOK='https://hooks.slack.com/services/YOUR/WEBHOOK/URL'"
        echo "  $0 'Stack recovered successfully' success"
        echo ""
        echo "  # Discord"
        echo "  export NOTIFY_WEBHOOK='https://discord.com/api/webhooks/YOUR/WEBHOOK'"
        echo "  $0 'Service restarted' warning"
        echo ""
        echo "  # Telegram"
        echo "  export NOTIFY_TOKEN='YOUR_BOT_TOKEN'"
        echo "  export NOTIFY_CHAT_ID='YOUR_CHAT_ID'"
        echo "  $0 'Auto-heal triggered' error"
        exit 1
    fi

    send_notification "$1" "${2:-info}"
fi
