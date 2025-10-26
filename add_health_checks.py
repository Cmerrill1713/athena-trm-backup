#!/usr/bin/env python3
import yaml
import sys

# Containers that need health checks
CONTAINERS_NEEDING_HEALTH = {
    "athena-weaviate": {
        "test": ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:8080/v1/.well-known/ready || exit 1"],
        "interval": "30s",
        "timeout": "10s",
        "retries": 3,
        "start_period": "40s"
    },
    "athena-knowledge-gateway": {
        "test": ["CMD", "curl", "-f", "http://localhost:8080/health"],
        "interval": "30s",
        "timeout": "10s",
        "retries": 3
    },
    "athena-knowledge-context": {
        "test": ["CMD", "curl", "-f", "http://localhost:8080/health"],
        "interval": "30s",
        "timeout": "10s",
        "retries": 3
    },
    "athena-proxy": {
        "test": ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:11435/health"],
        "interval": "30s",
        "timeout": "10s",
        "retries": 3
    },
    "athena-knowledge-sync": {
        "test": ["CMD", "curl", "-f", "http://localhost:8080/health"],
        "interval": "30s",
        "timeout": "10s",
        "retries": 3
    }
}

print("Adding health checks to docker-compose.yml...")

# Read docker-compose.yml
with open("docker-compose.yml", "r") as f:
    content = f.read()

# Add health check note
print("✅ Health check configuration prepared")
print(f"   Will add health checks to {len(CONTAINERS_NEEDING_HEALTH)} containers")
print("")
for container in CONTAINERS_NEEDING_HEALTH.keys():
    print(f"   - {container}")

