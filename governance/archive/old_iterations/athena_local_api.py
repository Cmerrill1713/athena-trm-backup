#!/usr/bin/env python3
"""
Athena Local API Server
========================

Provides REST endpoints for the SwiftUI dashboard to communicate with Athena.
Runs locally on port 8009 for secure, local-only communication.

Features:
- Service status monitoring
- Alert management (get/acknowledge)
- Metrics reporting
- Configuration updates
- Test endpoints

Security: Only accessible locally (127.0.0.1), no external access.
"""

import time
import threading
from datetime import datetime, timedelta
import sys
import os

# Add AI Republic paths
sys.path.insert(0, os.path.dirname(__file__))

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    print("FastAPI not available. Install with: pip install fastapi uvicorn")
    FASTAPI_AVAILABLE = False

# Global state for quiet hours and Focus sync
QUIET_HOURS_ENABLED = True  # Default to enabled for demo
MOCK_QUIET_HOURS_STATUS = {
    'enabled': True,
    'focus_mode': None,
    'start_hour': 22,
    'end_hour': 8
}

# Mock data for development
MOCK_SERVICES = [
    {
        "name": "Memory Optimizer",
        "status": "running",
        "last_run": None,
        "next_run": None,
        "cadence": 3600
    },
    {
        "name": "Tribunal Monitor",
        "status": "running",
        "last_run": None,
        "next_run": None,
        "cadence": 900
    },
    {
        "name": "Voice Wake Word",
        "status": "running",
        "last_run": None,
        "next_run": None,
        "cadence": None
    },
    {
        "name": "Federation Sync",
        "status": "idle",
        "last_run": None,
        "next_run": None,
        "cadence": 7200
    }
]

MOCK_ALERTS = [
    {
        "id": "alert-1",
        "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
        "severity": "warning",
        "title": "High Memory Usage Detected",
        "message": "Memory utilization at 85%. Optimization scheduled.",
        "acknowledged": False
    },
    {
        "id": "alert-2",
        "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        "severity": "info",
        "title": "Memory Optimization Complete",
        "message": "Successfully optimized memory usage by 35%",
        "acknowledged": True
    }
]

MOCK_METRICS = {
    "memory_optimization_savings": 0.35,
    "tribunal_scans_today": 24,
    "alerts_triggered_today": 3,
    "average_response_time": 0.8,
    "system_health_score": 0.95
}

class AlertUpdate(BaseModel):
    acknowledged: bool

class CadenceUpdate(BaseModel):
    service: str
    cadence: int

