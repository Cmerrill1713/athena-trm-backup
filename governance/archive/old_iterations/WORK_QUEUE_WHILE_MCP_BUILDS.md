# Work Queue While MCP Store Builds

**Status**: User is building MCP store - working on other items

---

## Available Tasks (Priority Order):

### 1. SwiftUI App Fixes (Build Errors)
**Issue**: Missing ServiceHealthCard.swift file causing compilation errors
**Files affected**: ModernOpsWindow.swift, ServiceRegistry.swift
**Action needed**: Either create missing file or remove references
**Priority**: HIGH (app won't build)

### 2. Research Implementation Testing
**Status**: 5 implementations generated, not yet tested
**Files**: `orchestrator/providers/*.py`
**Action**: Run pytest on all implementations
**Priority**: MEDIUM

### 3. Thompson Sampling Integration
**Status**: New providers registered but not wired to bandit
**Action**: Update scorer.py to include new providers in rotation
**Priority**: MEDIUM

### 4. Docker Stack Verification
**Status**: Multiple docker-compose files, unclear which is authoritative
**Action**: Consolidate and verify all services start correctly
**Priority**: MEDIUM

### 5. Documentation Cleanup
**Status**: Many *_COMPLETE.md files created during session
**Action**: Consolidate into single comprehensive guide
**Priority**: LOW

---

## Currently On Hold (Waiting for User):
- MCP Store integration
- Supabase → Weaviate/Postgres migration
- Dual storage for validation results

---

## Recommended Next Action:
Fix SwiftUI build errors so app is functional
