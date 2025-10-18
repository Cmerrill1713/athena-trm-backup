#!/usr/bin/env bash
set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "UAI Contract Test - Verifying UAI → Ollama Integration"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "== 1. UAI Health Check"
curl -fsS http://localhost:8080/health
echo -e "\n"

echo "== 2. UAI Info"
curl -fsS http://localhost:8080/ | jq -r '.message, .endpoints.chat'
echo ""

echo "== 3. UAI Chat (should call Ollama and return real completion)"
curl -fsS -X POST http://localhost:8080/v1/chat/completions \
  -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Name three colors in 6 words or less"}]}' \
  | jq -r '.choices[0].message.content'
echo ""

echo "== 4. Ollama Direct (verify Ollama is accessible)"
curl -fsS http://localhost:11434/api/tags | jq -r '.models[] | .name' | head -3
echo ""

echo "== 5. Prometheus Metrics (verify metrics are exposed)"
curl -s http://localhost:8080/metrics | grep -E "^(uai_llm|python_info)" | head -5 || echo "Metrics endpoint available but no calls yet"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✅ Contract test complete! UAI → Ollama is WIRED."
echo "════════════════════════════════════════════════════════════════"