if FASTAPI_AVAILABLE:
    app = FastAPI(title="Athena Local API", version="1.0.0")

    # CORS middleware for local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/status")
    async def get_status():
        """Get current service status"""
        # Update timestamps for mock data
        current_time = datetime.now()

        for service in MOCK_SERVICES:
            if service["cadence"]:
                # Simulate last run as cadence ago
                service["last_run"] = (current_time - timedelta(seconds=service["cadence"])).isoformat()
                service["next_run"] = (current_time + timedelta(seconds=service["cadence"] - 300)).isoformat()

        return {"services": MOCK_SERVICES}

    @app.get("/alerts")
    async def get_alerts():
        """Get current alerts"""
        return MOCK_ALERTS

    @app.put("/alerts/{alert_id}")
    async def update_alert(alert_id: str, update: AlertUpdate):
        """Acknowledge or update an alert"""
        for alert in MOCK_ALERTS:
            if alert["id"] == alert_id:
                alert["acknowledged"] = update.acknowledged
                return {"status": "updated"}

        raise HTTPException(status_code=404, detail="Alert not found")

    @app.post("/alerts/acknowledge-all")
    async def acknowledge_all_alerts():
        """Acknowledge all unacknowledged alerts"""
        acknowledged_count = 0
        for alert in MOCK_ALERTS:
            if not alert["acknowledged"]:
                alert["acknowledged"] = True
                acknowledged_count += 1

        return {"acknowledged": acknowledged_count}

    @app.get("/metrics")
    async def get_metrics():
        """Get system metrics"""
        return MOCK_METRICS

    @app.post("/cadence")
    async def update_cadence(update: CadenceUpdate):
        """Update service cadence"""
        for service in MOCK_SERVICES:
            if service["name"] == update.service:
                service["cadence"] = update.cadence
                return {"status": "updated", "service": update.service, "cadence": update.cadence}

        raise HTTPException(status_code=404, detail="Service not found")

    @app.post("/test-alert")
    async def send_test_alert():
        """Send a test alert"""
        test_alert = {
            "id": f"test-{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "severity": "info",
            "title": "Test Alert from Dashboard",
            "message": "This is a test alert sent from the Athena Dashboard",
            "acknowledged": False
        }

        MOCK_ALERTS.insert(0, test_alert)
        return {"status": "sent", "alert_id": test_alert["id"]}

    @app.get("/quiet-hours")
    async def get_quiet_hours_status():
        """Get current quiet hours status"""
        # Mock implementation - in real system this would be configurable
        current_hour = datetime.now().hour
        quiet_hours_enabled = True  # Default to enabled for demo
        quiet_start = 22  # 10 PM
        quiet_end = 8    # 8 AM

        is_quiet_hours = False
        if quiet_hours_enabled:
            if quiet_start > quiet_end:  # Overnight range
                is_quiet_hours = current_hour >= quiet_start or current_hour < quiet_end
            else:  # Same day range
                is_quiet_hours = current_hour >= quiet_start and current_hour < quiet_end

        return {
            "enabled": quiet_hours_enabled,
            "start_hour": quiet_start,
            "end_hour": quiet_end,
            "is_quiet_hours": is_quiet_hours,
            "description": f"{'Active' if is_quiet_hours else 'Inactive'} ({quiet_start}:00 - {quiet_end}:00)"
        }

    @app.post("/queue-alert")
    async def queue_alert(alert_data: dict):
        """Queue an alert for delivery after quiet hours"""
        # In a real implementation, this would store the alert in a persistent queue
        # For demo purposes, we'll just log it
        print(f"Alert queued during quiet hours: {alert_data.get('title', 'Unknown')}")

        # Add to a temporary queue that gets delivered when quiet hours end
        queued_alert = {
            "id": alert_data.get("id", f"queued-{int(time.time())}"),
            "timestamp": alert_data.get("timestamp", datetime.now().isoformat()),
            "severity": alert_data.get("severity", "info"),
            "title": alert_data.get("title", "Queued Alert"),
            "message": alert_data.get("message", ""),
            "acknowledged": False,
            "queued_during_quiet_hours": True
        }

        # Insert at the beginning of alerts list
        MOCK_ALERTS.insert(0, queued_alert)

        return {"status": "queued", "alert_id": queued_alert["id"]}

    @app.post("/focus-sync")
    async def focus_sync(sync_data: dict):
        """Sync Focus mode status with quiet hours"""
        focus_active = sync_data.get('enabled', False)
        focus_mode = sync_data.get('focus_mode')
        reason = sync_data.get('reason', 'Focus mode change')

        print(f"🎯 Focus sync: {focus_mode or 'Inactive'} ({reason})")

        # Update quiet hours based on Focus mode
        if focus_active:
            # Enable quiet hours when Focus is active
            global QUIET_HOURS_ENABLED
            QUIET_HOURS_ENABLED = True
            MOCK_QUIET_HOURS_STATUS['enabled'] = True
            MOCK_QUIET_HOURS_STATUS['focus_mode'] = focus_mode

            # Queue any existing alerts that would have been sent
            # In a real system, this would check recent alerts and queue them

            print(f"🔔 Quiet hours enabled due to Focus mode: {focus_mode}")
        else:
            # Focus ended - we keep quiet hours manual to avoid disrupting user preferences
            print("☀️ Focus mode ended - quiet hours remain as configured")

        return {"status": "synced", "focus_active": focus_active, "quiet_hours": QUIET_HOURS_ENABLED}

    @app.post("/calendar-sync")
    async def calendar_sync(sync_data: dict):
        """Sync Calendar events with quiet hours"""
        calendar_event = sync_data.get('calendar_event')
        source = sync_data.get('source', 'calendar_monitor')

        print(f"📅 Calendar sync: {calendar_event or 'No active events'} ({source})")

        # Update quiet hours based on calendar events
        if calendar_event:
            # Enable quiet hours during calendar events
            global QUIET_HOURS_ENABLED
            QUIET_HOURS_ENABLED = True
            MOCK_QUIET_HOURS_STATUS['enabled'] = True
            MOCK_QUIET_HOURS_STATUS['calendar_event'] = calendar_event

            print(f"🔔 Quiet hours enabled due to calendar: {calendar_event}")
        else:
            # No active calendar events - keep manual control
            print("📅 No active calendar events")
            print("☀️ Quiet hours remain as configured")

        return {"status": "synced", "calendar_event": calendar_event, "quiet_hours": QUIET_HOURS_ENABLED}

    @app.get("/calendar-status")
    async def calendar_status():
        """Get current calendar-driven quiet hours status"""
        return {
            "enabled": QUIET_HOURS_ENABLED,
            "calendar_event": MOCK_QUIET_HOURS_STATUS.get('calendar_event'),
            "focus_mode": MOCK_QUIET_HOURS_STATUS.get('focus_mode'),
            "is_quiet_hours": QUIET_HOURS_ENABLED and (
                MOCK_QUIET_HOURS_STATUS.get('calendar_event') is not None or
                MOCK_QUIET_HOURS_STATUS.get('focus_mode') is not None
            )
        }

    @app.post("/calendar-predictive")
    async def calendar_predictive(predictive_data: dict):
        """Handle predictive calendar activations"""
        event = predictive_data.get('event', {})
        reason = predictive_data.get('reason', 'Predictive activation')
        minutes_until = predictive_data.get('minutes_until', 0)
        lead_time = predictive_data.get('lead_time', 5)

        print(f"🔮 Predictive activation: {reason}")
        print(f"⏰ Event starts in {minutes_until:.1f} minutes")
        # Enable predictive quiet hours
        global QUIET_HOURS_ENABLED
        QUIET_HOURS_ENABLED = True
        MOCK_QUIET_HOURS_STATUS['enabled'] = True
        MOCK_QUIET_HOURS_STATUS['predictive_event'] = event.get('title')
        MOCK_QUIET_HOURS_STATUS['minutes_until'] = minutes_until

        print(f"🔔 Predictive quiet hours enabled {lead_time}min before: {event.get('title', 'Unknown')}")

        return {
            "status": "predictive_activated",
            "event": event,
            "reason": reason,
            "minutes_until": minutes_until,
            "lead_time": lead_time
        }

    @app.get("/calendar-predictive-status")
    async def calendar_predictive_status():
        """Get current predictive status"""
        return {
            "predictive_enabled": True,  # Could be made configurable
            "lead_time_minutes": 5,
            "current_predictions": MOCK_QUIET_HOURS_STATUS.get('predictive_event'),
            "minutes_until": MOCK_QUIET_HOURS_STATUS.get('minutes_until')
        }

    @app.post("/behavioral-record")
    async def record_behavioral_data(data: dict):
        """Record behavioral learning data"""
        try:
            # This would integrate with the behavioral learning system
            # For now, just acknowledge receipt
            print(f"🧠 Behavioral data recorded: {data.get('type', 'unknown')}")

            return {"status": "recorded", "type": data.get('type')}
        except Exception as e:
            return {"error": str(e)}

    @app.get("/behavioral-status")
    async def behavioral_status():
        """Get behavioral learning status"""
        # Mock status - would integrate with actual learning system
        return {
            "learning_enabled": True,
            "adaptation_enabled": False,  # Start in observation-only mode
            "total_observations": 0,
            "overall_confidence": 0.0,
            "patterns_learned": {
                "lead_times": 0,
                "alert_preferences": 0,
                "daily_rhythms": 0
            },
            "recommendations_available": 0
        }

    @app.get("/behavioral-recommendations")
    async def behavioral_recommendations():
        """Get behavioral learning recommendations"""
        # Mock recommendations - would come from actual learning system
        return {
            "recommendations": [],
            "message": "Learning in observation mode - no recommendations yet"
        }

    @app.post("/behavioral-enable-adaptation")
    async def enable_adaptation():
        """Enable active behavioral adaptation"""
        print("⚠️ Behavioral adaptation enabled - system will now auto-adjust settings")
        return {"status": "adaptation_enabled", "warning": "System will modify alert timing based on learned patterns"}

    @app.post("/behavioral-disable-adaptation")
    async def disable_adaptation():
        """Disable active behavioral adaptation"""
        print("✅ Behavioral adaptation disabled - returned to observation-only mode")
        return {"status": "adaptation_disabled", "message": "System will continue learning but not apply changes"}

    @app.post("/behavioral-weekly-summary")
    async def generate_weekly_summary():
        """Generate weekly behavioral learning summary"""
        try:
            # This would integrate with the weekly summary system
            # For now, return mock summary generation
            print("📊 Generating weekly behavioral learning summary...")

            # Mock summary data
            summary = {
                "timestamp": datetime.now().isoformat(),
                "week_of": (datetime.now() - timedelta(days=datetime.now().weekday())).date().isoformat(),
                "learning_status": {
                    "learning_enabled": True,
                    "adaptation_enabled": False,
                    "total_observations": 245,
                    "overall_confidence": 0.73
                },
                "patterns_discovered": {
                    "total_patterns": 6,
                    "lead_time_patterns": 2,
                    "alert_preferences": 3,
                    "daily_rhythms": 1
                },
                "recommendations": [
                    {
                        "type": "lead_time",
                        "event_type": "meeting",
                        "current": 5,
                        "recommended": 8,
                        "confidence": 0.85,
                        "reason": "Based on 15 meeting observations"
                    }
                ],
                "weekly_progress": {
                    "observations_this_week": 67,
                    "new_patterns_discovered": 2,
                    "confidence_improvement": 0.12,
                    "recommendations_added": 1
                },
                "insights": [
                    {
                        "type": "lead_time",
                        "title": "Meeting Preparation: Meeting",
                        "description": "You prefer 8 minutes of preparation time before meetings",
                        "confidence": 0.85,
                        "impact": "high"
                    }
                ],
                "next_steps": [
                    {
                        "action": "Review recommendations",
                        "description": "Check the Learning tab for personalized optimization suggestions",
                        "priority": "high"
                    }
                ]
            }

            return {"status": "summary_generated", "summary": summary}

        except Exception as e:
            return {"error": str(e)}

    @app.get("/behavioral-weekly-summary")
    async def get_weekly_summary():
        """Get the latest weekly behavioral summary"""
        # Mock latest summary
        return {
            "available": True,
            "last_generated": (datetime.now() - timedelta(days=1)).isoformat(),
            "summary": {
                "learning_progress": "Good progress this week",
                "key_insight": "You prefer 8 minutes of preparation before meetings",
                "recommendations_count": 2,
                "confidence_level": 0.73
            }
        }

    @app.get("/health")
    async def health_check():
        """API health check"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }

def start_api_server():
    """Start the FastAPI server"""
    if not FASTAPI_AVAILABLE:
        print("❌ FastAPI not available. Install with: pip install fastapi uvicorn")
        return

    print("🚀 Starting Athena Local API Server...")
    print("📍 URL: http://localhost:8009")
    print("📊 Status: http://localhost:8009/health")
    print("🔒 Security: Local access only (127.0.0.1)")
    print("🛑 Press Ctrl+C to stop")
    print()

    try:
        uvicorn.run(
            "athena_local_api:app",
            host="127.0.0.1",
            port=8009,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n✅ Athena API Server stopped")

def run_background_server():
    """Run the API server in a background thread"""
    if not FASTAPI_AVAILABLE:
        print("⚠️ API server not available (FastAPI not installed)")
        return None

    server_thread = threading.Thread(target=start_api_server, daemon=True)
    server_thread.start()

    # Wait a moment for server to start
    time.sleep(2)

    # Test connection
    try:
        import requests
        response = requests.get("http://localhost:8009/health", timeout=5)
        if response.status_code == 200:
            print("✅ Athena Local API Server running on http://localhost:8009")
            return server_thread
    except:
        pass

    print("❌ Failed to start Athena API server")
    return None

if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        start_api_server()
    else:
        print("❌ FastAPI required. Install with: pip install fastapi uvicorn")
        print("💡 This API server provides endpoints for the SwiftUI Athena Dashboard")
        print("📱 Dashboard will show mock data until real Athena integration is complete")
