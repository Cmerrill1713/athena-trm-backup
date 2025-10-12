#!/usr/bin/env python3
"""
Seed Weaviate - Initialize schema and learned patterns

Creates schema and seeds with initial learned patterns for RAG/learning agents.
"""

import requests
import json

WEAVIATE_URL = "http://localhost:8090"

# Schema definitions
SCHEMA_CLASSES = [
    {
        "class": "LearnedPattern",
        "vectorizer": "none",
        "properties": [
            {"name": "name", "dataType": ["text"]},
            {"name": "tags", "dataType": ["text[]"]},
            {"name": "snippet", "dataType": ["text"]},
            {"name": "notes", "dataType": ["text"]},
            {"name": "task_type", "dataType": ["text"]},
            {"name": "success_rate", "dataType": ["number"]},
            {"name": "usage_count", "dataType": ["int"]}
        ]
    },
    {
        "class": "ConversationMemory",
        "vectorizer": "none",
        "properties": [
            {"name": "sessionId", "dataType": ["text"]},
            {"name": "turn", "dataType": ["int"]},
            {"name": "role", "dataType": ["text"]},
            {"name": "content", "dataType": ["text"]},
            {"name": "timestamp", "dataType": ["date"]}
        ]
    },
    {
        "class": "ModelOutcome",
        "vectorizer": "none",
        "properties": [
            {"name": "model", "dataType": ["text"]},
            {"name": "task_type", "dataType": ["text"]},
            {"name": "success", "dataType": ["boolean"]},
            {"name": "latency_ms", "dataType": ["int"]},
            {"name": "timestamp", "dataType": ["date"]}
        ]
    }
]

# Seed data - learned patterns
SEED_PATTERNS = [
    {
        "class": "LearnedPattern",
        "properties": {
            "name": "macos_nstext_visibility_pattern",
            "tags": ["swiftui", "nstext", "color", "theme"],
            "snippet": "typingAttributes + textStorage.attributes",
            "notes": "Fixes white/invisible text regardless of theme. Use typingAttributes to set color.",
            "task_type": "ui_fix",
            "success_rate": 0.98,
            "usage_count": 45
        }
    },
    {
        "class": "LearnedPattern",
        "properties": {
            "name": "doCommand_ime_safe",
            "tags": ["keyboard", "ime", "input", "macos"],
            "snippet": "interpretKeyEvents + doCommand(by:)",
            "notes": "ENTER=send, SHIFT+ENTER=newline; IME safe. Use interpretKeyEvents for proper keyboard handling.",
            "task_type": "keyboard_handling",
            "success_rate": 0.95,
            "usage_count": 78
        }
    },
    {
        "class": "LearnedPattern",
        "properties": {
            "name": "fastvlm_chart_extraction",
            "tags": ["vision", "chart", "ocr", "data"],
            "snippet": "Extract data from this chart as a markdown table with headers",
            "notes": "Optimal prompt for FastVLM chart extraction. Returns structured data.",
            "task_type": "vision_chart",
            "success_rate": 0.88,
            "usage_count": 156
        }
    },
    {
        "class": "LearnedPattern",
        "properties": {
            "name": "wilson_interval_canary_eval",
            "tags": ["statistics", "canary", "ab_test"],
            "snippet": "wilson_score_interval(successes, trials, confidence=0.95)",
            "notes": "Use Wilson intervals for canary evaluation. Prevents false rollbacks.",
            "task_type": "canary_evaluation",
            "success_rate": 1.0,
            "usage_count": 23
        }
    }
]


def main():
    """Main entry point"""
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║          Weaviate Schema + Seed                                ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")

    # Check Weaviate is running
    try:
        response = requests.get(f"{WEAVIATE_URL}/v1/.well-known/ready", timeout=5)
        if response.status_code != 200:
            print("❌ Weaviate not ready")
            return 1
        print("✅ Weaviate is ready\n")
    except Exception as e:
        print(f"❌ Cannot connect to Weaviate: {e}")
        print("   Start with: docker compose up -d weaviate")
        return 1

    # Create schema
    print("[1/2] Creating schema...")
    for schema_class in SCHEMA_CLASSES:
        class_name = schema_class["class"]

        try:
            response = requests.post(
                f"{WEAVIATE_URL}/v1/schema",
                json=schema_class,
                timeout=5
            )

            if response.status_code in [200, 422]:  # 422 = already exists
                print(f"   ✓ {class_name}")
            else:
                print(f"   ⚠ {class_name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ✗ {class_name}: {e}")

    # Seed patterns
    print("\n[2/2] Seeding learned patterns...")
    for pattern in SEED_PATTERNS:
        name = pattern["properties"]["name"]

        try:
            response = requests.post(
                f"{WEAVIATE_URL}/v1/objects",
                json=pattern,
                timeout=5
            )

            if response.status_code in [200, 422]:
                print(f"   ✓ {name}")
            else:
                print(f"   ⚠ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ✗ {name}: {e}")

    print("\n" + "="*68)
    print("✅ Weaviate Seeded")
    print("="*68)
    print(f"\n📊 Classes: {len(SCHEMA_CLASSES)}")
    print(f"📚 Patterns: {len(SEED_PATTERNS)}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
