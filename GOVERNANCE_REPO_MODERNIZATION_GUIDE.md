# Universal AI Tools: Governance Modernization Guide

## Overview

This guide helps you audit, clean, and modernize the `universal-ai-tools` repository to align with the Athena governance stack we just built in your GitHub workspace.

## 🔍 Step 1: Run the Audit

From the `universal-ai-tools` repo root:

```bash
# Copy the audit script
cp /path/to/GitHub/scripts/audit_governance_readiness.sh ./

# Run the audit
./audit_governance_readiness.sh

# Review results
cat _governance_audit/REPORT.md
cat _governance_audit/governance_gaps.txt
```

### What the Audit Finds

- **Directory structure** and file depth analysis
- **Size by directory** to identify heavy areas
- **All Docker/compose files** scattered across repo
- **Dependency snapshots** (Python + JS)
- **Secret-like patterns** that need env vars
- **Stale files** (>180 days untouched)
- **Governance gaps** - what's missing vs Athena stack
- **Test coverage** signals

## 🎯 Target End-State Architecture

### Recommended Repo Layout

```
/universal-ai-tools/
├── apps/                       # Runnable applications/UI
│   ├── web/                    # Web frontend
│   ├── desktop/                # Desktop app
│   └── mobile/                 # Mobile app (if any)
├── services/                   # Microservices
│   ├── api/                    # Main API service
│   ├── workers/                # Background workers
│   └── realtime/               # WebSocket/real-time service
├── packages/                   # Shared libraries/SDK
│   ├── core/                   # Core business logic
│   ├── utils/                  # Utilities
│   └── types/                  # Shared types
├── governance/                 # Athena governance system
│   ├── policy/                 # Policy YAML files
│   │   ├── governance_policy.yaml
│   │   ├── god_judge_verdict_mapping.yaml
│   │   └── bundles/           # Environment-specific policies
│   ├── legislative/            # Policy compilation
│   ├── judicial/               # ECE gates, verdict generation
│   ├── executive/              # Verdict execution
│   │   ├── verdict_actions.py
│   │   ├── playbook_executor.py
│   │   └── playbooks/         # Auto-remediation playbooks
│   └── observability/          # Metrics exporter
├── infra/                      # Infrastructure as code
│   ├── docker/                 # Dockerfiles (one per service)
│   │   ├── Dockerfile.api
│   │   ├── Dockerfile.worker
│   │   └── Dockerfile.frontend
│   └── compose/                # Docker compose files
│       └── docker-compose.athena-governance.yml
├── monitoring/                 # Observability configs
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── alerts.yml
│   └── grafana/
│       ├── dashboards/
│       └── provisioning/
├── scripts/                    # Operational scripts
│   ├── gov_*.py               # Governance scripts
│   ├── gov_*.sh               # Deployment scripts
│   └── audit_*.sh             # Audit/maintenance scripts
├── .github/
│   └── workflows/              # CI/CD (governance workflows only)
│       ├── governance-deploy.yml
│       ├── governance-canary-watch.yml
│       ├── governance-adaptive-learning.yml
│       └── governance-window-tuning.yml
├── state/                      # Runtime state (gitignored)
├── logs/                       # Audit logs (gitignored)
└── archive/                    # Quarantined legacy code
    └── README.md               # Why things are archived
```

## 🧹 Cleanup Strategy

### A. Docker & Compose Consolidation

#### Find Duplicates
```bash
cat _governance_audit/dockerfiles.rg  # List all Dockerfiles
cat _governance_audit/compose_files.rg  # List all compose files
```

#### Consolidation Plan
1. **Move** all Dockerfiles to `infra/docker/`
2. **Name** consistently: `Dockerfile.{service-name}`
3. **Merge** all compose files into `infra/compose/docker-compose.athena-governance.yml`
4. **Delete** old compose files after merge
5. **Update** references in scripts and CI

```bash
# Example consolidation
mkdir -p infra/docker infra/compose
mv docker/Dockerfile.api infra/docker/
mv Dockerfile infra/docker/Dockerfile.main
# ... merge compose files manually ...
```

### B. Configuration Deduplication

#### Identify Duplicates
```bash
# Find duplicate configs
cat _governance_audit/config_hits.rg | grep -i "prometheus\|grafana\|env"
```

