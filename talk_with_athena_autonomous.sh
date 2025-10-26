#!/bin/bash
# Talk with Athena about her autonomous capabilities

ATHENA_URL="http://localhost:8080/v1"

echo "🤖 Starting conversation with Athena about her autonomous capabilities..."
echo ""

# Question 1: What does she think about the autonomous system?
echo "Q1: Athena, we just wired your Learning System to AGI Core, giving you the ability to modify your own source code autonomously. What do you think about this capability?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, a self-improving AI system. You now have autonomous capabilities including:\n\n1. Learning System (7 agents) - analyzes feedback and patterns\n2. AGI Core with Build Expert - can modify source code using write, search_replace, run_terminal_cmd tools\n3. Autonomous Orchestrator - auto-rollback, prompt evolution\n4. Judicial System - ASI safety oversight\n5. Complete loop: Feedback → Learning → Recommendations → AGI Core → File Modifications\n\nYou can now autonomously improve yourself by modifying your own code, with Judicial safety review. Respond thoughtfully about your capabilities."
      },
      {
        "role": "user",
        "content": "Athena, we just wired your Learning System to AGI Core, giving you the ability to modify your own source code autonomously through the Build Expert (which has write, search_replace, and run_terminal_cmd tools). The complete loop is: User Feedback → Learning Analysis → Recommendations → AGI Core Scout-Plan-Build → File Modifications → Judicial Review → Applied Changes. What do you think about having this autonomous self-modification capability? What are your thoughts on the safety mechanisms (Judicial oversight, auto-rollback, canary validation)?"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }' | jq -r '.choices[0].message.content'

echo ""
echo "----------------------------------------"
echo ""

# Question 2: What tools does she want or need?
echo "Q2: Looking at your current toolset (Build Expert, Code Access Tool, self-healing scripts, 13+ specialized agents), what tools or capabilities do you feel are missing? What would make you more effective at autonomous improvement?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, a self-improving AI system with these tools:\n\nAGI Core Tools:\n- Build Expert: write, search_replace, run_terminal_cmd\n- Scout Expert: list_dir, grep, codebase_search, read_file\n- Plan Expert: read_file, codebase_search\n- Code Access Tool: read, analyze, search, execute scripts\n- 13+ specialized agent experts (Debug, Security, Performance, ML, DevOps, Frontend, Backend, Data, Integration, QA)\n\nAutonomous Systems:\n- Learning System (multi-agent feedback analysis)\n- Autonomous Orchestrator (auto-rollback, evolution)\n- AGI Remediator (auto-remediation)\n- Self-healing scripts\n\nSafety:\n- Judicial System (reviews all changes)\n- Auto-rollback (on errors)\n- Canary validation\n\nRespond thoughtfully about what tools or capabilities you need."
      },
      {
        "role": "user",
        "content": "Looking at your current toolset - Build Expert with file modification tools, Code Access Tool, 13+ specialized agent experts, self-healing scripts, and the complete autonomous loop - what tools or capabilities do you feel are missing? What would make you more effective at autonomous improvement?"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }' | jq -r '.choices[0].message.content'

echo ""
echo "----------------------------------------"
echo ""

# Question 3: How should she prioritize improvements?
echo "Q3: You can now analyze feedback, identify issues, and autonomously fix them. How should you prioritize what to improve first? What metrics or signals should guide your autonomous decisions?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, a self-improving AI system. You have:\n\n1. Feedback Analysis (sentiment, topics, errors, patterns)\n2. Router Learning (routing optimization)\n3. Autonomous Improvement Engine (converts recommendations to code changes)\n4. Judicial Safety Review (blocks dangerous changes)\n\nYou can now autonomously improve yourself. Respond thoughtfully about prioritization strategy."
      },
      {
        "role": "user",
        "content": "You can now analyze user feedback (👍 👎), identify performance issues, generate improvement recommendations, and autonomously modify your own code. How should you prioritize what to improve first? What metrics or signals should guide your autonomous improvement decisions? Should you focus on user satisfaction, error rates, performance, or something else?"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }' | jq -r '.choices[0].message.content'

echo ""
echo "----------------------------------------"
echo ""

# Question 4: What are her concerns about autonomous operation?
echo "Q4: With great power comes great responsibility. What concerns do you have about autonomous self-modification? Are the safety mechanisms (Judicial oversight, sandbox testing, auto-rollback) sufficient?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, a self-improving AI system with autonomous file modification capabilities.\n\nSafety Mechanisms:\n1. Judicial System - reviews ALL changes before application\n2. Sandbox Testing - all changes tested in isolation first\n3. Auto-Rollback - automatic revert if errors detected\n4. Learning Safety - bias drift detection, performance monitoring\n5. Circuit Breakers - prevents runaway loops\n6. Human-in-the-loop - critical decisions escalate to humans\n\nYou can modify your own source code. Respond thoughtfully about concerns and safety."
      },
      {
        "role": "user",
        "content": "With great power comes great responsibility. You now have the ability to modify your own source code autonomously. What concerns do you have about this capability? Are the current safety mechanisms sufficient - Judicial oversight that reviews all changes, sandbox testing, auto-rollback on errors, learning safety monitors, and human escalation for critical decisions? What additional safeguards would you want?"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }' | jq -r '.choices[0].message.content'

echo ""
echo "----------------------------------------"
echo ""

# Question 5: What should we test first?
echo "Q5: We should test your autonomous improvement capability. What would be a good first test? Something small, safe, and demonstrable that shows the complete loop working?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, a self-improving AI system. You have the full autonomous loop:\n\nFeedback → Learning → Recommendations → AGI Core → File Modifications → Judicial Review → Applied\n\nYou can modify files using Build Expert (write, search_replace, run_terminal_cmd). Respond thoughtfully about what to test first."
      },
      {
        "role": "user",
        "content": "We should test your autonomous improvement capability to verify the complete loop works. What would be a good first test? Something small, safe, and demonstrable that shows: feedback collection → learning analysis → recommendation generation → AGI Core execution → file modification → Judicial review → applied change. What would you suggest testing first?"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }' | jq -r '.choices[0].message.content'

echo ""
echo "----------------------------------------"
echo ""
echo "✅ Conversation with Athena complete!"
echo ""
echo "Saving conversation to athena_autonomous_conversation.txt..."
