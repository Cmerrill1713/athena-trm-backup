#!/bin/bash
# Continuous Testing Loop - Keep validating Athena

echo "🔄 CONTINUOUS ATHENA TESTING"
echo "Running comprehensive tests every 5 minutes..."
echo "Press Ctrl+C to stop"
echo ""

while true; do
    echo "⏰ $(date '+%H:%M:%S') - Running tests..."
    echo ""
    
    # Run comprehensive test
    python3 test_full_system_continuous.py
    
    # Save timestamped results
    cp comprehensive_test_results.json "test_results/results_$(date +%Y%m%d_%H%M%S).json"
    
    echo ""
    echo "✅ Test complete. Sleeping 5 minutes..."
    echo "Next test at: $(date -v+5M '+%H:%M:%S')"
    echo ""
    
    sleep 300  # 5 minutes
done
