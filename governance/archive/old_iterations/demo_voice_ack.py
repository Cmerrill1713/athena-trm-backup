#!/usr/bin/env python3
"""
Demo: Voice Acknowledgment for AI Republic Alerts
Shows how to acknowledge alerts using voice commands.
"""

import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

def demo_voice_ack():
    """Demonstrate voice acknowledgment workflow"""
    print("🎤 AI REPUBLIC VOICE ACKNOWLEDGMENT DEMO")
    print("=" * 50)

    # Step 1: Simulate an alert escalation
    print("1️⃣ Simulating critical alert...")
    ack_id = str(uuid.uuid4())

    from athena_notifications import send_tier3_escalation
    send_tier3_escalation(
        tts_text="Critical system alert. Memory utilization at 95%. Immediate action required.",
        minutes_to_escalate=1,  # 1 minute for demo
        ack_id=ack_id
    )

    print("✅ Alert escalation started - voice alerts will begin in 30 seconds")
    print("🎤 Say 'acknowledge' or 'ack' to stop the escalation")
    print()

    # Step 2: Show voice acknowledgment
    print("2️⃣ Testing voice acknowledgment...")

    # Simulate user saying "acknowledge"
    from athena_voice_integration import AthenaVoiceAssistant
    assistant = AthenaVoiceAssistant()

    # Test the acknowledgment command
    response = assistant.process_text_input("acknowledge")
    print(f"🤖 Athena: {response}")

    print()
    print("✅ Voice acknowledgment demo complete!")
    print()
    print("How it works:")
    print("• Say 'Athena, acknowledge' when you hear alert escalation")
    print("• Or type 'acknowledge' in text mode")
    print("• Escalation stops immediately with confirmation")

if __name__ == "__main__":
    demo_voice_ack()
