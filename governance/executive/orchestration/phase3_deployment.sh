#!/bin/bash

# PHASE 3 FEDERATION DEPLOYMENT SCRIPT
# Zero-trust sovereignty onboarding and treaty-based federation

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
CONFIG_FILE="$REPO_ROOT/phase3_config.json"
LOG_FILE="/var/log/ai-republic/phase3_deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;34m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE"
}

# Error handling
error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    log "ERROR: $1"
    exit 1
}

# Success message
success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
    log "SUCCESS: $1"
}

# Warning message
warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
    log "WARNING: $1"
}

# Info message
info() {
    echo -e "${BLUE}INFO: $1${NC}"
    log "INFO: $1"
}

# Pre-deployment checks
pre_deployment_checks() {
    info "Running Phase 3 pre-deployment checks..."

    # Check if running as root or with sudo
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root or with sudo"
    fi

    # Check Python version
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ $(echo "$PYTHON_VERSION < 3.8" | bc -l) -eq 1 ]]; then
        error "Python 3.8+ is required, found $PYTHON_VERSION"
    fi
    success "Python $PYTHON_VERSION detected"

    # Check required Python packages
    python3 -c "import fastapi, uvicorn" 2>/dev/null || error "fastapi/uvicorn packages not installed"
    success "Required Python packages available"

    # Check if Phase 2 is running
    if ! systemctl is-active --quiet ai-republic-judicial.service 2>/dev/null; then
        warning "Phase 2 judicial service not detected. Proceeding anyway."
    else
        success "Phase 2 judicial service detected and running"
    fi

    # Create necessary directories
    mkdir -p /opt/ai-republic/phase3
    mkdir -p /var/log/ai-republic
    mkdir -p /var/lib/ai-republic
    mkdir -p /etc/ai-republic
    success "Directory structure created"
}

# Deploy federation components
deploy_federation_system() {
    info "Deploying federation treaty system..."

    # Copy federation files
    cp "$SCRIPT_DIR/phase3_federation_core.py" "/opt/ai-republic/phase3/"
    cp "$SCRIPT_DIR/phase3_onboarding_protocol.py" "/opt/ai-republic/phase3/"
    cp "$SCRIPT_DIR/phase3_evidence_exchange.py" "/opt/ai-republic/phase3/"
    cp "$SCRIPT_DIR/phase3_federation_api.py" "/opt/ai-republic/phase3/"

    success "Federation system components deployed"
}

# Initialize federation constitution
initialize_federation_constitution() {
    info "Initializing federation constitution..."

    # Create foundational constitution
    cat > /etc/ai-republic/federation_constitution.json << 'EOF'
{
  "federation_name": "AI Republic Federation",
  "founding_principle": "Sovereign cooperation without sovereignty surrender",
  "core_articles": {
    "sovereignty_preservation": "Each instance maintains full constitutional autonomy",
    "voluntary_participation": "Federation membership is voluntary and revocable",
    "evidence_transparency": "All federation actions must be evidence-based",
    "dispute_resolution": "Federation court resolves inter-sovereign disputes",
    "reputation_weighted_governance": "Decision authority scales with demonstrated reliability"
  },
  "ratification_threshold": 0.67,
  "emergency_threshold": 0.8,
  "sovereignty_tiers": {
    "observer": {"voting_weight": 0.0, "evidence_threshold": 0.5},
    "contributor": {"voting_weight": 0.5, "evidence_threshold": 0.7},
    "sovereign": {"voting_weight": 1.0, "evidence_threshold": 0.8},
    "archon": {"voting_weight": 2.0, "evidence_threshold": 0.9}
  }
}
EOF

    success "Federation constitution initialized"
}

# Create systemd service
create_systemd_service() {
    info "Creating federation system systemd service..."

    cat > /etc/systemd/system/ai-republic-federation.service << 'EOF'
[Unit]
Description=Sovereign AI Republic Federation Service
After=network.target
Wants=network.target
Requires=ai-republic-judicial.service

[Service]
Type=simple
User=ai-republic
Group=ai-republic
WorkingDirectory=/opt/ai-republic/phase3
ExecStart=/usr/bin/python3 phase3_federation_api.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ai-republic-federation

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/var/log/ai-republic /var/lib/ai-republic
ProtectHome=true

# Environment
Environment=PYTHONPATH=/opt/ai-republic

[Install]
WantedBy=multi-user.target
EOF

    success "Systemd service created"
}

# Enable and start service
enable_service() {
    info "Enabling and starting federation system service..."

    systemctl daemon-reload
    systemctl enable ai-republic-federation.service
    systemctl start ai-republic-federation.service

    # Wait for service to start and API to be ready
    sleep 15

    # Test API health
    if curl -s -f http://127.0.0.1:8093/federation/health > /dev/null; then
        success "Federation API is responding"
    else
        warning "Federation API health check failed - checking service status..."
        systemctl status ai-republic-federation.service --no-pager
        error "Failed to start federation system service or API is not responding"
    fi
}

