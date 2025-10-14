#!/bin/bash

# PHASE 2 JUDICIAL ENFORCEMENT DEPLOYMENT SCRIPT
# Machine-speed constitutional court with graduated response tribunals

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
CONFIG_FILE="$REPO_ROOT/phase2_config.json"
LOG_FILE="/var/log/ai-republic/phase2_deployment.log"

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
    info "Running Phase 2 pre-deployment checks..."

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
    python3 -c "import flask" 2>/dev/null || error "flask package not installed"
    success "Required Python packages available"

    # Check if Phase 1 is running
    if ! systemctl is-active --quiet ai-republic-constitutional.service 2>/dev/null; then
        warning "Phase 1 constitutional service not detected. Proceeding anyway."
    else
        success "Phase 1 constitutional service detected and running"
    fi

    # Create necessary directories
    mkdir -p /opt/ai-republic/phase2
    mkdir -p /var/log/ai-republic
    mkdir -p /var/lib/ai-republic
    mkdir -p /etc/ai-republic
    success "Directory structure created"
}

# Deploy judicial system
deploy_judicial_system() {
    info "Deploying judicial enforcement system..."

    # Copy judicial files
    cp "$SCRIPT_DIR/phase2_judicial_runtime.py" "/opt/ai-republic/phase2/"
    cp "$REPO_ROOT/phase2_config.json" "/etc/ai-republic/judicial.json"

    success "Judicial system components deployed"
}

# Initialize reputation system
initialize_reputation_system() {
    info "Initializing reputation system..."

    # Create initial reputation database
    cat > /var/lib/ai-republic/reputation.db << 'EOF'
{
  "republic_founding_actors": {
    "constitutional_court": 1.0,
    "phase1_runtime": 1.0,
    "judicial_system": 1.0
  }
}
EOF

    success "Reputation system initialized with founding actors"
}

# Create systemd service
create_systemd_service() {
    info "Creating judicial system systemd service..."

    cat > /etc/systemd/system/ai-republic-judicial.service << 'EOF'
[Unit]
Description=Sovereign AI Republic Judicial System
After=network.target
Wants=network.target
Requires=ai-republic-constitutional.service

[Service]
Type=simple
User=ai-republic
Group=ai-republic
WorkingDirectory=/opt/ai-republic/phase2
ExecStart=/usr/bin/python3 phase2_judicial_runtime.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ai-republic-judicial

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
    info "Enabling and starting judicial system service..."

    systemctl daemon-reload
    systemctl enable ai-republic-judicial.service
    systemctl start ai-republic-judicial.service

    # Wait for service to start and API to be ready
    sleep 10

    # Test API health
    if curl -s -f http://127.0.0.1:8092/v2/health > /dev/null; then
        success "Judicial API is responding"
    else
        warning "Judicial API health check failed - checking service status..."
        systemctl status ai-republic-judicial.service --no-pager
        error "Failed to start judicial system service or API is not responding"
    fi
}

