#!/bin/zsh
#
# Athena Unified Launcher
# ========================
#
# Unified control script for Athena frontend and backend services
# Usage: ./athena_launcher.sh {frontend|backend|restart|stop|status}
#

set -e

ACTION=$1
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_PATH="$PROJECT_ROOT/NeuroForgeApp"
BACKEND_PATH="$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check if process is running
is_running() {
    local process_name=$1
    pgrep -f "$process_name" > /dev/null 2>&1
}

# Wait for process to start
wait_for_process() {
    local process_name=$1
    local timeout=${2:-10}
    local count=0

    while [ $count -lt $timeout ]; do
        if is_running "$process_name"; then
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done
    return 1
}

# Start frontend (NeuroForge SwiftUI app)
start_frontend() {
    log "🚀 Starting Athena Frontend (NeuroForge)..."

    if is_running "NeuroForge"; then
        warning "Frontend already running"
        return 0
    fi

    cd "$FRONTEND_PATH"
    if [ ! -d "$FRONTEND_PATH" ]; then
        error "Frontend path not found: $FRONTEND_PATH"
        return 1
    fi

    # For SwiftUI apps, we can use open command
    open NeuroForge.app 2>/dev/null || {
        # If .app doesn't exist, try to build and run
        info "Building NeuroForge app..."
        xcodebuild -project NeuroForge.xcodeproj -scheme NeuroForge -configuration Debug build
        if [ $? -eq 0 ]; then
            open build/Debug/NeuroForge.app
        else
            error "Failed to build NeuroForge app"
            return 1
        fi
    }

    if wait_for_process "NeuroForge"; then
        log "✅ Frontend started successfully"
        return 0
    else
        error "Frontend failed to start"
        return 1
    fi
}

# Start backend services
start_backend() {
    log "⚙️ Starting Athena Backend Services..."

    cd "$BACKEND_PATH"
    if [ ! -f "launch_burn_in.sh" ]; then
        warning "launch_burn_in.sh not found, trying alternative launch methods"

        # Try starting individual services
        if [ -f "athena_local_api.py" ]; then
            log "Starting Athena Local API..."
            python3 athena_local_api.py &
        fi

        if [ -f "voice_activation.py" ]; then
            log "Starting Voice Activation..."
            python3 voice_activation.py --start &
        fi

        # Try starting monitoring services
        if [ -f "start_monitoring.sh" ]; then
            log "Starting Monitoring Services..."
            ./start_monitoring.sh &
        fi

    else
        # Use the existing launch script
        ./launch_burn_in.sh &
    fi

    # Wait a bit for services to start
    sleep 3

    # Check if any Python services are running
    if is_running "python3.*athena" || is_running "python3.*voice_activation" || is_running "python3.*api"; then
        log "✅ Backend services started successfully"
        return 0
    else
        error "Backend services failed to start"
        return 1
    fi
}

# Stop all services
stop_services() {
    log "🛑 Stopping Athena Services..."

    # Stop frontend
    if is_running "NeuroForge"; then
        log "Stopping NeuroForge..."
        pkill -f "NeuroForge" || true
    fi

    # Stop backend services
    if is_running "launch_burn_in.sh"; then
        log "Stopping launch_burn_in.sh..."
        pkill -f "launch_burn_in.sh" || true
    fi

    # Stop individual Python services
    local services=("athena_local_api" "voice_activation" "athena_notifications" "monitoring")
    for service in "${services[@]}"; do
        if is_running "python3.*$service"; then
            log "Stopping $service..."
            pkill -f "python3.*$service" || true
        fi
    done

    # Stop any remaining Python processes in the project
    if pgrep -f "python3.*$BACKEND_PATH" > /dev/null; then
        log "Stopping remaining Python processes..."
        pkill -f "python3.*$BACKEND_PATH" || true
    fi

    sleep 2
    log "✅ All services stopped"
}

# Restart all services
restart_all() {
    log "🔄 Restarting Athena (Full Restart)..."

    stop_services
    sleep 3

    start_backend
    sleep 2
    start_frontend

    log "✅ Restart complete"
}

# Check status of services
check_status() {
    echo "📊 Athena Service Status"
    echo "========================"

    # Frontend status
    if is_running "NeuroForge"; then
        echo -e "${GREEN}✅ Frontend (NeuroForge): RUNNING${NC}"
    else
        echo -e "${RED}❌ Frontend (NeuroForge): STOPPED${NC}"
    fi

    # Backend services
    local backend_running=false

    if is_running "launch_burn_in.sh"; then
        echo -e "${GREEN}✅ Backend (launch_burn_in.sh): RUNNING${NC}"
        backend_running=true
    fi

    if is_running "python3.*athena_local_api"; then
        echo -e "${GREEN}✅ Local API: RUNNING${NC}"
        backend_running=true
    fi

    if is_running "python3.*voice_activation"; then
        echo -e "${GREEN}✅ Voice Activation: RUNNING${NC}"
        backend_running=true
    fi

    if is_running "python3.*monitoring"; then
        echo -e "${GREEN}✅ Monitoring: RUNNING${NC}"
        backend_running=true
    fi

    if [ "$backend_running" = false ]; then
        echo -e "${RED}❌ Backend Services: STOPPED${NC}"
    fi

    echo ""
    echo "Service URLs:"
    echo "  Frontend: Check macOS Dock for NeuroForge app"
    echo "  API: http://localhost:8009"
    echo "  Health: http://localhost:8009/health"
}

# Main command handling
case "$ACTION" in
    frontend)
        start_frontend
        ;;
    backend)
        start_backend
        ;;
    restart)
        restart_all
        ;;
    stop)
        stop_services
        ;;
    status)
        check_status
        ;;
    *)
        echo "🎯 Athena Unified Launcher"
        echo "========================="
        echo ""
        echo "Usage: $0 {frontend|backend|restart|stop|status}"
        echo ""
        echo "Commands:"
        echo "  frontend  - Start NeuroForge frontend (SwiftUI app)"
        echo "  backend   - Start backend services (API, voice, monitoring)"
        echo "  restart   - Stop all services and restart everything"
        echo "  stop      - Stop all Athena services"
        echo "  status    - Show current service status"
        echo ""
        echo "Examples:"
        echo "  $0 restart    # Full restart"
        echo "  $0 frontend   # Start just the UI"
        echo "  $0 status     # Check what's running"
        echo ""
        exit 1
        ;;
esac