#### Consolidation Rules
- **Prometheus**: Single `monitoring/prometheus/prometheus.yml`
- **Grafana**: Dashboards in `monitoring/grafana/dashboards/`
- **Environment vars**: `.env.example` only, actual values from secrets/env

### C. Delete Stale Code

#### Review Candidates
```bash
# Files not touched in 180+ days
cat _governance_audit/stale_files.txt
```

#### Deletion Criteria (ALL must be true)
- [ ] Last modified > 180 days ago
- [ ] Not referenced in any Makefile, compose file, or README
- [ ] Not imported by active services
- [ ] Not part of governance system

#### Safe Deletion Process
```bash
# Don't delete - move to archive with context
mkdir -p archive/legacy-$(date +%F)
for file in $(cat _governance_audit/stale_files.txt); do
  if [ -f "$file" ]; then
    mkdir -p "archive/legacy-$(date +%F)/$(dirname $file)"
    mv "$file" "archive/legacy-$(date +%F)/$file"
  fi
done

# Document why
echo "Archived on $(date): Files untouched for 180+ days" > archive/legacy-$(date +%F)/README.md
```

### D. Dependency Cleanup

#### Python
```bash
# Review current dependencies
cat _governance_audit/requirements.lock

# Modernize to pyproject.toml
cat > pyproject.toml <<'EOF'
[project]
name = "universal-ai-tools"
version = "2.0.0"
requires-python = ">=3.11"

dependencies = [
    "fastapi>=0.104.0",
    "pydantic>=2.0.0",
    "prometheus-client>=0.19.0",
    "pyyaml>=6.0.1",
    "requests>=2.31.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
EOF
```

#### JavaScript/TypeScript (if present)
```bash
# Migrate to pnpm
pnpm import  # Convert package-lock.json
pnpm prune --prod  # Remove unused deps
```

### E. Secrets & Environment Hygiene

#### Review Secret Patterns
```bash
# Find hardcoded secrets
cat _governance_audit/secret_like_hits.rg | grep -v ".env.example" | grep -v "test"
```

#### Fix Hardcoded Secrets
```bash
# Replace with environment variables
# Example: API_KEY="hardcoded" → API_KEY=os.getenv("API_KEY")

# Create .env.example template
cat > .env.example <<'EOF'
# Governance
SLACK_WEBHOOK_URL=
GRAFANA_URL=http://localhost:3001
GRAFANA_TOKEN=
PROM_URL=http://localhost:9090

# Database
POSTGRES_HOST=athena-postgres
POSTGRES_PASSWORD=

# API Keys (never commit actual values)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
EOF
```

#### Delete Old .env Files
```bash
# Remove all .env files from git (keep only .env.example)
git rm --cached .env* || true
echo ".env" >> .gitignore
echo ".env.*" >> .gitignore
echo "!.env.example" >> .gitignore
```

### F. CI/CD Consolidation

#### Keep Only Governance Workflows
```bash
cd .github/workflows/

# Keep these
ls governance-*.yml

# Archive old workflows
mkdir -p ../../archive/old-ci-workflows-$(date +%F)
for f in *.yml; do
  if [[ ! "$f" =~ ^governance- ]]; then
    mv "$f" "../../archive/old-ci-workflows-$(date +%F)/"
  fi
done
```

## 🔧 Modernization Diffs

### Docker Standardization

#### Before (Scattered)
```
./Dockerfile
./docker/Dockerfile.api
./services/worker/Dockerfile
./Dockerfile.old
```

#### After (Consolidated)
```
./infra/docker/Dockerfile.api
./infra/docker/Dockerfile.worker
./infra/docker/Dockerfile.frontend
```

### Compose Consolidation

#### Before (Multiple Files)
```
docker-compose.yml
docker-compose.dev.yml
docker-compose.prod.yml
docker-compose.monitoring.yml
```

#### After (Single Unified File)
```
./infra/compose/docker-compose.athena-governance.yml
```

### Governance Integration

#### Before (Ad-hoc)
```
scripts/deploy.sh
scripts/check-health.sh
.github/workflows/deploy.yml
```

#### After (Governance-Driven)
```
scripts/gov_deploy.sh
scripts/gov_predeploy_gate.py
scripts/gov_canary_decider.py
.github/workflows/governance-deploy.yml
.github/workflows/governance-canary-watch.yml
```

## 📋 Checklist: Repository Modernization

