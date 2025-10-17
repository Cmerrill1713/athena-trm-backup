# Duplicate Cleanup Plan - 2025-10-17

## Canonical Sources of Truth

✅ **Router:** `services/router/`  
✅ **Governance:** `governance/`  
✅ **Swift App:** `NeuroForgeApp/`  
✅ **Infra/Obs:** `infra/`  
✅ **Shared libs:** `clients/`, `tools/`

## Findings

### 1. Router Duplicates

**KEEP:**

- ✅ `services/router/app.py` - NEW canonical router (A2)
- ✅ `services/router/health.py`
- ✅ `services/router/providers/` - NEW provider implementations
- ✅ `services/router/policies/local_first.yaml`

**ARCHIVE:**

- ❌ `services/router/athena_router.py` - OLD router (pre-A2)
- ❌ `services/router/internal/` - Go implementation (unused, we're using Python)
- ❌ `services/router/cmd/` - Go implementation
- ❌ `services/router/pkg/` - Go implementation

**KEEP (Different Purpose):**

- ✅ `services/mcp/router/` - MCP tool, not the main router
- ✅ `services/router-exporter/` - Metrics exporter (separate service)

### 2. ChatService.swift Duplicates

**KEEP:**

- ✅ `NeuroForgeApp/Sources/Services/ChatService.swift` - CANONICAL (just updated in A1)

**DELETE (Wrong Location):**

- ❌ `governance/legislative/policy_compiler/ChatService.swift` - 163 lines, WRONG LOCATION
- ❌ `governance/archive/old_iterations/ChatService.swift` - 163 lines, already archived

**IGNORE (Already Archived):**

- ✅ `archive/**` - All archive copies are fine

### 3. governance/legislative/policy_compiler/ Contamination

This directory has **2.6GB of random files** that don't belong:

- ChatService.swift
- SQL files
- K8s YAML
- Random numbered files

**EXPECTED CONTENTS:**

- `orchestrator.py` - Policy compilation orchestrator
- `bridge.py` - Policy bridge/interface
- Policy-related Python modules only

**ACTION:** Clean out all non-policy files from this directory.

### 4. app.py Duplicates

**KEEP (Different Purposes):**

- ✅ `services/router/app.py` - Router service (NEW, A2)
- ✅ `governance/legislative/policy_compiler/app.py` - Policy compiler (if it exists and is relevant)
- ✅ `orchestrator/app.py` - Orchestrator service

**IGNORE:**

- ✅ `archive/**` - Already archived
- ✅ `.venv/**`, `pydantic-ai/**` - Dependencies

### 5. Governance API Duplicate

**KEEP:**

- ✅ `governance/executive/api.py` - NEW (A2)

**CHECK:**

- ❓ `orchestrator/app.py` - Is this the same as governance API or different?

## Cleanup Actions

### Phase 1: Archive Old Router (Safe)

```bash
# Create archive directory
mkdir -p archive/2025-10-17-router-consolidation

# Move old router implementation
mv services/router/athena_router.py archive/2025-10-17-router-consolidation/
mv services/router/cmd archive/2025-10-17-router-consolidation/
mv services/router/internal archive/2025-10-17-router-consolidation/
mv services/router/pkg archive/2025-10-17-router-consolidation/
mv services/router/go.mod archive/2025-10-17-router-consolidation/
mv services/router/go.sum archive/2025-10-17-router-consolidation/

# Keep only:
# - app.py (NEW)
# - health.py (NEW)
# - providers/ (NEW)
# - policies/ (NEW)
# - requirements.txt (NEW)
# - README.md (NEW)
# - bin/router (if needed)
```

### Phase 2: Clean governance/legislative/policy_compiler/

```bash
# Backup first
tar -czf archive/2025-10-17-policy-compiler-dump.tar.gz \
  governance/legislative/policy_compiler/

# Keep only Python files related to policy compilation
cd governance/legislative/policy_compiler/
find . -type f ! -name "*.py" ! -name "*.yaml" ! -name "*.md" -delete
# Manual review of remaining .py files
```

### Phase 3: Remove Misplaced Swift Files

```bash
# These Swift files don't belong in governance/
rm governance/legislative/policy_compiler/ChatService.swift
rm governance/archive/old_iterations/ChatService.swift

# Canonical version already exists in NeuroForgeApp/
```

### Phase 4: Verify No Breakage

```bash
# Test router
make router-verify

# Test governance API
curl http://127.0.0.1:9110/health

# Test Swift app
cd NeuroForgeApp && swift build

# Run integration tests
make pre-ship-quick
```

## Risk Assessment

### Low Risk (Safe to delete):

- ✅ Old router Go implementation (unused)
- ✅ Misplaced Swift files in governance/
- ✅ Duplicate files in archive/

### Medium Risk (Review first):

- ⚠️ governance/legislative/policy_compiler/ cleanup
- ⚠️ orchestrator/app.py vs governance/executive/api.py

### High Risk (Don't touch):

- 🔴 Services actively in use
- 🔴 NeuroForgeApp/ canonical files

## Post-Cleanup Verification

1. ✅ Router health: `curl :9113/health`
2. ✅ Governance health: `curl :9110/health`
3. ✅ Swift build: `cd NeuroForgeApp && swift build`
4. ✅ Metrics flowing: `curl :9090/api/v1/targets`
5. ✅ No broken imports: `git grep "services/router/athena_router"`
6. ✅ Pre-ship passes: `make pre-ship-quick`

## Guardrails (Post-Cleanup)

### 1. CODEOWNERS

```
services/router/        @christianmerrill
governance/             @christianmerrill
NeuroForgeApp/          @christianmerrill
infra/                  @christianmerrill
```

### 2. CI Check (Prevent Future Dupes)

Add to `.github/workflows/no-dupes.yml`:

```yaml
name: no-dupes
on: [pull_request]
jobs:
  check:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check for duplicate routers
        run: |
          COUNT=$(find . -name "*router*.py" -not -path "*/archive/*" -not -path "*/.venv/*" | wc -l)
          if [ $COUNT -gt 5 ]; then
            echo "Too many router files: $COUNT"
            exit 1
          fi
      - name: Check for misplaced Swift in governance
        run: |
          if find governance -name "*.swift" | grep -v archive; then
            echo "Swift files found in governance/"
            exit 1
          fi
```

### 3. Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Block commits of duplicate router implementations
if git diff --cached --name-only | grep -E "router.*\.py" | grep -v "services/router"; then
    echo "❌ Router code must be in services/router/"
    exit 1
fi

# Block Swift files in governance
if git diff --cached --name-only | grep -E "governance/.*\.swift"; then
    echo "❌ Swift files don't belong in governance/"
    exit 1
fi
```

## Timeline

- **Phase 1 (Archive Old Router):** 5 minutes
- **Phase 2 (Clean Policy Compiler):** 15 minutes
- **Phase 3 (Remove Misplaced Swift):** 2 minutes
- **Phase 4 (Verification):** 10 minutes
- **Total:** ~30 minutes

## Success Criteria

✅ Only ONE router implementation in `services/router/app.py`  
✅ Only ONE ChatService.swift in `NeuroForgeApp/Sources/Services/`  
✅ No Swift files in `governance/`  
✅ `governance/legislative/policy_compiler/` contains only policy code  
✅ All services pass health checks  
✅ `make pre-ship-quick` passes  
✅ Grafana dashboards still work  
✅ CI no-dupes check passes
