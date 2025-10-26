#!/bin/bash
echo "⚙️  TESTING MAKEFILE AUTOMATION FEATURES"
echo "========================================================================"
echo ""

if [ ! -f "Makefile" ]; then
    echo "❌ No Makefile found"
    exit 1
fi

echo "Testing Makefile targets..."
echo ""

# Test safe read-only targets
echo "1. wire-check (Verify system wiring):"
make wire-check 2>&1 | head -10 || echo "  ⚠️  Target may need setup"

echo ""
echo "2. prom-verify (Check Prometheus targets):"
make prom-verify 2>&1 | head -10 || echo "  ⚠️  Target may need setup"

echo ""
echo "3. repo-inventory (Generate file inventory):"
make repo-inventory 2>&1 | head -10 || echo "  ⚠️  Target may need setup"

echo ""
echo "4. wire-report (Wiring validation report):"
make wire-report 2>&1 | head -15 || echo "  ⚠️  Target may need setup"

echo ""
echo "✅ Makefile feature test complete!"
