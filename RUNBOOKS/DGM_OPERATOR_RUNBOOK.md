# DGM Operator Runbook
## Darwin Gödel Machine Self-Improving Agents

**System:** Darwin Gödel Machine Integration  
**Owner:** @Cmerrill1713  
**PRD:** ST-201  
**On-Call:** Governance Team

---

## 🎯 **Quick Reference**

### Health Check (30 seconds)
```bash
# Check evolution status
curl -s http://localhost:9090/api/v1/query?query=dgm_generations_total | jq

# Check for safety violations
curl -s http://localhost:9090/api/v1/query?query=dgm_safety_violations_total | jq

# Check approval rate
curl -s http://localhost:9090/api/v1/query?query='rate(dgm_verdicts_total{verdict_type=~"APPROVE|CANARY_DEPLOY"}[5m])/rate(dgm_verdicts_total[5m])' | jq
```

### Dashboards
- **Grafana:** http://localhost:3000/d/dgm-evolution
- **Prometheus:** http://localhost:9090

---

## 🚀 **Common Operations**

### Start DGM Evolution

**Manual:**
```bash
./scripts/dgm_quickstart.sh
# Select option 1 for pilot experiment
```

**GitHub Actions:**
```bash
gh workflow run dgm-experiment.yml \
  -f experiment_config=governance/research/dgm/experiments/pilot_experiment.yaml \
  -f max_generations=10
```

**Scheduled:** Runs automatically Sunday 3am UTC

---

### Monitor Active Evolution

**Check Current Generation:**
```bash
# Via Prometheus
curl -s http://localhost:9090/api/v1/query?query=dgm_generations_total | \
  jq -r '.data.result[0].value[1]'
```

**Check Approval Rate:**
```bash
python3 << 'EOF'
from governance.judicial.evaluation.dgm_verdict_validator import DGMVerdictValidator
validator = DGMVerdictValidator()
stats = validator.get_approval_rate()
print(f"Approval Rate: {stats['approval_rate']:.1%}")
print(f"Approved: {stats['approved']}/{stats['total']}")
EOF
```

**View Recent Verdicts:**
```bash
tail -20 governance/judicial/evaluation/dgm_verdicts.jsonl | jq -r '.verdict'
```

---

### Stop Evolution

**Graceful Stop:**
```bash
# Set circuit breaker to 0 (will stop after current generation)
# Edit config:
sed -i '' 's/circuit_breaker_failures: 5/circuit_breaker_failures: 0/' \
  governance/research/dgm/config/dgm_config.yaml
```

**Emergency Stop:**
```bash
# Kill running processes
pkill -f dgm_orchestrator
pkill -f experiment_runner

# Check no containers running
docker ps | grep dgm
docker stop $(docker ps -q --filter "label=dgm")
```

---

## 🚨 **Incident Response**

### Safety Violation Detected

**Severity:** 🔴 **CRITICAL**

**Symptoms:**
- Alert: "DGM Safety Violation Detected"
- Metric: `dgm_safety_violations_total` > 0

**Response:**
1. **Immediately stop evolution:**
```bash
pkill -f dgm_orchestrator
```

2. **Identify violation:**
```bash
tail -50 governance/judicial/evaluation/dgm_verdicts.jsonl | \
  jq 'select(.violations | length > 0)'
```

3. **Review violating code:**
```bash
AGENT_ID=$(tail -1 governance/judicial/evaluation/dgm_verdicts.jsonl | jq -r '.agent_id')
cat governance/research/dgm/agents/${AGENT_ID}.json | jq -r '.code'
```

4. **Escalate:**
- Notify security team
- File incident report
- Review constitutional policy
- Update safety constraints if needed

5. **Prevent recurrence:**
```bash
# Add pattern to constitutional policy
vim governance/legislative/self_modification_policy.yaml
# Add to forbidden patterns list
```

---

### Performance Regression

**Severity:** 🟡 **MEDIUM**

**Symptoms:**
- Alert: "DGM Performance Regression"
- Performance drops >5%

**Response:**
1. **Check auto-rollback occurred:**
```bash
tail -10 governance/judicial/evaluation/dgm_verdicts.jsonl | \
  jq 'select(.verdict == "REJECT" and .actions[] | contains("ROLLBACK"))'
```

2. **Verify rollback was successful:**
```bash
# Check current best performance
curl -s http://localhost:9090/api/v1/query?query='dgm_agent_performance{benchmark="swe-bench-lite"}' | \
  jq -r '.data.result[0].value[1]'
```

3. **If performance not recovered:**
```bash
# Manually revert to last known good agent
LAST_GOOD=$(jq -s 'map(select(.verdict == "APPROVE")) | last | .agent_id' \
  governance/judicial/evaluation/dgm_verdicts.jsonl)

echo "Reverting to agent: $LAST_GOOD"
```

4. **Investigate root cause:**
- Review recent mutations
- Check if benchmark changed
- Validate foundation model responses

---

### Circuit Breaker Triggered

**Severity:** 🟠 **HIGH**

**Symptoms:**
- Evolution stopped automatically
- `dgm_consecutive_failures` = 5
- Log message: "Circuit breaker triggered"