# Test Phase 1 → Phase 2 integration
test_integration() {
    info "Testing Phase 1 → Phase 2 integration..."

    # Test judicial adjudication endpoint
    TEST_RESULT=$(python3 << 'EOF'
import json
import urllib.request

# Test data
test_payload = {
    "event_id": "test_integration_001",
    "instance_id": "sovereign-A",
    "actor_id": "test_agent",
    "article": "II",
    "severity": 0.85,
    "confidence": 0.9,
    "classification": "authority_breach",
    "details": {"integration_test": True},
    "timestamp": __import__('time').time()
}

try:
    data = json.dumps(test_payload).encode()
    req = urllib.request.Request('http://127.0.0.1:8092/v2/judicial/adjudicate', data=data, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        response = json.loads(r.read().decode())
        print(json.dumps(response))
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
EOF
)

    if [[ $? -eq 0 ]]; then
        VERDICT=$(echo "$TEST_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('verdict', 'UNKNOWN'))")
        if [[ "$VERDICT" == "BLOCK" ]] || [[ "$VERDICT" == "QUARANTINE" ]] || [[ "$VERDICT" == "TRIBUNAL" ]]; then
            success "Integration test passed - judicial system operational"
            info "Test verdict: $VERDICT (expected for severity 0.85 authority breach)"
        else
            warning "Unexpected verdict: $VERDICT"
        fi
    else
        error "Integration test failed"
    fi
}

# Create monitoring and alerting
setup_monitoring() {
    info "Setting up judicial monitoring..."

    # Create monitoring script
    cat > /opt/ai-republic/phase2/monitor_judicial_health.sh << 'EOF'
#!/bin/bash
# Judicial System Health Monitor

HEALTH_CHECK=$(curl -s -f http://127.0.0.1:8092/v2/health 2>/dev/null)
if [[ $? -eq 0 ]]; then
    STATUS=$(echo "$HEALTH_CHECK" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))")
    DECISIONS=$(echo "$HEALTH_CHECK" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('decisions_processed', 0))")

    echo "✅ Judicial System: $STATUS"
    echo "⚖️ Decisions Processed: $DECISIONS"

    # Check recent decisions
    RECENT_DECISIONS=$(curl -s "http://127.0.0.1:8092/v2/judicial/history?limit=5" 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data:
        print('📋 Recent Verdicts:')
        for decision in data[-3:]:
            print(f'   {decision[\"decision\"][\"verdict\"]} - {decision[\"event\"][\"classification\"]}')
    else:
        print('📋 No recent decisions')
except:
    print('📋 Unable to fetch recent decisions')
")
else
    echo "❌ Judicial System: FAILED"
    exit 1
fi
EOF

    chmod +x /opt/ai-republic/phase2/monitor_judicial_health.sh

    # Add to cron for monitoring
    (crontab -l ; echo "*/5 * * * * /opt/ai-republic/phase2/monitor_judicial_health.sh >> /var/log/ai-republic/judicial_health_monitor.log 2>&1") | crontab -

    success "Judicial monitoring setup complete"
}

# Final validation
final_validation() {
    info "Running Phase 2 final validation..."

    # Test API endpoints
    if ! curl -s -f http://127.0.0.1:8092/v2/health > /dev/null; then
        error "Judicial API health endpoint not responding"
    fi

    # Check reputation system
    if [[ ! -f /var/lib/ai-republic/reputation.db ]]; then
        error "Reputation database not created"
    fi

    # Verify service status
    if ! systemctl is-active --quiet ai-republic-judicial.service; then
        error "Judicial service not running"
    fi

    # Check log files exist
    if [[ ! -f /var/log/ai-republic/judicial_audit.log ]]; then
        error "Judicial audit log not created"
    fi

    success "Phase 2 final validation passed"
}

# Main deployment function
main() {
    echo "⚖️ AI REPUBLIC PHASE 2 JUDICIAL DEPLOYMENT"
    echo "=========================================="
    log "Starting Phase 2 deployment"

    # Execute deployment phases
    pre_deployment_checks
    echo

    deploy_judicial_system
    initialize_reputation_system
    echo

    create_systemd_service
    enable_service
    test_integration
    echo

    setup_monitoring
    final_validation

    # Deployment complete
    echo
    echo "🎉 PHASE 2 JUDICIAL DEPLOYMENT COMPLETE!"
    echo "========================================"
    echo "⚖️ The Constitutional Court is now operational"
    echo
    echo "📊 Key Achievements:"
    echo "   ✅ Judicial API deployed and responding"
    echo "   ✅ Reputation system initialized"
    echo "   ✅ Phase 1→Phase 2 integration tested"
    echo "   ✅ Machine-speed adjudication active"
    echo "   ✅ Graduated response tribunals ready"
    echo
    echo "🎯 Next Steps:"
    echo "   • Phase 1 violations now trigger judicial review"
    echo "   • Reputation system tracks actor reliability"
    echo "   • Tribunal system ready for critical violations"
    echo "   • Ready for Phase 3: Treaty Federation"
    echo
    echo "📋 Service Status:"
    systemctl status ai-republic-judicial --no-pager
    echo
    echo "📊 Health Check:"
    /opt/ai-republic/phase2/monitor_judicial_health.sh
    echo
    echo "🔗 API Endpoint: http://127.0.0.1:8092/v2/judicial/adjudicate"
    echo
    echo "📋 Recent Judicial Decisions:"
    tail -n 3 /var/log/ai-republic/judicial_audit.log | python3 -m json.tool

    log "Phase 2 deployment completed successfully"
}

# Run main deployment
main "$@"