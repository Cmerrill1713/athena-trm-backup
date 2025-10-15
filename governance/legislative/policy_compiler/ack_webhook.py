#!/usr/bin/env python3
"""
SMS Acknowledgment Webhook for Athena Alerts
Allows acknowledging alerts via SMS reply to prevent voice call escalation.
"""

from flask import Flask, request
import time
app = Flask(__name__)

@app.post("/twilio/ack")
def ack():
    body = (request.form.get("Body") or "").strip().lower()
    ack_id = (request.form.get("To") or "athena")  # or pass ?id=… if you prefer
    if body in {"ack","acknowledged","ok"}:
        path = f"/tmp/athena_alert_ack_{int(time.time())}"
        open(path,"w").close()
        return "<Response><Message>Athena: Acknowledged ✅</Message></Response>"
    return "<Response><Message>Athena: Send 'ACK' to acknowledge.</Message></Response>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5055, debug=True)
