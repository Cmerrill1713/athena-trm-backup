# 🚀 Athena Operational Readiness Guide

## ✅ System Status: Production Ready

Your Athena AGI stack is now **boring-reliable** and operationally hardened with:

- **LLM-Agnostic Architecture**: Router handles model selection with `model: "auto"`
- **21/21 Smoke Tests Passing**: Complete system verification
- **TRM Adaptive Policy**: Learning and self-tuning reasoning
- **Dynamic RAG**: Multi-tier retrieval with 1.5M+ vectors
- **Automated Monitoring**: Hourly health checks + nightly RAG updates

## 🔧 Keep-It-Green Commands

### Daily Operations

```bash
# Quick system health check
make system-smoke

# Operational status overview
make ops-status

# View recent logs
make ops-logs
```

### RAG Management

```bash
# Seed RAG for immediate hits
make rag-seed-agi     # Fast, small seed
make rag-seed-full    # Full repo seed (best accuracy)

# Test RAG quality
make rag-golden       # Should get 8-9/10 after full seed
```

### TRM Tuning

```bash
# Make TRM more aggressive (lower threshold = more TRM)
export TRM_TRIGGER_THRESH=0.45   # Default ~0.60
make stack-restart

# Force TRM for demo
curl -sX POST :8000/api/execute \
  -H 'content-type: application/json' \
  -d '{"objective":"demo trm","tools":[],"max_steps":1,"flags":{"force_trm":true,"adaptive_trm":true}}' | jq .

# Check TRM policy stats
curl :8000/trm/policy | jq .stats
```

## 🤖 Automated Operations

### Set Up Monitoring (One-time)

```bash
# Hourly smoke tests
make smoke-cron-setup

# Nightly RAG delta updates
make rag-delta-setup

# Import Grafana health dashboard
make grafana-import-health
```

### Remove Automation

```bash
make smoke-cron-remove
```

## 🚨 Troubleshooting

### Common Issues & Fixes

**"RAG returns 0 hits"**

- Weaviate is running but empty → `make rag-seed-agi`
- Cross-check with smoke test → `make system-smoke`

**"TRM never fires"**

- Check policy stats → `curl :8000/trm/policy | jq .stats`
- Lower threshold → `export TRM_TRIGGER_THRESH=0.45`
- Force for testing → Use `flags: {"force_trm": true}`

**"Service 404/timeout"**

- Almost always network isolation → Start via compose to join common network
- Check service health → `make ops-status`

**"Weaviate not ready"**

- Container running but still loading 1.5M vectors → Wait 2-3 minutes
- Check readiness → `curl http://localhost:8090/v1/.well-known/ready`

## 📊 Monitoring Dashboard

The Grafana dashboard (`config/grafana_system_health_dashboard.json`) provides:

- **🎯 System Health Score**: 6-service uptime percentage
- **🚀 TRM Activity**: Predictions per hour
- **🧠 RAG Performance**: P95 latency with thresholds
- **📊 Model Swaps**: Hot-swap frequency monitoring
- **🎯 Overall Score**: Combined health metric

## 🎛️ Configuration

### Router Policy (LLM Selection)

The router automatically selects models based on complexity:

- **Low complexity** → Fast models (qwen2.5:0.5b)
- **Medium complexity** → Balanced models (7B)
- **High complexity** → Precise models (14B)

### TRM Adaptive Policy

- **Conservative by default**: Skips until confidence > threshold
- **Learning enabled**: Adapts based on task outcomes
- **Configurable thresholds**: Adjust `TRM_TRIGGER_THRESH` for more/less TRM

### RAG Dynamic Routing

- **Multi-tier retrieval**: Mini → Base → Long based on query complexity
- **Hybrid search**: Vector KNN + BM25 keyword fusion
- **Context budgeting**: Caps injected context to 20-25% of model context

## 🚀 Production Checklist

- [x] All services healthy and cross-networked
- [x] LLM-agnostic routing with `model: "auto"`
- [x] TRM adaptive policy learning and operational
- [x] Dynamic RAG with 1.5M+ vectors loaded
- [x] Comprehensive smoke tests (21/21 passing)
- [x] Automated monitoring and alerting
- [x] Nightly RAG delta updates
- [x] Grafana health dashboard
- [x] Operational runbooks and troubleshooting guides

## 🎉 You're Ready!

Your Athena system is now **production-hardened** with:

- **Boring reliability**: Automated monitoring and self-healing
- **LLM agnosticism**: Router handles model selection transparently
- **Adaptive intelligence**: TRM learns and improves over time
- **Rich context**: RAG provides relevant information for complex tasks
- **Operational visibility**: Comprehensive logging and metrics

The system will automatically maintain itself with hourly health checks and nightly RAG updates. Just monitor the Grafana dashboard for the green health score! 🚀
