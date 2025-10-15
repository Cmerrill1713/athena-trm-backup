#!/usr/bin/env python3
"""
ATHENA VOICE INTEGRATION
Voice Input/Output capabilities for conversational AI Republic operations

Provides speech-to-text and text-to-speech integration for hands-free operation.
"""

import time
import queue
from typing import Optional

# Voice integration imports (optional - graceful degradation if not available)
VOICE_ENABLED = False
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_ENABLED = True
except ImportError:
    sr = None
    pyttsx3 = None

from athena_conversation_engine import AthenaConversationEngine

class VoiceProcessor:
    """Handles voice input/output processing"""

    def __init__(self):
        self.recognizer = None
        self.engine = None
        self.voice_enabled = VOICE_ENABLED

        if self.voice_enabled:
            try:
                self.recognizer = sr.Recognizer()
                self.engine = pyttsx3.init()

                # Configure voice settings
                voices = self.engine.getProperty('voices')
                if voices:
                    # Prefer female voice for Athena
                    female_voice = None
                    for voice in voices:
                        if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                            female_voice = voice
                            break
                    if female_voice:
                        self.engine.setProperty('voice', female_voice.id)

                self.engine.setProperty('rate', 180)  # Slightly slower for clarity
                self.engine.setProperty('volume', 0.8)

            except Exception as e:
                print(f"Voice initialization failed: {e}")
                self.voice_enabled = False
        else:
            print("Voice libraries not available. Install with: pip install SpeechRecognition pyttsx3")

    def listen_for_command(self, timeout: int = 5) -> Optional[str]:
        """Listen for voice command and convert to text"""
        if not self.voice_enabled:
            return None

        try:
            with sr.Microphone() as source:
                print("🎤 Listening... (speak your command)")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout)

                print("🔄 Processing speech...")
                text = self.recognizer.recognize_google(audio)
                print(f"📝 Heard: '{text}'")
                return text

        except sr.WaitTimeoutError:
            print("⏰ No speech detected within timeout")
            return None
        except sr.UnknownValueError:
            print("❓ Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"❌ Speech recognition service error: {e}")
            return None
        except Exception as e:
            print(f"❌ Voice input error: {e}")
            return None

    def speak_response(self, text: str):
        """Convert text response to speech"""
        if not self.voice_enabled:
            return

        try:
            print(f"🗣️ Speaking: {text[:100]}{'...' if len(text) > 100 else ''}")
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"❌ Speech output error: {e}")

