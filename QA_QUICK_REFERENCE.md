# 🎯 QA Sweep - Quick Reference

## ⚡ Quick Commands

```bash
# Full QA sweep (advisory mode)
make qa

# Strict mode (fail-fast)
make qa-strict

# Individual checks
swiftlint                       # Swift lint
swiftformat --lint Sources/     # Swift format
ruff check scripts src          # Python lint
mypy scripts src               # Python types
bandit -r scripts src          # Python security
shellcheck scripts/*.sh        # Shell lint
yamllint .                     # YAML lint
hadolint Dockerfile*           # Docker lint
```

## 🔧 Auto-Fix Commands

```bash
# Auto-fix Swift formatting
cd NeuroForgeApp
swiftformat Sources/

# Auto-fix Python issues
ruff check --fix scripts src

# Auto-fix YAML formatting
yamllint --fix .
```

## 📊 Current Issues (Summary)

### 🔴 High Priority (7)
- Force unwrapping in `AppConfig`, `APIBase`, `VoiceRecorder`

### 🟡 Medium Priority (30)
- Short variable names (`m`, `ev`, `u`, `s`, etc.)
- Missing trailing newlines (12 files)
- Comma spacing (8 instances)
- TODO in `HealthBanner.swift`

### 🟢 Low Priority (20)
- Docker apt pinning
- Consolidate RUN commands

## 🛠️ Common Fixes

### Force Unwrapping → Error Handling
```swift
// Before
let url = URL(string: baseURL)!

// After
guard let url = URL(string: baseURL) else {
    throw APIError.invalidURL
}
```

### Short Variable Names
```swift
// Before
let m = NSEvent.addLocalMonitorForEvents...
let ev = event

// After
let monitor = NSEvent.addLocalMonitorForEvents...
let event = event
```

### Trailing Newline
```swift
// Just add one blank line at end of file
```

### Comma Spacing
```swift
// Before
["status":"ok","shown":["critical","tribunal"]]

// After
["status": "ok", "shown": ["critical", "tribunal"]]
```

## 📈 Metrics

- **Total Files Scanned:** 39 Swift + Python/Shell/YAML/Docker
- **Issues Found:** ~60
- **Auto-Fixable:** ~30 (50%)
- **Manual Required:** ~30 (50%)

## 🎯 Quick Win Strategy

1. **Run auto-fixes** (5 min)
   ```bash
   cd NeuroForgeApp && swiftformat Sources/
   ```

2. **Fix trailing newlines** (2 min)
   - Add blank line at end of 12 files

3. **Fix comma spacing** (3 min)
   - Auto-fixed by swiftformat

4. **Rename short vars** (15 min)
   - Use find-replace for common ones

5. **Remove force unwrapping** (30 min)
   - Add proper error handling

**Total time:** ~1 hour to fix all issues

## 🚀 CI Integration

The `qa-sweep.yml` workflow runs on:
- Every PR
- Every push to main/tier4-foundation
- Manual dispatch

**Location:** `.github/workflows/qa-sweep.yml`

## 📝 Configuration Files

- `.swiftlint.yml` - Swift linting rules
- `.swiftformat` - Swift formatting config  
- `.sqlfluff` - SQL linting config
- `scripts/athena_qa.sh` - Master QA script

## 🎓 Best Practices

### Before Commit
```bash
make qa
```

### Before PR
```bash
make qa-strict
```

### Auto-fix Everything Possible
```bash
cd NeuroForgeApp && swiftformat Sources/
ruff check --fix scripts src
```

### Check Single File
```bash
swiftlint lint --path NeuroForgeApp/Sources/main.swift
```

## 🔍 Interpreting Results

- **Errors** 🔴 - Must fix
- **Warnings** 🟡 - Should fix  
- **Info** 🔵 - Nice to fix
- **`|| true`** - Advisory (won't block)

## 💡 Pro Tips

1. Run `make qa` frequently during development
2. Use `swiftformat` auto-fix before committing
3. Enable SwiftLint Xcode plugin for real-time feedback
4. Add pre-commit hooks for automatic checking
5. Review QA logs in CI artifacts for detailed reports

## ⚠️ Exclusions

Configured to skip:
- `build/`
- `DerivedData/`
- `.build/`
- `node_modules/`
- Third-party dependencies

## 📚 Documentation

- **Full Report:** `QA_SWEEP_REPORT.md`
- **SwiftLint Rules:** https://realm.github.io/SwiftLint/rule-directory.html
- **SwiftFormat Options:** https://github.com/nicklockwood/SwiftFormat#options

---

**Last Updated:** $(date)
**Status:** 🟢 Operational
