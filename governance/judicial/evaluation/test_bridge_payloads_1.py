import os
import httpx
BASE="http://localhost:8014"
H={"Authorization": f"Bearer {os.environ['BRIDGE_TOKEN']}"}

def test_text_payload():
    r = httpx.post(f"{BASE}/api/chat", json={"text":"ping"}, headers=H)
    assert r.status_code == 200

def test_swift_payload():
    r = httpx.post(f"{BASE}/api/chat", json={"kind":"chat","text":"ping"}, headers=H)
    assert r.status_code == 200
