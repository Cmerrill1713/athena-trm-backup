#!/usr/bin/env bash
set -euo pipefail
mkdir -p logs/archive
ts=$(date +%F_%H%M%S)
[ -f logs/canary_decisions.log ] || exit 0
cp logs/canary_decisions.log "logs/archive/canary_decisions.$ts.log"
: > logs/canary_decisions.log
gzip -9 "logs/archive/canary_decisions.$ts.log"
sha256sum "logs/archive/canary_decisions.$ts.log.gz" > "logs/archive/canary_decisions.$ts.log.gz.sha256"
