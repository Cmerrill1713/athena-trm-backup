#!/bin/bash
# Validate all service integrations are up and responding

set -e
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

printf '%s\n\n' "Validating Service Integrations..."

# Service endpoints
BRIDGE="http://127.0.0.1:8014/ready"
ATHENA="http://127.0.0.1:8090/ready"
UAT="http://127.0.0.1:8181/health"
KOKORO="http://127.0.0.1:8020/health"

# Test function
check_service() {
    local name=$1
    local url=$2
    
    if curl -sf -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" | grep -q "200"; then
        printf "${GREEN}OK${NC} %s ready\n" "$name"
        return 0
    else
        printf "${RED}FAIL${NC} %s DOWN\n" "$name"
        return 1
    fi
}

# Check all services
up=0
total=4

if check_service "Bridge" "$BRIDGE"; then ((up++)); fi
if check_service "Athena" "$ATHENA"; then ((up++)); fi
if check_service "UAT" "$UAT"; then ((up++)); fi
if check_service "Kokoro" "$KOKORO"; then ((up++)); fi

printf '\n'
printf '%s\n' "========================================"

# Status summary
if [ $up -eq $total ]; then
    printf "${GREEN}OK${NC} All services up: %d/%d\n" "$up" "$total"
    exit 0
elif [ $up -ge 3 ]; then
    printf "${YELLOW}WARN${NC} Partial services: %d/%d\n" "$up" "$total"
    exit 0
else
    printf "${RED}FAIL${NC} Insufficient services: %d/%d\n" "$up" "$total"
    printf '\n%s\n' "Start services with:"
    printf '  %s\n' "make stack-full"
    exit 1
fi

