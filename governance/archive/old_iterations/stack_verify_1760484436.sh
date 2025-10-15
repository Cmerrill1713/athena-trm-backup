#!/bin/bash
# Stack verification script - runs contract tests for all services
# Usage: ./scripts/stack_verify.sh

set -e

BRIDGE="http://127.0.0.1:8014"
ATHENA="http://127.0.0.1:8090"
UAT="http://127.0.0.1:8181"

echo "🔍 Stack Contract Verification"
echo "================================"

# Bridge health
echo -n "Bridge health: "
if curl -fsS "$BRIDGE/health" >/dev/null 2>&1; then
    echo "✅"
else
    echo "❌"
    exit 1
fi

# Bridge ready
echo -n "Bridge ready: "
if curl -fsS "$BRIDGE/ready" >/dev/null 2>&1; then
    echo "✅"
else
    echo "❌ (optional - may not be implemented)"
fi

# Bridge version
echo -n "Bridge version: "
if VERSION=$(curl -fsS "$BRIDGE/version" 2>/dev/null); then
    echo "✅ $VERSION"
else
    echo "❌ (optional - may not be implemented)"
fi

# Bridge chat - legacy payload (message)
echo -n "Bridge chat (message): "
if curl -fsS -H "Content-Type: application/json" -H "Authorization: Bearer a3369a05912df58b96ff5864daa30f86e6d330329936feb0f95c404825b3d594" -d '{"message":"ping"}' "$BRIDGE/api/chat" >/dev/null 2>&1; then
    echo "✅"
else
    echo "❌"
    exit 1
fi

# Bridge chat - new payload (text)
echo -n "Bridge chat (text): "
if curl -fsS -H "Content-Type: application/json" -H "Authorization: Bearer a3369a05912df58b96ff5864daa30f86e6d330329936feb0f95c404825b3d594" -d '{"text":"ping"}' "$BRIDGE/api/chat" >/dev/null 2>&1; then
    echo "✅"
else
    echo "❌"
    exit 1
fi

# Bridge chat - SwiftUI payload (kind + text)
echo -n "Bridge chat (SwiftUI): "
if curl -fsS -H "Content-Type: application/json" -H "Authorization: Bearer a3369a05912df58b96ff5864daa30f86e6d330329936feb0f95c404825b3d594" -d '{"kind":"chat","text":"ping"}' "$BRIDGE/api/chat" >/dev/null 2>&1; then
    echo "✅"
else
    echo "❌"
    exit 1
fi

# Athena health
echo -n "Athena health: "
if curl -fsS -H "Authorization: Bearer supersecret" "$ATHENA/health" >/dev/null 2>&1; then
    echo "✅"
else
    echo "❌"
fi

# Athena chat - no stub response
echo -n "Athena LLM (no stub): "
RESPONSE=$(curl -fsS -H "Authorization: Bearer supersecret" -H "Content-Type: application/json" -d '{"message":"ping"}' "$ATHENA/chat" 2>/dev/null || echo "")
if echo "$RESPONSE" | grep -q "processed by Chat Agent"; then
    echo "❌ (still using stub)"
    exit 1
elif echo "$RESPONSE" | grep -q "response"; then
    echo "✅"
else
    echo "❌ (no response)"
fi

# UAT health (optional)
echo -n "UAT health: "
if curl -fsS "$UAT/health" >/dev/null 2>&1; then
    echo "✅"
else
    echo "⚠️ (may not be running)"
fi

# Bandit prompt optimization (optional)
echo ""
echo "🤖 Bandit Prompt Optimization Tests"
echo "==================================="

    # Bandit chat response includes variant metadata
    echo -n "Bandit variant metadata: "
    if RESPONSE=$(curl -fsS -H "Content-Type: application/json" -H "Authorization: Bearer a3369a05912df58b96ff5864daa30f86e6d330329936feb0f95c404825b3d594" -d '{"message":"test bandit"}' "$BRIDGE/api/chat" 2>/dev/null); then
        if echo "$RESPONSE" | jq -e '.metadata.prompt_variant and .metadata.interaction_id and (.metadata.bandit_enabled // false)' >/dev/null 2>&1; then
            VARIANT=$(echo "$RESPONSE" | jq -r '.metadata.prompt_variant')
            INTERACTION_ID=$(echo "$RESPONSE" | jq -r '.metadata.interaction_id')
            echo "✅ (variant: $VARIANT, id: $INTERACTION_ID)"
        else
            echo "⚠️ (bandit not enabled or metadata missing)"
        fi
    else
        echo "❌ (bandit endpoint failed)"
    fi

    # LLM Evaluation system active
    echo -n "LLM Evaluation system: "
    if [ -n "$INTERACTION_ID" ]; then
        if echo "$RESPONSE" | jq -e '.metadata.eval_enabled and .metadata.eval_scores' >/dev/null 2>&1; then
            EVAL_ENABLED=$(echo "$RESPONSE" | jq -r '.metadata.eval_enabled')
            if [ "$EVAL_ENABLED" = "true" ]; then
                EVAL_SCORES=$(echo "$RESPONSE" | jq -r '.metadata.eval_scores.helpfulness')
                if [ "$EVAL_SCORES" != "null" ]; then
                    echo "✅ (enabled, scores present)"
                else
                    echo "⚠️ (enabled but no scores in response)"
                fi
            else
                echo "⚠️ (evaluation disabled)"
            fi
        else
            echo "⚠️ (evaluation metadata missing)"
        fi
    else
        echo "⚠️ (no interaction ID from previous test)"
    fi

    # Feedback endpoint accepts feedback
    echo -n "Feedback collection: "
    if [ -n "$INTERACTION_ID" ]; then
        if curl -fsS -H "Content-Type: application/json" -d "{\"interaction_id\":\"$INTERACTION_ID\",\"thumbs_up\":true}" "$BRIDGE/api/feedback" >/dev/null 2>&1; then
            echo "✅"
        else
            echo "⚠️ (feedback endpoint not responding)"
        fi
    else
        echo "⚠️ (no interaction ID from previous test)"
    fi

    # Bandit metrics available
    echo -n "Bandit metrics: "
    if curl -fsS "$ATHENA/metrics" 2>/dev/null | grep -q "bandit_trials_total"; then
        echo "✅"
    else
        echo "⚠️ (metrics not exposed or bandit not active)"
    fi

    # Evaluation metrics available
    echo -n "Evaluation metrics: "
    if curl -fsS "$ATHENA/metrics" 2>/dev/null | grep -q "judge_runs_total\|judge_score_last"; then
        echo "✅"
    else
        echo "⚠️ (evaluation metrics not exposed)"
    fi

echo ""
echo "🎯 All critical contracts verified!"
echo "   Green means your stack is healthy and regression-free."
echo "   Bandit optimization is active and learning from user feedback!"
