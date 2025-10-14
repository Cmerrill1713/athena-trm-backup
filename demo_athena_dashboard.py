#!/usr/bin/env python3
"""
Demo Athena Dashboard Integration
=================================

Demonstrates the complete SwiftUI dashboard + local API integration.
Starts the local API server and shows how the dashboard connects.

Usage:
    python3 demo_athena_dashboard.py     # Start API server for dashboard
    # Then open NeuroForge app and use Cmd+Shift+A to open Athena Dashboard
"""

import time
import sys

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")

    try:
        import fastapi
        import uvicorn
        print("✅ FastAPI available")
    except ImportError:
        print("❌ FastAPI not installed. Install with:")
        print("   pip install fastapi uvicorn")
        return False

    return True

def start_api_server():
    """Start the Athena local API server"""
    print("🚀 Starting Athena Local API Server...")
    print("📍 Dashboard will connect to: http://localhost:8009")
    print("📊 Status endpoint: http://localhost:8009/health")
    print()

    # Import and run the API server
    try:
        import athena_local_api
        athena_local_api.start_api_server()
    except KeyboardInterrupt:
        print("\n✅ Athena API Server stopped")
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")

def show_dashboard_instructions():
    """Show instructions for using the dashboard"""
    print("🎛️ Athena Dashboard Integration Complete!")
    print("=" * 50)
    print()
    print("📱 Dashboard Features:")
    print("• Live Status Panel - Real-time service monitoring")
    print("• Alert History - View and acknowledge alerts")
    print("• Controls Panel - Adjust cadences and settings")
    print("• Metrics Dashboard - Performance analytics")
    print()
    print("🖥️ To Open Dashboard:")
    print("1. Open NeuroForge app")
    print("2. Use menu: Tools → Open Athena Dashboard")
    print("   Or keyboard: Cmd + Shift + A")
    print()
    print("🔄 Dashboard Behavior:")
    print("• Auto-refreshes every 5 seconds")
    print("• Shows 'Disconnected' if API server is down")
    print("• Falls back to mock data for development")
    print("• Real-time updates when API is available")
    print()
    print("🧪 Test Features:")
    print("• Click 'Send Test Alert' to trigger notifications")
    print("• Use 'Acknowledge' buttons to clear alerts")
    print("• Try adjusting service cadences")
    print("• View metrics and performance data")
    print()
    print("🔌 API Endpoints:")
    print("• GET /status - Service status")
    print("• GET /alerts - Current alerts")
    print("• GET /metrics - Performance metrics")
    print("• POST /test-alert - Send test alert")
    print("• PUT /alerts/{id} - Acknowledge alert")
    print()
    print("🔒 Security:")
    print("• Local-only access (127.0.0.1:8009)")
    print("• No external network exposure")
    print("• Secure communication between app and API")
    print()
    print("💡 Pro Tips:")
    print("• Keep API server running while using dashboard")
    print("• Dashboard gracefully handles API disconnections")
    print("• Use 'Refresh' button to force immediate updates")
    print("• Check logs with: tail -f /tmp/athena_*.out")
    print()

def run_demo():
    """Run the complete dashboard demo"""
    print("🎛️ Athena Dashboard Demo")
    print("=" * 30)
    print()

    if not check_dependencies():
        return

    print("📋 Demo Steps:")
    print("1. Start local API server (this terminal)")
    print("2. Open NeuroForge app in another terminal")
    print("3. Use Cmd+Shift+A to open Athena Dashboard")
    print("4. Watch real-time updates and test features")
    print()

    # Show instructions first
    show_dashboard_instructions()

    print("🚀 Starting API server in 3 seconds...")
    print("Press Ctrl+C to stop the demo")
    print()
    time.sleep(3)

    # Start the API server
    try:
        start_api_server()
    except KeyboardInterrupt:
        print("\n✅ Demo completed!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--instructions":
        show_dashboard_instructions()
    else:
        run_demo()
