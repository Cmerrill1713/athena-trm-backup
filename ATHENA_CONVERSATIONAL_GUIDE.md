# 🤖 ATHENA CONVERSATIONAL GUIDE

**Natural Language Operations for AI Republic Governance**

---

## OVERVIEW

Athena is your conversational AI assistant for AI Republic operations. Instead of memorizing CLI commands, you can now speak naturally about system operations.

### Key Capabilities
- **Natural Language Processing**: Understand plain English commands
- **Context Awareness**: Remembers conversation history and preferences
- **Confirmation Workflows**: Safe execution of sensitive operations
- **Multi-Modal Interface**: Text, voice, or hybrid interaction modes
- **Autonomous Operations**: Scheduled briefings and health monitoring

---

## CONVERSATIONAL COMMANDS

### Status & Health Checking
```
"How is the system running?"
"What's the current status?"
"Run a health check"
"Check system status"
"Is everything okay?"
```

### Log & Activity Review
```
"Show me the logs"
"What happened recently?"
"Recent activity"
"Check the activity feed"
"Show system events"
```

### Metrics & Performance
```
"What are the metrics?"
"Show performance stats"
"Compliance status"
"How's compliance today?"
"Tribunal count"
```

### Tribunal Management
```
"Check tribunal alerts"
"Are there any tribunals?"
"Show pending cases"
"Approve the tribunal"
"Release quarantines"
"Override tribunal decision"
"Escalate to council"
```

### Service Operations
```
"Restart services"
"Restart the system"
"Reboot services"
"Stop all services"
"Start services"
```

### Context & Memory
```
"Do that again"
"Repeat the last command"
"What did I just ask?"
"Go back"
"Previous results"
```

### Help & Information
```
"Help"
"What can you do?"
"Show commands"
"Available options"
"Command list"
```

---

## INTERACTION MODES

### 1. Text Conversation Mode
```bash
athena
# or
athena-chat
```

**Features:**
- Interactive text chat
- Command completion suggestions
- Conversation history
- Context awareness

**Example Session:**
```
🤖 Athena Ops Co-Pilot activated. Type 'quit' to exit.
You: how is the system running?
🤖 Everything's running smoothly. Compliance at 99.8%, 0 tribunals today.
You: show me the logs
🤖 Recent activity (5 entries):
  JUDICIAL VERDICT: ALLOW for op_user_query_123
  JUDICIAL VERDICT: WARN for op_policy_check_456
  ...
You: quit
🤖 Goodbye! The AI Republic continues operating autonomously.
```

### 2. Voice Conversation Mode
```bash
athena-voice --mode voice
```

**Requirements:**
```bash
pip install SpeechRecognition pyttsx3
# Ubuntu/Debian additional packages:
sudo apt install portaudio19-dev python3-pyaudio
```

**Features:**
- Speech-to-text input
- Text-to-speech responses
- Voice activity detection
- Ambient noise adjustment

**Example Session:**
```
🎤 ATHENA VOICE ASSISTANT - Voice Mode
Speak your commands naturally. Say 'quit' to exit.

🎤 Listening... (speak your command)
You said: "Check system status"
🤖 System status: All services operational, compliance at 99.7%, no active alerts.
🗣️ Speaking response...

🎤 Listening... (speak your command)
You said: "Quit"
🤖 Goodbye! The AI Republic continues operating.
```

### 3. Hybrid Mode (Text + Voice)
```bash
athena-voice --mode hybrid
```

**Features:**
- Type commands or say "voice mode"
- Switch between text and voice input
- Voice responses for voice commands
- Text responses for typed commands

**Example Session:**
```
🔄 ATHENA HYBRID ASSISTANT - Text & Voice Mode
Type commands or say 'voice mode' to speak

You (or 'voice mode' to speak): voice mode
🎤 Voice mode active - speak your command...
🎤 Heard: "Show me tribunal alerts"
🤖 No tribunal alerts currently active. System is operating within normal parameters.
🗣️ Speaking response...

You (or 'voice mode' to speak): show metrics
🤖 Current metrics: Compliance 99.7%, Tribunals today: 0, Uptime: up 2 days
```

