# Athena Docker Stack - Quick Start

**One command to rule them all:** `docker-compose up -d`

## Quick Links

| Service | URL | Purpose |
|---------|-----|---------|
| **Router** | http://localhost:9113/health | A2 local-first routing |
| **Governance** | http://localhost:9110/health | A3 policy control |
| **API** | http://localhost:8888/health | Core Python API |
| **Evolutionary** | http://localhost:8014/health | Self-improvement |
| **MCP Tools** | http://localhost:8412/health | Context Protocol |
| **Prometheus** | http://localhost:9090 | Metrics |
| **Grafana** | http://localhost:3001 | Dashboards (admin/admin) |
| **Netdata** | http://localhost:19999 | Real-time monitoring |

## Start Stack (3 Steps)

```bash
# 1. Start host services (separate terminals)
mlx_lm.server --model mlx-community/qwen2.5-coder-7b --port 8080  # Terminal 1
ollama serve                                                        # Terminal 2

# 2. Start Docker stack
docker-compose up -d

# 3. Verify everything is running
docker-compose ps
```

Expected output:
```
✅ 25 services running
✅ All health checks passing
```

## Full Service List (25 Services)

### A2 Layer (1)
- ✅ Router (9113)

### A3 Governance (5)
- ✅ Orchestrator (9110)
- ✅ Metrics Exporter (9109)
- ✅ Canary Monitor (9111)
- ✅ AGI Remediator (9112)
- ✅ Governance Exporter (9108)

### Core Services (4)
- ✅ Athena API (8888)
- ✅ Evolutionary API (8014)
- ✅ MCP Ecosystem (8412)
- ✅ Slack Bot (8082)

### Knowledge Layer (3)
- ✅ Knowledge Gateway (8088)
- ✅ Knowledge Context (8091)
- ✅ Knowledge Sync (8089)

### Observability (8)
- ✅ Prometheus (9090)
- ✅ Pushgateway (9091)
- ✅ Grafana (3001)
- ✅ Alertmanager (9093)
- ✅ Netdata (19999)
- ✅ Node Exporter (9100)
- ✅ Postgres Exporter (9187)
- ✅ Redis Exporter (9121)

### Storage (4)
- ✅ PostgreSQL (5432)
- ✅ Redis (6379)
- ✅ Weaviate (8090, 50051)
- ✅ SearXNG (8081)

## Test Everything

```bash
# Router
curl http://localhost:9113/health | jq
curl http://localhost:9113/canary | jq

# Governance
curl http://localhost:9110/health | jq

# Core Services
curl http://localhost:8888/health | jq
curl http://localhost:8014/health | jq
curl http://localhost:8412/health | jq

# Storage
docker-compose exec athena-postgres pg_isready -U postgres
docker-compose exec athena-redis redis-cli ping

# Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[].labels.job'

# Open dashboards
open http://localhost:3001   # Grafana
open http://localhost:19999  # Netdata
```

## View Logs

```bash
# All services
docker-compose logs -f

# Specific services
docker-compose logs -f athena-router
docker-compose logs -f governance-orchestrator
docker-compose logs -f athena-api

# Last 50 lines
docker-compose logs --tail=50 -f
```

## Stop Everything

```bash
# Stop (keeps data)
docker-compose down

# Stop and remove volumes (deletes data)
docker-compose down -v
```

## Restart Everything

```bash
docker-compose restart
```

## Restart Single Service

```bash
docker-compose restart athena-router
docker-compose restart governance-orchestrator
docker-compose restart athena-api
```

## Troubleshooting

### "Router not healthy"

```bash
# Check logs
docker-compose logs athena-router

# Common cause: MLX not running
mlx_lm.server --model mlx-community/qwen2.5-coder-7b --port 8080

# Verify connectivity
docker-compose exec athena-router curl http://host.docker.internal:8080/health
```

### "Governance orchestrator unhealthy"

```bash
# Check dependencies
docker-compose ps athena-postgres athena-redis athena-prometheus

# Check state file
ls -la state/exec_state.json

# Restart with deps
docker-compose restart athena-prometheus governance-orchestrator
```

