# 🚀 EXECUTE NOW - v0.9.4-meta-ux

## GO
```bash
cd /Users/christianmerrill/Documents/GitHub
./GREEN_LIGHTS.sh
export META_PROMPTING=1 META_REFLECTION=1 META_RAG=1 META_SELFCRITIQUE=1
make stack-up && make truth
python3 scripts/kokoro_server.py || true &
cd NeuroForgeApp
API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run
```

## VERIFY (60s terminal)
```bash
curl -fsS http://127.0.0.1:8014/ready && \
curl -fsS http://127.0.0.1:8090/ready && \
curl -fsS http://127.0.0.1:8181/ready && echo "✅ backends ready"

curl -is http://127.0.0.1:8014/health | grep -i "x-meta" && echo "✅ meta active"
```

**In app (2 min):**
- Say "logs?" → 🔴
- Say "backend errors" → 🟡
- Say "top 3" → 🟢
- Press Cmd+Shift+P → overlay

## SHIP
```bash
cd /Users/christianmerrill/Documents/GitHub
git add -A
git commit -m "Meta Dashboard + Adaptive UX: confidence, plan, tools, voice"
git tag -a v0.9.4-meta-ux -m "Meta UX end-to-end"
git push && git push origin v0.9.4-meta-ux
```

## FIXES
```bash
# No meta panel
export META_PROMPTING=1 && make stack-restart

# No voice
python3 scripts/kokoro_server.py

# No 429s
python3 -m pip install slowapi anyio && make stack-restart

# Ghosts
make nuke-ports && make stack-up
```

## ROLLBACK
```bash
git reset --hard v0.9.3-tier3-4 && make stack-restart
```

---

**READY TO LAUNCH** 🚀

