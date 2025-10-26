# RAG Delta Report — Quick Reference

**One-page cheat sheet for RAG A/B testing.**

---

## 🚀 Common Commands

```bash
# Basic comparison: BM25 → Semantic
make rag-delta WEAVIATE_URL=http://127.0.0.1:8080

# With quality gates (fail CI if not improved)
make rag-delta-gates WEAVIATE_URL=http://127.0.0.1:8080

# Hybrid vs BM25
make rag-delta-hybrid WEAVIATE_URL=http://127.0.0.1:8080

# Custom modes
python3 scripts/rag_delta_report.py \
  --baseline-mode nearText \
  --treatment-mode hybrid \
  --seed seeds/eval_seed.jsonl \
  --min-delta-hit 0.01 \
  --fail-on-delta-gates
```

---

## 📊 Metrics Reference

| Metric          | Description                     | Good Value |
| --------------- | ------------------------------- | ---------- |
| **hit@k**       | % queries finding relevant docs | ≥97%       |
| **support@k**   | % queries with strong evidence  | ≥95%       |
| **mrr@k**       | Mean reciprocal rank (position) | ≥0.85      |
| **p50 latency** | Median query time               | <50ms      |
| **p95 latency** | 95th percentile                 | <100ms     |

---

## 🎯 Quality Gates

### Standard Thresholds

```bash
--min-delta-hit 0.01           # +1% hit improvement
--min-delta-support 0.01       # +1% support improvement
--min-delta-mrr 0.01           # +0.01 MRR improvement
--max-delta-latency-p95 0.1    # ≤+100ms latency increase
```

### Gate Interpretation

| Gate Status   | Action                              |
| ------------- | ----------------------------------- |
| ✅ **PASSED** | Merge PR, deploy to prod            |
| ❌ **FAILED** | Block merge, investigate regression |

---

## 📁 Output Files

```
artifacts/
├── delta_bm25_vs_nearText_20251018T153045Z.json  # Machine-readable
├── delta_bm25_vs_nearText_20251018T153045Z.md    # Human-readable
├── eval_bm25_20251018T153045Z.json               # Baseline raw results
└── eval_nearText_20251018T153045Z.json           # Treatment raw results
```

---

## 🔍 Reading Results

### JSON Structure

```json
{
  "delta": {
    "hit@k": 0.07, // +7% improvement ✅
    "support@k": 0.1, // +10% improvement ✅
    "latency_sec_p95": 0.01 // +10ms (acceptable) ✅
  },
  "delta_gates": {
    "passed": true,
    "violations": []
  }
}
```

### Markdown Table

```markdown
| Metric      | Baseline | Treatment | Δ        |
| ----------- | -------- | --------- | -------- |
| hit@k       | 90.0%    | 97.0%     | +7.0%    |
| support@k   | 85.0%    | 95.0%     | +10.0%   |
| latency p95 | 0.1000s  | 0.1100s   | +0.0100s |
```

**Interpretation:**

- ✅ **+7% hit rate** — Semantic search finds 7% more relevant docs
- ✅ **+10% support** — Evidence quality improved significantly
- ✅ **+10ms latency** — Acceptable cost for quality gain

---

## 🛠️ Troubleshooting

| Problem                       | Cause                     | Fix                                            |
| ----------------------------- | ------------------------- | ---------------------------------------------- |
| "Report not found"            | Evaluation crashed        | Run eval script manually: `make rag-eval-bm25` |
| "Gates failed" (but looks OK) | Thresholds too strict     | Lower `--min-delta-*` values                   |
| "Latency increased too much"  | Semantic slower than BM25 | Increase `--max-delta-latency-p95 0.2`         |
| "No delta improvement"        | Baseline already optimal  | Switch to hybrid mode or tune embeddings       |

---

## 🔗 CI Integration

### GitHub Actions

```yaml
- name: RAG Delta Gates
  run: make rag-delta-gates WEAVIATE_URL=http://weaviate:8080

- name: Post to PR
  run: cat artifacts/delta_*.md >> $GITHUB_STEP_SUMMARY
```

### Exit Codes

```bash
0  # Success (gates passed)
1  # Quality gates failed (block merge)
2  # Script error (infra issue)
```

---

## 📋 Checklist: Before Production

- [ ] Delta report shows **+1% hit@k** minimum
- [ ] Delta report shows **+1% support@k** minimum
- [ ] Latency increase **≤100ms p95**
- [ ] Both baseline and treatment **passed underlying gates**
- [ ] Seed file has **≥20 representative queries**
- [ ] CI workflow enabled on RAG code changes

---

## 🎓 Decision Matrix

| Scenario               | Baseline  | Treatment | Expected Δ                |
| ---------------------- | --------- | --------- | ------------------------- |
| **Initial validation** | BM25      | Semantic  | +3–7% hit, +50–100ms      |
| **Hybrid experiment**  | Semantic  | Hybrid    | +1–2% hit, +20–50ms       |
| **Embedding upgrade**  | Old model | New model | +2–5% hit, stable latency |
| **Regression check**   | Prod      | PR branch | 0% delta (no change)      |

---

## 📞 Help

- **Full docs:** [`RAG_DELTA_REPORTS.md`](RAG_DELTA_REPORTS.md)
- **Evaluation guide:** [`RAG_EVALUATION_README.md`](RAG_EVALUATION_README.md)
- **Script source:** [`scripts/rag_delta_report.py`](../scripts/rag_delta_report.py)

---

**Last updated:** 2025-10-18