class AthenaVoiceAssistant:
    """Voice-enabled Athena assistant with conversational capabilities"""

    def __init__(self, voice_enabled: bool = True):
        self.conversation_engine = AthenaConversationEngine()
        self.voice_processor = VoiceProcessor() if voice_enabled else None
        self.voice_enabled = voice_enabled and (self.voice_processor is not None)
        self.response_queue = queue.Queue()
        self.listening_active = False

        if self.voice_enabled:
            print("🎤 Voice capabilities enabled - you can speak commands to Athena")
        else:
            print("📝 Text-only mode - voice capabilities not available")

    def process_text_input(self, text: str) -> str:
        """Process text input and return response"""
        text_lower = text.lower().strip()

        # Handle alert acknowledgment commands
        ack_keywords = ['acknowledge', 'ack', 'acknowledged', 'confirm', 'got it', 'understood']
        if any(keyword in text_lower for keyword in ack_keywords):
            from athena_notifications import acknowledge_alert_by_voice

            # Try to acknowledge alerts
            acknowledged = acknowledge_alert_by_voice()
            if acknowledged:
                return f"✅ Alert{'s' if acknowledged > 1 else ''} acknowledged. Escalation stopped."
            else:
                return "No active alerts to acknowledge."

        # Handle other commands
        response = self.conversation_engine.process_input(text)
        return response

    def process_voice_input(self) -> Optional[str]:
        """Process voice input and return response"""
        if not self.voice_enabled:
            return "Voice input not available. Please use text input."

        command = self.voice_processor.listen_for_command()
        if command:
            response = self.process_text_input(command)
            self.voice_processor.speak_response(response)
            return response
        return None

    def start_voice_conversation(self):
        """Start voice-based conversation session"""
        if not self.voice_enabled:
            print("❌ Voice capabilities not available")
            return

        print("🎤 ATHENA VOICE ASSISTANT - Voice Mode")
        print("=" * 50)
        print("Speak your commands naturally. Say 'quit' to exit.")
        print("Available voice commands:")
        print("• 'Check system status'")
        print("• 'Show me the logs'")
        print("• 'What are the metrics?'")
        print("• 'Check tribunals'")
        print("• 'Quit' or 'Exit'")
        print()

        self.listening_active = True

        try:
            while self.listening_active:
                print("\n🎤 Listening for command...")

                # Listen for command
                command = self.process_voice_input()

                if command:
                    print(f"🤖 {command}")

                    # Check for exit commands
                    if any(word in command.lower() for word in ['quit', 'exit', 'bye', 'goodbye']):
                        self.voice_processor.speak_response("Goodbye! The AI Republic continues operating.")
                        break

                # Small delay to prevent rapid retriggering
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n🤖 Voice conversation ended by user")
            self.voice_processor.speak_response("Conversation ended.")
        except Exception as e:
            print(f"❌ Voice conversation error: {e}")

        self.listening_active = False

    def start_hybrid_conversation(self):
        """Start hybrid text/voice conversation session"""
        print("🔄 ATHENA HYBRID ASSISTANT - Text & Voice Mode")
        print("=" * 50)
        print("Type commands or say 'voice mode' to switch to voice input")
        print("Type 'help' for available commands")
        print()

        voice_mode = False

        while True:
            try:
                if voice_mode:
                    print("🎤 Voice mode active - speak your command...")
                    command = self.process_voice_input()
                    if command:
                        print(f"🎤 Heard: {command}")
                        if 'text mode' in command.lower():
                            voice_mode = False
                            print("📝 Switched to text mode")
                            continue
                else:
                    user_input = input("You (or 'voice mode' to speak): ").strip()

                    if not user_input:
                        continue

                    if user_input.lower() == 'voice mode':
                        if self.voice_enabled:
                            voice_mode = True
                            print("🎤 Switched to voice mode")
                            continue
                        else:
                            print("❌ Voice mode not available")
                            continue

                    command = user_input

                if command:
                    if command.lower() in ['quit', 'exit', 'bye']:
                        response = "Goodbye! The AI Republic continues operating autonomously."
                        print(f"🤖 {response}")
                        if self.voice_enabled:
                            self.voice_processor.speak_response(response)
                        break

                    response = self.process_text_input(command)
                    print(f"🤖 {response}")

                    # Speak response if in voice mode
                    if voice_mode and self.voice_enabled:
                        self.voice_processor.speak_response(response)

            except KeyboardInterrupt:
                print("\n🤖 Conversation ended by user")
                if self.voice_enabled:
                    self.voice_processor.speak_response("Conversation ended.")
                break
            except Exception as e:
                error_msg = f"I encountered an error: {e}"
                print(f"🤖 {error_msg}")
                if voice_mode and self.voice_enabled:
                    self.voice_processor.speak_response(error_msg)

    def get_status_summary(self) -> str:
        """Get a quick status summary"""
        try:
            status = self.conversation_engine.copilot.perform_health_check()
            if 'error' in status:
                return f"Status check failed: {status['error']}"

            overall = status.get('overall_status', 'UNKNOWN')
            metrics = status.get('metrics', {})
            compliance = metrics.get('compliance_rate', 0) * 100
            tribunals = metrics.get('tribunals_today', 0)

            return f"System {overall.lower()}: {compliance:.1f}% compliance, {tribunals} tribunals today"
        except Exception as e:
            return f"Status check error: {e}"

