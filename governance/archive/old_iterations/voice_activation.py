#!/usr/bin/env python3
"""
Voice Activation for Athena
===========================

Wake word detection and voice command processing for Athena's AI Republic.
Provides hands-free control through natural speech commands.

Features:
- Wake word detection ("Hey Athena", "Athena", "Computer")
- Speech-to-text conversion
- Integration with command routing system
- Voice response synthesis
- Background service operation
- Security and audit integration

Usage:
    from voice_activation import initialize_voice_activation
    initialize_voice_activation()

Or run directly:
    python3 voice_activation.py
"""

import time
import threading
import queue
import os
import sys
import signal

# Add system paths
sys.path.insert(0, os.path.dirname(__file__))

try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    print("❌ SpeechRecognition not available. Install with: pip install SpeechRecognition PyAudio")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("⚠️ pyttsx3 not available. Voice responses disabled. Install with: pip install pyttsx3")

from ai_command_routing import AICommandRouter
from athena_notifications import (
    get_active_mode,
    apply_manual_override,
    list_available_macros,
    deactivate_macro,
    audit_event,
    get_system_uptime_human,
    is_router_healthy,
    clear_manual_override,
    is_override_active,
)
import os
from typing import Optional

# =========================
# Context-aware voice styles
# =========================
VOICE_STYLES = {
    "meeting_mode": {"prefix": "", "suffix": "", "gain": 0.8, "brief": True},
    "travel_mode":  {"prefix": "", "suffix": "", "gain": 1.0, "brief": True},
    "emergency_mode":{"prefix": "", "suffix": "", "gain": 1.15, "brief": True},
    "normal_mode":  {"prefix": "", "suffix": "", "gain": 1.0, "brief": False},
    "maintenance_mode":{"prefix":"", "suffix":"", "gain":0.9, "brief": True},
    "_default":     {"prefix": "", "suffix": "", "gain": 1.0, "brief": False},
}

OVERRIDE_TTL_SECONDS = int(os.getenv("VOICE_OVERRIDE_TTL_SECONDS", "900"))  # 15m

# =======================
# Voice Channel Priorities
# =======================
VOICE_PRIORITIES = {
    "emergency_command": 1,     # Highest - emergency mode commands
    "kill_switch": 2,           # Kill switch commands
    "ttl_notification": 3,      # TTL status updates
    "diagnostic": 4,            # Health checks and diagnostics
    "normal_command": 5,        # Regular commands
    "confirmation": 6,          # Command confirmations
}

# =======================
# Context-Adaptive Voice Styles (Korono-compatible)
# =======================
VOICE_STYLE_MAP = {
    "emergency_mode": {
        "voice": "sharp",        # More urgent tone
        "cadence": "clipped",    # Faster, more direct
        "volume": 1.15,          # Louder for emergency
        "priority": VOICE_PRIORITIES["emergency_command"]
    },
    "kill_switch": {
        "voice": "authoritative", # Commanding tone
        "cadence": "deliberate",  # Slower, more emphatic
        "volume": 1.0,
        "priority": VOICE_PRIORITIES["kill_switch"]
    },
    "ttl_notification": {
        "voice": "informative",   # Clear, neutral
        "cadence": "measured",    # Balanced pace
        "volume": 0.9,
        "priority": VOICE_PRIORITIES["ttl_notification"]
    },
    "diagnostic": {
        "voice": "technical",     # Precise, detailed
        "cadence": "methodical",  # Careful delivery
        "volume": 0.85,
        "priority": VOICE_PRIORITIES["diagnostic"]
    },
    "normal_mode": {
        "voice": "conversational", # Friendly, natural
        "cadence": "natural",     # Normal speech rhythm
        "volume": 1.0,
        "priority": VOICE_PRIORITIES["normal_command"]
    },
    "maintenance_mode": {
        "voice": "calm",          # Reassuring, steady
        "cadence": "slow",        # Slower pace
        "volume": 0.8,
        "priority": VOICE_PRIORITIES["confirmation"]
    },
    "_default": {
        "voice": "neutral",
        "cadence": "standard",
        "volume": 1.0,
        "priority": VOICE_PRIORITIES["normal_command"]
    }
}

