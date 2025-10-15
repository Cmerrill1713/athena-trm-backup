# 🧪 Safe Tinkering Guide

**How to experiment without breaking production**

---

## 🛡️ The "Green" State

You've tagged a known-good build: **v0.9.1-green**

This is your **rollback point** - if anything breaks, you can always return here.

---

## ✅ Pre-Tinkering Checklist

### **Before Making Changes**

```bash
# 1. Verify current state is green
make green
make validate-green

# 2. Create a branch
git checkout -b experiment/your-feature-name

# 3. Commit current state
git add -A
git commit -m "Checkpoint before tinkering"
```

---

### **Safe Tinkering Zones**

| Area | Safe? | Notes |
|------|-------|-------|
| `config/routing_policy.json` | ✅ | Change tasks/providers freely |
| `scripts/*` | ✅ | Add new scripts anytime |
| `fastvlm/fastvlm_server.py` | ✅ | Behind watchdog (auto-recovers) |
| `monitoring/alerts/*.yml` | ✅ | Just reload Prometheus |
| Database queries | ✅ | Read-only queries always safe |
| `src/core/routing/*` | ⚠️ | Test with canary first |
| Swift UI code | ⚠️ | Test locally before deploying |
| Database schema | 🚨 | Always backup first |
| Production cron jobs | 🚨 | Test manually first |

---

## 🧪 Safe Experimentation Patterns

### **Pattern 1: Feature Flags**

```python
# Add to config or env
ENABLE_EXPERIMENTAL_FEATURE = os.environ.get("ENABLE_X", "false") == "true"

if ENABLE_EXPERIMENTAL_FEATURE:
    # Your new code
    result = new_fancy_algorithm()
else:
    # Proven path
    result = old_reliable_way()
```

**Test**:
```bash
ENABLE_X=true make test-your-feature
```

---

### **Pattern 2: Canary Testing**

```bash
# 1. Deploy as canary at 10%
export CANARY_MODEL="your-experimental-model"
make canary-10
source /tmp/canary.env

# 2. Monitor for issues
make canary-eval

# 3. Rollback if needed
make canary-rollback
source /tmp/canary.env
```

---

### **Pattern 3: Database Changes**

```bash
# 1. Backup first
make pg-backup

# 2. Test on copy
createdb athena_test -T athena_db
export DATABASE_URL="postgresql://localhost:5433/athena_test"
psql "$DATABASE_URL" -f your_migration.sql

# 3. If good, apply to prod
export DATABASE_URL="postgresql://localhost:5433/athena_db"
psql "$DATABASE_URL" -f your_migration.sql
```

---

### **Pattern 4: Routing Changes**

```bash
# 1. Update routing_policy.json
vim config/routing_policy.json

# 2. Test with one request
curl -X POST http://localhost:8014/api/route \
  -H "Content-Type: application/json" \
  -d '{"input": "test", "meta": {"task": "your.new.task"}}'

# 3. If good, reload services
# (Most services hot-reload config automatically)
```

---

## 🚨 Rollback Procedures

### **Quick Rollback** (< 30 seconds)

```bash
# 1. Return to green tag
git checkout v0.9.1-green

# 2. Restart services
make fastvlm-down
make fastvlm-server &

# 3. Verify
make green
```

---

### **Canary Rollback** (< 5 seconds)

```bash
make canary-rollback
source /tmp/canary.env
```

---

### **Database Rollback**

```bash
# Restore from backup
psql "$DATABASE_URL" < backups/athena_db_YYYYMMDD.sql
```

---

## 🧪 What You Can Safely Tinker With

### **1. Model-Agnostic Routing** ✅

Edit `config/routing_policy.json`:
- Add new task types
- Change provider endpoints
- Adjust latency budgets
- Add fallback rules

**No restart needed** (hot-reloaded)

---

### **2. Learned Patterns** ✅

Add to Weaviate:
```bash
# Add pattern via Python
python3 -c "
import requests
requests.post('http://localhost:8090/v1/objects', json={
    'class': 'LearnedPattern',
    'properties': {
        'name': 'your_pattern',
        'tags': ['tag1', 'tag2'],
        'snippet': 'code snippet',
        'notes': 'what it does',
        'task_type': 'your_task',
        'success_rate': 0.85
    }
})
"
```

---

### **3. Prometheus Alerts** ✅

Edit `monitoring/alerts/*.yml`, then:
```bash
# Reload Prometheus
curl -X POST http://localhost:9090/-/reload
# or
docker restart prometheus
```

---

### **4. Grafana Dashboards** ✅

Add panels freely - dashboards are stateless

---

### **5. New Vision Tasks** ✅

