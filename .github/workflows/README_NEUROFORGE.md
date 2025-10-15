# NeuroForge Platform Validation Workflow

File: `neuroforge_validation.yml`  
Purpose: Automated quality gates for platform integration  
Runs on: PRs, pushes to main/tier4-foundation, manual dispatch

---

## What It Does

Enforces 6 quality gates before merge:

1. **Encoding Safety** - Blocks non-ASCII in shell/config files
2. **Service Validation** - Checks scripts are executable and valid
3. **Swift Build & Tests** - Compiles app and runs unit tests
4. **Security Check** - Runs log redaction tests, checks for exposed secrets
5. **Athena Tools** - Validates tool manifest and scripts
6. **Documentation** - Checks required docs exist

---

## Gates in Detail

### Gate 1: Encoding Safety

**Blocks**:
- Emojis in .sh files
- Non-ASCII in .env, .yml, .yaml files
- Smart quotes and special characters

**Why**: Prevents terminal encoding corruption (the cmdand issue)

**Example Failure**:
```
FAIL: Non-ASCII detected in shell/config files:
scripts/deploy.sh:15:echo "Starting deployment..."
Use printf instead of echo with emojis
```

### Gate 2: Service Validation

**Checks**:
- Validation scripts are executable
- Bash syntax is valid
- No shell errors

### Gate 3: Swift Build & Tests

**Runs**:
- Clean build of NeuroForgeApp
- All unit tests (including OpsGuardrailsTests)
- SwiftLint (if installed)

**Platform**: macOS runner (Xcode 15)

### Gate 4: Security Check

**Runs**:
- Log redaction tests (pytest)
- Secret pattern scanning
- Blocks exposed API keys, tokens

**Patterns blocked**:
- `sk-...` (OpenAI keys)
- `ghp_...` (GitHub tokens)
- `xox...` (Slack tokens)

### Gate 5: Athena Tools

**Validates**:
- `athena_tools.yaml` is valid YAML
- All referenced scripts exist
- Intent patterns defined

### Gate 6: Documentation

**Checks**:
- Required docs exist
- No broken markdown links (basic check)
- Warns but doesn't block

---

## Workflow Triggers

### Pull Requests
```yaml
on:
  pull_request:
    branches: [main, tier4-foundation]
```
Runs on every PR to main or tier4-foundation

### Push to Main
```yaml
on:
  push:
    branches: [main, tier4-foundation]
```
Validates after merge (post-check)

### Manual Dispatch
```yaml
on:
  workflow_dispatch:
```
Run manually from Actions tab

---

## Local Testing (Before Push)

Run the same checks locally:

```bash
# Encoding check
git diff --cached --name-only | grep -E '\.(sh|env|yml|yaml)$' | \
  xargs -I{} grep -nP '[^\x00-\x7F]' {}

# Service validation
cd NeuroForgeApp && scripts/validate_services.sh

# Swift build
cd NeuroForgeApp && xcodebuild -scheme NeuroForgeApp

# Security tests
pytest tests/test_log_redaction.py -v
```

---

## Bypassing (Emergency Only)

If you need to bypass validation temporarily:

```bash
# Push with skip-ci flag
git commit -m "urgent fix [skip ci]"
git push
```

**WARNING**: Only use for critical hotfixes

---

## Status Badges

Add to README.md:

```markdown
![NeuroForge Validation](https://github.com/YOUR_ORG/YOUR_REPO/actions/workflows/neuroforge_validation.yml/badge.svg)
```

---

## Monitoring

### View Results

1. Go to **Actions** tab in GitHub
2. Click **NeuroForge Platform Validation**
3. See gate-by-gate results

### Failed PR Example

```
Gate 1: Encoding Safety    PASS
Gate 2: Service Validation PASS
Gate 3: Swift Build        FAIL
  -> Unit test failure in OpsGuardrailsTests
Gate 4: Security           BLOCKED

PR Status: BLOCKED - Fix failures before merge
```

### Passed PR Example

```
All Gates Passed:
  OK Encoding safety
  OK Service validation
  OK Swift build & tests
  OK Security checks
  OK Athena tools
  OK Documentation

Ready to Merge
```

---

## Integration with Branch Protection

Add to repository settings:

**Settings** → **Branches** → **Branch protection rules** → `main`

**Require status checks**:
- ✓ Encoding Safety Check
- ✓ Service Health Check
- ✓ Swift Build & Tests
- ✓ Security Check
- ✓ Athena Tools Validation

**Result**: Cannot merge without passing all gates

---

## Customization

### Adjust Gates

Edit `neuroforge_validation.yml`:

```yaml
# Make security non-blocking
security-check:
  continue-on-error: true  # Warning only
```

### Add New Checks

```yaml
- name: Performance tests
  run: |
    pytest tests/test_performance.py
    # Must complete in <5s
```

### Change Xcode Version

```yaml
- name: Select Xcode version
  run: sudo xcode-select -s /Applications/Xcode_15.2.app
```

---

## Troubleshooting

### macOS Runner Unavailable

**Error**: "No macOS runners available"  
**Fix**: Use self-hosted runner or wait for availability

### Swift Tests Timeout

**Error**: Tests hang  
**Fix**: Add timeout:

```yaml
- name: Run unit tests
  timeout-minutes: 10
  run: xcodebuild test ...
```

### Encoding Check False Positive

**Error**: Flags valid UTF-8  
**Fix**: Adjust regex or exclude specific files

---

## Cost Optimization

### GitHub Free Tier

- **Linux runners**: 2,000 min/month free
- **macOS runners**: 200 min/month free (10x multiplier)

### This Workflow

**Per run**:
- Linux gates: ~5 minutes
- macOS gate: ~10 minutes
- Total: ~15 minutes

**Optimization**: Skip macOS build on doc-only changes

```yaml
swift-validation:
  if: |
    !contains(github.event.head_commit.message, '[docs only]')
```

---

## Success Criteria

**All gates must pass**:
- ✅ No encoding issues
- ✅ Scripts valid
- ✅ App builds
- ✅ Tests pass
- ✅ No secrets exposed
- ✅ Tools validated

**Then**: Auto-comment on PR: "Ready to merge"

---

This workflow makes your integration **bulletproof for future changes**.

No more encoding surprises  
No more broken scripts  
No more secret leaks  
No more untested merges

Ship with confidence!

