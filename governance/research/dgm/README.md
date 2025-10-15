# Darwin Gödel Machine Integration
## Self-Improving AI Agents with Governance Oversight

<p align="center">
  <a href="https://arxiv.org/abs/2505.22954"><img src="https://img.shields.io/badge/arXiv-2505.22954-b31b1b.svg?logo=arxiv&style=for-the-badge"></a>
  <a href="../../../docs/prd/DGM_INTEGRATION_PRD.md"><img src="https://img.shields.io/badge/PRD-ST--201-blue?style=for-the-badge"></a>
</p>

---

## 🎯 **What is This?**

Integration of the [Darwin Gödel Machine](https://arxiv.org/abs/2505.22954) with Athena's governance framework, enabling **safe, self-improving coding agents**.

**DGM** iteratively modifies its own code and validates changes empirically. Our integration adds **governance oversight** to ensure all self-improvements are:
- ✅ Constitutionally compliant
- ✅ Judicially approved
- ✅ Canary-deployed safely
- ✅ Continuously monitored

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────┐
│                    DGM Evolution Cycle                  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  1. Select Parent Agent from Archive                    │
│  2. Generate Offspring (Foundation Model)               │
│  3. Constitutional Compliance Check  ◄──────────────┐   │
│  4. Run Benchmarks (SWE-bench, Polyglot)            │   │
│  5. Judicial Verdict Request         ◄──────────────┤   │
│  6. Execute Verdict Actions                         │   │
│  7. Update Archive if Approved                      │   │
└─────────────────────────────────────────────────────┘   │
                          │                                │
                          ▼                                │
              ┌───────────────────────┐                    │
              │  Governance Oversight  │                   │
              └───────────────────────┘                    │
                │         │         │                      │
    ┌───────────┘         │         └───────────┐          │
    ▼                     ▼                     ▼          │
Legislative          Judicial             Executive        │
    │                     │                     │          │
    ├─ Constitutional     ├─ Verdict            ├─ Orchestrate
    │  Policy             │  Validator          │  Evolution
    │                     │                     │          │
    └─────────────────────┴─────────────────────┴──────────┘
```

---

## 🚀 **Quick Start**

### Prerequisites
```bash
# Ensure you're in the repo root
cd /Users/christianmerrill/Documents/GitHub

# API keys in environment
export ANTHROPIC_API_KEY='your-key'
export OPENAI_API_KEY='your-key'

# Docker running
docker --version
```

### Run Pilot Experiment
```bash
# Run 10 generations with governance oversight
python governance/research/dgm/experiments/experiment_runner.py \
  governance/research/dgm/experiments/pilot_experiment.yaml
```

### Via GitHub Actions
```bash
# Trigger via workflow_dispatch
gh workflow run dgm-experiment.yml \
  -f experiment_config=governance/research/dgm/experiments/pilot_experiment.yaml \
  -f max_generations=10
```

---

## 📁 **Directory Structure**

```
governance/research/dgm/
├── README.md                          # This file
├── dgm-upstream/                      # Cloned DGM repo
├── dgm_governance_adapter.py          # Main adapter
├── agents/                            # Agent archive (gitignored)
│   └── dgm_gen_*.json
├── experiments/
│   ├── experiment_runner.py           # Experiment framework
│   └── pilot_experiment.yaml          # Sample config
├── results/                           # Experiment results
│   └── dgm_pilot_001/
│       └── experiment_report.json
└── config/
    └── dgm_config.yaml                # DGM configuration
```

---

## 🛡️ **Governance Integration**

### Legislative Layer
**File:** `governance/legislative/self_modification_policy.yaml`

**Constitutional Constraints:**
- ✓ Mandatory sandboxed execution
- ✓ No arbitrary code execution (eval, exec)
- ✓ File access restrictions
- ✓ Performance regression limits
- ✓ ECE-based human oversight

### Judicial Layer
**File:** `governance/judicial/evaluation/dgm_verdict_validator.py`

**Verdict Process:**
1. Safety violation check
2. Performance delta calculation
3. Code complexity analysis
4. Verdict rendering:
   - `APPROVE`: Strong improvement (>10%)
   - `CANARY_DEPLOY`: Moderate improvement (2-10%)
   - `REJECT`: Regression or safety issues
   - `REVIEW_REQUIRED`: Low confidence

### Executive Layer
**File:** `governance/executive/orchestration/dgm_orchestrator.py`

**Orchestration:**
- Coordinates evolution cycles
- Enforces circuit breakers
- Manages agent archive
- Executes verdict actions

---

## 📊 **Monitoring**

### Prometheus Metrics
```python
# Generation metrics
dgm_generations_total
dgm_verdicts_total{verdict_type="APPROVE|REJECT|CANARY"}

# Performance metrics
dgm_agent_performance{benchmark="swe-bench-lite"}
dgm_performance_improvement

# Safety metrics
dgm_safety_violations_total{violation_type="eval|exec|..."}
dgm_ece_estimate

# Archive metrics
dgm_archive_size
dgm_archive_diversity
```

### Grafana Dashboards
- **DGM Evolution:** Track performance trends
- **Verdict Analysis:** Approval rates, rejection reasons
- **Safety Monitoring:** Violations, ECE estimates
- **Archive Health:** Size, diversity, quality

---

## 🧪 **Experiments**

### Pilot Experiment (ST-204)
**Goal:** Validate governance integration  
**Config:** `experiments/pilot_experiment.yaml`  
**Hypothesis:** 20% → 30% on SWE-bench in 10 generations  

**Success Criteria:**
- ✓ 100% governance compliance
- ✓ Zero safety violations
- ✓ >30% approval rate
- ✓ >5% performance improvement

### Running Custom Experiments

1. Create experiment config:
```yaml
# my_experiment.yaml
experiment_id: "my_exp_001"
description: "Testing DGM with custom constraints"
parameters:
  max_generations: 20
  foundation_model: "claude-sonnet-4"
  benchmark: "swe-bench-lite"
```

2. Run experiment:
```bash
python governance/research/dgm/experiments/experiment_runner.py my_experiment.yaml
```

3. View results:
```bash
cat governance/research/dgm/results/my_exp_001/experiment_report.json
```

---

## 🔐 **Safety**

### Sandbox Execution
All agent code runs in isolated Docker containers:
```python
# Automatic sandboxing via constitutional policy
docker run --rm --memory=4g --cpus=2 \
  --network=none \  # No network access
  --read-only \     # Read-only filesystem
  agent:latest
```

### Circuit Breakers
```yaml
# Configured in dgm_config.yaml
evolution_limits:
  circuit_breaker_failures: 5
  max_iterations_per_day: 50
```

### Human Oversight
```python
if ece < 0.7:
    verdict = "REVIEW_REQUIRED"
    actions = ["HUMAN_REVIEW", "PAUSE_EVOLUTION"]
```

---

## 📈 **Performance Targets**

Based on paper results and governance constraints:

| Benchmark | Baseline | Target (10 gen) | Target (50 gen) |
|-----------|----------|-----------------|-----------------|
| SWE-bench-lite | 20% | 30% | 40% |
| Polyglot | 14% | 20% | 25% |
| Governance Integration | 0% | 70% | 85% |

---

## 🔧 **Configuration**

### Key Settings (`config/dgm_config.yaml`)

```yaml
# Safety thresholds
safety:
  require_judicial_verdict: true
  human_oversight_threshold: 0.7
  max_archive_size: 1000

# Canary integration
canary:
  enabled: true
  traffic_percentage: 0.05
  rollback_threshold: 0.15

# Monitoring
monitoring:
  alert_on_ece_below: 0.5
  slack_notifications: true
```

---

## 📚 **Related Documentation**

- **PRD:** [DGM Integration PRD](../../../docs/prd/DGM_INTEGRATION_PRD.md)
- **Policy:** [Self-Modification Policy](../../legislative/self_modification_policy.yaml)
- **Validator:** [Verdict Validator](../../judicial/evaluation/dgm_verdict_validator.py)
- **Orchestrator:** [Executive Orchestrator](../../executive/orchestration/dgm_orchestrator.py)
- **Upstream:** [DGM Original Repo](https://github.com/jennyzzt/dgm)
- **Paper:** [arXiv:2505.22954](https://arxiv.org/abs/2505.22954)

---

## 🎯 **Roadmap**

### ✅ Phase 1: Foundation (Complete)
- [x] Clone DGM repository
- [x] Create integration scaffolding
- [x] Wire to judicial verdict system
- [x] Define constitutional policies

### 🏗️ Phase 2: Integration (In Progress)
- [ ] Connect to canary deployment system
- [ ] Add Prometheus/Grafana dashboards
- [ ] Implement full benchmark suite
- [ ] Create operator runbook

### 📊 Phase 3: Validation (Planned)
- [ ] Run pilot experiment (10 generations)
- [ ] Validate safety mechanisms
- [ ] Measure performance improvements
- [ ] Gather approval rate statistics

### 🚀 Phase 4: Production (Planned)
- [ ] Continuous evolution (weekly scheduled)
- [ ] Auto-deployment of approved agents
- [ ] Integration with existing services
- [ ] Long-term monitoring

---

## 🤝 **Contributing**

See [PRD ST-201](../../../docs/prd/DGM_INTEGRATION_PRD.md) for user stories and acceptance criteria.

**Key Areas:**
- Benchmark integration (ST-202)
- Canary deployment (ST-204)
- Monitoring dashboards (ST-205)
- Safety testing (ST-206)

---

## 📄 **License**

DGM upstream: Apache 2.0  
Athena Governance Integration: [See repo LICENSE]

---

## 🎓 **Citation**

If you use this integration in research, please cite both:

```bibtex
@article{zhang2025darwin,
  title={Darwin Godel Machine: Open-Ended Evolution of Self-Improving Agents},
  author={Zhang, Jenny and Hu, Shengran and Lu, Cong and Lange, Robert and Clune, Jeff},
  journal={arXiv preprint arXiv:2505.22954},
  year={2025}
}
```

---

**Status:** 🟡 **ACTIVE DEVELOPMENT**  
**Next Milestone:** Pilot experiment validation  
**Contact:** @Cmerrill1713

