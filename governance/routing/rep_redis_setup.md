# REP Redis Setup for Project Iceberg

This guide covers setting up local Redis for Ripple Effect Protocol (REP) coordination.

## Overview

REP uses Redis pubsub for local-only multi-agent coordination. All communication stays within your infrastructure - zero cloud calls.

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Start Redis container
docker run -d \
  --name athena-rep-redis \
  -p 6379:6379 \
  redis:7-alpine \
  redis-server --appendonly yes

# Verify it's running
docker logs athena-rep-redis
redis-cli ping  # Should return PONG
```

### Option 2: Docker Compose

Add to your `docker-compose.yml`:

```yaml
services:
  rep-redis:
    image: redis:7-alpine
    container_name: athena-rep-redis
    ports:
      - "6379:6379"
    volumes:
      - rep-redis-data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - athena-network

volumes:
  rep-redis-data:
    driver: local

networks:
  athena-network:
    driver: bridge
```

Start it:

```bash
docker-compose up -d rep-redis
```

### Option 3: Homebrew (macOS)

```bash
# Install Redis
brew install redis

# Start Redis
brew services start redis

# Or run in foreground
redis-server /opt/homebrew/etc/redis.conf
```

### Option 4: APT (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install redis-server

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Check status
sudo systemctl status redis-server
```

## Configuration

### Security (Local-Only)

Ensure Redis only accepts local connections:

Edit `/etc/redis/redis.conf` or `/opt/homebrew/etc/redis.conf`:

```conf
# Bind to localhost only (CRITICAL for security)
bind 127.0.0.1 ::1

# Disable protected mode (safe because we bind to localhost)
protected-mode yes

# Set a password (optional but recommended)
requirepass your_secure_password_here

# Disable remote connections
rename-command CONFIG ""
rename-command DEBUG ""
```

Restart Redis after changes:

```bash
# Docker
docker restart athena-rep-redis

# Homebrew
brew services restart redis

# Systemd
sudo systemctl restart redis-server
```

### Environment Variables

Set these in your environment or `.env` file:

```bash
# Redis connection (must be local)
ATHENA_REP_REDIS_URL=redis://127.0.0.1:6379

# With password
ATHENA_REP_REDIS_URL=redis://:your_password@127.0.0.1:6379

# REP channel
ATHENA_REP_CHANNEL=athena:rep:routing

# Enable REP coordination
ATHENA_REP_ENABLED=true

# Local-first enforcement
ATHENA_NO_CLOUD=1
```

## Testing REP Coordination

### Test 1: Basic Connection

```python
import redis

# Connect to local Redis
r = redis.from_url("redis://127.0.0.1:6379")

# Test connection
print(r.ping())  # Should print True
```

### Test 2: Pubsub

```python
import redis
import json
import time

# Publisher
r = redis.from_url("redis://127.0.0.1:6379")
r.publish("athena:rep:routing", json.dumps({
    "agent_id": "test_agent",
    "timestamp": time.time(),
    "message": "Hello REP!"
}))

# Subscriber (in another terminal/process)
r = redis.from_url("redis://127.0.0.1:6379")
pubsub = r.pubsub()
pubsub.subscribe("athena:rep:routing")

for message in pubsub.listen():
    if message['type'] == 'message':
        data = json.loads(message['data'])
        print(f"Received: {data}")
```

### Test 3: REP Coordinator

```python
from governance.routing.rep_protocol import (
    REPCoordinator,
    REPDecision,
    SystemState
)

# Create coordinator
coordinator = REPCoordinator(
    agent_id="test_agent_1",
    redis_url="redis://127.0.0.1:6379"
)

# Create test decision
decision = REPDecision(
    model="qwen2.5-coder:7b",
    confidence=0.85,
    domain="code"
)

# Create test system state
state = SystemState(
    available_models=["qwen2.5-coder:7b", "llama3.1:8b"],
    accumulated_cost=50.0,
    cost_budget=100.0
)

# Broadcast message
message = coordinator.broadcast_message(decision, state)
print(f"Broadcasted: {message}")

# Receive messages
messages = coordinator.receive_messages()
print(f"Received {len(messages)} messages")

# Get peer summary
summary = coordinator.get_peer_summary()
print(f"Peer summary: {summary}")
```

### Test 4: Multi-Agent Coordination

Run multiple agents simultaneously:

```bash
# Terminal 1
python -c "
from governance.routing.rep_router import REPEnhancedRouter
from governance.routing.basic_router import RoutingRequest
from pathlib import Path
import time

router = REPEnhancedRouter(
    profiles_path=Path('governance/routing/model_profiles.json'),
    agent_id='router_1'
)

while True:
    request = RoutingRequest(query='test', domain='code')
    choice = router.route(request)
    print(f'Agent 1 chose: {choice.model}')
    time.sleep(2)
"

# Terminal 2
python -c "
from governance.routing.rep_router import REPEnhancedRouter
from governance.routing.basic_router import RoutingRequest
from pathlib import Path
import time

router = REPEnhancedRouter(
    profiles_path=Path('governance/routing/model_profiles.json'),
    agent_id='router_2'
)

while True:
    request = RoutingRequest(query='test', domain='code')
    choice = router.route(request)
    print(f'Agent 2 chose: {choice.model}')
    time.sleep(2)
"
```

