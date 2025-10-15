# GitHub Actions Workflows

## Active Workflows

### ui-golden.yml
**Trigger**: Pull Requests to main
**Purpose**: UI tests + golden screenshot diffing
**Runs**: On every PR to ensure no visual regressions
**Artifacts**: Screenshots, diffs, test results

### qa-sweep.yml
**Trigger**: Push to main
**Purpose**: Full QA sweep validation
**Runs**: After merge to main
**Artifacts**: Complete QA report

### services-health.yml
**Trigger**: Every 6 hours (schedule)
**Purpose**: Monitor service health
**Runs**: Creates issues if services are down
**Artifacts**: Health check logs

### ci.yml
**Trigger**: Push/PR
**Purpose**: General CI checks
**Runs**: Existing CI pipeline

### broker-ci.yml
**Trigger**: Push/PR
**Purpose**: Broker service CI
**Runs**: Existing broker tests

## Status Badges

Add to README.md:

```markdown
![UI Golden Tests](https://github.com/Cmerrill1713/athena-trm-backup/workflows/ui-golden/badge.svg)
![QA Sweep](https://github.com/Cmerrill1713/athena-trm-backup/workflows/qa-sweep/badge.svg)
![Services Health](https://github.com/Cmerrill1713/athena-trm-backup/workflows/services-health/badge.svg)
```

## Local Testing

Test workflows locally:
```bash
# Simulate PR check
cd ~/Documents/GitHub/NeuroForgeApp
GOLDEN_TOLERANCE=0.003 make golden-ci

# Simulate main push
make qa
```

## Branch Protection

Recommended settings for main branch:
- ✅ Require pull request reviews
- ✅ Require status checks to pass: `ui-golden`
- ✅ Require branches to be up to date
- ✅ Include administrators