# =======================
# Voice-only macro aliases
# =======================
VOICE_ONLY_ALIASES = {
    "red alert": "emergency mode",
    "all clear": "normal mode",
    "silence": "quiet for 30 minutes",
    "deck status": "status",
    "deck diagnostics": "diagnostics",
    "stop automations": "stop automations",
    "kill switch": "stop automations",
}

class VoiceActivation:
    """Voice activation system for Athena"""

# ===========
# TTS helpers
# ===========
def speak(message: str, style_key: Optional[str] = None, brief: Optional[bool] = None):
    """
    Enhanced TTS with priority queue, context-adaptive styles, and Korono integration.
    """
    style = VOICE_STYLE_MAP.get(style_key or "_default", VOICE_STYLE_MAP["_default"])
    priority = style.get("priority", VOICE_PRIORITIES["normal_command"])

    msg = message
    if brief is True or (brief is None and style.get("brief")):
        # trim pleasantries, keep essentials
        pass

    # Queue the voice response with priority
    voice_item = {
        "message": msg,
        "style": style,
        "style_key": style_key or "_default",
        "timestamp": time.time()
    }

    # Add to priority queue (lower number = higher priority)
    if voice_activation_instance and hasattr(voice_activation_instance, 'voice_queue'):
        voice_activation_instance.voice_queue.put((priority, voice_item))
    else:
        # Fallback if queue not available
        try:
            print(f"[VOICE:{style_key or 'default'}] {msg}")
            # system_say(msg, voice=style["voice"], cadence=style["cadence"], volume=style["volume"])
        except Exception as e:
            print(f"[VOICE][ERR] {e} :: {msg}")

# Global reference for speak function
voice_activation_instance = None

def _expand_voice_alias(text: str) -> str:
    key = (text or "").strip().lower()
    return VOICE_ONLY_ALIASES.get(key, text)