Add to `scripts/athena_vision.py` or create new helpers:
```bash
# New task-specific helper
make vision-NEWTASK:
	@python3 scripts/athena_vision.py "$(IMG)" "Your custom prompt"
```

---

## 🔒 What Requires Extra Care

### **1. Schema Changes** 🚨

**Always**:
```bash
# Backup
make pg-backup

# Test migration
psql "$DATABASE_URL" -f migration.sql

# Rollback plan ready
```

---

### **2. Cron Jobs** 🚨

**Test manually first**:
```bash
# Don't add to cron until tested
make your-new-command

# If good, then add
bash scripts/setup_your_cron.sh
```

---

### **3. Core Routing Logic** 🚨

**Use canary**:
```bash
# Test with canary first
export CANARY_MODEL="experimental"
make canary-10
# Monitor for 24h
make canary-eval
```

---

## 📊 Validation Commands

### **Quick** (2 seconds)
```bash
make green
```

### **Medium** (90 seconds)
```bash
make daily-ops
```

### **Full** (2 minutes)
```bash
make validate-green
make e2e-sweep
```

---

## 🎯 Safe Tinkering Workflow

### **Standard Flow**

```bash
# 1. Branch
git checkout -b experiment/new-feature

# 2. Make changes
vim your_file.py

# 3. Test locally
make your-test-command

# 4. Commit
git add -A
git commit -m "Add new feature"

# 5. Validate
make green
make e2e-sweep

# 6. If good, merge
git checkout main
git merge experiment/new-feature
git push

# 7. If bad, rollback
git checkout main
# Branch abandoned
```

---

### **Canary Flow** (Production Testing)

```bash
# 1. Deploy experimental model as canary
make canary-10 CANARY_MODEL=experimental
source /tmp/canary.env

# 2. Monitor (6-48 hours)
make canary-eval       # Every few hours
make canary-check      # Traffic split

# 3. Decision
make canary-auto-promote   # If winning
# or
make canary-rollback       # If losing
source /tmp/canary.env
```

---

## 🎨 Example Experiments

### **Experiment 1: New Vision Task Type**

```bash
# Add to routing_policy.json
"vision.whiteboard": {
  "provider": "llm_router",
  "modality": "vision",
  "task_type": "whiteboard"
}

# Test
make vision IMG=whiteboard.png PROMPT="Extract handwriting"

# If good, commit
git add config/routing_policy.json
git commit -m "Add whiteboard vision task"
```

---

### **Experiment 2: Faster Model for Smalltalk**

```bash
# Deploy as canary
make canary-10 CANARY_MODEL=fast-model-0.5b
source /tmp/canary.env

# Generate smalltalk traffic
for i in {1..100}; do
  # Send to chat endpoint with task=chat.smalltalk
  sleep 2
done

# Check if faster + equal quality
make canary-eval
```

---

### **Experiment 3: New Learned Pattern**

```bash
# Add pattern
python3 scripts/add_learned_pattern.py \
  --name "your_pattern" \
  --tags "tag1,tag2" \
  --snippet "code snippet" \
  --notes "what it does"

# Query it
curl -X POST http://localhost:8090/v1/graphql \
  -d '{"query": "{ Get { LearnedPattern(where: {path: [\"name\"], operator: Equal, valueString: \"your_pattern\"}) { name snippet } } }"}'
```

---

## 🚨 Emergency Procedures

### **System Broken? Rollback Immediately**

```bash
# 1. Stop everything
make fastvlm-down
docker compose down

# 2. Return to green
git checkout v0.9.1-green

# 3. Restart
docker compose up -d
make fastvlm-server &

# 4. Verify
sleep 30
make green
```

**Recovery time**: < 2 minutes

---

### **Canary Gone Wrong?**

```bash
make canary-rollback
source /tmp/canary.env
```

**Recovery time**: < 5 seconds

---

### **Database Corrupted?**

```bash
# Latest backup
ls -lt backups/athena_db_*.sql | head -1

# Restore
dropdb athena_db
createdb athena_db
psql athena_db < backups/athena_db_YYYYMMDD.sql
```

---

## ✅ Validation After Tinkering

```bash
# Quick
make green

# Full
make validate-green
make e2e-sweep

# If all pass
git tag -a v0.9.2-experimental -m "Your changes"
git push --tags
```

---

## 🎯 Summary

**Safe zones**: Config, scripts, alerts, queries, new helpers
**Guarded zones**: Routing logic, models (use canary)
**Danger zones**: Schema, cron, core services (backup first)

**Always have rollback ready!**

```bash
# Before tinkering
git tag -a checkpoint-$(date +%Y%m%d) -m "Before experiment"

# After tinkering
make validate-green
```

**Happy tinkering!** 🧪✨
