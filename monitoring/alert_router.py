#!/usr/bin/env python3
import os, json, time, urllib.request

SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK_URL","")  # set this!
def slack(msg: str):
    if not SLACK_WEBHOOK:
        print("[alert] (no webhook) " + msg); return
    data = json.dumps({"text": msg}).encode("utf-8")
    req = urllib.request.Request(SLACK_WEBHOOK, data=data, headers={"Content-Type":"application/json"})
    try:
        urllib.request.urlopen(req, timeout=5).read()
    except Exception as e:
        print(f"[alert] slack error: {e}")

def on_ece_high(value: float):
    slack(f":rotating_light: ECE high ({value:.3f} > 0.06). ToT disabled, traffic quarantined.")

def on_entropy_critical(value: float):
    slack(f":fire: Entropy drift critical ({value:.3f} >= 0.25). Rolling back.")

# You can wire this to Prometheus alertmanager webhooks, or poll metrics directly.
if __name__ == "__main__":
    print("[alert] set SLACK_WEBHOOK_URL to enable Slack routing")

# Example polling implementation (uncomment to use)
# def poll_metrics():
#     import urllib.request
#     try:
#         resp = urllib.request.urlopen("http://localhost:9109/metrics", timeout=5).read().decode()
#         # Parse governance_ece and governance_entropy_drift
#         for line in resp.split('\n'):
#             if line.startswith('governance_ece{component="god_judge"}'):
#                 ece_val = float(line.split(' ')[1])
#                 if ece_val > 0.06:
#                     on_ece_high(ece_val)
#             elif line.startswith('governance_entropy_drift{component="god_judge"}'):
#                 drift_val = float(line.split(' ')[1])
#                 if drift_val >= 0.25:
#                     on_entropy_critical(drift_val)
#     except Exception as e:
#         print(f"[alert] metrics poll error: {e}")

# if __name__ == "__main__":
#     print("[alert] polling governance metrics every 30s...")
#     while True:
#         poll_metrics()
#         time.sleep(30)
