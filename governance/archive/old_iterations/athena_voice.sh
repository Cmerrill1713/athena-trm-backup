#!/usr/bin/env bash
# Athena Voice Trigger Script
# Talk to your infrastructure - Athena executes

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$(dirname "$0")" && pwd)}"
VOICE_MAP="${WORKSPACE_ROOT}/athena_voice_map.json"
ATHENA_BASE="${ATHENA_BASE:-http://127.0.0.1:8090}"
ATH_TOKEN="${ATH_TOKEN:-supersecret}"

# Audio settings
RECORD_SECONDS="${RECORD_SECONDS:-5}"
AUDIO_FILE="/tmp/athena_voice_input.wav"

# ============================================================================
# Check Dependencies
# ============================================================================

check_deps() {
    local missing=()
    
    # Check for audio recording
    if ! command -v sox &>/dev/null && ! command -v ffmpeg &>/dev/null; then
        missing+=("sox or ffmpeg (for audio)")
    fi
    
    # Check for jq
    if ! command -v jq &>/dev/null; then
        missing+=("jq (for JSON parsing)")
    fi
    
    # Check for whisper (optional but recommended)
    if ! command -v whisper &>/dev/null; then
        echo "⚠️  Whisper not found - will use Athena for transcription"
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo "❌ Missing dependencies:"
        printf '  - %s\n' "${missing[@]}"
        echo ""
        echo "Install with:"
        echo "  brew install sox jq"
        echo "  pip install openai-whisper"
        exit 1
    fi
}

# ============================================================================
# Audio Capture
# ============================================================================

record_audio() {
    echo "🎤 Listening... (${RECORD_SECONDS}s)"
    
    if command -v sox &>/dev/null; then
        # macOS with sox
        sox -d "$AUDIO_FILE" trim 0 "$RECORD_SECONDS" 2>/dev/null
    elif command -v ffmpeg &>/dev/null; then
        # Fallback to ffmpeg
        ffmpeg -f avfoundation -i ":0" -t "$RECORD_SECONDS" -y "$AUDIO_FILE" 2>/dev/null
    else
        echo "❌ No audio recording tool available"
        exit 1
    fi
    
    echo "✅ Audio captured"
}

# ============================================================================
# Transcription
# ============================================================================

transcribe_local() {
    if command -v whisper &>/dev/null; then
        whisper "$AUDIO_FILE" --model base.en --language en --output_format txt --output_dir /tmp >/dev/null 2>&1
        cat /tmp/athena_voice_input.txt 2>/dev/null || echo ""
    else
        echo ""
    fi
}

transcribe_athena() {
    # Use Athena's tool call to transcribe (if available)
    # This is a placeholder - implement based on your Athena capabilities
    echo ""
}

transcribe() {
    local text=$(transcribe_local)
    
    if [ -z "$text" ]; then
        text=$(transcribe_athena)
    fi
    
    echo "$text" | tr '[:upper:]' '[:lower:]' | sed 's/[[:punct:]]//g' | xargs
}

# ============================================================================
# Command Mapping & Execution
# ============================================================================

execute_command() {
    local spoken="$1"
    
    # Check if command exists in mapping
    if [ ! -f "$VOICE_MAP" ]; then
        echo "❌ Voice map not found: $VOICE_MAP"
        exit 1
    fi
    
    local cmd=$(jq -r --arg key "$spoken" '.[$key] // empty' "$VOICE_MAP")
    
    if [ -n "$cmd" ]; then
        echo "🧠 Athena: Executing '$spoken'"
        say_response "Executing: $spoken"
        
        # Execute the command
        echo "   Running: $cmd"
        eval "$cmd"
        
        say_response "Done"
    else
        echo "🤔 Command not mapped: $spoken"
        say_response "I don't recognize that command"
        
        # Show suggestions
        echo ""
        echo "Did you mean one of these?"
        jq -r 'keys[]' "$VOICE_MAP" | head -5
    fi
}

# ============================================================================
# Text-to-Speech Response
# ============================================================================

say_response() {
    local text="$1"
    
    if command -v say &>/dev/null; then
        # macOS
        say -v Samantha "$text"
    elif command -v spd-say &>/dev/null; then
        # Linux
        spd-say "$text"
    else
        # Fallback: just echo
        echo "🔊 Athena: $text"
    fi
}

# ============================================================================
# Main Loop
# ============================================================================

main() {
    check_deps
    
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  🧠 Athena Voice Control - Talk to Your Infrastructure    ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Available commands:"
    jq -r 'to_entries[] | "  • \"\(.key)\" → \(.value)"' "$VOICE_MAP" | head -10
    echo "  • (and more...)"
    echo ""
    echo "Press Ctrl+C to quit"
    echo ""
    
    say_response "Athena voice control active"
    
    while true; do
        echo ""
        echo "───────────────────────────────────────────────────────────"
        
        # Record audio
        record_audio
        
        # Transcribe
        echo "🧠 Transcribing..."
        spoken=$(transcribe)
        
        if [ -z "$spoken" ]; then
            say_response "I didn't catch that"
            continue
        fi
        
        echo "📝 You said: \"$spoken\""
        
        # Execute
        execute_command "$spoken"
        
        sleep 1
    done
}

# ============================================================================
# Entry Point
# ============================================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

