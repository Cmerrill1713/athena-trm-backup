#!/usr/bin/env python3
"""
Demo: Voice Activation for Athena
=================================

Demonstrates wake word detection, voice command processing, and
integration with Athena's command routing system.

Features:
- Wake word detection testing
- Voice command recognition
- Integration with existing command system
- Voice response synthesis
- Error handling and recovery

Usage:
    python3 demo_voice_activation.py --basic     # Basic voice recognition test
    python3 demo_voice_activation.py --commands  # Test voice command processing
    python3 demo_voice_activation.py --macros    # Test voice macros
    python3 demo_voice_activation.py --full      # Complete voice interaction demo
"""

import time
import sys
import os

# Add system paths
sys.path.insert(0, os.path.dirname(__file__))

try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

from voice_activation import VoiceActivation

def demo_basic_recognition():
    """Demonstrate basic speech recognition"""
    print("\n🎤 Basic Speech Recognition Demo")
    print("=" * 40)

    if not SPEECH_AVAILABLE:
        print("❌ SpeechRecognition not available")
        return

    va = VoiceActivation()

    print("Testing speech recognition capabilities...")
    print()

    # Test 1: Ambient noise adjustment
    print("1️⃣ Calibrating for ambient noise...")
    try:
        with sr.Microphone() as source:
            va.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("✅ Ambient noise calibration complete")
    except Exception as e:
        print(f"❌ Calibration failed: {e}")
        return

    # Test 2: Simple speech recognition
    print("\n2️⃣ Speech recognition test...")
    print("   Say something simple like 'hello' or 'test'...")

    try:
        with sr.Microphone() as source:
            audio = va.recognizer.listen(source, timeout=5, phrase_time_limit=3)
            text = va.recognizer.recognize_google(audio)
            print(f"✅ Recognized: '{text}'")
    except sr.WaitTimeoutError:
        print("⏰ No speech detected (timeout)")
    except sr.UnknownValueError:
        print("❓ Speech not understood")
    except Exception as e:
        print(f"❌ Recognition failed: {e}")

    print("\n✅ Basic recognition demo complete!")

def demo_wake_word_detection():
    """Demonstrate wake word detection"""
    print("\n🔔 Wake Word Detection Demo")
    print("=" * 35)

    if not SPEECH_AVAILABLE:
        print("❌ SpeechRecognition not available")
        return

    va = VoiceActivation()

    print("Testing wake word detection...")
    print(f"Wake words: {', '.join(va.wake_words)}")
    print()

    print("Say something containing a wake word (e.g., 'Hey Athena, status')")
    print("Or say 'stop test' to end")
    print()

    try:
        wake_detected, heard_text = va.listen_for_wake_word()

        if wake_detected:
            print("🔔 WAKE WORD DETECTED!")
            print(f"   Heard: '{heard_text}'")

            # Extract command part (after wake word)
            for wake_word in va.wake_words:
                if wake_word in heard_text:
                    command_part = heard_text.replace(wake_word, '').strip()
                    if command_part:
                        print(f"   Command: '{command_part}'")
                    else:
                        print("   (No command detected after wake word)")
                    break
        else:
            if heard_text:
                print(f"ℹ️ Heard: '{heard_text}' (no wake word)")
            else:
                print("⏰ No speech detected")

    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    except Exception as e:
        print(f"❌ Wake word test failed: {e}")

def demo_voice_commands():
    """Demonstrate voice command processing"""
    print("\n🎯 Voice Command Processing Demo")
    print("=" * 40)

    if not SPEECH_AVAILABLE:
        print("❌ SpeechRecognition not available")
        return

    va = VoiceActivation()

    print("Testing voice command processing...")
    print("Available voice commands:")
    for macro, command in va.voice_macros.items():
        print(f"  • '{macro}' → {command}")
    print()

    print("Say one of the voice commands above...")
    print()

    try:
        command = va.listen_for_command()

        if command:
            print(f"🎤 Heard command: '{command}'")

            # Check if it's a voice macro
            if command in va.voice_macros:
                actual_command = va.voice_macros[command]
                print(f"🎬 Voice macro: '{command}' → '{actual_command}'")

                # Show what would happen (don't actually execute for demo)
                print("📋 Command would be processed through routing system:")
                print("   Intent parsing → execution → voice response")

            else:
                print("📝 Direct command processing:")
                print(f"   Would route '{command}' through command system")

        else:
            print("⏰ No command recognized")

    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    except Exception as e:
        print(f"❌ Command test failed: {e}")