### Phase 1: Audit & Inventory
- [ ] Run `audit_governance_readiness.sh`
- [ ] Review `_governance_audit/REPORT.md`
- [ ] Identify stale files for archival
- [ ] Find duplicate Docker/compose configurations

### Phase 2: Structural Cleanup
- [ ] Create `infra/docker/` and `infra/compose/` directories
- [ ] Move all Dockerfiles to `infra/docker/`
- [ ] Consolidate compose files to single unified stack
- [ ] Archive stale files (>180 days) to `archive/`
- [ ] Update all references in scripts and CI

### Phase 3: Governance Integration
- [ ] Copy governance components from GitHub workspace
- [ ] Verify all components in `governance_gaps.txt` are present
- [ ] Update paths in workflows and scripts
- [ ] Test governance deployment end-to-end

### Phase 4: Dependency Modernization
- [ ] Migrate to `pyproject.toml` (Python)
- [ ] Migrate to `pnpm` (JavaScript/TypeScript)
- [ ] Pin all dependencies with lock files
- [ ] Remove unused dependencies

### Phase 5: Security Hardening
- [ ] Remove all hardcoded secrets
- [ ] Create `.env.example` template
- [ ] Add secrets to CI/CD via GitHub secrets
- [ ] Verify no secrets in git history

### Phase 6: CI/CD Cleanup
- [ ] Keep only governance-*.yml workflows
- [ ] Archive old CI workflows
- [ ] Update deployment scripts
- [ ] Test complete CI/CD pipeline

### Phase 7: Documentation
- [ ] Update README with new structure
- [ ] Create architecture diagram
- [ ] Document environment promotion flow
- [ ] Add runbooks for operations

## 🚀 Migration Commands

### Quick Migration Script
```bash
#!/usr/bin/env bash
set -euo pipefail

echo "🔄 Migrating to governance-aligned structure..."

# 1. Create new structure
mkdir -p infra/docker infra/compose
mkdir -p governance/policy/bundles
mkdir -p governance/executive/playbooks
mkdir -p archive/pre-governance-$(date +%F)

# 2. Move Docker files
find . -maxdepth 3 -name "Dockerfile*" ! -path "./infra/*" ! -path "./.git/*" \
  -exec mv {} infra/docker/ \;

# 3. Backup old compose files
find . -name "*compose*.yml" ! -path "./infra/*" ! -path "./.git/*" \
  -exec cp {} archive/pre-governance-$(date +%F)/ \;

# 4. Copy governance components from GitHub workspace
GITHUB_WORKSPACE="/Users/christianmerrill/Documents/GitHub"

# Core governance files
cp "$GITHUB_WORKSPACE/docker-compose.athena-governance.yml" infra/compose/
cp "$GITHUB_WORKSPACE/policy/governance_policy.yaml" governance/policy/
cp "$GITHUB_WORKSPACE/policy/god_judge_verdict_mapping.yaml" governance/policy/
cp -r "$GITHUB_WORKSPACE/policy/bundles/" governance/policy/

# Scripts
cp "$GITHUB_WORKSPACE"/scripts/gov_*.py scripts/
cp "$GITHUB_WORKSPACE"/scripts/gov_*.sh scripts/
cp "$GITHUB_WORKSPACE"/scripts/rotate_audit.sh scripts/
cp "$GITHUB_WORKSPACE"/scripts/devil_advocate_probe.py scripts/

# Executive layer
cp "$GITHUB_WORKSPACE/exec/verdict_actions.py" governance/executive/
cp "$GITHUB_WORKSPACE/exec/playbook_executor.py" governance/executive/
cp -r "$GITHUB_WORKSPACE/exec/playbooks/" governance/executive/

# CI/CD
cp "$GITHUB_WORKSPACE"/.github/workflows/governance-*.yml .github/workflows/

# Monitoring
cp -r "$GITHUB_WORKSPACE/monitoring/" ./

# Makefile
cp "$GITHUB_WORKSPACE/Makefile" ./Makefile.governance
echo "# Include governance commands" >> Makefile
cat Makefile.governance >> Makefile

echo "✅ Governance components migrated"
echo "📋 Review changes and commit when ready"
```

## 📊 Alignment Checklist

### Required Governance Components

#### Docker & Compose
- [ ] `infra/compose/docker-compose.athena-governance.yml` - Unified stack
- [ ] `infra/docker/Dockerfile.{service}` - One per service

