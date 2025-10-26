# RAG Evaluation System

=====================

Production-ready evaluation suite for DocsV2 semantic search with hard-fail quality gates.

## 🎯 Features

- **hit@k**: Any expected_id appears in top-k results
- **support@k**: Any support_id appears in top-k results
- **MRR@k**: Mean Reciprocal Rank using expected_ids
- **Latency**: P50/P95 query performance metrics
- **Hard-fail**: CI/CD integration with quality gates
- **JSON Reports**: Detailed evaluation results in `artifacts/`

## 🚀 Quick Start

```bash
# Evaluate semantic search (DocsV2)
make rag-eval WEAVIATE_URL=http://127.0.0.1:8090

# Compare semantic vs BM25
make rag-compare WEAVIATE_URL=http://127.0.0.1:8090

# Run all evaluations
make rag-eval-all WEAVIATE_URL=http://127.0.0.1:8090
```

## 📊 Quality Gates

| Metric      | Threshold | Description                       |
| ----------- | --------- | --------------------------------- |
| hit@5       | ≥ 0.97    | 97% of queries find relevant docs |
| support@3   | ≥ 0.95    | 95% of queries have good docs     |
| MRR@5       | -         | Mean Reciprocal Rank              |
| P95 Latency | -         | 95th percentile query time        |

## 🔧 Usage

### Command Line

```bash
python3 scripts/eval_rag_hit_support.py \
  --weaviate-url http://127.0.0.1:8090 \
  --class DocsV2 \
  --seed seeds/eval_seed.jsonl \
  --k 5 --support-k 3 \
  --expect-hit 0.97 --expect-support 0.95 \
  --mode nearText \
  --report artifacts/eval_rag_$(date -u +%Y%m%dT%H%M%SZ).json
```

### Modes

- **nearText** (default): Uses Weaviate's HF vectorizer
- **bm25**: Keyword baseline for comparison
- **hybrid**: Runs both and merges client-side

### Seed File Format

**JSONL** (recommended):

```jsonl
{"query":"reset password", "expected_ids":["doc_12","doc_98"], "support_ids":["doc_12"]}
{"query":"refund policy",  "expected_ids":["doc_7"]}
{"query":"cancel subscription", "expected_ids":["doc_33","doc_34"]}
```

**CSV**:

```csv
query,expected_ids,support_ids
"reset password","doc_12|doc_98","doc_12"
"refund policy","doc_7",""
```

## 📁 File Structure

```
├── scripts/
│   └── eval_rag_hit_support.py    # Main evaluation script
├── seeds/
│   └── eval_seed.jsonl            # Test queries with ground truth
├── artifacts/
│   ├── eval_rag_20241018T123456Z.json
│   ├── eval_semantic_20241018T123456Z.json
│   └── eval_bm25_20241018T123456Z.json
└── Makefile.rag                   # Evaluation targets
```

## 🎯 Makefile Targets

| Target            | Description                            |
| ----------------- | -------------------------------------- |
| `rag-eval`        | Evaluate semantic search (DocsV2)      |
| `rag-eval-bm25`   | Evaluate BM25 baseline                 |
| `rag-eval-hybrid` | Evaluate hybrid mode (BM25 + semantic) |
| `rag-compare`     | Compare semantic vs BM25 performance   |
| `rag-eval-all`    | Run all evaluations                    |
| `rag-clean`       | Clean evaluation artifacts             |
| `rag-help`        | Show help and usage                    |

## 📈 Example Output

```json
{
  "total_queries": 10,
  "k": 5,
  "support_k": 3,
  "mode": "nearText",
  "class": "DocsV2",
  "hit@k": 0.98,
  "support@k": 0.96,
  "mrr@k": 0.845,
  "latency_sec_p50": 0.1234,
  "latency_sec_p95": 0.2345,
  "thresholds": {
    "hit@k": 0.97,
    "support@k": 0.95
  },
  "passed": true
}
```

## 🔍 Pro Tips

### ID Alignment

Ensure your DocsV2 objects expose a stable `doc_id` that matches `expected_ids` in your seed file.

### Latency Baselines

Run once with `--mode bm25` to record P95 baseline, then compare semantic delta in validation reports.

### Hybrid Merge

Switch to `--mode hybrid` during canary phase to keep recall high while fine-tuning HNSW parameters.

### CI/CD Integration

The script exits with code 1 if quality gates aren't met, perfect for CI/CD pipelines:

```yaml
# GitHub Actions example
- name: RAG Quality Gates
  run: make rag-eval WEAVIATE_URL=${{ env.WEAVIATE_URL }}
```

## 🚨 Troubleshooting

### Common Issues

1. **No seeds loaded**: Check seed file format and path
2. **GraphQL errors**: Verify Weaviate URL and class name
3. **Timeout errors**: Increase `--timeout` for slow queries
4. **ID field mismatch**: Use `--id-field` to specify correct property

### Debug Mode

Add `--retries 0` to disable retries and see immediate failures.

## 📊 Performance Monitoring

The evaluation script provides comprehensive metrics:

- **Query Latency**: P50/P95 response times
- **Recall Metrics**: hit@k and support@k scores
- **Ranking Quality**: MRR@k for ranking performance
- **Success Rate**: Overall evaluation pass/fail

## 🔄 Integration with Existing Tools

### Prometheus Metrics

Export evaluation results to Prometheus for monitoring:

```python
# Add to your monitoring pipeline
from prometheus_client import Gauge, Counter

hit_at_k_gauge = Gauge('rag_hit_at_k', 'Hit@k score')
support_at_k_gauge = Gauge('rag_support_at_k', 'Support@k score')
latency_p95_gauge = Gauge('rag_latency_p95_seconds', 'P95 query latency')
```

### Grafana Dashboards

Create dashboards using the JSON reports in `artifacts/` directory.

## 🎉 Success Criteria

Your RAG system is production-ready when:

- ✅ hit@5 ≥ 0.97 (97% queries find relevant docs)
- ✅ support@3 ≥ 0.95 (95% queries have good docs)
- ✅ P95 latency < 1.0s (sub-second response times)
- ✅ MRR@5 > 0.8 (good ranking quality)
- ✅ All quality gates pass consistently

## 📚 Further Reading

- [RAG Quality Gates Documentation](./rag_quality_gates.py)
- [HNSW Performance Tuning](./hnsw_tuner.py)
- [Dual-Read Rollout Strategy](./dual_read_rollout.py)
- [Production Monitoring](./rag_monitoring.sh)