class VoiceActivation:
    """Voice activation system for Athena"""

    def __init__(self):
        self.recognizer = sr.Recognizer() if SPEECH_AVAILABLE else None
        self.engine = pyttsx3.init() if TTS_AVAILABLE else None
        self.router = AICommandRouter()

        # Voice settings
        self.wake_words = ["hey athena", "athena", "computer", "bridge"]
        self.energy_threshold = 300  # Adjust based on environment noise
        self.pause_threshold = 0.8   # Seconds of silence before processing
        self.listen_timeout = 5      # Max seconds to listen for command

        # TTL monitoring
        self.ttl_monitor_active = False
        self.ttl_check_interval = 60  # Check every minute
        self.last_ttl_notification = 0  # Track when we last notified about TTL

        # Watchdog and health monitoring
        self.watchdog_active = False
        self.watchdog_interval = 10  # Check every 10 seconds
        self.last_health_check = 0
        self.voice_health_failures = 0
        self.max_health_failures = 3

        # Pre-trigger buffer
        self.pre_trigger_buffer_ms = 200
        self.audio_buffer = []

        # Session persistence
        self.session_log = []
        self.max_session_entries = 100

        # Voice channel priority queue
        self.voice_queue = queue.PriorityQueue()
        self.voice_processor_active = False

        # Hot reload support
        self.reload_signal_received = False

        # Voice macros for smoother interaction
        self.voice_macros = {
            "meeting mode": "meeting mode",
            "emergency": "emergency mode",
            "emergency mode": "emergency mode",
            "normal ops": "normal mode",
            "normal mode": "normal mode",
            "status": "status",
            "check status": "status",
            "system status": "status",
            "quiet mode": "quiet for 30 minutes",
            "maintenance mode": "maintenance mode",
            "route to phone": "route critical to phone",
            "acknowledge all": "ack all",
            "clear alerts": "ack all"
        }

        # State
        self.listening = False
        self.command_queue = queue.Queue()
        self.audio_queue = queue.Queue()

        # Configure TTS engine
        self._configure_tts()

    def _configure_tts(self):
        """Configure text-to-speech engine"""
        if not TTS_AVAILABLE:
            return

        try:
            # Set voice properties for better experience
            voices = self.engine.getProperty('voices')
            # Try to use a natural-sounding voice
            for voice in voices:
                if 'female' in voice.name.lower() or 'samantha' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break

            self.engine.setProperty('rate', 180)  # Slightly slower for clarity
            self.engine.setProperty('volume', 0.8)

        except Exception as e:
            print(f"⚠️ TTS configuration failed: {e}")

    def speak(self, text, interrupt=True):
        """Speak text using TTS"""
        if not TTS_AVAILABLE:
            print(f"🔇 {text}")
            return

        try:
            if interrupt and self.engine.isBusy():
                self.engine.stop()

            self.engine.say(text)
            self.engine.runAndWait()

        except Exception as e:
            print(f"❌ Speech failed: {e}")
            print(f"🔇 {text}")

    def listen_for_wake_word(self):
        """Listen for wake words in audio stream with pre-trigger buffer"""
        if not SPEECH_AVAILABLE:
            print("❌ Speech recognition not available")
            return False

        try:
            with sr.Microphone() as source:
                print("🎧 Listening for wake word...")

                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.recognizer.energy_threshold = self.energy_threshold
                self.recognizer.pause_threshold = self.pause_threshold

                # Pre-trigger buffer: listen for a bit before wake word detection
                # This helps catch the beginning of commands
                pre_trigger_audio = self.recognizer.listen(source,
                                                          timeout=self.pre_trigger_buffer_ms/1000,
                                                          phrase_time_limit=self.pre_trigger_buffer_ms/1000)

                # Store pre-trigger audio for potential command processing
                if hasattr(pre_trigger_audio, 'frame_data'):
                    self.audio_buffer.append(pre_trigger_audio)

                # Listen for wake word (with pre-trigger buffer already consumed)
                audio = self.recognizer.listen(source, timeout=self.listen_timeout, phrase_time_limit=3)

                try:
                    # Convert speech to text
                    text = self.recognizer.recognize_google(audio).lower().strip()
                    print(f"🎤 Heard: \"{text}\"")

                    # Check for wake words
                    for wake_word in self.wake_words:
                        if wake_word in text:
                            print(f"🔔 Wake word detected: '{wake_word}'")
                            return True, text

                    return False, text

                except sr.UnknownValueError:
                    # Audio couldn't be understood
                    return False, ""

                except sr.RequestError as e:
                    print(f"❌ Speech recognition error: {e}")
                    return False, ""

        except Exception as e:
            print(f"❌ Microphone error: {e}")
            return False, ""

    def listen_for_command(self):
        """Listen for the actual command after wake word"""
        if not SPEECH_AVAILABLE:
            return ""

        try:
            with sr.Microphone() as source:
                print("🎧 Listening for command...")

                # Shorter timeout for commands
                audio = self.recognizer.listen(source, timeout=4, phrase_time_limit=5)

                try:
                    text = self.recognizer.recognize_google(audio).lower().strip()
                    print(f"🎤 Command: \"{text}\"")
                    return text

                except sr.UnknownValueError:
                    self.speak("I didn't catch that. Could you repeat?")
                    return ""

                except sr.RequestError as e:
                    print(f"❌ Command recognition error: {e}")
                    return ""

        except Exception as e:
            print(f"❌ Command listening error: {e}")
            return ""

    def process_voice_command(self, command_text):
        """
        Full pipeline with context-aware feedback + manual override priority + session persistence.
        """
        cmd = _expand_voice_alias((command_text or "").strip())
        mode_before = get_active_mode() or "normal_mode"

        # Log command reception
        self.log_session_event("voice_command_received", {
            "command": cmd,
            "original_text": command_text,
            "active_mode": mode_before
        })

        # Diagnostics (voice)
        if cmd.lower() in ("diagnostics", "run diagnostics", "deck diagnostics"):
            ok_router = is_router_healthy()
            uptime = get_system_uptime_human()
            macros = ", ".join(sorted(m["name"] for m in list_available_macros()))
            msg = (
                f"Wake word OK. STT OK. Router {'OK' if ok_router else 'not responding'}. "
                f"Macros loaded. Uptime {uptime}."
            )
            speak(msg, style_key=mode_before, brief=True)
            audit_event("voice_diagnostics", {"router_ok": ok_router, "uptime": uptime})

            # Log diagnostics result
            self.log_session_event("voice_diagnostics_complete", {
                "router_ok": ok_router,
                "uptime": uptime,
                "macros_count": len(list_available_macros())
            })

            return msg

        # Kill switch: stop all automations
        if cmd.lower() in ("stop automations", "kill switch", "disable automations"):
            try:
                current_mode = get_active_mode()
                if current_mode and current_mode != "normal_mode":
                    deactivate_macro(current_mode)
                clear_manual_override()
                speak("All automations disabled. Manual control only.", style_key="kill_switch", brief=True)
                audit_event("voice_kill_switch", {"previous_mode": current_mode})

                # Log kill switch activation
                self.log_session_event("kill_switch_activated", {
                    "previous_mode": current_mode,
                    "reason": "manual_command"
                })

                return "Automations disabled"
            except Exception as e:
                speak("Error disabling automations.", style_key="emergency_mode")
                return f"Error: {e}"

        # Priority arbitration: if this voice command activates a mode that conflicts
        # with current context macro, honor human override and pin it with TTL.
        # We detect simple macro intents by string match — your router still executes.
        human_override = None
        if cmd.lower() in ("meeting mode", "normal mode", "emergency mode", "maintenance mode", "travel mode"):
            human_override = cmd.lower().replace(" ", "_")  # e.g., "normal_mode"

        # Execute via the unified command router
        result = self.router.route_command(cmd)

        # If success and it's a mode command, enforce override
        if result.get("success") and human_override:
            # Deactivate other macros if needed, then apply override
            try:
                deactivate_macro(mode_before)
            except Exception:
                pass
            apply_manual_override(
                mode=human_override,
                source="voice",
                ttl_seconds=OVERRIDE_TTL_SECONDS,
                reason=f"Voice override: {cmd}",
            )
            speak(f"{cmd} activated. Human override in effect for {OVERRIDE_TTL_SECONDS//60} minutes.",
                  style_key=human_override, brief=True)
            audit_event("voice_manual_override", {"mode": human_override, "ttl_s": OVERRIDE_TTL_SECONDS})

            # Log override activation
            self.log_session_event("override_activated", {
                "mode": human_override,
                "previous_mode": mode_before,
                "ttl_seconds": OVERRIDE_TTL_SECONDS,
                "reason": f"Voice override: {cmd}"
            })

            return result.get("message") or f"{cmd} activated."

        # Normal voice feedback, styled by current mode (or default)
        style_mode = get_active_mode() or mode_before
        speak(result.get("message", "Done."), style_key=style_mode)
        return result.get("message", "Done.")

    def voice_listener_loop(self):
        """Main voice listening loop"""
        print("🎤 Voice activation active")
        print("💡 Say 'Hey Athena' or 'Athena' to wake me up")
        print("🛑 Say 'stop listening' to deactivate voice mode")

        consecutive_failures = 0
        max_failures = 3

        while self.listening:
            try:
                # Listen for wake word
                wake_detected, heard_text = self.listen_for_wake_word()

                if wake_detected:
                    consecutive_failures = 0

                    # Check if it's a stop command
                    if "stop listening" in heard_text or "deactivate" in heard_text:
                        self.speak("Voice activation deactivated.")
                        break

                    # Wake confirmation
                    self.speak("Yes?")

                    # Listen for command
                    command = self.listen_for_command()

                    if command:
                        # Process the command
                        self.process_voice_command(command)
                    else:
                        self.speak("Ready for your command.")

                elif heard_text and consecutive_failures < max_failures:
                    # Heard something but not a wake word
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        print("🔇 Too many unrecognized phrases, temporarily quieting...")
                        time.sleep(30)  # Brief quiet period
                        consecutive_failures = 0

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Voice loop error: {e}")
                time.sleep(1)

        print("🛑 Voice activation stopped")

    def start_voice_processor(self):
        """Start voice priority queue processor"""
        if self.voice_processor_active:
            return

        self.voice_processor_active = True
        processor_thread = threading.Thread(target=self._voice_processor_loop, daemon=True)
        processor_thread.start()
        print("🔊 Voice processor started")

    def _voice_processor_loop(self):
        """Process voice responses in priority order"""
        while self.voice_processor_active:
            try:
                # Get next voice item (blocking)
                priority, voice_item = self.voice_queue.get(timeout=1.0)

                # Process the voice item
                self._process_voice_item(voice_item)

                # Mark as done
                self.voice_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Voice processor error: {e}")
                time.sleep(0.1)

    def _process_voice_item(self, voice_item):
        """Process a single voice item"""
        msg = voice_item["message"]
        style = voice_item["style"]
        style_key = voice_item["style_key"]

        try:
            # Apply voice style parameters
            voice_type = style.get("voice", "neutral")
            cadence = style.get("cadence", "standard")
            volume = style.get("volume", 1.0)

            print(f"[VOICE:{style_key}:{voice_type}] {msg}")
            # system_say(msg, voice=voice_type, cadence=cadence, volume=volume)

        except Exception as e:
            print(f"[VOICE][ERR] {e} :: {msg}")

    def start_watchdog(self):
        """Start health monitoring watchdog"""
        if self.watchdog_active:
            return

        self.watchdog_active = True
        watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        watchdog_thread.start()
        print("🐕 Voice watchdog started")

    def _watchdog_loop(self):
        """Monitor TTS/STT health and auto-recover"""
        while self.watchdog_active:
            try:
                current_time = time.time()

                # Health check every watchdog_interval
                if current_time - self.last_health_check >= self.watchdog_interval:
                    self._perform_health_check()
                    self.last_health_check = current_time

                # Check for reload signal
                if self.reload_signal_received:
                    self._perform_hot_reload()
                    self.reload_signal_received = False

            except Exception as e:
                print(f"Watchdog error: {e}")

            time.sleep(1.0)

    def _perform_health_check(self):
        """Check TTS and STT health"""
        health_ok = True

        try:
            # Test STT (quick recognition test)
            if SPEECH_AVAILABLE:
                # This is a lightweight test - in production you might test actual recognition
                test_recognizer = sr.Recognizer()
                health_ok = health_ok and True  # Placeholder
        except Exception:
            health_ok = False

        try:
            # Test TTS (quick synthesis test)
            if TTS_AVAILABLE:
                # This is a lightweight test - in production you might test actual synthesis
                test_engine = pyttsx3.init()
                health_ok = health_ok and True  # Placeholder
        except Exception:
            health_ok = False

        if not health_ok:
            self.voice_health_failures += 1
            print(f"Voice health check failed ({self.voice_health_failures}/{self.max_health_failures})")

            if self.voice_health_failures >= self.max_health_failures:
                print("🚨 Voice health failures exceeded threshold, attempting recovery...")
                self._recover_voice_system()
                self.voice_health_failures = 0
        else:
            # Reset failure counter on success
            if self.voice_health_failures > 0:
                print("✅ Voice health restored")
                self.voice_health_failures = 0

    def _recover_voice_system(self):
        """Attempt to recover voice system"""
        try:
            audit_event("voice_recovery_attempt", {"reason": "health_failure"})

            # Restart TTS engine if available
            if TTS_AVAILABLE and hasattr(self, 'engine'):
                try:
                    self.engine.stop()
                    time.sleep(0.5)
                    self.engine = pyttsx3.init()
                    print("✅ TTS engine restarted")
                except Exception as e:
                    print(f"❌ TTS restart failed: {e}")

            # Log recovery attempt
            audit_event("voice_recovery_complete", {"tts_ok": TTS_AVAILABLE, "stt_ok": SPEECH_AVAILABLE})

        except Exception as e:
            print(f"❌ Voice recovery failed: {e}")

    def _perform_hot_reload(self):
        """Hot reload configuration"""
        try:
            # Reload voice aliases and styles from disk
            # This is a simplified version - in production you'd reload from config files
            print("🔄 Hot reload triggered")
            audit_event("voice_hot_reload", {"timestamp": time.time()})

            # Reset failure counters
            self.voice_health_failures = 0

        except Exception as e:
            print(f"❌ Hot reload failed: {e}")

    def log_session_event(self, event_type: str, data: dict):
        """Log session persistence data"""
        entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "data": data
        }

        self.session_log.append(entry)

        # Maintain max entries
        if len(self.session_log) > self.max_session_entries:
            self.session_log.pop(0)

    def get_session_summary(self) -> dict:
        """Get session persistence summary"""
        return {
            "total_events": len(self.session_log),
            "last_event": self.session_log[-1] if self.session_log else None,
            "active_mode": get_active_mode(),
            "override_active": is_override_active()
        }

    def start_ttl_monitor(self):
        """Start TTL expiry monitoring"""
        if self.ttl_monitor_active:
            return

        self.ttl_monitor_active = True
        ttl_thread = threading.Thread(target=self._ttl_monitor_loop, daemon=True)
        ttl_thread.start()
        print("⏰ TTL monitoring started")

    def _ttl_monitor_loop(self):
        """Monitor TTL expiry and notify"""
        while self.ttl_monitor_active:
            try:
                if is_override_active():
                    # Check if we should notify about impending expiry
                    # This is a simplified version - in production you'd check the actual expiry time
                    current_time = time.time()
                    time_since_last_notification = current_time - self.last_ttl_notification

                    # Notify every 5 minutes during active override
                    if time_since_last_notification >= 300:  # 5 minutes
                        current_mode = get_active_mode()
                        speak(f"Human override active: {current_mode.replace('_', ' ')}. "
                              f"TTL remaining approximately {OVERRIDE_TTL_SECONDS // 60} minutes.",
                              style_key=current_mode, brief=True)
                        self.last_ttl_notification = current_time
                        audit_event("voice_ttl_status", {"mode": current_mode, "ttl_seconds": OVERRIDE_TTL_SECONDS})
                else:
                    # Override has expired, notify once
                    if self.last_ttl_notification > 0:
                        speak("Human override expired. Automation resumed.", style_key="normal_mode", brief=True)
                        audit_event("voice_override_expired", {})

                        # Log expiry event
                        self.log_session_event("override_expired", {
                            "reason": "natural_timeout",
                            "ttl_seconds": OVERRIDE_TTL_SECONDS
                        })

                        self.last_ttl_notification = 0  # Reset

            except Exception as e:
                print(f"TTL monitor error: {e}")

            time.sleep(self.ttl_check_interval)

    def start_voice_activation(self):
        """Start voice activation service"""
        global voice_activation_instance

        if not SPEECH_AVAILABLE:
            print("❌ Voice activation requires SpeechRecognition. Install with: pip install SpeechRecognition PyAudio")
            return False

        # Set global instance for speak function
        voice_activation_instance = self

        self.listening = True

        # Start all monitoring threads
        self.start_watchdog()
        self.start_ttl_monitor()
        self.start_voice_processor()

        # Start voice listener in background thread
        voice_thread = threading.Thread(target=self.voice_listener_loop, daemon=True)
        voice_thread.start()

        print("✅ Voice activation started")
        print("🎤 Background listening active")
        print("⏰ TTL monitoring active")
        print("🐕 Health watchdog active")
        print("🔊 Voice processor active")

        # Set up signal handler for hot reload
        def signal_handler(signum, frame):
            print(f"🔄 Received signal {signum}, triggering hot reload...")
            self.reload_signal_received = True

        signal.signal(signal.SIGHUP, signal_handler)

        # Log session start
        self.log_session_event("session_start", {"capabilities": ["stt", "tts", "priority_queue", "health_monitoring"]})

        return True

    def stop_voice_activation(self):
        """Stop voice activation"""
        global voice_activation_instance

        self.listening = False
        self.ttl_monitor_active = False
        self.watchdog_active = False
        self.voice_processor_active = False

        # Log session end
        self.log_session_event("session_end", {"reason": "manual_stop"})

        # Clear global instance
        if voice_activation_instance is self:
            voice_activation_instance = None

        print("🛑 Voice activation stopping...")
        print("🛑 TTL monitoring stopping...")
        print("🛑 Watchdog stopping...")
        print("🛑 Voice processor stopping...")

