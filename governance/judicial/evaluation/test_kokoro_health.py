import httpx
def test_kokoro_health():
    r = httpx.get("http://localhost:8020/health")
    assert r.status_code == 200