class VoiceCommandProcessor:
    """Processes voice commands with wake word detection"""

    def __init__(self, athena_assistant: AthenaVoiceAssistant, sensitivity: str = 'medium'):
        self.assistant = athena_assistant
        self.wake_words = ['athena', 'hey athena', 'ai republic', 'system']
        self.listening = False

        # Wake-word sensitivity configuration
        self.sensitivity_profiles = {
            'low': {  # For quiet environments
                'energy_threshold': 100,
                'wake_word_threshold': 0.3,
                'pause_threshold': 0.5,
                'phrase_threshold': 0.3,
                'non_speaking_duration': 0.3
            },
            'medium': {  # Default balanced setting
                'energy_threshold': 200,
                'wake_word_threshold': 0.4,
                'pause_threshold': 0.6,
                'phrase_threshold': 0.4,
                'non_speaking_duration': 0.5
            },
            'high': {  # For noisy environments
                'energy_threshold': 400,
                'wake_word_threshold': 0.6,
                'pause_threshold': 0.8,
                'phrase_threshold': 0.6,
                'non_speaking_duration': 0.8
            }
        }

        self.sensitivity = sensitivity
        self._apply_sensitivity_profile()

    def _apply_sensitivity_profile(self):
        """Apply the current sensitivity profile to voice recognition"""
        if not hasattr(self, 'sensitivity_profiles'):
            return

        profile = self.sensitivity_profiles.get(self.sensitivity, self.sensitivity_profiles['medium'])

        # Store profile settings for use in recognition
        self.energy_threshold = profile['energy_threshold']
        self.wake_word_threshold = profile['wake_word_threshold']
        self.pause_threshold = profile['pause_threshold']
        self.phrase_threshold = profile['phrase_threshold']
        self.non_speaking_duration = profile['non_speaking_duration']

    def set_sensitivity(self, level: str) -> bool:
        """Change wake-word sensitivity level"""
        if level not in self.sensitivity_profiles:
            print(f"❌ Invalid sensitivity level. Choose from: {', '.join(self.sensitivity_profiles.keys())}")
            return False

        self.sensitivity = level
        self._apply_sensitivity_profile()

        profile = self.sensitivity_profiles[level]
        print(f"✅ Wake-word sensitivity set to '{level}'")
        print(f"   Energy threshold: {profile['energy_threshold']}")
        print(f"   Wake word confidence: {profile['wake_word_threshold']}")
        print(f"   Suitable for: {'quiet environments' if level == 'low' else 'balanced use' if level == 'medium' else 'noisy environments'}")

        return True

    def get_sensitivity_info(self) -> str:
        """Get current sensitivity configuration info"""
        profile = self.sensitivity_profiles.get(self.sensitivity, self.sensitivity_profiles['medium'])
        return f"""Current wake-word sensitivity: {self.sensitivity.upper()}
• Energy threshold: {profile['energy_threshold']} (higher = less sensitive to noise)
• Wake word confidence: {profile['wake_word_threshold']} (higher = fewer false activations)
• Environment: {'Quiet rooms' if self.sensitivity == 'low' else 'General use' if self.sensitivity == 'medium' else 'Noisy environments'}
• Available levels: low, medium, high"""

    def start_continuous_listening(self):
        """Start continuous listening with wake word detection"""
        if not self.assistant.voice_enabled:
            print("❌ Continuous listening requires voice capabilities")
            return

        print("🎤 CONTINUOUS LISTENING ACTIVE")
        print(f"Wake words: {', '.join(self.wake_words)}")
        print(f"Sensitivity: {self.sensitivity.upper()} ({'quiet' if self.sensitivity == 'low' else 'balanced' if self.sensitivity == 'medium' else 'noisy'} environment)")
        print("Say a wake word + command, or 'stop listening' to exit")
        print()

        self.listening = True

        try:
            while self.listening:
                # Listen with sensitivity-adjusted settings
                command = self._listen_with_sensitivity(timeout=10)

                if command:
                    command_lower = command.lower()

                    # Check for wake words
                    wake_word_detected = any(wake_word in command_lower for wake_word in self.wake_words)

                    if 'stop listening' in command_lower:
                        print("🛑 Stopped continuous listening")
                        self.assistant.voice_processor.speak_response("Continuous listening deactivated.")
                        break

                    if wake_word_detected:
                        # Remove wake word and process command
                        for wake_word in self.wake_words:
                            command_lower = command_lower.replace(wake_word, '').strip()

                        if command_lower:
                            print(f"🎤 Processing: {command_lower}")
                            response = self.assistant.process_text_input(command_lower)
                            print(f"🤖 {response}")
                            self.assistant.voice_processor.speak_response(response)
                        else:
                            response = "Yes? What can I help you with?"
                            print(f"🤖 {response}")
                            self.assistant.voice_processor.speak_response(response)
                    else:
                        print(f"💭 Heard '{command}' - no wake word detected")

        except KeyboardInterrupt:
            print("\n🛑 Continuous listening stopped")
            self.assistant.voice_processor.speak_response("Continuous listening deactivated.")
        except Exception as e:
            print(f"❌ Continuous listening error: {e}")

        self.listening = False

    def _listen_with_sensitivity(self, timeout: int = 5) -> Optional[str]:
        """Listen for commands with sensitivity-adjusted recognition"""
        if not self.assistant.voice_enabled:
            return None

        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise with sensitivity
                self.assistant.voice_processor.recognizer.adjust_for_ambient_noise(
                    source, duration=0.5
                )

                # Set energy threshold based on sensitivity
                self.assistant.voice_processor.recognizer.energy_threshold = self.energy_threshold

                # Set pause thresholds for better wake word detection
                self.assistant.voice_processor.recognizer.pause_threshold = self.pause_threshold
                self.assistant.voice_processor.recognizer.phrase_threshold = self.phrase_threshold
                self.assistant.voice_processor.recognizer.non_speaking_duration = self.non_speaking_duration

                print("🎤 Listening... (speak your command)")
                audio = self.assistant.voice_processor.recognizer.listen(source, timeout=timeout)

                print("🔄 Processing speech...")
                # Use Google recognition with language model for better wake word detection
                text = self.assistant.voice_processor.recognizer.recognize_google(audio)
                print(f"📝 Heard: '{text}'")
                return text

        except sr.WaitTimeoutError:
            # Silent timeout - don't print for continuous listening
            return None
        except sr.UnknownValueError:
            # Unclear speech - print only for debugging
            if hasattr(self, '_debug_mode') and self._debug_mode:
                print("❓ Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"❌ Speech recognition service error: {e}")
            return None
        except Exception as e:
            if hasattr(self, '_debug_mode') and self._debug_mode:
                print(f"❌ Voice input error: {e}")
            return None

def setup_voice_environment():
    """Setup voice environment with required dependencies"""
    print("🎤 Setting up voice environment...")

    # Check for microphone access
    try:
        import pyaudio
        print("✅ PyAudio available for microphone access")
    except ImportError:
        print("⚠️ PyAudio not available - install with: pip install pyaudio")
        print("   On Ubuntu/Debian: sudo apt install portaudio19-dev python3-pyaudio")

    # Test voice capabilities
    voice_proc = VoiceProcessor()
    if voice_proc.voice_enabled:
        print("✅ Voice capabilities fully available")
        print("   • Speech recognition: Available")
        print("   • Text-to-speech: Available")

        # Test TTS
        try:
            voice_proc.engine.say("Voice system test successful")
            voice_proc.engine.runAndWait()
            print("✅ Text-to-speech test passed")
        except Exception as e:
            print(f"⚠️ Text-to-speech test failed: {e}")
    else:
        print("❌ Voice capabilities not available")
        print("   Install required packages:")
        print("   pip install SpeechRecognition pyttsx3")
        print("   pip install pyaudio  # May require system dependencies")

def main():
    """Main entry point for voice-enabled Athena"""
    import argparse

    parser = argparse.ArgumentParser(description='Athena Voice-Enabled AI Assistant')
    parser.add_argument('--mode', choices=['text', 'voice', 'hybrid', 'continuous', 'status', 'sensitivity'],
                       default='hybrid', help='Interaction mode')
    parser.add_argument('--no-voice', action='store_true', help='Disable voice capabilities')
    parser.add_argument('--setup', action='store_true', help='Setup voice environment')
    parser.add_argument('--sensitivity', choices=['low', 'medium', 'high'], default='medium',
                       help='Wake word sensitivity level (low=quiet, medium=balanced, high=noisy)')
    parser.add_argument('--set-sensitivity', choices=['low', 'medium', 'high'],
                       help='Change wake word sensitivity and exit')

    args = parser.parse_args()

    if args.setup:
        setup_voice_environment()
        return

    if args.set_sensitivity:
        # Quick sensitivity change without full assistant startup
        voice_enabled = not args.no_voice
        assistant = AthenaVoiceAssistant(voice_enabled=voice_enabled)
        processor = VoiceCommandProcessor(assistant, sensitivity=args.set_sensitivity)
        processor.set_sensitivity(args.set_sensitivity)
        return

    # Initialize Athena assistant
    voice_enabled = not args.no_voice
    assistant = AthenaVoiceAssistant(voice_enabled=voice_enabled)

    if args.mode == 'status':
        summary = assistant.get_status_summary()
        print(f"🤖 {summary}")

    elif args.mode == 'sensitivity':
        # Show current sensitivity info
        processor = VoiceCommandProcessor(assistant, sensitivity=args.sensitivity)
        info = processor.get_sensitivity_info()
        print("🎚️ WAKE WORD SENSITIVITY SETTINGS")
        print("=" * 40)
        print(info)

    elif args.mode == 'text':
        # Text-only conversation
        assistant.conversation_engine.start_conversation()

    elif args.mode == 'voice':
        # Voice-only conversation
        assistant.start_voice_conversation()

    elif args.mode == 'continuous':
        # Continuous listening with wake words
        processor = VoiceCommandProcessor(assistant, sensitivity=args.sensitivity)
        processor.start_continuous_listening()

    else:  # hybrid (default)
        # Hybrid text/voice conversation
        assistant.start_hybrid_conversation()

if __name__ == '__main__':
    main()
