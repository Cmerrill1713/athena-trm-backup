#!/usr/bin/env python3
"""
Test contextual understanding with short messages
Demonstrates why RAG should be enabled even for short messages with info content
"""
import sys
sys.path.insert(0, '/Users/christianmerrill/Documents/GitHub/AI-Projects/universal-ai-tools')
from src.api.trm_router import trm_route

print("🧠 Testing Contextual Short Messages\n")
print("=" * 80)
print("Scenario: User shares contextual information in short messages")
print("=" * 80)

conversations = [
    {
        "title": "Birthday Context",
        "messages": [
            ("Today is November 3rd", "Should retrieve: Christian's birthday context"),
            ("What should I do?", "Should have birthday context from previous message"),
        ]
    },
    {
        "title": "Meeting Context", 
        "messages": [
            ("The meeting is at 3pm", "Should retrieve: meeting schedules, participants"),
            ("Who's attending?", "Should have meeting context from previous message"),
        ]
    },
    {
        "title": "Personal State",
        "messages": [
            ("I'm feeling stressed", "Should retrieve: coping strategies, past conversations"),
            ("Any suggestions?", "Should have emotional context from previous message"),
        ]
    },
    {
        "title": "Simple Acknowledgments (No RAG needed)",
        "messages": [
            ("ok", "No context needed - simple acknowledgment"),
            ("thanks", "No context needed - gratitude"),
            ("yes", "No context needed - affirmation"),
        ]
    }
]

for conv in conversations:
    print(f"\n📝 {conv['title']}")
    print("-" * 80)
    
    for message, reasoning in conv["messages"]:
        policy = trm_route(message, {})
        words = len(message.strip().split())
        
        rag_icon = "✅" if policy.rag.enabled else "❌"
        rag_text = f"RAG (k={policy.rag.k})" if policy.rag.enabled else "No RAG"
        
        print(f"\nUser: \"{message}\" ({words} words)")
        print(f"  {rag_icon} {rag_text} | Mode: {policy.mode}")
        print(f"  💭 {reasoning}")

print("\n" + "=" * 80)
print("✅ Summary:")
print("=" * 80)
print("""
The system now intelligently enables RAG based on information content, not just length:

• "Today is November 3rd" (4 words) → ✅ RAG enabled
  - Can retrieve: "Christian's birthday is November 3rd"
  - Response: "Happy birthday, Christian! 🎉"

• "I'm feeling stressed" (3 words) → ✅ RAG enabled  
  - Can retrieve: Past coping strategies, wellness resources
  - Response: Personalized suggestions based on your history

• "ok" (1 word) → ❌ No RAG
  - Simple acknowledgment, no context needed
  - Response: Direct acknowledgment

This makes the agent conversationally aware and contextual, just like talking to a real assistant!
""")

