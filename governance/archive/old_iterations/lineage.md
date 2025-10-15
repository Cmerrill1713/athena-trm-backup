# Model Lineage Report

- **Nodes**: 4
- **Edges**: 4
- **Generated**: 2025-10-12 03:46:28 UTC

## Promotion / Rollback History

| Time (UTC) | Event | Transition | Reason | Canary | Control | Δ | p |
|------------|-------|------------|--------|-------:|--------:|---:|---|
| 2025-10-12T10:00:00Z | PROMOTION | `baseline` → `fastvlm-1.5b` | initial_deployment | - | - | - | - |
| 2025-10-14T12:00:01Z | PROMOTION | `fastvlm-1.5b` → `fastvlm-0.5b` | canary_win_stat_sig | 92.0% | 85.9% | +6.1% | 0.012 |
| 2025-10-16T18:30:22Z | PROMOTION | `fastvlm-0.5b` → `fastvlm-7b` | canary_win_stat_sig | 89.2% | 85.9% | +3.3% | 0.048 |
| 2025-10-17T03:15:44Z | ROLLBACK | `fastvlm-7b` → `fastvlm-0.5b` | oom_issues | - | - | - | - |

## Notes

- **Δ**: Improvement (canary - control success rate)
- **p**: Statistical p-value from Wilson intervals
- **Canary/Control**: Success rates during evaluation
- **PROMOTION**: Stat-sig win sustained for 48h
- **ROLLBACK**: Stat-sig regression detected

## Lineage Graph

See `lineage.svg` for visual representation (requires Graphviz).

Or ASCII tree in `lineage.txt`