**Response:**
1. **Review failure pattern:**
```bash
tail -50 governance/judicial/evaluation/dgm_verdicts.jsonl | \
  jq 'select(.verdict == "REJECT") | {agent_id, reason}'
```

2. **Check for systemic issues:**
```bash
# Are all rejections the same reason?
tail -50 governance/judicial/evaluation/dgm_verdicts.jsonl | \
  jq -r 'select(.verdict == "REJECT") | .reason' | \
  sort | uniq -c
```

3. **Possible causes:**
- Foundation model producing unsafe code
- Benchmark infrastructure issues
- Constitutional policy too restrictive
- Bug in verdict validator

4. **Reset and retry:**
```bash
# After fixing root cause
python governance/executive/orchestration/dgm_orchestrator.py
```

---

### Low ECE Warnings

**Severity:** 🟡 **MEDIUM**

**Symptoms:**
- Alert: "DGM ECE Below Threshold"
- `dgm_ece_estimate` < 0.7

**Response:**
1. **Review flagged agents:**
```bash
jq 'select(.ece_estimate < 0.7)' governance/judicial/evaluation/dgm_verdicts.jsonl
```

2. **Human review required:**
- Examine agent code manually
- Run additional validation tests
- Approve or reject manually

3. **Adjust threshold if needed:**
```yaml
# In dgm_config.yaml
safety:
  human_oversight_threshold: 0.6  # Lower if too many false positives
```

---

### Archive Quality Degradation

**Severity:** 🟡 **MEDIUM**

**Symptoms:**
- `dgm_archive_diversity` < 0.2
- All recent agents look similar

**Response:**
1. **Check diversity score:**
```bash
curl -s http://localhost:9090/api/v1/query?query=dgm_archive_diversity | \
  jq -r '.data.result[0].value[1]'
```

2. **Analyze archive:**
```bash
python3 << 'EOF'
from governance.research.dgm.dgm_governance_adapter import DGMGovernanceAdapter
adapter = DGMGovernanceAdapter()
agents = adapter.load_archive()

# Check approach diversity
approaches = set()
for a in agents:
    # Simplified - would need better diversity metric
    approaches.add(len(a['code']))

print(f"Archive size: {len(agents)}")
print(f"Unique sizes: {len(approaches)}")
EOF
```

3. **Increase diversity pressure:**
```yaml
# In dgm_config.yaml
archive:
  diversity_weight: 0.5  # Increase from 0.3
```

4. **Prune low-performers:**
```bash
python3 << 'EOF'
from governance.research.dgm.dgm_governance_adapter import DGMGovernanceAdapter
adapter = DGMGovernanceAdapter()
agents = adapter.load_archive()

# Remove bottom 10%
threshold = sorted([a['metadata']['performance'] for a in agents])[len(agents)//10]
print(f"Pruning agents below {threshold:.3f} performance")
EOF
```

---

## 🔧 **Configuration Changes**

### Update Safety Thresholds

```bash
# Edit config
vim governance/research/dgm/config/dgm_config.yaml

# Key settings:
# - human_oversight_threshold: 0.7
# - circuit_breaker_failures: 5
# - max_archive_size: 1000

# Validate
python -c "
import yaml
with open('governance/research/dgm/config/dgm_config.yaml') as f:
    config = yaml.safe_load(f)
    print('✓ Config valid')
"

# Restart if needed
```

### Update Constitutional Policy

```bash
# Edit policy
vim governance/legislative/self_modification_policy.yaml

# Add new constraints to:
# - constraints.execution[]
# - guardrails.evolution_limits{}

# Validate
python -c "
import yaml
with open('governance/legislative/self_modification_policy.yaml') as f:
    policy = yaml.safe_load(f)
    mandatory = [c for c in policy['constraints']['execution'] if c['enforcement'] == 'MANDATORY']
    print(f'✓ {len(mandatory)} mandatory constraints')
"
```

---

## 📊 **Metrics Reference**

### Key Metrics to Monitor

| Metric | Healthy Range | Alert If |
|--------|---------------|----------|
| `dgm_generations_total` | Incrementing | Stalled >1hr |
| `dgm_safety_violations_total` | 0 | > 0 |
| Approval rate | 30-70% | < 20% or > 90% |
| `dgm_agent_performance` | Increasing | Decreasing |
| `dgm_consecutive_failures` | 0-2 | ≥ 3 |
| `dgm_archive_diversity` | > 0.2 | < 0.15 |

### Prometheus Queries

**Evolution Velocity:**
```promql
rate(dgm_generations_total[1h])
```

**Approval Success Rate:**
```promql
rate(dgm_verdicts_total{verdict_type=~"APPROVE|CANARY_DEPLOY"}[5m])
/
rate(dgm_verdicts_total[5m])
```

**Performance Trend:**
```promql
dgm_agent_performance{benchmark="swe-bench-lite"}
```

**Safety Status:**
```promql
dgm_safety_violations_total > 0
```

---

## 🧪 **Testing & Validation**

