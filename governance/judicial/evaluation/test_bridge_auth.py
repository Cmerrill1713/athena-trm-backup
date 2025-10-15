import os
import httpx

BASE="http://localhost:8014"

def test_chat_unauth_401():
    r = httpx.post(f"{BASE}/api/chat", json={"message":"ping"})
    assert r.status_code == 401

def test_chat_auth_message_200():
    tok = os.environ["BRIDGE_TOKEN"]
    r = httpx.post(f"{BASE}/api/chat", json={"message":"ping"}, headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
