# 🚀 MISSION CONTROL - v0.9.4-meta-ux

## LAUNCH BLOCK
```bash
cd /Users/christianmerrill/Documents/GitHub
./GREEN_LIGHTS.sh
export META_PROMPTING=1 META_REFLECTION=1 META_RAG=1 META_SELFCRITIQUE=1
make stack-up && make truth
cd NeuroForgeApp
API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run
```

## MICRO-TRIAGE (Same Terminal)
```bash
# Meta panel missing
export META_PROMPTING=1 && make stack-restart

# Voice silent
python3 scripts/kokoro_server.py || echo "Using system TTS fallback"

# No 429s
python3 -m pip install slowapi anyio && make stack-restart

# Anything "off"
make truth && make nuke-ports && make stack-up
```

## QUICK EVIDENCE
```bash
for p in 8014 8090 8181; do echo "==== :$p ===="; curl -sS 127.0.0.1:$p/ready || true; done; \
curl -is 127.0.0.1:8014/health | sed -n '1,60p' | sed 's/Authorization: .*/Authorization: ***REDACTED***/'
```

## VERIFY (In App)
1. "logs?" → 🔴 + Reflection
2. "backend errors last 5 minutes" → 🟡/🟢 + RAG
3. "run smoke tests" → 🟢 + plan
4. Cmd+Shift+P → overlay

## SHIP
```bash
git add -A
git commit -m "Meta Dashboard + Adaptive UX: confidence, plan, tools, voice"
git tag -a v0.9.4-meta-ux -m "Meta UX end-to-end"
git push && git push origin v0.9.4-meta-ux
```

## SIGNALS
- "Shipping now" → On comms
- "Works!" → Celebration + next steps
- "Shipped!" → Post-launch checklist
- Paste error → Immediate triage

---

**STANDING BY** 🚀

