# RAG Delta Reports

**Automated A/B comparison of retrieval strategies with quality gates.**

---

## 🎯 Overview

The RAG delta report system compares two retrieval modes (e.g., BM25 vs semantic search) by running evaluations side-by-side and computing performance deltas. This enables:

- **Data-driven retrieval decisions** (semantic vs BM25 vs hybrid)
- **Regression detection** in CI/CD pipelines
- **Performance validation** for retrieval changes
- **Quality gates** with minimum improvement thresholds

---

## 📊 What It Measures

| Metric          | Description                                                  |
| --------------- | ------------------------------------------------------------ |
| **hit@k**       | % of queries where any expected doc appears in top-k results |
| **support@k**   | % of queries where support docs appear in top-k (stricter)   |
| **mrr@k**       | Mean Reciprocal Rank (1/position of first relevant doc)      |
| **latency p50** | Median query latency (seconds)                               |
| **latency p95** | 95th percentile query latency (seconds)                      |

---

## 🚀 Quick Start

### Basic Comparison: BM25 → Semantic

```bash
make rag-delta WEAVIATE_URL=http://127.0.0.1:8080
```

**Output:**

- `artifacts/delta_bm25_vs_nearText_<timestamp>.json` — Machine-readable delta
- `artifacts/delta_bm25_vs_nearText_<timestamp>.md` — Human-readable summary

### With Quality Gates (CI/CD)

```bash
make rag-delta-gates WEAVIATE_URL=http://127.0.0.1:8080
```

**Quality gates:**

- Δ hit@k ≥ +1.0%
- Δ support@k ≥ +1.0%
- Δ mrr@k ≥ +0.01
- Δ latency p95 ≤ +0.1s (100ms)

**Exit code:**

- `0` = All gates passed
- `1` = Gates failed (blocks CI merge)

### Hybrid vs BM25

```bash
make rag-delta-hybrid WEAVIATE_URL=http://127.0.0.1:8080
```

---

## 📖 Usage

### CLI Invocation

```bash
python3 scripts/rag_delta_report.py \
  --baseline-mode bm25 \
  --treatment-mode nearText \
  --weaviate-url http://127.0.0.1:8080 \
  --clazz DocsV2 \
  --seed seeds/eval_seed.jsonl \
  --k 5 --support-k 3 \
  --expect-hit 0.97 --expect-support 0.95 \
  --out-json artifacts/delta.json \
  --out-md artifacts/delta.md
```

### With Delta Gates

```bash
python3 scripts/rag_delta_report.py \
  --baseline-mode bm25 \
  --treatment-mode nearText \
  --seed seeds/eval_seed.jsonl \
  --min-delta-hit 0.01 \
  --min-delta-support 0.01 \
  --max-delta-latency-p95 0.1 \
  --fail-on-delta-gates
```

**Gate Parameters:**

| Flag                      | Description                    | Example       |
| ------------------------- | ------------------------------ | ------------- |
| `--min-delta-hit`         | Minimum hit@k improvement      | `0.01` = +1%  |
| `--min-delta-support`     | Minimum support@k improvement  | `0.01` = +1%  |
| `--min-delta-mrr`         | Minimum MRR improvement        | `0.01`        |
| `--max-delta-latency-p95` | Max p95 latency increase (sec) | `0.1` = 100ms |
| `--fail-on-delta-gates`   | Exit code 1 if gates fail      | flag          |

---

## 📄 Output Formats

### JSON Report

```json
{
  "timestamp": "20251018T153045Z",
  "class": "DocsV2",
  "seed_file": "seeds/eval_seed.jsonl",
  "seed_count": 10,
  "baseline_mode": "bm25",
  "treatment_mode": "nearText",
  "baseline": {
    "hit@k": 0.9,
    "support@k": 0.85,
    "mrr@k": 0.8,
    "latency_sec_p50": 0.05,
    "latency_sec_p95": 0.1,
    "passed": true
  },
  "treatment": {
    "hit@k": 0.97,
    "support@k": 0.95,
    "mrr@k": 0.88,
    "latency_sec_p50": 0.055,
    "latency_sec_p95": 0.11,
    "passed": true
  },
  "delta": {
    "hit@k": 0.07,
    "support@k": 0.1,
    "mrr@k": 0.08,
    "latency_sec_p50": 0.005,
    "latency_sec_p95": 0.01
  },
  "delta_gates": {
    "passed": true,
    "violations": []
  }
}
```

### Markdown Summary

```markdown
## RAG Delta Report (bm25 → nearText)

**Timestamp:** 20251018T153045Z UTC  
**Class:** `DocsV2` • **Seed:** `seeds/eval_seed.jsonl` • **N=10**

| Metric          | Baseline | Treatment |       Δ |
| --------------- | -------: | --------: | ------: |
| hit@k           |    90.0% |     97.0% |   +7.0% |
| support@k       |    85.0% |     95.0% |  +10.0% |
| mrr@k           |   0.8000 |    0.8800 | +0.0800 |
| latency p50 (s) |   0.0500 |    0.0550 | +0.0050 |
| latency p95 (s) |   0.1000 |    0.1100 | +0.0100 |

**Baseline passed gates:** true  
**Treatment passed gates:** true

**✅ Delta improvement gates: PASSED**
```

---

## 🔗 CI/CD Integration

### GitHub Actions