You should see agents coordinating to avoid clustering on the same model.

## Monitoring

### Redis CLI

```bash
# Monitor all commands in real-time
redis-cli monitor

# Watch pubsub activity
redis-cli
> PUBSUB CHANNELS
> PUBSUB NUMSUB athena:rep:routing
```

### Prometheus Metrics

REP coordinator exposes metrics:

```python
# governance/observability/rep_metrics.py
from prometheus_client import Counter, Gauge, Histogram

rep_messages_sent = Counter(
    'athena_rep_messages_sent_total',
    'Total REP messages sent',
    ['agent_id', 'channel']
)

rep_messages_received = Counter(
    'athena_rep_messages_received_total',
    'Total REP messages received',
    ['agent_id', 'channel']
)

rep_peer_count = Gauge(
    'athena_rep_peer_count',
    'Number of active peers',
    ['agent_id']
)

rep_coordination_adjustments = Counter(
    'athena_rep_coordination_adjustments_total',
    'Number of routing decisions adjusted by REP',
    ['agent_id', 'reason']
)
```

### Grafana Dashboard

Create a dashboard with panels:

1. **REP Message Rate**: `rate(athena_rep_messages_sent_total[5m])`
2. **Peer Count**: `athena_rep_peer_count`
3. **Coordination Adjustments**: `rate(athena_rep_coordination_adjustments_total[5m])`
4. **Model Distribution**: Clustered by peer agents

## Troubleshooting

### Connection Refused

```bash
# Check if Redis is running
redis-cli ping

# If not, start it
docker start athena-rep-redis
# or
brew services start redis
# or
sudo systemctl start redis-server
```

### Permission Denied

```bash
# Check Redis logs
docker logs athena-rep-redis
# or
tail -f /var/log/redis/redis-server.log

# Fix permissions
sudo chown redis:redis /var/lib/redis
sudo chmod 755 /var/lib/redis
```

### Messages Not Arriving

```bash
# Check if pubsub is working
redis-cli
> SUBSCRIBE athena:rep:routing

# In another terminal
redis-cli
> PUBLISH athena:rep:routing "test"

# First terminal should show the message
```

### High Memory Usage

```bash
# Check memory usage
redis-cli INFO memory

# Set maxmemory limit
redis-cli CONFIG SET maxmemory 256mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## Security Checklist

- [ ] Redis bound to `127.0.0.1` only
- [ ] Protected mode enabled
- [ ] Password set (optional but recommended)
- [ ] Dangerous commands disabled
- [ ] Firewall blocks external access to port 6379
- [ ] `ATHENA_NO_CLOUD=1` environment variable set
- [ ] REP coordinator validates local-only URLs

## Performance Tuning

### Low Latency Settings

Add to `redis.conf`:

```conf
# Disable disk persistence for lowest latency
save ""
appendonly no

# TCP settings
tcp-backlog 511
tcp-keepalive 300

# Memory settings
maxmemory 256mb
maxmemory-policy allkeys-lru

# Pubsub settings
client-output-buffer-limit pubsub 32mb 8mb 60
```

### High Throughput Settings

```conf
# Enable disk persistence
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# Increase connections
maxclients 10000

# Memory settings
maxmemory 1gb
maxmemory-policy allkeys-lru
```

## Production Deployment

### Docker Compose (Production)

```yaml
services:
  rep-redis:
    image: redis:7-alpine
    container_name: athena-rep-redis
    restart: always
    ports:
      - "127.0.0.1:6379:6379" # Bind to localhost only
    volumes:
      - rep-redis-data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf:ro
    command: redis-server /usr/local/etc/redis/redis.conf
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    networks:
      - athena-network

volumes:
  rep-redis-data:
    driver: local

networks:
  athena-network:
    driver: bridge
```

### Kubernetes (Advanced)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: rep-redis
spec:
  ports:
    - port: 6379
  selector:
    app: rep-redis
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rep-redis
spec:
  selector:
    matchLabels:
      app: rep-redis
  template:
    metadata:
      labels:
        app: rep-redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
          volumeMounts:
            - name: redis-data
              mountPath: /data
      volumes:
        - name: redis-data
          persistentVolumeClaim:
            claimName: rep-redis-pvc
```

## References

- [REP Paper (ICLR 2026)](https://openreview.net/forum?id=MjQCuQhtn4)
- [Redis Pubsub Documentation](https://redis.io/docs/manual/pubsub/)
- [redis-py Documentation](https://redis-py.readthedocs.io/)
