# 🛡️ SAFE CLEANUP PLAN - NO DATA LOSS

## ✅ Phase 1: Remove ONLY Build Artifacts (Safe)

### These are generated files that can be recreated:

```bash
# Add to .gitignore (don't commit these)
echo "logs/" >> .gitignore
echo "state/" >> .gitignore
echo "artifacts/" >> .gitignore
echo "snapshots/" >> .gitignore
echo "backups/" >> .gitignore
echo ".pytest_cache/" >> .gitignore
echo ".ruff_cache/" >> .gitignore

# Remove from git tracking only
git rm -r --cached logs/ state/ artifacts/ snapshots/
```

**Why this is safe:** These are runtime files that get regenerated.

## ✅ Phase 2: Fix node_modules in git (Safe)

```bash
# athena-macapp-ui has node_modules committed (bad practice)
cd athena-macapp-ui
echo "node_modules/" >> .gitignore
git rm -r --cached node_modules/
```

**Why this is safe:** node_modules can be reinstalled with `npm install`.

## ✅ Phase 3: Move Large Folders (Keep Data, Move Out of Git)

### Option A: External Storage (Recommended)
```bash
# Move to external storage (not deleting!)
mkdir -p ~/athena-archives/$(date +%Y-%m-%d)
mv archive/ ~/athena-archives/$(date +%Y-%m-%d)/
mv AI-Projects/ ~/athena-archives/$(date +%Y-%m-%d)/

# Remove from git
git add archive/ AI-Projects/
git commit -m "chore: move archive and AI-Projects to external storage"
```

### Option B: Separate Git Repos (Keep in Git, Separate Repos)
```bash
# Keep the data in separate repositories
# This preserves history and allows independent cloning
```

**Why this works:** Data is preserved, just not in main repo.

## ✅ Phase 4: Clean Governance Test Artifacts (Keep Recent)

```bash
# governance/judicial/evaluation has thousands of old .zip files
# Keep last 10, archive the rest

cd governance/judicial/evaluation
# Keep recent artifacts
git rm old_*.zip  # Remove only old ones
# Upload to S3/external storage if you need them
```

## 🔍 What We're NOT Deleting

**KEEP ALL:**
- ✅ NeuroForgeApp/ (your primary app
- ✅ ollama-source/ (your Ollama fork
- ✅ services/ (all backend services
- ✅ governance/ (just clean up old test results
- ✅ all Swift code
- ✅ all Python code
- ✅ all configurations
- ✅ all your work

**ONLY "Delete" FROM GIT:**
- 🔧 Build artifacts (can be regenerated)
- 🔧 Log files (can be regenerated)
- 🔧 node_modules (can be reinstalled)

**MOVE OUT OF GIT (But Keep Locally):**
- 📦 archive/ → Move to ~/athena-archives/
- 📦 AI-Projects/ → Either keep as-is or make submodule
