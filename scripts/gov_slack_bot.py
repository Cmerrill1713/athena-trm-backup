#!/usr/bin/env python3
"""
Slack Bot for Human-in-the-Loop Governance Control
Provides slash commands for manual governance overrides and status checks.

Setup:
1. Create Slack App at https://api.slack.com/apps
2. Enable "Slash Commands" feature
3. Add commands: /governance-status, /governance-force-promote, /governance-force-rollback, /governance-override
4. Set Request URL to: https://your-domain.com/slack/governance
5. Add to channels where governance notifications go

Usage:
/governance-status - Show current governance health and recent decisions
/governance-force-promote - Force promote current canary (emergency override)
/governance-force-rollback - Force rollback current canary (emergency)
/governance-override threshold=0.08 duration=300 - Temporarily override ECE threshold
"""
import os, sys, json, time, hmac, hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import subprocess

SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
PORT = int(os.getenv("PORT", "8082"))

def verify_slack_request(request_body, timestamp, signature):
    """Verify Slack request signature for security"""
    if not SLACK_SIGNING_SECRET:
        return True  # Skip verification in development

    basestring = f"v0:{timestamp}:{request_body}"
    my_signature = 'v0=' + hmac.new(
        SLACK_SIGNING_SECRET.encode(),
        basestring.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(my_signature, signature)

def get_governance_status():
    """Get current governance system status"""
    try:
        # Run governance gate check
        result = subprocess.run([
            "python3", "scripts/gov_predeploy_gate.py"
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))

        gate_status = "✅ PASSED" if result.returncode == 0 else "❌ BLOCKED"

        # Get recent decisions
        try:
            with open("logs/canary_decisions.log", "r") as f:
                recent_lines = f.readlines()[-5:]
                recent_decisions = "\n".join(line.strip() for line in recent_lines)
        except:
            recent_decisions = "No recent decisions found"

        return f"""*Governance Status Report*

🔍 *Gate Check*: {gate_status}

📋 *Recent Decisions*:
{recent_decisions}

🕐 *Timestamp*: {time.ctime()}"""

    except Exception as e:
        return f"❌ Error getting status: {str(e)}"

def force_promote():
    """Force promote current canary (emergency override)"""
    try:
        # Run promote script
        result = subprocess.run([
            "bash", "scripts/gov_promote.sh"
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))

        # Log the manual override
        with open("logs/canary_decisions.log", "a") as f:
            f.write(f"{time.asctime()} - DECISION: MANUAL_FORCE_PROMOTE - REASON: Slack command override\n")

        return "✅ *Force Promote Executed*\nCanary has been promoted via manual override."

    except Exception as e:
        return f"❌ Force promote failed: {str(e)}"

def force_rollback():
    """Force rollback current canary (emergency)"""
    try:
        # Run rollback script
        result = subprocess.run([
            "bash", "scripts/gov_rollback.sh"
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))

        # Log the manual override
        with open("logs/canary_decisions.log", "a") as f:
            f.write(f"{time.asctime()} - DECISION: MANUAL_FORCE_ROLLBACK - REASON: Slack command emergency rollback\n")

        return "🚨 *Emergency Rollback Executed*\nCanary has been rolled back immediately."

    except Exception as e:
        return f"❌ Force rollback failed: {str(e)}"

def override_threshold(params):
    """Temporarily override governance thresholds"""
    try:
        # Parse parameters like "threshold=0.08 duration=300"
        param_dict = {}
        for param in params.split():
            if "=" in param:
                key, value = param.split("=", 1)
                param_dict[key] = value

        threshold = param_dict.get("threshold")
        duration = int(param_dict.get("duration", "300"))  # Default 5 minutes

        if not threshold:
            return "❌ Missing threshold parameter. Usage: /governance-override threshold=0.08 duration=300"

        # Create temporary override file
        override_data = {
            "ece_threshold": float(threshold),
            "expires_at": time.time() + duration,
            "created_by": "slack_override"
        }

        with open("state/threshold_override.json", "w") as f:
            json.dump(override_data, f, indent=2)

        return f"""✅ *Threshold Override Applied*

🔧 *ECE Threshold*: {threshold} (was 0.06)
⏰ *Duration*: {duration} seconds
👤 *Override expires*: {time.ctime(override_data['expires_at'])}

Override will automatically expire. Use carefully!"""

    except Exception as e:
        return f"❌ Override failed: {str(e)}"

class SlackBotHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check endpoint"""
        if self.path == "/health":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "service": "governance-slack-bot"}).encode())
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')

            # Parse form data
            data = urllib.parse.parse_qs(post_data)

            # Extract Slack request details
            token = data.get('token', [''])[0]
            team_id = data.get('team_id', [''])[0]
            channel_id = data.get('channel_id', [''])[0]
            user_id = data.get('user_id', [''])[0]
            command = data.get('command', [''])[0]
            text = data.get('text', [''])[0]

            # Verify Slack signature (if configured)
            timestamp = self.headers.get('X-Slack-Request-Timestamp')
            signature = self.headers.get('X-Slack-Signature')

            if not verify_slack_request(post_data, timestamp, signature):
                self.send_error(403, "Invalid signature")
                return

            # Process command
            response_text = self.process_command(command, text, user_id)

            # Send response
            response = {
                "response_type": "in_channel",
                "text": response_text
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            self.send_error(500, f"Internal error: {str(e)}")

    def process_command(self, command, text, user_id):
        """Process Slack slash command"""
        if command == "/governance-status":
            return get_governance_status()

        elif command == "/governance-force-promote":
            return force_promote()

        elif command == "/governance-force-rollback":
            return force_rollback()

        elif command == "/governance-override":
            return override_threshold(text)

        else:
            return f"❓ Unknown command: {command}\n\nAvailable commands:\n• `/governance-status` - Show current status\n• `/governance-force-promote` - Force promote canary\n• `/governance-force-rollback` - Emergency rollback\n• `/governance-override threshold=X duration=Y` - Temporary threshold override"

def main():
    server = HTTPServer(('0.0.0.0', PORT), SlackBotHandler)
    print(f"🚀 Governance Slack Bot listening on port {PORT}")
    print("Configure your Slack app with these slash commands:")
    print("• /governance-status")
    print("• /governance-force-promote")
    print("• /governance-force-rollback")
    print("• /governance-override")
    server.serve_forever()

if __name__ == "__main__":
    main()
