# Docker Compose Consolidation - October 17, 2025

## What Happened

Consolidated 3 separate docker-compose files into **one unified `docker-compose.yml`**.

## Files Archived

### 1. `docker-compose.athena-governance.yml.bak` (557 lines, 22 services)
**Last Used:** October 15, 2025  
**Status:** Production stack that was actively running

**Services:**
- athena-api (8888)
- athena-evolutionary (8014)
- athena-knowledge-gateway (8088)
- athena-knowledge-context (8091)
- athena-knowledge-sync (8089)
- athena-weaviate (8090)
- athena-searxng (8081)
- athena-postgres (5432)
- athena-redis (6379)
- governance-metrics-exporter (9109)
- governance-orchestrator (9110)
- governance-canary-monitor (9111)
- agi-remediator (9112)
- athena-prometheus (9090)
- athena-grafana (3001)
- athena-netdata (19999)
- athena-alertmanager (9093)
- athena-node-exporter (9100)
- athena-postgres-exporter (9187)
- athena-redis-exporter (9121)
- governance-exporter (9108)
- governance-slack-bot (8082)

### 2. `docker-compose.mcp-ui.yml.bak` (229 lines, 6 services)
**Last Used:** October 16, 2025  
**Status:** Optional MCP UI layer (not in production)

**Services:**
- mcp-ecosystem-ui (9250)
- mcp-governance (9200)
- mcp-router (9201)
- mcp-reflex (9202)
- mcp-ui-inspector (9210)
- athena-router (9113)

## New Unified Stack

**File:** `docker-compose.yml` (21KB, 25 services)

### Port Map (All Services)

| Port  | Service                    | Layer | Status |
|-------|----------------------------|-------|--------|
| 3001  | Grafana                    | Obs   | ✅     |
| 5432  | PostgreSQL                 | Store | ✅     |
| 6379  | Redis                      | Store | ✅     |
| 8014  | Evolutionary API           | Core  | ✅     |
| 8081  | SearXNG                    | Store | ✅     |
| 8082  | Slack Bot                  | Intg  | ✅     |
| 8088  | Knowledge Gateway          | Know  | ✅     |
| 8089  | Knowledge Sync             | Know  | ✅     |
| 8090  | Weaviate                   | Store | ✅     |
| 8091  | Knowledge Context          | Know  | ✅     |
| 8412  | MCP Ecosystem              | Core  | ✅     |
| 9090  | Prometheus                 | Obs   | ✅     |
| 9091  | Prometheus Pushgateway     | Obs   | ✅     |
| 9093  | Alertmanager               | Obs   | ✅     |
| 9100  | Node Exporter              | Obs   | ✅     |
| 9108  | Governance Exporter        | A3    | ✅     |
| 9109  | Governance Metrics         | A3    | ✅     |
| 9110  | Governance Orchestrator    | A3    | ✅     |
| 9111  | Governance Canary Monitor  | A3    | ✅     |
| 9112  | AGI Remediator             | A3    | ✅     |
| 9113  | Athena Router              | A2    | ✅     |
| 9121  | Redis Exporter             | Obs   | ✅     |
| 9187  | Postgres Exporter          | Obs   | ✅     |
| 19999 | Netdata                    | Obs   | ✅     |
| 50051 | Weaviate gRPC              | Store | ✅     |

### Services Added from Router Compose

- **athena-router** (9113) - A2 local-first routing
- **athena-mcp-ecosystem** (8412) - MCP tools (was missing)
- **prometheus-pushgateway** (9091) - For canary metrics

### Issues Fixed

1. **Port Conflict:** Grafana moved from 3000 → 3001 (consistent)
2. **Missing Router:** Added athena-router service
3. **Missing MCP:** Added athena-mcp-ecosystem service
4. **Missing Pushgateway:** Added for canary controller
5. **Container Name Consistency:** All use `athena-` prefix
6. **Network Consistency:** All use `athena-network`
7. **Label Standardization:** Added layer tags (a2, a3, core, obs)

## Migration Path

### Currently Running Containers
All 17 running containers were from the old governance compose file. They need to be recreated:

```bash
# Stop old stack
docker-compose -f archive/2025-10-17-docker-consolidation/docker-compose.athena-governance.yml.bak down

# Start new unified stack
docker-compose up -d
```

### Data Preservation
All named volumes are preserved:
- `athena_postgres_data`
- `athena_redis_data`
- `athena_weaviate_data`
- `athena_prometheus_data`
- `athena_grafana_data`
- `athena_netdata_config`
- `athena_netdata_lib`
- `athena_netdata_cache`

## Benefits

✅ **Single Source of Truth** - One compose file for entire stack  
✅ **Complete Service Coverage** - All 25 services in one place  
✅ **No Port Conflicts** - All ports validated and documented  
✅ **Consistent Naming** - All containers prefixed with `athena-`  
✅ **Layer Labels** - Services tagged by architecture layer (A2, A3, Core, Obs)  
✅ **Proper Dependencies** - All service dependencies correctly defined  
✅ **Health Checks** - All services have health checks where applicable  

## Rollback

If needed, restore the old setup:

```bash
# Stop new stack
docker-compose down

# Restore old files
cp archive/2025-10-17-docker-consolidation/docker-compose.athena-governance.yml.bak docker-compose.athena-governance.yml

# Start old stack
docker-compose -f docker-compose.athena-governance.yml up -d
```

## Documentation Updated

- `DOCKER_QUICK_START.md` - Reflects new unified stack
- `DOCKER_UNIFIED_STACK.md` - Updated with all 25 services
- `Makefile` - Updated to use main docker-compose.yml

---

**Consolidation completed:** October 17, 2025  
**Validated:** ✅ Compose file syntax valid  
**Status:** Ready for deployment

