#!/usr/bin/env bash
# Final GO/NO-GO validation before ship

set -e
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

printf '%s\n' "========================================"
printf '%s\n' "FINAL GO/NO-GO VALIDATION"
printf '%s\n' "========================================"
printf '\n'

PASS=0
FAIL=0
WARN=0

check() {
    local name="$1"
    local cmd="$2"
    local critical="${3:-true}"
    
    printf 'Checking %s ... ' "$name"
    
    if eval "$cmd" >/dev/null 2>&1; then
        printf 'GO\n'
        PASS=$((PASS + 1))
        return 0
    else
        if [ "$critical" = "true" ]; then
            printf 'NO-GO\n'
            FAIL=$((FAIL + 1))
            return 1
        else
            printf 'WARN\n'
            WARN=$((WARN + 1))
            return 0
        fi
    fi
}

printf '%s\n' "Critical Gates:"
printf '\n'

# Gate 1: Core services
check "Bridge :8014" "curl -sf http://127.0.0.1:8014/ready"
check "Athena :8090" "curl -sf http://127.0.0.1:8090/ready"
check "UAT :8181" "curl -sf http://127.0.0.1:8181/ready"
check "Kokoro :8020" "curl -sf http://127.0.0.1:8020/health"

printf '\n%s\n' "Observability Gates:"
printf '\n'

# Gate 2: Observability
check "Prometheus :9090" "curl -sf http://localhost:9090/-/healthy" false
check "Alert rules valid" "[ -f prometheus/alerts/slo_rules.yaml ]" false
check "Dashboards exist" "[ -f grafana/dashboards/redaction_dashboard.json ]" false

printf '\n%s\n' "Code Quality Gates:"
printf '\n'

# Gate 3: Code quality
check "Scripts executable" "[ -x grafana/import_dashboards.sh ]"
check "No encoding issues" "! grep -rP '[^\x00-\x7F]' NeuroForgeApp/scripts/*.sh 2>/dev/null | grep -v '^$'" false

printf '\n%s\n' "App Gates:"
printf '\n'

# Gate 4: App files
check "Ops files exist" "[ -f NeuroForgeApp/Sources/Ops/OpsState.swift ]" false
check "Config files exist" "[ -f config/routing_policy.yaml ]"
check "Eval framework exists" "[ -f eval/tandem.yaml ]"

printf '\n%s\n' "========================================"
printf '%s\n' "RESULTS:"
printf '  GO:     %d\n' "$PASS"
printf '  WARN:   %d\n' "$WARN"
printf '  NO-GO:  %d\n' "$FAIL"
printf '%s\n' "========================================"
printf '\n'

if [ $FAIL -eq 0 ]; then
    printf '%s\n' "STATUS: GO FOR SHIP"
    printf '\n%s\n' "Next steps:"
    printf '  1. Start Grafana (if warnings)\n'
    printf '  2. Import dashboards: make grafana-import\n'
    printf '  3. Tag release: git tag v0.9.6\n'
    printf '  4. Push: git push origin v0.9.6\n'
    printf '  5. Deploy: ./tools/ship_it.sh\n'
    exit 0
else
    printf '%s\n' "STATUS: NO-GO - Fix failures before ship"
    printf '\n%s\n' "Critical failures detected. Address them first."
    exit 1
fi

