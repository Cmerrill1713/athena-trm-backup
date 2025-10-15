# NeuroForge Guardrails Setup

**Purpose**: Automated quality gates to keep your codebase boringly green
**Time**: 5 minutes to set up
**Value**: Prevents regressions, catches issues early

---

## 🛡️ Guardrail 1: Pre-Push QA Gate

### **What It Does:**
- Runs `make qa` before every `git push`
- Blocks push if tests fail
- Ensures only green code reaches remote

### **Status:**
✅ **Already Installed** - `.git/hooks/pre-push` created and executable

### **How It Works:**
```bash
git push

# Output:
🔍 Pre-push QA gate: running comprehensive validation...
🧹 Step 1: Clean build artifacts...
🔧 Step 2: Verify backend services...
🔥 Step 3: Warm up services...
🧪 Step 4: UI tests (QA mode)...
📊 Step 5: Golden diff (CI tolerance)...

✅ QA green — proceeding with push.
```

### **If QA Fails:**
```bash
❌ QA failed — push blocked.
Check: NeuroForgeApp/artifacts/xcodebuild-ui-tests.log

To bypass (not recommended): git push --no-verify
```

### **Bypass (Emergency Only):**
```bash
# Skip QA gate if absolutely necessary
git push --no-verify
```

---

## 🛡️ Guardrail 2: Nightly QA Sweep

### **What It Does:**
- Runs complete QA sweep nightly at 2:00 AM
- Archives artifacts with timestamps
- Logs results to `/tmp/neuroforge_qa/`
- Catches regressions while you sleep

### **Script:**
✅ **Already Created** - `scripts/nightly_qa.sh`

### **Install Cron Job:**
```bash
# Add to crontab (runs at 2:00 AM daily)
(crontab -l 2>/dev/null; echo "0 2 * * * /Users/christianmerrill/Documents/GitHub/NeuroForgeApp/scripts/nightly_qa.sh") | crontab -

# Verify installation
crontab -l
```

### **Check Results:**
```bash
# View latest log
ls -lt /tmp/neuroforge_qa/*.log | head -1 | awk '{print $NF}' | xargs tail -50

# View all nightly runs
ls -lh /tmp/neuroforge_qa/

# If failure, check artifacts
ls -la /tmp/neuroforge_qa/failures/
```

### **Disable Nightly Run:**
```bash
# Remove from crontab
crontab -l | grep -v nightly_qa.sh | crontab -
```

---

## 🛡️ Guardrail 3: GitHub Actions (CI)

### **What It Does:**
- Runs on every PR to main or v0.9.* branches
- Validates UI tests and golden diffs
- Uploads artifacts for review
- Blocks merge if tests fail

### **Status:**
✅ **Already Created** - `.github/workflows/ui-golden.yml`

### **Enable Branch Protection:**
```bash
# GitHub → Settings → Branches → Add rule

Branch name pattern: main

☑ Require pull requests before merging
☑ Require status checks to pass:
  - UI Golden (ui-golden job)
  - UI Tests (ui-tests job)
☑ Require conversation resolution
☑ Require linear history (optional)
```

### **PR Workflow:**
1. Developer creates PR
2. GitHub Actions runs `make qa`
3. If pass: ✅ Merge allowed
4. If fail: ❌ Review artifacts, fix issues

---

## 📊 Monitoring

### **Daily Health Check:**
```bash
# Quick confidence check (manual)
make green
make -C NeuroForgeApp xctest

# Full QA sweep (manual)
make -C NeuroForgeApp qa
```

### **Weekly Review:**
```bash
# Check nightly logs
ls -lh /tmp/neuroforge_qa/

# Count successes vs failures
grep -l "PASSED" /tmp/neuroforge_qa/*.log | wc -l
grep -l "FAILED" /tmp/neuroforge_qa/*.log | wc -l
```

### **Monthly Cleanup:**
```bash
# Archive old logs
mkdir -p ~/Archives/neuroforge_qa
mv /tmp/neuroforge_qa/qa_2025* ~/Archives/neuroforge_qa/

# Keep last 7 days
find /tmp/neuroforge_qa -name "*.log" -mtime +7 -delete
```