### 4. Continuous Listening Mode
```bash
athena-voice --mode continuous
```

**Wake Words:** "Athena", "Hey Athena", "AI Republic", "System"

**Features:**
- Always listening for wake words
- Hands-free operation
- Background monitoring
- Instant response to commands

**Example Usage:**
```
🎤 CONTINUOUS LISTENING ACTIVE
Wake words: Athena, Hey Athena, AI Republic, System

🎤 Listening for command...
🗣️ Athena, check system status
🎤 Processing: check system status
🤖 System status: All services operational, compliance at 99.7%, no active alerts.
🗣️ Speaking response...
```

---

## CONFIRMATION WORKFLOWS

### Sensitive Operations
Athena requires explicit confirmation for high-impact actions:

#### Service Restart
```
You: restart services
🤖 Are you sure you want to restart AI Republic services? This will temporarily interrupt system operations.
You: yes
🤖 Confirmed. All AI Republic services restarted successfully.
```

#### Tribunal Actions
```
You: approve tribunal
🤖 Are you sure you want to approve tribunal? This will uphold the automated tribunal decision.
You: tell me more
🤖 Pending action: approve tribunal decision. Tribunal details: Agent gamma_core severity 0.83.
You: yes
🤖 Confirmed. Tribunal decision upheld for gamma_core.
```

### Confirmation Options
- **"yes" / "confirm" / "approve"**: Execute the action
- **"no" / "cancel" / "deny"**: Cancel the action
- **"tell me more" / "explain" / "details"**: Get more information before deciding

---

## CONTEXT AWARENESS

### Conversation Memory
Athena remembers your conversation context:

```
You: show me the logs
🤖 Recent activity (5 entries): [log entries shown]

You: do that again
🤖 Referring to your previous request: 'show me the logs' which resulted in: Recent activity (5 entries)...

You: what was the compliance rate?
🤖 Current metrics: Compliance 99.7%, Tribunals today: 0, Uptime: up 2 days
```

### Command History
Access previous commands and results:
- **"do that again"**: Repeat last command
- **"what did I just ask?"**: Show last command
- **"previous results"**: Show last response

### Smart Suggestions
Athena suggests corrections for unrecognized commands:

```
You: show me the login
🤖 I'm not sure I understand that command. Did you mean: 'show me the logs', 'show metrics', 'check tribunals'?
```

---

## SCHEDULED OPERATIONS

### Automated Briefings
Athena provides regular status updates without prompting:

#### Daily Briefing
- **Time**: 9:00 AM (configurable)
- **Days**: Monday-Friday (configurable)
- **Content**: Full system status summary

#### Startup Briefing
- **Trigger**: 60 seconds after system boot
- **Content**: Post-boot system verification
- **Purpose**: Confirm successful initialization

#### Health Monitoring
- **Frequency**: Every hour
- **Trigger**: Only when status changes to WARNING/CRITICAL
- **Content**: Alert-focused summary

### Configuration
Edit `/etc/ai-republic/athena_schedule.json`:
```json
{
  "daily_briefing": "09:00",
  "startup_delay": 60,
  "health_check_interval": 3600,
  "briefing_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
  "timezone": "UTC"
}
```

### Managing Schedules
```bash
# Enable scheduled briefings
sudo systemctl enable athena-scheduler
sudo systemctl start athena-scheduler

# Check schedule status
sudo systemctl status athena-scheduler

# View schedule logs
journalctl -u athena-scheduler --since "1 hour ago"
```

---

## ADVANCED FEATURES

### Custom Commands
Extend Athena by modifying `athena_conversation_engine.py`:

```python
def execute_command(self, command: str) -> str:
    # Add custom command handling
    if "custom action" in command:
        return "Custom action executed"
    # ... existing commands
```

### Voice Customization
Configure voice settings in `athena_voice_integration.py`:

```python
# Voice selection
voices = engine.getProperty('voices')
for voice in voices:
    if 'female' in voice.name.lower():
        engine.setProperty('voice', voice.id)

# Voice parameters
engine.setProperty('rate', 180)  # Speed
engine.setProperty('volume', 0.8)  # Volume
```

### Integration APIs
Athena can be integrated with external systems:

```python
from athena_conversation_engine import AthenaConversationEngine

# Create instance
athena = AthenaConversationEngine()

# Process commands programmatically
response = athena.process_input("check system status")
print(response)

# Access underlying systems
status = athena.conversation_engine.copilot.perform_health_check()
```

---

## TROUBLESHOOTING

### Common Issues

#### "Voice capabilities not available"
```bash
# Install voice libraries
pip install SpeechRecognition pyttsx3 pyaudio

# Test voice setup
python3 /opt/ai-republic/athena_voice_integration.py --setup
```

#### "Command not recognized"
- Try rephrasing: "How is the system?" instead of "System status?"
- Use help: Type "help" or "what can you do?"
- Check suggestions for similar commands

#### "Service restart failed"
- Confirm you have sudo privileges
- Check systemctl status for error details
- Verify AI Republic services are installed

#### Voice Recognition Issues
```bash
# Check microphone access
python3 -c "import speech_recognition as sr; print('Microphone available')"

# Test recognition
python3 /opt/ai-republic/athena_voice_integration.py --mode voice
# Speak clearly and check for background noise
```

#### Scheduled Briefings Not Working
```bash
# Check scheduler service
sudo systemctl status athena-scheduler

# Test manual briefing
python3 /opt/ai-republic/athena_copilot_scheduler.py --mode test-daily

# Verify configuration
cat /etc/ai-republic/athena_schedule.json
```

### Performance Tuning

#### Response Time Optimization
- Reduce voice processing for faster text responses
- Cache frequent status checks
- Optimize intent classification patterns

#### Memory Management
- Limit conversation history (default: 20 commands)
- Clear old context data periodically
- Monitor memory usage in long sessions

---

## SECURITY CONSIDERATIONS

### Access Control
- Athena runs with ai-republic user permissions
- Voice commands logged for audit trails
- Sensitive operations require explicit confirmation
- All interactions timestamped and traceable

### Data Privacy
- Commands and responses logged locally
- No external data transmission by default
- Voice data processed locally (not sent to cloud services)
- Conversation history retained for context only

### Operational Boundaries
- Athena cannot override constitutional decisions
- Tribunal actions logged and auditable
- Service operations require appropriate permissions
- All automated actions are reversible

---

## COMMAND REFERENCE

### Quick Reference Table

| Intent | Example Commands | Response Type |
|--------|------------------|---------------|
| Status | "system status", "how are things" | Status briefing |
| Logs | "show logs", "recent activity" | Activity summary |
| Metrics | "performance metrics", "compliance" | Statistics display |
| Tribunals | "check tribunals", "approve case" | Alert management |
| Services | "restart services" | Confirmation workflow |
| Context | "do that again", "previous" | History access |
| Help | "help", "commands" | Command guidance |

### Voice-Specific Commands
- **"Voice mode"**: Switch to voice input (hybrid mode)
- **"Text mode"**: Switch to text input (hybrid mode)
- **"Stop listening"**: End continuous listening mode

### Exit Commands
- **"quit"**, **"exit"**, **"bye"**, **"goodbye"**: End conversation
- **Ctrl+C**: Force exit (any mode)

---

**Athena transforms complex AI Republic operations into natural conversation, making constitutional governance accessible while maintaining full operational integrity and security.**

*Ready to speak with your AI Republic? Just say "Athena, check system status."* 🤖💬