def demo_voice_responses():
    """Demonstrate voice response capabilities"""
    print("\n🔊 Voice Response Demo")
    print("=" * 25)

    va = VoiceActivation()

    print("Testing voice response synthesis...")
    print()

    test_responses = [
        "Voice activation active",
        "Command executed successfully",
        "Meeting mode activated",
        "Emergency mode engaged",
        "System status: healthy"
    ]

    if TTS_AVAILABLE:
        print("🔊 Playing voice responses...")
        for response in test_responses:
            print(f"   Speaking: '{response}'")
            va.speak(response, interrupt=False)
            time.sleep(1)  # Brief pause between responses
        print("\n✅ Voice responses complete!")
    else:
        print("⚠️ Text-to-speech not available")
        print("Install with: pip install pyttsx3")
        print()
        print("🔇 Text responses:")
        for response in test_responses:
            print(f"   '{response}'")

def demo_full_interaction():
    """Demonstrate complete voice interaction flow"""
    print("\n🎭 Complete Voice Interaction Demo")
    print("=" * 40)

    if not SPEECH_AVAILABLE:
        print("❌ SpeechRecognition not available")
        return

    va = VoiceActivation()

    print("Simulating complete voice interaction...")
    print("This would normally be a continuous listening loop")
    print()

    # Simulate the interaction flow
    print("1️⃣ Wake Word Detection Phase")
    print("   User says: 'Hey Athena'")
    print("   System detects wake word")
    print("   System responds: 'Yes?'")
    print()

    time.sleep(1)

    print("2️⃣ Command Recognition Phase")
    print("   User says: 'meeting mode'")
    print("   System recognizes: 'meeting mode'")
    print("   System maps to macro: 'meeting mode'")
    print()

    time.sleep(1)

    print("3️⃣ Command Processing Phase")
    print("   System routes to command router")
    print("   Checks authorization (auth level 2)")
    print("   Executes macro: quiet + route")
    print("   Logs to audit trail")
    print()

    time.sleep(1)

    print("4️⃣ Response Phase")
    print("   System speaks: 'Meeting mode activated. Alerts quieted and critical notifications routed to phone.'")
    print("   Returns to listening state")
    print()

    print("🎯 Interaction Flow Complete!")
    print()
    print("In real usage, this happens seamlessly:")
    print("   'Hey Athena, meeting mode' → [processing] → 'Meeting mode activated...'")

def demo_error_handling():
    """Demonstrate error handling and recovery"""
    print("\n🛠️ Error Handling & Recovery Demo")
    print("=" * 35)

    print("Testing voice activation error scenarios...")
    print()

    # Test 1: No speech recognition
    print("1️⃣ No Speech Recognition Available")
    if not SPEECH_AVAILABLE:
        print("   ❌ SpeechRecognition library not installed")
        print("   💡 Install with: pip install SpeechRecognition PyAudio")
    else:
        print("   ✅ SpeechRecognition available")
    print()

    # Test 2: No text-to-speech
    print("2️⃣ No Text-to-Speech Available")
    if not TTS_AVAILABLE:
        print("   ⚠️ pyttsx3 library not installed")
        print("   💡 Install with: pip install pyttsx3")
        print("   🔇 Responses will be text-only")
    else:
        print("   ✅ Text-to-speech available")
    print()

    # Test 3: Microphone permissions
    print("3️⃣ Microphone Access Check")
    if SPEECH_AVAILABLE:
        try:
            with sr.Microphone() as source:
                print("   ✅ Microphone access available")
        except Exception as e:
            print(f"   ❌ Microphone access failed: {e}")
            print("   💡 Enable in: System Settings → Privacy & Security → Microphone")
    print()

    # Test 4: Recovery scenarios
    print("4️⃣ Error Recovery Scenarios")
    print("   • Wake word timeout → Returns to listening")
    print("   • Unrecognized speech → Prompts for repeat")
    print("   • Command failure → Speaks error message")
    print("   • Network issues → Continues with local commands")
    print("   • System busy → Queues command for later")

def main():
    print("🎤 Athena Voice Activation Demo")
    print("=" * 40)
    print()

    if len(sys.argv) < 2:
        print("Complete voice activation system demonstration.")
        print()
        print("Commands:")
        print("  --basic       Basic speech recognition test")
        print("  --wake        Wake word detection test")
        print("  --commands    Voice command processing test")
        print("  --responses   Voice response synthesis test")
        print("  --full        Complete interaction flow demo")
        print("  --errors      Error handling demonstration")
        print()
        print("Requirements:")
        print("  • pip install SpeechRecognition PyAudio pyobjc")
        print("  • brew install portaudio")
        print("  • macOS microphone permissions")
        print()
        print("Example: python3 demo_voice_activation.py --basic")

        return

    command = sys.argv[1]

    if command == "--basic":
        demo_basic_recognition()

    elif command == "--wake":
        demo_wake_word_detection()

    elif command == "--commands":
        demo_voice_commands()

    elif command == "--responses":
        demo_voice_responses()

    elif command == "--full":
        demo_full_interaction()

    elif command == "--errors":
        demo_error_handling()

    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