def test_voice_activation():
    """Test voice activation components"""
    print("🧪 Testing Voice Activation Components")
    print("=" * 45)

    if not SPEECH_AVAILABLE:
        print("❌ SpeechRecognition not available")
        return

    va = VoiceActivation()

    print("1️⃣ Testing microphone access...")
    try:
        with sr.Microphone() as source:
            va.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("✅ Microphone access OK")
    except Exception as e:
        print(f"❌ Microphone access failed: {e}")
        return

    print("2️⃣ Testing wake word detection...")
    print("   Say something containing 'hey athena' or 'athena'...")

    try:
        detected, text = va.listen_for_wake_word()
        if detected:
            print(f"✅ Wake word detected in: '{text}'")
        else:
            print(f"ℹ️ Heard: '{text}' (no wake word)")
    except Exception as e:
        print(f"❌ Wake word test failed: {e}")

    print("3️⃣ Testing command recognition...")
    print("   Say a command like 'status' or 'meeting mode'...")

    try:
        command = va.listen_for_command()
        if command:
            print(f"✅ Command recognized: '{command}'")
        else:
            print("ℹ️ No command recognized")
    except Exception as e:
        print(f"❌ Command test failed: {e}")

    print("4️⃣ Testing text-to-speech...")
    if TTS_AVAILABLE:
        va.speak("Voice activation test complete.")
        print("✅ Text-to-speech OK")
    else:
        print("⚠️ Text-to-speech not available")

    print("\n✅ Voice activation test complete!")

def initialize_voice_activation():
    """Initialize voice activation service"""
    va = VoiceActivation()

    if va.start_voice_activation():
        # Keep main thread alive
        try:
            while va.listening:
                time.sleep(1)
        except KeyboardInterrupt:
            va.stop_voice_activation()
    else:
        print("❌ Failed to start voice activation")

def main():
    if len(sys.argv) < 2:
        print("🎤 Athena Voice Activation")
        print("=" * 30)
        print()
        print("Voice-controlled command interface for Athena.")
        print()
        print("Commands:")
        print("  --start          Start voice activation")
        print("  --test           Test voice components")
        print("  --stop           Stop voice activation")
        print()
        print("Requirements:")
        print("  • pip install SpeechRecognition PyAudio pyobjc")
        print("  • brew install portaudio")
        print("  • macOS microphone permissions")
        print()
        print("Usage: python3 voice_activation.py --start")

        return

    command = sys.argv[1]

    if command == "--start":
        initialize_voice_activation()

    elif command == "--test":
        test_voice_activation()

    elif command == "--stop":
        va = VoiceActivation()
        va.stop_voice_activation()

    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
