#!/usr/bin/env bash
set -euo pipefail
services=("athena-router" "governance-orchestrator" "governance-metrics-exporter" "governance-canary-monitor" \
          "agi-remediator" "athena-mcp-ecosystem" "fastvlm" "kokoro-tts")

echo "== Compose ps (key services) =="
docker compose ps "${services[@]}" || true
echo

echo "== Health endpoints =="
declare -A ports=(
  ["athena-router"]=9113
  ["governance-orchestrator"]=9110
  ["athena-mcp-ecosystem"]=8412
  ["fastvlm"]=8088
  ["kokoro-tts"]=8091
)
for s in "${!ports[@]}"; do
  p="${ports[$s]}"
  printf "%-26s :%s  " "$s" "$p"
  curl -fsS "http://localhost:$p/health" >/dev/null 2>&1 && echo OK || echo FAIL
done
echo

echo "== Recent logs (errors last) =="
for s in "${services[@]}"; do
  echo "--- $s"; docker compose logs --since=10m "$s" | tail -n 150 | grep -E "ERROR|WARN|Exception|Traceback|Refused|timeout|connection" || true; echo
done

echo "== Prometheus targets =="
curl -fsS 'http://localhost:9090/api/v1/targets' | jq '.data.activeTargets[] | {job: .labels.job, health: .health, lastError: .lastError}' 2>/dev/null || echo "Prometheus not reachable"
