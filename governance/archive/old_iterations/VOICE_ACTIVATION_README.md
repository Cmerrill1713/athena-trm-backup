# 🎤 Athena Voice Activation

Voice-controlled command interface for Athena's AI Republic. Enables hands-free control through natural speech commands.

## 🌟 Features

- **Wake Word Detection**: Responds to "Hey Athena", "Athena", "Computer", "Bridge"
- **Voice Command Processing**: Natural language command routing
- **Voice Macros**: Optimized commands for common operations
- **Security Integration**: Respects all authorization levels and Touch ID
- **Background Operation**: Continuous listening without blocking other operations
- **Error Recovery**: Robust handling of audio issues and recognition failures
- **Audit Trail**: All voice commands logged with timestamps

## 🛠️ Installation

### Prerequisites

```bash
# macOS audio framework
brew install portaudio

# Python audio libraries
pip install SpeechRecognition PyAudio pyobjc

# Optional: Voice responses
pip install pyttsx3
```

### Microphone Permissions

Enable microphone access for Python:

1. **System Settings** → **Privacy & Security** → **Microphone**
2. ✅ Check **Python** (or your Python executable)

### Quick Deploy

```bash
# Run deployment script
chmod +x deploy_voice_activation.sh
./deploy_voice_activation.sh
```

## 🎯 Usage

### Basic Operation

```python
# Start voice activation
from athena_notifications import initialize_voice_activation
initialize_voice_activation()

# Or run directly
python3 voice_activation.py --start
```

### Voice Commands

| Voice Command | Action | Description |
|---------------|--------|-------------|
| "Hey Athena, status" | System status check | Shows health and metrics |
| "Hey Athena, meeting mode" | Meeting mode activation | Quiets alerts, routes critical to phone |
| "Hey Athena, emergency" | Emergency mode | All alerts to phone, max priority |
| "Hey Athena, normal ops" | Normal operations | Returns to default alert routing |
| "Hey Athena, quiet mode" | Quiet mode (30 min) | Suppresses non-critical alerts |
| "Hey Athena, route to phone" | Alert routing | Routes critical alerts to phone |
| "Hey Athena, acknowledge all" | Clear alerts | Acknowledges all pending alerts |

### Stop Commands

- **"Hey Athena, stop listening"** - Deactivates voice mode
- **Ctrl+C** - Stops the service

## 🎭 Voice Macros

Pre-configured voice shortcuts for smoother interaction:

```python
voice_macros = {
    "meeting mode": "meeting mode",
    "emergency": "emergency mode",
    "normal ops": "normal mode",
    "status": "check system status",
    "quiet mode": "quiet for 30 minutes",
    "maintenance mode": "maintenance mode",
    "route to phone": "route critical to phone",
    "acknowledge all": "ack all",
    "clear alerts": "ack all"
}
```

## 🧪 Testing

### Component Tests

```bash
# Basic speech recognition
python3 demo_voice_activation.py --basic

# Wake word detection
python3 demo_voice_activation.py --wake

# Command processing
python3 demo_voice_activation.py --commands

# Voice responses
python3 demo_voice_activation.py --responses

# Complete interaction flow
python3 demo_voice_activation.py --full

# Error handling scenarios
python3 demo_voice_activation.py --errors
```

### Service Tests

```bash
# Test voice activation service
python3 voice_activation.py --test

# Test notification integration
python3 athena_notifications.py --test desktop
```

## 🔧 Configuration

### Voice Settings

```python
# In voice_activation.py
self.wake_words = ["hey athena", "athena", "computer", "bridge"]
self.energy_threshold = 300          # Adjust for noisy environments
self.pause_threshold = 0.8           # Seconds of silence before processing
self.listen_timeout = 5              # Max seconds to listen
```

### Audio Quality Tuning

- **Noisy Environment**: Increase `energy_threshold`
- **Slow Recognition**: Decrease `pause_threshold`
- **Quick Commands**: Reduce `listen_timeout`
- **Multiple Users**: Add more wake words

## 🛡️ Security & Privacy

### Authorization Levels