#### Policy & Governance
- [ ] `governance/policy/governance_policy.yaml` - Main policy
- [ ] `governance/policy/god_judge_verdict_mapping.yaml` - Verdict mapping
- [ ] `governance/policy/bundles/dev.yaml` - Dev environment policy
- [ ] `governance/policy/bundles/staging.yaml` - Staging policy
- [ ] `governance/policy/bundles/prod.yaml` - Production policy

#### Executive Layer
- [ ] `governance/executive/verdict_actions.py` - Verdict execution
- [ ] `governance/executive/playbook_executor.py` - Auto-remediation
- [ ] `governance/executive/playbooks/*.yaml` - Remediation playbooks (5 total)

#### Scripts
- [ ] `scripts/gov_predeploy_gate.py` - Pre-deploy health checks
- [ ] `scripts/gov_deploy.sh` - Deployment orchestration
- [ ] `scripts/gov_rollback.sh` - Emergency rollback
- [ ] `scripts/gov_canary_decider.py` - Auto-promote/rollback
- [ ] `scripts/gov_adaptive_thresholds.py` - Threshold learning
- [ ] `scripts/gov_window_tuner.py` - Window optimization
- [ ] `scripts/gov_predictor.py` - Predictive forecasting
- [ ] `scripts/gov_incident_reporter.py` - Incident automation
- [ ] `scripts/gov_promotion_chain.py` - Multi-env promotions
- [ ] `scripts/gov_slack_bot.py` - ChatOps interface
- [ ] `scripts/gov_notify_slack.sh` - Slack notifications
- [ ] `scripts/gov_notify_grafana.sh` - Grafana annotations
- [ ] `scripts/rotate_audit.sh` - Log rotation
- [ ] `scripts/devil_advocate_probe.py` - Synthetic testing

#### Monitoring
- [ ] `monitoring/prometheus/prometheus.yml` - Scrape configs
- [ ] `monitoring/prometheus/alerts.yml` - Alert rules
- [ ] `monitoring/grafana/dashboards/governance-overview.json`
- [ ] `monitoring/grafana/dashboards/governance-predictive.json`

#### CI/CD
- [ ] `.github/workflows/governance-deploy.yml`
- [ ] `.github/workflows/governance-canary-watch.yml`
- [ ] `.github/workflows/governance-adaptive-learning.yml`
- [ ] `.github/workflows/governance-window-tuning.yml`
- [ ] `.github/workflows/governance-nightly-probe.yml`
- [ ] `.github/workflows/governance-predictive-analysis.yml`

#### Build System
- [ ] `Makefile` - All governance make targets (15+)

## 🔄 Migration Steps

### 1. Backup Current State
```bash
# Create backup branch
git checkout -b pre-governance-backup
git add -A
git commit -m "Backup before governance modernization"
git push origin pre-governance-backup

# Return to main
git checkout main
git checkout -b governance-modernization
```

### 2. Run Audit
```bash
./scripts/audit_governance_readiness.sh
```

### 3. Review Audit Results
```bash
# Check what's missing
cat _governance_audit/governance_gaps.txt

# Identify large directories to clean
head -20 _governance_audit/size_by_dir.txt

# Review stale files
wc -l _governance_audit/stale_files.txt
```

### 4. Archive Stale Code
```bash
# Move stale files to archive
while read file; do
  if [ -f "$file" ]; then
    mkdir -p "archive/stale-$(date +%F)/$(dirname $file)"
    git mv "$file" "archive/stale-$(date +%F)/$file" || true
  fi
done < _governance_audit/stale_files.txt
```

### 5. Consolidate Infrastructure
```bash
# Move Dockerfiles
mkdir -p infra/docker
find . -maxdepth 2 -name "Dockerfile*" ! -path "./infra/*" -exec mv {} infra/docker/ \;

# Create compose directory
mkdir -p infra/compose
```

