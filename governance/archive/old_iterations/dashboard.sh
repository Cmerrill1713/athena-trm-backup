#!/bin/bash
# Quick dashboard control script

case "$1" in
    start)
        echo "🖥️ Starting AI Republic Dashboard..."
        launchctl start com.athena.dashboard
        sleep 2
        echo "📊 Dashboard available at: http://localhost:8090"
        echo "🔄 Auto-refreshes every 30 seconds"
        ;;
    stop)
        echo "🛑 Stopping AI Republic Dashboard..."
        launchctl stop com.athena.dashboard
        echo "✅ Dashboard stopped"
        ;;
    status)
        echo "📊 Dashboard Status:"
        launchctl list com.athena.dashboard 2>/dev/null || echo "Dashboard not running"
        ;;
    open)
        echo "🌐 Opening dashboard in browser..."
        open http://localhost:8090
        ;;
    *)
        echo "Usage: $0 {start|stop|status|open}"
        echo ""
        echo "Commands:"
        echo "  start  - Start the dashboard"
        echo "  stop   - Stop the dashboard"
        echo "  status - Check if dashboard is running"
        echo "  open   - Open dashboard in browser"
        echo ""
        echo "Dashboard URL: http://localhost:8090"
        ;;
esac