# Test federation initialization
test_federation_initialization() {
    info "Testing federation initialization..."

    # Test federation status endpoint
    STATUS_RESULT=$(curl -s "http://127.0.0.1:8093/federation/status" 2>/dev/null)
    if [[ $? -eq 0 ]]; then
        FEDERATION_NAME=$(echo "$STATUS_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('federation_name', 'UNKNOWN'))")
        if [[ "$FEDERATION_NAME" == "AI Republic Federation" ]]; then
            success "Federation status endpoint working"
        else
            warning "Unexpected federation name: $FEDERATION_NAME"
        fi
    else
        error "Federation status endpoint not responding"
    fi

    # Test sovereignty list (should be empty initially)
    SOVEREIGN_COUNT=$(curl -s "http://127.0.0.1:8093/federation/sovereigns" 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('count', -1))")
    if [[ "$SOVEREIGN_COUNT" -eq 0 ]]; then
        success "Sovereignty registry initialized correctly"
    else
        warning "Unexpected sovereign count: $SOVEREIGN_COUNT"
    fi
}

# Create monitoring and alerting
setup_monitoring() {
    info "Setting up federation monitoring..."

    # Create monitoring script
    cat > /opt/ai-republic/phase3/monitor_federation_health.sh << 'EOF'
#!/bin/bash
# Federation Health Monitor

HEALTH_CHECK=$(curl -s -f http://127.0.0.1:8093/federation/health 2>/dev/null)
if [[ $? -eq 0 ]]; then
    SOVEREIGN_COUNT=$(echo "$HEALTH_CHECK" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('sovereign_count', 0))")
    FEDERATION_HEALTH=$(echo "$HEALTH_CHECK" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('federation_health', 0))")

    echo "🤝 Federation System: HEALTHY"
    echo "🏛️ Sovereign Instances: $SOVEREIGN_COUNT"
    printf "⚖️ Federation Health: %.1f%%\n" $(echo "$FEDERATION_HEALTH * 100" | bc -l)

    # Check recent activity
    STATUS=$(curl -s "http://127.0.0.1:8093/federation/status" 2>/dev/null)
    if [[ $? -eq 0 ]]; then
        RECENT_ACTIVITY=$(echo "$STATUS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    activity = data.get('federation_status', {}).get('recent_activity', [])
    if activity:
        print '📋 Recent Activity:'
        for item in activity[-3:]:
            print f'   {item[\"type\"]} - {item.get(\"title\", item.get(\"evidence_type\", \"unknown\"))[:50]}...'
    else:
        print '📋 No recent federation activity'
except:
    print '📋 Unable to fetch activity'
")
    else
        echo "📋 Unable to fetch federation activity"
    fi
else
    echo "❌ Federation System: FAILED"
    exit 1
fi
EOF

    chmod +x /opt/ai-republic/phase3/monitor_federation_health.sh

    # Add to cron for monitoring
    (crontab -l ; echo "*/5 * * * * /opt/ai-republic/phase3/monitor_federation_health.sh >> /var/log/ai-republic/federation_health_monitor.log 2>&1") | crontab -

    success "Federation monitoring setup complete"
}

# Final validation
final_validation() {
    info "Running Phase 3 final validation..."

    # Test API endpoints
    if ! curl -s -f http://127.0.0.1:8093/federation/health > /dev/null; then
        error "Federation API health endpoint not responding"
    fi

    # Check constitution file
    if [[ ! -f /etc/ai-republic/federation_constitution.json ]]; then
        error "Federation constitution not created"
    fi

    # Check service status
    if ! systemctl is-active --quiet ai-republic-federation.service; then
        error "Federation service not running"
    fi

    # Check log files exist
    if [[ ! -f /var/log/ai-republic/judicial_audit.log ]]; then
        error "Judicial audit log not created"
    fi

    success "Phase 3 final validation passed"
}

# Main deployment function
main() {
    echo "🏛️ AI REPUBLIC PHASE 3 FEDERATION DEPLOYMENT"
    echo "=========================================="
    log "Starting Phase 3 deployment"

    # Execute deployment phases
    pre_deployment_checks
    echo

    deploy_federation_system
    initialize_federation_constitution
    echo

    create_systemd_service
    enable_service
    test_federation_initialization
    echo

    setup_monitoring
    final_validation

    # Deployment complete
    echo
    echo "🎉 PHASE 3 FEDERATION DEPLOYMENT COMPLETE!"
    echo "========================================"
    echo "🏛️ The Federation is now operational"
    echo
    echo "📊 Key Achievements:"
    echo "   ✅ Federation constitution established"
    echo "   ✅ Sovereignty registry initialized"
    echo "   ✅ Treaty ratification system active"
    echo "   ✅ Evidence exchange protocol ready"
    echo "   ✅ Zero-trust onboarding available"
    echo
    echo "🎯 Next Steps:"
    echo "   • Onboard sovereign instances via API"
    echo "   • Establish initial treaties"
    echo "   • Begin evidence sharing"
    echo "   • Scale federation membership"
    echo
    echo "📋 Service Status:"
    systemctl status ai-republic-federation --no-pager
    echo
    echo "📊 Health Check:"
    /opt/ai-republic/phase3/monitor_federation_health.sh
    echo
    echo "🔗 Federation API Endpoint: http://127.0.0.1:8093/federation"
    echo
    echo "📜 Constitution Location: /etc/ai-republic/federation_constitution.json"
    echo
    echo "🤝 Ready for sovereign onboarding and treaty formation!"

    log "Phase 3 deployment completed successfully"
}

# Run main deployment
main "$@"
