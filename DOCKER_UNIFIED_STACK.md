# Athena Unified Docker Stack ✅

**ONE compose file. ALL services. ZERO fragmentation.**

## Overview

Complete production stack with 25 services across 5 layers:
- **A2 Layer:** Local-first model routing
- **A3 Layer:** Governance, policy, and oversight
- **Core Services:** APIs, tools, and integrations
- **Knowledge Layer:** RAG, context, and grounding
- **Observability:** Metrics, monitoring, and alerting
- **Storage:** Databases, cache, and search

## Quick Start

```bash
# Start everything
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop everything
docker-compose down
```

## Service Map

### A2: Local-First Routing (1 service)

| Service | Port | Container | Description |
|---------|------|-----------|-------------|
| Router | 9113 | athena-router | A2 local-first model routing with cloud blocking |

### A3: Governance & Oversight (5 services)

| Service | Port | Container | Description |
|---------|------|-----------|-------------|
| Governance Orchestrator | 9110 | governance-orchestrator | Central governance API |
| Metrics Exporter | 9109 | governance-metrics-exporter | Policy metrics collection |
| Canary Monitor | 9111 | governance-canary-monitor | Auto-rollback controller |
| AGI Remediator | 9112 | agi-remediator | Self-healing agent |
| Governance Exporter | 9108 | governance-exporter | Additional metrics |

### Core Services (4 services)

| Service | Port | Container | Description |
|---------|------|-----------|-------------|
| Athena API | 8888 | athena-api | Main Python API |
| Evolutionary API | 8014 | athena-evolutionary | Self-improvement engine |
| MCP Ecosystem | 8412 | athena-mcp-ecosystem | Model Context Protocol tools |
| Slack Bot | 8082 | governance-slack-bot | Governance notifications |

### Knowledge Layer (3 services)

| Service | Port | Container | Description |
|---------|------|-----------|-------------|
| Knowledge Gateway | 8088 | athena-knowledge-gateway | RAG entry point |
| Knowledge Context | 8091 | athena-knowledge-context | Context enrichment |
| Knowledge Sync | 8089 | athena-knowledge-sync | Vector sync service |

### Observability (8 services)

| Service | Port | Container | Description |
|---------|------|-----------|-------------|
| Prometheus | 9090 | athena-prometheus | Metrics database |
| Pushgateway | 9091 | prometheus-pushgateway | Batch metrics |
| Grafana | 3001 | athena-grafana | Dashboards UI |
| Alertmanager | 9093 | athena-alertmanager | Alert routing |
| Netdata | 19999 | athena-netdata | Real-time monitoring |
| Node Exporter | 9100 | athena-node-exporter | Host metrics |
| Postgres Exporter | 9187 | athena-postgres-exporter | DB metrics |
| Redis Exporter | 9121 | athena-redis-exporter | Cache metrics |

### Storage (4 services)

| Service | Port | Container | Description |
|---------|------|-----------|-------------|
| PostgreSQL | 5432 | athena-postgres | Primary database |
| Redis | 6379 | athena-redis | Cache & queue |
| Weaviate | 8090, 50051 | athena-weaviate | Vector database |
| SearXNG | 8081 | athena-searxng | Meta-search engine |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ATHENA UNIFIED STACK                         │
│                   (docker-compose.yml)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ A2: LOCAL-FIRST ROUTING                                │    │
│  │  • Router (9113) - MLX/Ollama routing                  │    │
│  └────────────────┬───────────────────────────────────────┘    │
│                   │                                             │
│                   ▼                                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ A3: GOVERNANCE & OVERSIGHT                             │    │
│  │  • Orchestrator (9110)   • Remediator (9112)           │    │
│  │  • Metrics (9109)        • Canary (9111)               │    │
│  │  • Exporter (9108)                                     │    │
│  └────────────────┬───────────────────────────────────────┘    │
│                   │                                             │
│                   ▼                                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ CORE SERVICES                                           │   │
│  │  • API (8888)         • MCP Tools (8412)                │   │
│  │  • Evolutionary (8014) • Slack Bot (8082)               │   │
│  └────────────────┬───────────────────────────────────────┘   │
│                   │                                             │
│                   ▼                                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ KNOWLEDGE LAYER                                         │   │
│  │  • Gateway (8088)  • Context (8091)  • Sync (8089)      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ OBSERVABILITY                                           │   │
│  │  • Prometheus (9090)  • Grafana (3001)  • Netdata (19999)│  │
│  │  • Alertmanager (9093) • 4 Exporters                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ STORAGE                                                 │   │
│  │  • Postgres (5432)  • Redis (6379)  • Weaviate (8090)   │   │
│  │  • SearXNG (8081)                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

Network: athena-network (bridge)
All ports: 127.0.0.1 (localhost only)
```

## Prerequisites

Only **MLX** and **Ollama** run on host (for Apple Silicon optimization):

```bash
# Terminal 1: MLX
mlx_lm.server --model mlx-community/qwen2.5-coder-7b --port 8080

# Terminal 2: Ollama
ollama serve
```

All other services run in Docker.

## Health Check

```bash
# Quick check all services
docker-compose ps

# Check individual services
curl http://localhost:9113/health  # Router
curl http://localhost:9110/health  # Governance
curl http://localhost:8888/health  # API
curl http://localhost:8014/health  # Evolutionary
curl http://localhost:8412/health  # MCP

# Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[].labels.job'

# Grafana
open http://localhost:3001  # admin/admin

# Netdata
open http://localhost:19999
```

## Common Operations

### View Logs

```bash
# All services
docker-compose logs -f

# Specific layer
docker-compose logs -f athena-router governance-orchestrator

# Last 100 lines
docker-compose logs --tail=100 -f athena-router
```

### Restart Services

```bash
# Restart single service
docker-compose restart athena-router

# Restart layer
docker-compose restart governance-orchestrator governance-metrics-exporter governance-canary-monitor

# Restart everything
docker-compose restart
```

### Update Configuration

```bash
# Reload Prometheus config without restart
curl -X POST http://localhost:9090/-/reload

# Restart after config changes
docker-compose up -d --force-recreate athena-router
```

### Scale Services

```bash
# Not applicable - all services are singletons
# Future: Use Kubernetes for horizontal scaling
```

## Troubleshooting

### Router Not Healthy

```bash
# Check logs
docker-compose logs athena-router

# Common: MLX not running
mlx_lm.server --model mlx-community/qwen2.5-coder-7b --port 8080

# Verify MLX reachable from container
docker-compose exec athena-router curl http://host.docker.internal:8080/health
```

### Governance Orchestrator Unhealthy

```bash
# Check state file permissions
ls -la state/exec_state.json

# Check dependencies
docker-compose ps athena-postgres athena-redis athena-prometheus

# Restart with dependencies
docker-compose restart athena-prometheus governance-orchestrator
```

### Prometheus Targets Down

```bash
# Check all targets
curl http://localhost:9090/api/v1/targets | jq

# Reload Prometheus
curl -X POST http://localhost:9090/-/reload

# Check service is actually up
docker-compose ps | grep Up
```

### Port Conflicts

```bash
# Find what's using a port
lsof -i :9113

# Stop conflicting service or change port in docker-compose.yml
```

### Out of Disk Space

```bash
# Check Docker disk usage
docker system df

# Clean up old images
docker image prune -a

# Clean up old volumes (CAUTION: removes data)
docker volume prune
```

### Database Connection Issues

```bash
# Check Postgres is healthy
docker-compose exec athena-postgres pg_isready -U postgres

# Check Redis is healthy
docker-compose exec athena-redis redis-cli ping

# Restart database services
docker-compose restart athena-postgres athena-redis
```

## Clean Reset

```bash
# Stop all services
docker-compose down

# Remove volumes (CAUTION: deletes data)
docker-compose down -v

# Clean slate
docker system prune -a --volumes
docker-compose up -d
```

## Data Persistence

All data is stored in named Docker volumes:

| Volume | Service | Size (typical) |
|--------|---------|----------------|
| athena_postgres_data | PostgreSQL | 1-10 GB |
| athena_redis_data | Redis | 100 MB - 1 GB |
| athena_weaviate_data | Weaviate | 5-50 GB |
| athena_prometheus_data | Prometheus | 10-100 GB |
| athena_grafana_data | Grafana | 100 MB |
| athena_netdata_* | Netdata | 500 MB |

### Backup Volumes

```bash
# Backup Postgres
docker-compose exec athena-postgres pg_dump -U postgres knowledge_base > backup.sql

# Backup all volumes
docker run --rm -v athena_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

### Restore Volumes

```bash
# Restore Postgres
cat backup.sql | docker-compose exec -T athena-postgres psql -U postgres knowledge_base

# Restore volume
docker run --rm -v athena_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

## Metrics & Dashboards

### Prometheus Queries

```promql
# Router throughput
rate(athena_router_requests_total[5m])

# Governance verdicts
athena_governance_verdicts_total

# Canary health
athena_canary_error_rate

# Database connections
pg_stat_activity_count
```

### Grafana Dashboards

Import these dashboards:
- Platform Health Glance (ID: 1)
- Router Performance (ID: 2)
- Governance Overview (ID: 3)
- Service Health (ID: 4)

## Environment Variables

```bash
# Optional: Slack notifications
export SLACK_SIGNING_SECRET=your_secret_here

# Optional: Event bus mode
export EVENT_BUS=redis  # or 'local'

# Start with variables
docker-compose up -d
```

## Migration Notes

**From:** `docker-compose.athena-governance.yml` (22 services)  
**To:** `docker-compose.yml` (25 services)

**Added Services:**
- athena-router (9113) - A2 routing layer
- athena-mcp-ecosystem (8412) - MCP tools
- prometheus-pushgateway (9091) - Canary metrics

**Port Changes:**
- Grafana: 3000 → 3001 (consistency)

**Volume Compatibility:**
All existing volumes are reused. No data migration needed.

---

## Success Checklist

✅ ONE docker-compose.yml file  
✅ ALL 25 services defined  
✅ ZERO port conflicts  
✅ Correct service dependencies  
✅ Health checks on all services  
✅ Prometheus scraping all targets  
✅ Grafana dashboards loaded  
✅ Data volumes persisted  
✅ Local-first routing working  
✅ Governance oversight active  

**Run:** `docker-compose up -d` and you're operational.

**Monitor:** http://localhost:3001 (Grafana)  
**Metrics:** http://localhost:9090 (Prometheus)  
**Real-time:** http://localhost:19999 (Netdata)