### "Prometheus targets down"

```bash
# Check targets
curl http://localhost:9090/api/v1/targets | jq

# Reload config
curl -X POST http://localhost:9090/-/reload

# Verify services are up
docker-compose ps | grep healthy
```

### "Port already in use"

```bash
# Find what's using the port
lsof -i :9113

# Stop conflicting process or change port in docker-compose.yml
```

### "Cannot connect to Docker daemon"

```bash
# Start Docker Desktop
open -a Docker

# Wait for it to start, then try again
docker-compose up -d
```

### "Service keeps restarting"

```bash
# Check logs for errors
docker-compose logs --tail=100 [service-name]

# Common issues:
# - Missing volumes/directories
# - Permission issues
# - Port conflicts
# - Missing dependencies
```

## Clean Reset

```bash
# Stop all services
docker-compose down

# Remove all containers, networks, images (keeps volumes)
docker-compose down --rmi all

# Nuclear option (removes EVERYTHING including data)
docker-compose down -v
docker system prune -a --volumes

# Then rebuild
docker-compose up -d
```

## Check Service Health

```bash
# All services status
docker-compose ps

# Detailed health check
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# Only unhealthy services
docker-compose ps --filter "health=unhealthy"

# Follow health status
watch -n 2 'docker-compose ps'
```

## Update Services

```bash
# Pull latest images
docker-compose pull

# Rebuild custom images
docker-compose build

# Restart with new images
docker-compose up -d
```

## Environment Variables

Optional environment variables:

```bash
# Slack integration
export SLACK_SIGNING_SECRET=your_secret_here

# Event bus mode
export EVENT_BUS=redis  # or 'local'

# Start with variables
docker-compose up -d
```

## Backup Data

```bash
# Backup Postgres
docker-compose exec athena-postgres pg_dump -U postgres knowledge_base > backup_$(date +%Y%m%d).sql

# Backup Redis
docker-compose exec athena-redis redis-cli --rdb /data/dump.rdb
docker cp athena-redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb

# Backup volumes
docker run --rm -v athena_postgres_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/postgres_$(date +%Y%m%d).tar.gz -C /data .
```

## Restore Data

```bash
# Restore Postgres
cat backup.sql | docker-compose exec -T athena-postgres psql -U postgres knowledge_base

# Restore Redis
docker cp redis_backup.rdb athena-redis:/data/dump.rdb
docker-compose restart athena-redis
```

## Performance Check

```bash
# Container resource usage
docker stats

# Service-specific stats
docker stats athena-router athena-api governance-orchestrator

# Disk usage
docker system df
```

## Network Diagnostics

```bash
# Test container connectivity
docker-compose exec athena-router ping -c 3 athena-postgres
docker-compose exec athena-api curl http://athena-redis:6379

# Check network
docker network inspect athena-network

# DNS resolution
docker-compose exec athena-router nslookup athena-postgres
```

## Quick Commands

```bash
# Restart Router + Governance
docker-compose restart athena-router governance-orchestrator

# View Router + API logs
docker-compose logs -f athena-router athena-api

# Check all health endpoints
for port in 9113 9110 8888 8014 8412; do
  echo "Port $port: $(curl -s http://localhost:$port/health | jq -r '.status // "N/A"')"
done

# Count running services
docker-compose ps | grep "Up" | wc -l
```

---

## Success Checklist

When everything is working:

✅ `docker-compose ps` shows 25 services "Up"  
✅ Router health: http://localhost:9113/health returns 200  
✅ Governance health: http://localhost:9110/health returns 200  
✅ Prometheus scraping: http://localhost:9090/targets shows targets "UP"  
✅ Grafana accessible: http://localhost:3001 (login: admin/admin)  
✅ No errors in `docker-compose logs`  

**You're ready to build! 🚀**

---

**For detailed architecture:** See [DOCKER_UNIFIED_STACK.md](DOCKER_UNIFIED_STACK.md)  
**For migration notes:** See [archive/2025-10-17-docker-consolidation/CONSOLIDATION_MANIFEST.md](archive/2025-10-17-docker-consolidation/CONSOLIDATION_MANIFEST.md)
