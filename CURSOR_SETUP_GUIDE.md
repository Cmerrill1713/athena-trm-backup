# Cursor/IDE Setup Guide for Athena

**Complete setup for Cursor AI IDE to see and understand your entire codebase**

---

## 🚀 Quick Start (One Command)

```bash
make cursor-bootstrap
```

This will:
- ✅ Initialize all submodules
- ✅ Generate repository inventory
- ✅ Make scripts executable
- ✅ Prepare workspace for Cursor

Then:
1. Open `athena.code-workspace` in Cursor
2. Install recommended extensions
3. Run: `Tasks → 🔌 Wire Check (Complete)`

---

## 📁 Files Created

### 1. **Multi-Root Workspace**
**File:** `athena.code-workspace`

Tells Cursor to index multiple directories:
- Core systems (governance, orchestrator, AGI core, workflows)
- Services & monitoring
- Documentation & runbooks
- Submodules (kokoro, pydantic-ai, A2A)

**How to use:**
```bash
# Open in Cursor
code athena.code-workspace

# Or from Cursor
File → Open Workspace → athena.code-workspace
```

---

### 2. **Cursor Rules**
**File:** `.cursorrules`

Teaches Cursor about your codebase:
- What code to index (and what to ignore)
- Project structure & key entrypoints
- How to run tests & verification
- Integration points between subsystems
- Code style & patterns

**What it does:**
- Helps Cursor give better answers
- Provides context on system architecture
- Suggests relevant files when asking questions
- Knows how to run/test your code

---

### 3. **VS Code Settings**
**File:** `.vscode/settings.json`

Configures language servers:
- **Python**: Uses workspace virtualenv, adds module paths
- **Go**: Configures gopls with proper filters
- **Rust**: Enables clippy and proc macros
- **TypeScript**: Allocates more memory
- **YAML**: Schema validation for config files

**What it does:**
- Enables autocomplete across all modules
- Shows type hints and documentation
- Lints code as you type
- Formats on save

---

### 4. **VS Code Tasks**
**File:** `.vscode/tasks.json`

One-click commands in Cursor:
- 🔌 Wire Check (Complete)
- 🔍 Prometheus: Verify Targets
- 📊 Prometheus: Query Metrics
- 🚀 Start: Governance Stack
- 🎯 Master Orchestrator: Status
- 🧪 Test: DGM Integration
- ✅ Verdict: Send Test (PASS)
- And more...

**How to use:**
```
⇧⌘P (or Ctrl+Shift+P) → Tasks: Run Task
```

Or: `Terminal → Run Task...`

---

### 5. **Repository Inventory**
**File:** `tools/index/repo_inventory.txt`
**Script:** `tools/index/generate_repo_inventory.sh`

Index of all code files:
- Python, YAML, Shell, Go, Rust, TypeScript
- Organized by file type
- Summary statistics

**How to use:**
```bash
make repo-inventory  # Regenerate
cat tools/index/repo_inventory.txt  # View
```

**Why it's useful:**
- Helps you (and Cursor) find files quickly
- See what code exists at a glance
- Reference when asking Cursor questions

---

### 6. **Wiring Verification**
**Script:** `scripts/verify_wiring_complete.sh`

Comprehensive verification:
- ✅ Code imports
- ✅ System initialization
- ✅ Running services
- ✅ Verdict endpoint
- ✅ Metrics export
- ✅ Prometheus scraping
- ✅ State persistence
- ✅ Configuration files

**How to use:**
```bash
make wire-check
# Or directly:
./scripts/verify_wiring_complete.sh
```

---

## 🎯 How Cursor Uses This

### When You Ask a Question

**Before (without setup):**
> "How do I send a verdict?"

Cursor searches entire filesystem, may miss key files.

**After (with setup):**
> "How do I send a verdict?"

Cursor knows to look in:
- `governance/judicial/evaluation/dgm_verdict_validator.py`
- Port 9110 endpoint `/verdict`
- Schema in `.cursorrules`
- Example in `.vscode/tasks.json`

---

### When You Request Code Changes

**Before:**
```
"Add a new metric for DGM"
```
Cursor might suggest generic code without context.

**After:**
```
"Add a new metric for DGM"
```
Cursor knows:
1. Metrics defined in `governance/observability/dgm_metrics.py`
2. Export from orchestrator on port 9110
3. Add to Prometheus scrape config
4. Create Grafana panel
5. Follow existing patterns (labels, naming, etc.)

---

### When Running Tasks

**Before:**
```bash
# Manually type commands
python athena_master_orchestrator.py status
curl http://localhost:9110/verdict -X POST ...
```

**After:**
```
⇧⌘P → Tasks: Run Task → "Master Orchestrator: Status"
⇧⌘P → Tasks: Run Task → "Verdict: Send Test (PASS)"
```
One click, no typing!

---

## 📋 What Gets Indexed

