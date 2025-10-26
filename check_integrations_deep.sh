#!/bin/bash
echo "🔗 CHECKING ALL SERVICE INTEGRATIONS"
echo "========================================================================"
echo ""

echo "1️⃣  UAI Integration Points..."
echo "--------------------------------------------------------------------"
grep -r "http://\|https://" AI-Projects/universal-ai-tools/api/*.py 2>/dev/null | \
  grep -v "#" | grep -o "http://[^\"']*" | sort -u | head -20

echo ""
echo "2️⃣  Router Integration Points..."
echo "--------------------------------------------------------------------"
grep -r "http://\|https://" services/router/*.py 2>/dev/null | \
  grep -v "#" | grep -o "http://[^\"']*" | sort -u | head -15

echo ""
echo "3️⃣  Learning System Integration Points..."
echo "--------------------------------------------------------------------"
grep -r "http://\|https://" services/learning-agents/*.py 2>/dev/null | \
  grep -v "#" | grep -o "http://[^\"']*" | sort -u | head -15

echo ""
echo "4️⃣  Checking for external API integrations..."
echo "--------------------------------------------------------------------"
grep -r "api\.openai\|api\.anthropic\|api\.google" --include="*.py" \
  services/ AI-Projects/ 2>/dev/null | head -5 || echo "  ✅ No external cloud APIs (local-first confirmed!)"

echo ""
echo "5️⃣  Checking Prometheus scrape targets..."
echo "--------------------------------------------------------------------"
if [ -f "prometheus/prometheus.yml" ]; then
    grep "targets:" prometheus/prometheus.yml | head -10
else
    echo "  Checking via Docker..."
    docker exec athena-prometheus cat /etc/prometheus/prometheus.yml 2>/dev/null | \
      grep -A 1 "targets:" | head -20
fi

echo ""
echo "✅ Integration check complete!"