### 6. Copy Governance Components
```bash
# Copy from your GitHub workspace (where we built everything)
GITHUB_WS="/Users/christianmerrill/Documents/GitHub"

# Policies
cp -r "$GITHUB_WS/policy" governance/

# Executive layer
cp -r "$GITHUB_WS/exec/"* governance/executive/

# Scripts
cp "$GITHUB_WS/scripts/gov_"* scripts/
cp "$GITHUB_WS/scripts/rotate_audit.sh" scripts/
cp "$GITHUB_WS/scripts/devil_advocate_probe.py" scripts/
cp "$GITHUB_WS/scripts/audit_governance_readiness.sh" scripts/

# Monitoring
cp -r "$GITHUB_WS/monitoring" ./

# CI/CD
cp "$GITHUB_WS/.github/workflows/governance-"* .github/workflows/

# Docker compose
cp "$GITHUB_WS/docker-compose.athena-governance.yml" infra/compose/

# Makefile
cat "$GITHUB_WS/Makefile" >> Makefile

# Documentation
cp "$GITHUB_WS/GOVERNANCE_"*.md docs/governance/
cp "$GITHUB_WS/ATHENA_GOVERNANCE_DEPLOYMENT.md" docs/governance/
```

### 7. Update References
```bash
# Update compose file path in scripts
find scripts -name "gov_*.sh" -exec sed -i '' 's|docker-compose\.athena-governance\.yml|infra/compose/docker-compose.athena-governance.yml|g' {} \;

# Update Makefile paths
sed -i '' 's|docker-compose\.athena-governance\.yml|infra/compose/docker-compose.athena-governance.yml|g' Makefile
```

### 8. Clean Up Old CI/CD
```bash
# Archive non-governance workflows
mkdir -p archive/old-workflows-$(date +%F)
cd .github/workflows
for f in *.yml; do
  if [[ ! "$f" =~ ^governance- ]]; then
    git mv "$f" "../../archive/old-workflows-$(date +%F)/"
  fi
done
cd ../..
```

### 9. Test Everything
```bash
# Validate compose
docker compose -f infra/compose/docker-compose.athena-governance.yml config

# Test governance scripts
make governance-gate
make governance-playbooks-validate
python3 scripts/gov_promotion_chain.py --validate-chain

# Verify CI syntax
cd .github/workflows && for f in governance-*.yml; do yamllint "$f" || true; done
```

### 10. Commit & Document
```bash
# Commit changes
git add -A
git commit -m "feat: Modernize repo structure and integrate Athena governance

- Consolidate Docker/compose files to infra/
- Integrate complete governance system (predictive + adaptive + automated)
- Add multi-environment promotion chains (dev/staging/prod)
- Add auto-remediation playbooks for common failures
- Archive stale code (180+ days)
- Modernize dependencies (pyproject.toml)
- Clean up CI/CD (governance workflows only)

This brings the repo to governance maturity level 5 (Predictive Excellence)."

# Push for review
git push origin governance-modernization
```

## 🎯 Safety Rails (Don't Ship Without)

### Pre-Deployment Validation
```bash
# 1. All governance components present
python3 scripts/gov_promotion_chain.py --validate-chain

# 2. All playbooks valid
make governance-playbooks-validate

# 3. Compose file syntax valid
docker compose -f infra/compose/docker-compose.athena-governance.yml config

# 4. No hardcoded secrets
grep -r "api_key\|secret\|password" --include="*.py" --include="*.yml" . | grep -v ".env.example" | wc -l
# Should be 0

# 5. CI workflows valid
yamllint .github/workflows/*.yml
```

### Post-Migration Smoke Test
```bash
# Deploy stack
make governance-up

# Health checks
make governance-gate

# Predictive test
make governance-predict

# Playbook test
make governance-playbooks-list
```

## 📈 Expected Outcomes

### Repository Metrics
- **50% reduction** in file count (archived stale code)
- **70% reduction** in Docker/compose duplication
- **100% governance coverage** across environments
- **Zero hardcoded secrets**

### Operational Improvements
- **Single source of truth** for infrastructure (infra/compose/)
- **Clear separation** between apps, services, governance
- **Consistent patterns** across all services
- **Modern tooling** (pyproject.toml, pnpm, etc.)

---

## 🏆 Modern Repository Structure

After modernization, your `universal-ai-tools` repo will be:
- **Clean**: No duplicates, stale code archived
- **Governed**: Complete Athena governance integration
- **Modern**: Up-to-date dependencies and tooling
- **Secure**: No hardcoded secrets, proper RBAC
- **Observable**: Full Prometheus + Grafana + Slack integration

This represents **enterprise-grade repository hygiene** aligned with your world-class governance system! 🚀📦✨


