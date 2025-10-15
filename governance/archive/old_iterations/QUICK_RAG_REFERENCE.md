# 🚀 RAG System Quick Reference

## ⚡ Instant Access

### RAG Service
```bash
# Health
curl http://localhost:8015/api/rag/health

# Search
curl http://localhost:8015/api/rag/query \
  -d '{"query":"YOUR_QUERY","k":5}' | jq '.hits[] | {title,channel}'

# Stats
curl http://localhost:8015/api/rag/stats | jq
```

### NeuroForgeApp Setup (in Xcode)
1. **Edit Scheme** → Run → Environment Variables
2. Add: `API_BASE=http://localhost:8014` and `QA_MODE=1`
3. Press **⌘R** to launch

---

## 📚 Knowledge Base

**170 Transcripts** from:
- IndyDevDan (11)
- Cole Medin (20)
- David Ondrej (20)
- AI Jason (19)
- AI Advantage, Prompt Engineering, Fireship, Matt Wolfe, WorldofAI (80)

**Topics**: Claude Code, Cursor, Aider, Agentic Coding, MCP, Agent Architectures

---

## 🔗 Quick Links

- **IndyDevDan Info**: `INDYDEVDAN_INFO.md`
- **Full RAG Guide**: `RAG_SYSTEM_COMPLETE.md`
- **Knowledge Base Report**: `AI_CODING_KNOWLEDGE_BASE_COMPLETE.md`
- **Transcripts**: `indydevdan_transcripts/` + `ai_coding_transcripts/`

---

## 🧪 Test It

```bash
# Best practices query
curl http://localhost:8015/api/rag/query \
  -d '{"query":"best practices for agentic coding","k":3}' \
  | jq '.hits[0] | {title, channel, score}'
```

**Expected**: Top-scored results from IndyDevDan, Cole Medin, etc.

---

✅ **Everything is ready to use!** 🚀
