#!/usr/bin/env bash
# Fix Prometheus Scraping Issues
# Updates prometheus.yml to correctly scrape governance endpoints

set -euo pipefail

blue(){ echo -e "\033[34m$1\033[0m"; }
green(){ echo -e "\033[32m$1\033[0m"; }
yellow(){ echo -e "\033[33m$1\033[0m"; }

blue "🔧 Fixing Prometheus Scraping Configuration..."
echo ""

# Backup existing config
if [[ -f monitoring/prometheus/prometheus.yml ]]; then
    cp monitoring/prometheus/prometheus.yml monitoring/prometheus/prometheus.yml.backup
    green "✅ Backed up existing config"
fi

# Create updated prometheus.yml with correct paths
cat > monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - alerts.yml

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # ============================================================================
  # Governance Stack (FIXED PATHS)
  # ============================================================================
  
  # Governance Metrics Exporter
  - job_name: 'governance-metrics'
    static_configs:
      - targets: ['governance-metrics-exporter:8000']
    scrape_interval: 10s
    metrics_path: '/metrics'

  # Governance Orchestrator 
  - job_name: 'governance-orchestrator'
    static_configs:
      - targets: ['localhost:9110']  # Local port mapping
    scrape_interval: 15s
    metrics_path: '/metrics'

  # Governance Canary Monitor
  - job_name: 'governance-canary'
    static_configs:
      - targets: ['localhost:9111']  # Local port mapping
    scrape_interval: 15s
    metrics_path: '/metrics'

  # ============================================================================
  # AGI Core (if running)
  # ============================================================================
  
  - job_name: 'agi-core'
    static_configs:
      - targets: ['localhost:8100']
    scrape_interval: 15s
    metrics_path: '/metrics'

  # ============================================================================
  # Athena Core Services
  # ============================================================================
  
  - job_name: 'athena-api'
    static_configs:
      - targets: ['athena-api:8000']
    scrape_interval: 30s
    metrics_path: '/metrics'

  - job_name: 'athena-evolutionary'
    static_configs:
      - targets: ['athena-evolutionary:8004']
    scrape_interval: 30s
    metrics_path: '/metrics'

  - job_name: 'athena-knowledge-gateway'
    static_configs:
      - targets: ['athena-knowledge-gateway:8080']
    scrape_interval: 30s
    metrics_path: '/metrics'

  # ============================================================================
  # Infrastructure Exporters
  # ============================================================================
  
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['athena-node-exporter:9100']
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['athena-postgres-exporter:9187']
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['athena-redis-exporter:9121']
    scrape_interval: 30s

  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 30s
EOF

green "✅ Updated prometheus.yml with correct scrape paths"
echo ""

yellow "📋 Next steps:"
echo "  1. Reload Prometheus config:"
echo "     curl -X POST http://localhost:9090/-/reload"
echo ""
echo "  2. Or restart Prometheus container:"
echo "     docker restart prometheus"
echo ""
echo "  3. Verify targets are UP:"
echo "     curl -s 'http://localhost:9090/api/v1/targets' | jq '.data.activeTargets[] | select(.labels.job | contains(\"governance\")) | {job: .labels.job, health: .health}'"
echo ""

