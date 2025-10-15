# Lint Debt Tracker

**Status**: 1,673 style warnings (non-blocking)  
**Last Updated**: October 14, 2025  
**Baseline Commit**: 9700df8d

---

## 🎯 Strategy

- ✅ **Syntax errors**: ZERO TOLERANCE (CI fails)
- ⚠️ **Style warnings**: Pay down incrementally
- 📊 **Target**: <500 warnings by v1.0.3
- 🎨 **Approach**: Fix-on-touch (update files as you work on them)

---

## 📊 Warning Breakdown

| Rule | Count | Severity | Priority |
|------|-------|----------|----------|
| F841 (unused variable) | ~200 | Low | P3 |
| F401 (unused import) | ~150 | Low | P3 |
| E722 (bare except) | ~100 | Medium | P2 |
| E731 (lambda assignment) | ~80 | Low | P3 |
| E712 (== True/False) | ~70 | Low | P3 |
| E402 (import not at top) | ~50 | Medium | P2 |
| Others | ~1023 | Mixed | P3 |

---

## ✅ Quick Wins (Auto-Fixable)

### Unused Imports (F401)
```bash
# Auto-remove unused imports
autoflake -ir --remove-all-unused-imports --ignore-init-module-imports src/ scripts/
```

### Unused Variables (F841)
```bash
# Auto-remove unused assignments
autoflake -ir --remove-unused-variables src/ scripts/
```

### Code Formatting
```bash
# Apply consistent formatting
black src/ scripts/
isort src/ scripts/
```

---

## 🎯 Incremental Paydown Plan

### v1.0.3 (Target: <500 warnings)
- [ ] Run autoflake on src/ (remove unused imports/vars)
- [ ] Fix bare except in critical paths (E722)
- [ ] Convert lambda assignments to def (E731)
- [ ] Update == True/False comparisons (E712)

### v1.0.4 (Target: <200 warnings)
- [ ] Fix import order violations (E402)
- [ ] Add specific exception types to bare excepts
- [ ] Clean up test files

### v1.0.5 (Target: <50 warnings)
- [ ] Address remaining edge cases
- [ ] Tighten .flake8 rules
- [ ] Remove pragmatic exclusions

---

## 🚫 Files Excluded from Linting

### Demo/Spike Files (Broken)
- `scripts/demo_governance_drift_detection.py`
- `scripts/demo_governance_drift_detection_fixed.py`
- `scripts/integrate_governance_drift_detection.py`
- `spikes.py`
- `triggers.py`

### Large Demo Files (Too Many Warnings)
- `scripts/vision_smoke_test.py`
- `voice_activation.py`

### Action Items
- [ ] Fix or archive broken demo files
- [ ] Clean up vision_smoke_test.py
- [ ] Refactor voice_activation.py

---

## 📈 Progress Tracking

| Date | Total Warnings | Change | Notes |
|------|----------------|--------|-------|
| 2025-10-14 | 1,673 | Baseline | Initial measurement after syntax fixes |
| | | | |
| | | | |

---

## 🛠️ Tools

### Check Current Count
```bash
flake8 . | wc -l
```

### Check by Rule
```bash
flake8 . | grep E722 | wc -l  # Bare except
flake8 . | grep F401 | wc -l  # Unused imports
flake8 . | grep F841 | wc -l  # Unused variables
```

### Auto-Fix Safe Issues
```bash
# Preview changes
autoflake --remove-all-unused-imports --remove-unused-variables src/

# Apply fixes
autoflake -ir --remove-all-unused-imports --remove-unused-variables src/
black src/
isort src/
```

---

## 🎯 Fix-on-Touch Policy

When working on any file:
1. Run `ruff check --fix <file>` to auto-fix safe issues
2. Manually fix remaining warnings in your changes
3. Keep the file's warning count the same or lower
4. Update this tracker when a directory goes green

---

**Goal**: Ship quality code while maintaining momentum. Zero syntax errors, declining style debt.

