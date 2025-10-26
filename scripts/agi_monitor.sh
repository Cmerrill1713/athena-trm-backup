#!/usr/bin/env bash

MODE=${1:-all}

case "$MODE" in
    trace)
        echo "📊 AGI Task Trace (live):"
        docker compose logs -f agi-core | grep -i --line-buffered "task\|step\|agent"
        ;;
    
    metrics)
        echo "📈 Metrics (updating every 1s, Ctrl+C to stop):"
        watch -n 1 'echo "=== AGI Core ==="; curl -s http://localhost:8000/metrics | grep -E "agi_tasks_total|agi_steps_total"; echo ""; echo "=== LLM Gateway ==="; curl -s http://localhost:8015/metrics | grep llm_gateway_calls_total || curl -s http://localhost:8080/metrics | grep uai_llm_calls_total'
        ;;
    
    frontend)
        echo "🔧 Frontend Tools Activity:"
        docker compose logs -f mcp-frontend-tools 2>/dev/null || echo "No mcp-frontend-tools service found"
        ;;
    
    status)
        echo "════════════════════════════════════════════════════════════════"
        echo "  📊 AGI Fix Status"
        echo "════════════════════════════════════════════════════════════════"
        echo ""
        
        # Check lock
        if [ -f /tmp/agi_frontend_fix.lock ]; then
            echo "Status:     🔄 RUNNING"
        else
            echo "Status:     💤 IDLE"
        fi
        
        # Check metrics
        echo ""
        echo "AGI Core Metrics:"
        curl -s http://localhost:8000/metrics 2>/dev/null | grep -E "agi_tasks_total|agi_steps_total" || echo "  No metrics available"
        
        echo ""
        echo "Latest logs (last 10 lines):"
        docker compose logs agi-core --tail=10 2>/dev/null | tail -10
        ;;
    
    all)
        echo "════════════════════════════════════════════════════════════════"
        echo "  🔍 AGI Monitoring Dashboard"
        echo "════════════════════════════════════════════════════════════════"
        echo ""
        echo "Available modes:"
        echo "  ./scripts/agi_monitor.sh trace     - Live task trace"
        echo "  ./scripts/agi_monitor.sh metrics   - Live metrics (1s refresh)"
        echo "  ./scripts/agi_monitor.sh frontend  - Frontend tools logs"
        echo "  ./scripts/agi_monitor.sh status    - Current status snapshot"
        echo ""
        echo "Quick checks:"
        ./scripts/agi_monitor.sh status
        ;;
esac