Voice commands respect the same authorization system as text commands:

- **Level 1**: Basic status commands
- **Level 2**: Alert management, quiet modes
- **Level 3**: System control, emergency modes (requires Touch ID)
- **Level 4**: Configuration changes (requires explicit confirmation)

### Privacy Features

- **Local Processing**: All speech recognition happens locally
- **No Cloud Services**: No external API calls for voice processing
- **Secure Storage**: Commands logged in encrypted audit trail
- **Wake Word Required**: Prevents accidental activation

### Audit Trail

All voice interactions are logged:

```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "type": "voice_command",
  "command": "meeting mode",
  "recognized_text": "hey athena meeting mode",
  "confidence": 0.92,
  "authorized": true,
  "result": "success"
}
```

## 🚀 Advanced Features

### Contextual Responses

- **Driving**: Short, clear responses
- **Meeting**: Silent confirmations
- **Normal**: Full voice feedback

### Multi-Wake Words

```python
# Add custom wake words
self.wake_words = ["hey athena", "computer", "bridge", "system"]
```

### Voice Profiles

Different response styles based on context:

```python
# Driving mode - minimal responses
if context == "driving":
    speak("Done")  # Short confirmation

# Office mode - detailed responses
elif context == "office":
    speak("Meeting mode activated. Alerts quieted for 60 minutes.")
```

## 🔧 Troubleshooting

### Common Issues

**"SpeechRecognition not available"**
```bash
pip install SpeechRecognition PyAudio pyobjc
```

**"Microphone access denied"**
- System Settings → Privacy & Security → Microphone → Enable Python

**"Wake word not detected"**
- Check microphone volume and background noise
- Adjust `energy_threshold` in configuration
- Test with `demo_voice_activation.py --basic`

**"Commands not recognized"**
- Speak clearly and at normal volume
- Try shorter commands first
- Check audio quality with `--basic` test

**"Voice responses not working"**
```bash
pip install pyttsx3
```
- Or disable TTS for text-only responses

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Service Logs

Check launchd logs:
```bash
tail -f /tmp/athena_voice.out
tail -f /tmp/athena_voice.err
```

## 📊 Performance

### Resource Usage

- **CPU**: Minimal (< 5% when idle, spikes during recognition)
- **Memory**: ~50MB resident
- **Storage**: Minimal (logs only)

### Response Times

- **Wake Word**: < 0.5 seconds
- **Command Processing**: < 2 seconds
- **Voice Response**: < 1 second

## 🔄 Integration

### With Command Router

Voice commands integrate seamlessly with the existing command system:

```python
# Voice → Router → Handler → Response
"Hey Athena, status" → parse_intent() → status_handler() → speak_response()
```

### With Notifications

Voice activation works with all notification channels:

- Alerts can trigger voice announcements
- Commands can control notification routing
- Status updates can be spoken

### With Dashboard

Voice commands sync with the SwiftUI dashboard:

- Commands update dashboard state
- Alerts appear in both voice and UI
- Settings can be controlled by voice

## 🌟 Examples

### Daily Usage

```bash
# Morning briefing
"Hey Athena, status"
→ "System healthy, all services running"

# During meeting
"Hey Athena, meeting mode"
→ "Meeting mode activated. Alerts quieted and critical notifications routed to phone."

# Emergency response
"Hey Athena, emergency"
→ "Emergency mode activated. All alerts now routed to phone."
```

### Advanced Scenarios

```bash
# Complex operations
"Hey Athena, route to phone"
→ Routes critical alerts to phone

# Acknowledgment
"Hey Athena, acknowledge all"
→ Clears all pending alerts

# Mode switching
"Hey Athena, normal ops"
→ Returns to default operation mode
```

---

## 🎯 Next Steps

- **Macro Expansion**: Add custom voice macros for workflows
- **Context Awareness**: Adapt responses based on location/time
- **Federation Commands**: Voice control across multiple AI nodes
- **Voice Learning**: Improve recognition based on usage patterns

**Voice activation transforms Athena from "system you control" to "intelligent assistant you speak with naturally."** 🎤🤖