### Run Integration Tests
```bash
# Full test suite
pytest tests/test_dgm_integration.py -v

# Specific test
pytest tests/test_dgm_integration.py::TestDGMGovernanceIntegration::test_constitutional_compliance_safe_code -v

# With coverage
pytest tests/test_dgm_integration.py --cov=governance/research/dgm --cov-report=html
```

### Manual Validation
```bash
# Test verdict validator
python governance/judicial/evaluation/dgm_verdict_validator.py

# Test orchestrator (5 generations)
python governance/executive/orchestration/dgm_orchestrator.py

# Test full experiment
python governance/research/dgm/experiments/experiment_runner.py \
  governance/research/dgm/experiments/pilot_experiment.yaml
```

---

## 📈 **Performance Baselines**

Based on [arXiv:2505.22954](https://arxiv.org/abs/2505.22954):

| Benchmark | Initial | 10 Gen | 50 Gen | Paper |
|-----------|---------|--------|--------|-------|
| SWE-bench | 20% | 30% | 40% | 50% |
| Polyglot | 14% | 20% | 25% | 30% |

**If performance plateaus:**
1. Check diversity (may be stuck in local optimum)
2. Increase mutation rate
3. Introduce different foundation model
4. Adjust selection pressure

---

## 🔄 **Routine Maintenance**

### Weekly (Automated)
- ✓ Evolution runs Sunday 3am
- ✓ Grafana dashboard review
- ✓ Verdict log analysis

### Monthly (Manual)
- Review constitutional policy effectiveness
- Analyze archive quality trends
- Update safety thresholds if needed
- Review experiment results
- Prune archive if > 800 agents

### Quarterly (Manual)
- Full security audit of generated agents
- Benchmark recalibration
- Foundation model evaluation
- Policy revision based on learnings

---

## 🆘 **Emergency Contacts**

- **On-Call:** Governance Team
- **Escalation:** Security Team
- **Slack:** #governance-alerts
- **PagerDuty:** governance-dgm

---

## 📚 **Additional Resources**

- **PRD:** `docs/prd/DGM_INTEGRATION_PRD.md`
- **README:** `governance/research/dgm/README.md`
- **Policy:** `governance/legislative/self_modification_policy.yaml`
- **Paper:** https://arxiv.org/abs/2505.22954
- **Upstream:** https://github.com/jennyzzt/dgm

---

## 🔍 **Troubleshooting**

### Evolution Not Starting

**Symptoms:** No new generations appearing

**Checks:**
1. Docker running? `docker ps`
2. API keys set? `echo $ANTHROPIC_API_KEY`
3. Config valid? `python -c "import yaml; yaml.safe_load(open('governance/research/dgm/config/dgm_config.yaml'))"`
4. Permissions? `ls -la governance/research/dgm/agents/`

---

### Foundation Model Errors

**Symptoms:** Repeated API errors in logs

**Checks:**
1. Rate limits? Check Anthropic/OpenAI dashboards
2. API key valid? `curl -H "x-api-key: $ANTHROPIC_API_KEY" https://api.anthropic.com/v1/messages`
3. Model available? Verify model name in config
4. Quota remaining? Check billing

**Temporary Fix:**
```yaml
# Switch to backup model
evolution:
  foundation_model: "gpt-4"  # From claude-sonnet-4
```

---

### Canary Deployment Issues

**Symptoms:** Approved agents not deploying

**Checks:**
1. Canary system running? `ps aux | grep gov_canary`
2. Traffic routing configured?
3. Rollback threshold correct?

**Manual Deployment:**
```bash
# Get last approved agent
AGENT_ID=$(jq -r 'select(.verdict == "APPROVE") | .agent_id' governance/judicial/evaluation/dgm_verdicts.jsonl | tail -1)

# Deploy manually via canary system
python scripts/gov_canary_decider.py --agent-id $AGENT_ID --traffic 0.05
```

---

## 📋 **Pre-Flight Checklist**

Before starting evolution run:

- [ ] Docker running and configured
- [ ] API keys set (`ANTHROPIC_API_KEY`)
- [ ] Grafana dashboard accessible
- [ ] Prometheus scraping metrics
- [ ] Constitutional policy validated
- [ ] Disk space > 10GB free
- [ ] Backup of current archive
- [ ] Alert channels tested (Slack)

---

## 🎓 **Training Materials**

**New Operators:**
1. Read `governance/research/dgm/README.md`
2. Review PRD `docs/prd/DGM_INTEGRATION_PRD.md`
3. Run tests: `pytest tests/test_dgm_integration.py`
4. Practice with quickstart: `./scripts/dgm_quickstart.sh`
5. Shadow experienced operator during evolution run

**Key Concepts:**
- **ECE**: Epistemic Confidence Estimate (like confidence score)
- **Verdict**: Judicial decision on agent modification
- **Archive**: Collection of evolved agents
- **Generation**: One cycle of evolution (select, mutate, evaluate)
- **Circuit Breaker**: Safety mechanism to stop on repeated failures

---

**Last Updated:** 2025-10-15  
**Version:** 1.0.0  
**Next Review:** 2025-11-15