### ✅ Included
- `governance/*` - Complete governance system
- `orchestrator/*` - Master orchestration
- `agi_core/*` - AGI Core multi-agent
- `workflows/*` - Integration workflows
- `monitoring/*` - Observability stack
- `scripts/*` - Automation scripts
- `tests/*` - Test suites
- `config/*` - Configuration
- `docs/*` & `RUNBOOKS/*` - Documentation
- Submodules: `kokoro`, `pydantic-ai`, `A2A`

### ❌ Excluded
- `archive/**` - Historical code
- `backups/**` - Database backups
- `**/node_modules/**` - Dependencies
- `**/.venv/**` - Python virtualenvs
- `**/build/**`, `**/dist/**`, `**/target/**` - Build artifacts
- `**/__pycache__/**` - Python cache

**Why exclude?**
- Faster indexing
- Less noise in search
- Cursor focuses on actual source code

---

## 🔧 Makefile Commands

### Setup
```bash
make cursor-bootstrap  # One-time setup
make repo-inventory    # Regenerate file index
```

### Verification
```bash
make wire-check       # Complete wiring verification
make prom-verify      # Check Prometheus targets
make prom-query       # Query governance metrics
```

### Development
```bash
# In Cursor: ⇧⌘P → Tasks: Run Task
# Or use Makefile:
make governance-gate
make governance-up
```

---

## 🎓 Best Practices

### 1. **Keep Workspace Open**
Always open `athena.code-workspace` (not just the folder).
This ensures Cursor indexes all paths correctly.

### 2. **Update Inventory Regularly**
After adding significant new code:
```bash
make repo-inventory
```

### 3. **Use Tasks for Common Operations**
Don't memorize commands. Use:
```
⇧⌘P → Tasks: Run Task
```

### 4. **Ask Cursor Specific Questions**
**Bad:**
> "How does this work?"

**Good:**
> "How does the verdict flow work from POST /verdict to Prometheus metrics?"

Cursor can now answer with specific file paths and code.

### 5. **Reference .cursorrules When Confused**
Read `.cursorrules` to see what Cursor knows about the system.

---

## 🐛 Troubleshooting

### Cursor Can't Find Files

**Solution:**
1. Ensure workspace is open (not just folder)
2. Regenerate inventory: `make repo-inventory`
3. Check `.cursorrules` excludes aren't too broad

### Language Server Not Working

**Solution:**
1. Check Python interpreter: `⇧⌘P → Python: Select Interpreter`
2. Should point to: `.venv/bin/python`
3. Reload window: `⇧⌘P → Developer: Reload Window`

### Tasks Not Showing Up

**Solution:**
1. Open workspace file: `athena.code-workspace`
2. Reload window: `⇧⌘P → Developer: Reload Window`
3. Check: `Terminal → Run Task...`

### Imports Not Resolving

**Solution:**
1. Check `.vscode/settings.json` → `python.analysis.extraPaths`
2. Add missing module paths
3. Reload window

---

## 📊 What This Enables

### For You
- ✅ One-click testing & verification
- ✅ Faster navigation (Tasks + inventory)
- ✅ Better autocomplete & type hints
- ✅ Consistent code formatting

### For Cursor
- ✅ Understands system architecture
- ✅ Knows where to find code
- ✅ Suggests relevant files
- ✅ Provides better answers
- ✅ Follows your patterns & conventions

### For Your Team
- ✅ Consistent IDE setup
- ✅ Documented conventions
- ✅ Easy onboarding
- ✅ Shared tasks & commands

---

## 🚀 Next Steps

After running `make cursor-bootstrap`:

1. **Open Workspace**
   ```bash
   code athena.code-workspace
   ```

2. **Install Extensions** (Cursor will prompt)
   - Python
   - Go
   - Rust Analyzer
   - YAML
   - ShellCheck

3. **Verify Setup**
   ```
   ⇧⌘P → Tasks: Run Task → "🔌 Wire Check (Complete)"
   ```

4. **Explore**
   - Read `.cursorrules` to see what Cursor knows
   - Try tasks: `⇧⌘P → Tasks: Run Task`
   - Ask Cursor questions about the codebase

---

## 📚 Files Reference

| File | Purpose |
|------|---------|
| `athena.code-workspace` | Multi-root workspace config |
| `.cursorrules` | Cursor AI instructions |
| `.vscode/settings.json` | Language server config |
| `.vscode/tasks.json` | One-click commands |
| `tools/index/generate_repo_inventory.sh` | Generate file index |
| `tools/index/repo_inventory.txt` | File index (auto-generated) |
| `scripts/verify_wiring_complete.sh` | Wiring verification |
| `Makefile` | Automation commands |

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Workspace opens without errors
- [ ] Python imports resolve (no red squiggles)
- [ ] Tasks are visible in Command Palette
- [ ] `make wire-check` runs successfully
- [ ] `make repo-inventory` completes
- [ ] Cursor can answer: "Where is the verdict endpoint defined?"
- [ ] Cursor can answer: "How do I send a test verdict?"

---

**Everything is now wired up for Cursor to see and understand your entire codebase!** 🎉

Run `make cursor-bootstrap` and open `athena.code-workspace` to get started.

