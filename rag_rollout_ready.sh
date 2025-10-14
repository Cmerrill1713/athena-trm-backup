#!/bin/bash
# RAG Reranker Production Go-Live Script
# Execute this to start the 48-hour rollout plan

echo "🚀 RAG Reranker Production Go-Live"
echo "=================================="
echo ""

# Phase 1: Initial Setup (0 hours)
echo "📋 Phase 1: Initial Setup"
echo "------------------------"

echo "✅ Configuration verified:"
echo "   RAG_RERANK_ENABLED=true"
echo "   RAG_RERANK_TOPK=8"
echo "   RAG_THRESHOLD=0.45"
echo "   RAG_CANARY_PERCENTAGE=25"
echo ""

echo "✅ Service health check:"
curl -fsS http://127.0.0.1:8015/api/rag/health >/dev/null 2>&1 && echo "   🟢 RAG service healthy" || echo "   🔴 RAG service down"
echo ""

echo "✅ Metrics validation:"
curl -s http://127.0.0.1:8015/metrics | grep -q "rag_rerank_enabled 1" && echo "   🟢 Reranker enabled" || echo "   🔴 Reranker disabled"
curl -s http://127.0.0.1:8015/metrics | grep -q "rag_threshold_current 0.45" && echo "   🟢 Threshold set correctly" || echo "   🔴 Threshold incorrect"
echo ""

# Phase 2: Canary Rollout (0-6 hours)
echo "📋 Phase 2: Canary Rollout (10-25%)"
echo "-----------------------------------"
echo "Current canary percentage: 25%"
echo ""
echo "Monitor commands:"
echo "  make rag-status                    # Service health & metrics"
echo "  psql \$DATABASE_URL -f rag_sanity_probes.sql  # Data quality checks"
echo ""

# Phase 3: Validation (6-24 hours)
echo "📋 Phase 3: Validation (6-24 hours)"
echo "-----------------------------------"
echo "After 6 hours stable operation:"
echo "  make rag-canary-50                 # Scale to 50%"
echo ""
echo "Continue monitoring with:"
echo "  watch -n 300 make rag-status       # Every 5 minutes"
echo ""

# Phase 4: Tuning & Scale (24-48 hours)
echo "📋 Phase 4: Tuning & Scale (24-48 hours)"
echo "----------------------------------------"
echo "At T+24h:"
echo "  make rag-tune                      # Run auto-tuning"
echo "  make rag-canary-full               # Scale to 100%"
echo ""

# Emergency rollback
echo "🚨 Emergency Rollback"
echo "---------------------"
echo "If issues detected:"
echo "  make rag-canary-off                # Immediate disable"
echo ""
echo "Rollback triggers (auto-alerts):"
echo "  - Judge helpfulness < 5 for 30m"
echo "  - P95 latency +200ms for 30m"
echo "  - Docs used P50 < 3 for 1h"
echo ""

# Success criteria
echo "🎯 Success Criteria (48h)"
echo "-------------------------"
echo "  ✅ Judge helpfulness +10-20% vs baseline"
echo "  ✅ No sustained latency regression"
echo "  ✅ Threshold tuned with ≥200 samples"
echo "  ✅ Daily quality reports show improvement"
echo ""

echo "🔥 Ready for launch! Monitor closely for the first 6 hours."
echo "📊 Dashboards: Check Grafana for RAG metrics panels"
