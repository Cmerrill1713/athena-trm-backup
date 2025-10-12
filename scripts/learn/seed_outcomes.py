#!/usr/bin/env python3
"""
Seed some routing outcomes for testing the learning system
"""

import sys
sys.path.insert(0, '/Users/christianmerrill/Documents/GitHub')

from scripts.learn.outcome_logger import log_routing_decision
import random

prompts = [
    "Explain quantum computing",
    "Analyze this image of a neural network",
    "What's the weather in SF?",
    "Debug this Python code",
    "Summarize this research paper"
]

models = [
    "mlx/chat",
    "mlx/reason",
    "fastvlm/vision",
    "ollama/tool",
    "hybrid/rag"
]

print("🌱 Seeding routing outcomes...")

for i in range(50):
    prompt = random.choice(prompts)
    model = random.choice(models)
    engine, mode = model.split("/")
    
    policy = {
        "engine": engine,
        "mode": mode,
        "rag_enabled": random.choice([True, False]),
        "safety_web": False,
        "safety_shell": False
    }
    
    latency = random.uniform(50, 500)
    success = random.random() > 0.05  # 95% success rate
    
    log_routing_decision(
        prompt=f"{prompt} (test {i+1})",
        policy=policy,
        selected_model=model,
        latency_ms=latency,
        success=success,
        user_feedback=None,
        meta={"channel": "test", "seed": True}
    )
    
    if (i + 1) % 10 == 0:
        print(f"   ✅ Logged {i+1} outcomes...")

print(f"✅ Seeded {50} routing outcomes")
print("")
print("📊 Verify with: make learn-stats")

