# Health Checks to Add

## Containers Needing Health Checks:

### 1. athena-weaviate
```yaml
healthcheck:
  test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:8080/v1/.well-known/ready || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 2. athena-knowledge-gateway
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### 3. athena-proxy
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:11435/"]
  interval: 30s
  timeout: 10s
  retries: 3
```

(Note: Some containers are exporters and don't need health checks)