---

## 🚀 Usage Examples

### **Pre-Commit Workflow:**
```bash
# Make changes
vim Sources/Features/ChatView.swift

# Run QA before committing
make -C NeuroForgeApp qa

# If green, commit
git add -A
git commit -m "feat: my changes"

# Pre-push hook runs automatically
git push  # Blocked if QA fails ✅
```

### **PR Workflow:**
```bash
# Create feature branch
git checkout -b feature/my-feature

# Develop with continuous QA
make -C NeuroForgeApp qa

# Push and create PR
git push origin feature/my-feature

# GitHub Actions runs automatically
# Merge when green ✅
```

### **Release Workflow:**
```bash
# Before release, run full QA
make -C NeuroForgeApp qa

# If all green, tag and release
git tag v0.9.3-green
git push --tags

# Pre-push hook validates ✅
```

---

## 🔧 Configuration

### **Adjust Nightly Schedule:**
```bash
# Edit crontab
crontab -e

# Change time (format: minute hour day month weekday)
# Examples:
0 2 * * *   # 2:00 AM daily (current)
0 4 * * 1   # 4:00 AM every Monday
30 1 * * *  # 1:30 AM daily
```

### **Adjust Golden Tolerance:**
```bash
# In Makefile, change default
GOLDEN_TOLERANCE := 0.005  # More lenient

# Or set environment variable
GOLDEN_TOLERANCE=0.001 make xctest  # More strict
```

### **Adjust QA Steps:**
```bash
# Edit Makefile qa target to add/remove steps
# Current: clean → health → warmup → tests → golden
# Custom: Add performance benchmarks, memory checks, etc.
```

---

## 🆘 Troubleshooting

### **Pre-Push Hook Not Running:**
```bash
# Verify it's executable
ls -la .git/hooks/pre-push
chmod +x .git/hooks/pre-push

# Test it manually
.git/hooks/pre-push
```

### **Nightly Cron Not Running:**
```bash
# Verify crontab entry
crontab -l | grep nightly_qa

# Check cron logs (macOS)
log show --predicate 'process == "cron"' --last 1d

# Test script manually
bash NeuroForgeApp/scripts/nightly_qa.sh
```

### **GitHub Actions Failing:**
```bash
# Check workflow file
cat .github/workflows/ui-golden.yml

# View logs on GitHub
# Go to: Actions tab → Latest run → View logs
```

---

## ✅ Verification

### **Check Pre-Push Hook:**
```bash
# Should exist and be executable
ls -la .git/hooks/pre-push
# Expected: -rwxr-xr-x ... .git/hooks/pre-push
```

### **Check Nightly Cron:**
```bash
# Should be in crontab
crontab -l | grep nightly_qa
# Expected: 0 2 * * * .../nightly_qa.sh
```

### **Check CI Workflow:**
```bash
# Should exist
ls -la NeuroForgeApp/.github/workflows/ui-golden.yml
# Expected: -rw-r--r-- ... ui-golden.yml
```

---

## 🚀 All Guardrails Active

When properly set up, you'll have:
- ✅ **Pre-push gate** - Blocks bad pushes locally
- ✅ **Nightly sweep** - Catches regressions overnight
- ✅ **CI validation** - Protects main branch on GitHub
- ✅ **Golden diff** - Visual regression protection
- ✅ **Complete QA** - One-command validation

**Result**: Boringly green, every time! ✅

---

## 📝 Checklist

- [x] Pre-push hook installed (.git/hooks/pre-push)
- [x] Nightly QA script created (scripts/nightly_qa.sh)
- [x] Cron job ready to install
- [x] GitHub Actions workflow created
- [x] Branch protection ready to enable
- [x] Documentation complete
- [ ] **Cron job installed** (run: `crontab -e` and add line)
- [ ] **Branch protection enabled** (GitHub Settings)
- [ ] **First nightly run** (wait for 2:00 AM or run manually)

---

**GUARDRAILS READY** ✅
**Status**: Production-Grade Quality Gates
**Next**: Install cron job and enable branch protection! 🚀