```yaml
name: RAG Delta Validation

on:
  pull_request:
    paths:
      - "seeds/**"
      - "backend/rag/**"

jobs:
  delta-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Start Weaviate
        run: docker-compose up -d weaviate

      - name: Run Delta Report
        run: |
          make rag-delta-gates WEAVIATE_URL=http://127.0.0.1:8080

      - name: Upload Reports
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: rag-delta-reports
          path: artifacts/delta_*.{json,md}

      - name: Post Summary to PR
        if: always()
        run: |
          echo "## RAG Delta Summary" >> $GITHUB_STEP_SUMMARY
          cat artifacts/delta_*.md >> $GITHUB_STEP_SUMMARY
```

### GitLab CI

```yaml
rag-delta:
  stage: test
  script:
    - docker-compose up -d weaviate
    - make rag-delta-gates WEAVIATE_URL=http://weaviate:8080
  artifacts:
    paths:
      - artifacts/delta_*.json
      - artifacts/delta_*.md
    reports:
      junit: artifacts/delta_*.json
  only:
    changes:
      - seeds/**
      - backend/rag/**
```

---

## 🎯 Common Scenarios

### 1. Validate Semantic > BM25

**Goal:** Ensure semantic search beats BM25 baseline.

```bash
make rag-delta-gates WEAVIATE_URL=http://127.0.0.1:8080
```

**Expected deltas:**

- hit@k: +1–5%
- support@k: +1–3%
- mrr@k: +0.02–0.08
- latency p95: ≤+10%

### 2. Test Hybrid Mode

**Goal:** See if hybrid (BM25 + semantic) beats pure semantic.

```bash
python3 scripts/rag_delta_report.py \
  --baseline-mode nearText \
  --treatment-mode hybrid \
  --seed seeds/eval_seed.jsonl \
  --min-delta-hit 0.005
```

### 3. Regression Testing

**Goal:** Block PRs that degrade retrieval quality.

```yaml
# .github/workflows/rag-regression.yml
- name: Delta Gates (Fail on Regression)
  run: |
    make rag-delta-gates || \
      (echo "❌ Retrieval quality regressed!" && exit 1)
```

### 4. Performance Monitoring

**Goal:** Track delta over time (store in metrics DB).

```bash
# Run weekly, push to Prometheus/Grafana
make rag-delta | jq '.delta' | curl -X POST http://metrics:9090/push \
  --data-binary @-
```

---

## 🧪 Testing

### Unit Tests

```bash
python3 -m pytest tests/rag/test_delta_report.py -v
```

### Integration Test

```bash
# Requires running Weaviate + seeded data
make rag-delta WEAVIATE_URL=http://127.0.0.1:8080
```

**Checks:**

- Both evaluations complete
- JSON/MD files generated
- Delta calculations correct
- Gate logic works

---

## 🛠️ Troubleshooting

### Issue: "Report not found"

**Cause:** Underlying evaluation script failed before writing report.

**Fix:**

```bash
# Run evaluations manually to debug
python3 scripts/eval_rag_hit_support.py \
  --mode bm25 \
  --seed seeds/eval_seed.jsonl \
  --report /tmp/debug.json
```

### Issue: "Delta gates failed but metrics look good"

**Cause:** Thresholds too strict for your data.

**Fix:** Adjust gate thresholds:

```bash
--min-delta-hit 0.005  # Lower from 0.01 (1%) to 0.5%
```

### Issue: "Latency p95 increased too much"

**Cause:** Semantic search slower than BM25 (expected).

**Fix:** Increase tolerance:

```bash
--max-delta-latency-p95 0.2  # Allow +200ms instead of +100ms
```

---

## 📚 Related Documentation

- [`scripts/eval_rag_hit_support.py`](../scripts/eval_rag_hit_support.py) — Underlying evaluator
- [`seeds/eval_seed.jsonl`](../seeds/eval_seed.jsonl) — Evaluation queries
- [`Makefile.rag`](../Makefile.rag) — Make targets
- [`RAG_EVALUATION_README.md`](RAG_EVALUATION_README.md) — Quality gates overview

---

## 🎓 Best Practices

### 1. Seed Quality

**Bad:**

```jsonl
{
  "query": "docs",
  "expected_ids": [
    "doc_1"
  ]
}
```

**Good:**

```jsonl
{
  "query": "How do I reset my password?",
  "expected_ids": [
    "auth_password_reset.md",
    "troubleshooting.md"
  ],
  "support_ids": [
    "auth_password_reset.md"
  ]
}
```

**Why:** Specific queries with multiple candidates test ranking quality.

### 2. Baseline Selection

- Use **BM25** as baseline (fast, deterministic)
- Compare **semantic** vs BM25 first
- Compare **hybrid** vs semantic second

### 3. Gate Thresholds

Start conservative:

```bash
--min-delta-hit 0.01        # +1% minimum improvement
--min-delta-support 0.01    # +1% minimum improvement
--max-delta-latency-p95 0.1 # +100ms max latency cost
```

Tighten over time as retrieval improves.

### 4. CI Integration

```yaml
# Run on PRs touching retrieval code
on:
  pull_request:
    paths:
      - "backend/rag/**"
      - "seeds/**"
      - "scripts/eval_*.py"
```

---

## 🚦 Exit Codes

| Code | Meaning                                       |
| ---- | --------------------------------------------- |
| `0`  | Success (gates passed if enabled)             |
| `1`  | Delta gates failed (quality regression)       |
| `2`  | Evaluation script error (e.g., Weaviate down) |

---

## 📝 Changelog

### v1.0 (2025-10-18)

- ✅ Initial implementation
- ✅ JSON + Markdown output
- ✅ Delta gate logic (optional)
- ✅ CI/CD examples (GitHub Actions, GitLab)
- ✅ Unit tests

---

**Questions?** See [`QUICK_REFERENCE.md`](../QUICK_REFERENCE.md) or open an issue.
