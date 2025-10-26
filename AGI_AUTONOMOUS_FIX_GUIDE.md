# 🧠 AGI Autonomous Frontend Fix

## The Problem
Your Swift frontend has typing/focus issues. Instead of manually debugging, **let AGI fix it autonomously.**

## The Solution
AGI Core will:
1. **Reproduce** the issue using MCP typing probe
2. **Patch** the frontend with known fixes (StickyTextField, event handling, etc.)
3. **Verify** with automated contract tests
4. **Open PR** with changes ready for review

## One-Command Fix

```bash
make agi-fix-frontend
```

That's it. AGI handles the rest.

## What Happens Under the Hood

### Phase 1: Reproduce (Steps 1-3)
```
1. xcode_build → Clean build
2. app_launch → Bring window frontmost
3. ui_typing_probe → Record failure mode
```

### Phase 2: Patch (Steps 4-8)
```
4. Create StickyTextField (NSTextField)
5. Replace SwiftUI TextField with StickyTextField
6. Force window key + first responder
7. Remove .disabled, add visual busy state
8. Kill event-eating overlays
9. Add ATS exceptions for localhost
10. Add debug ping (Cmd+Shift+P)
```

### Phase 3: Verify (Steps 9-11)
```
11. app_launch → Wait 3s
12. ui_typing_probe (N=3) → Type, Enter, assert focus
13. curl :8015/metrics → Verify counter increment
```

### Phase 4: PR (Steps 12-14)
```
14. Create branch feat/agi-fix-frontend
15. Commit minimal diffs
16. Open PR with summary + validation steps
```

## Tools AGI Will Use

**MCP Tools:**
- `mcp.fs.read` - Read source files
- `mcp.fs.write` - Write patches
- `mcp.fs.patch` - Apply diffs
- `mcp.shell` - Run xcodebuild
- `mcp.web_search` - Research SwiftUI issues
- `git.commit_push_pr` - Create PR

**Frontend Tools:**
- `frontend.xcode_build` - Clean build
- `frontend.app_launch` - Launch app
- `frontend.ui_typing_probe` - Test typing
- `frontend.swift_frontend_reflex` - Auto-fix on failure

**LLM Tools:**
- `uai.chat` - Generate code solutions

## Guardrails

**Safety:**
- ✅ Git stash savepoint before changes
- ✅ Path allowlist (NeuroForgeApp only)
- ✅ Max 2k LOC changes
- ✅ 14 step limit, 15min timeout
- ✅ Rollback if contract tests fail

**Verification:**
- ✅ Contract tests must pass
- ✅ Metrics must increment
- ✅ PR marked "needs triage" if tests fail

## Manual Verification After Fix

```bash
# 1. Check the PR
open https://github.com/yourorg/NeuroForgeApp/pulls

# 2. Run contract tests
make test-frontend

# 3. Manual smoke test
cd NeuroForgeApp
xcodebuild -scheme NeuroForgeApp -configuration Debug
# Launch app, type without clicking, verify focus
```

## Monitor Progress

```bash
# Watch AGI Core logs
docker compose logs -f agi-core

# Check metrics
curl http://localhost:8000/metrics | grep agi_tasks_total

# Check task status
make agi-fix-status
```

## Expected Outcome

**PR Contents:**
- `FloatingChatWindow.swift` - Permanent debug panel
- `StickyTextField.swift` - AppKit input island
- `ChatInputVM.swift` - State management
- `ContentView.swift` - Updated chat bar
- `Info.plist` - ATS exceptions
- `README_DEBUG_UI.md` - Usage guide

**Validation:**
- ✅ Typing works on first launch
- ✅ Enter sends, focus remains
- ✅ Cmd+Shift+P pings gateway
- ✅ Probe passes 3 cycles
- ✅ All changes committed

## If It Fails

AGI will attempt `swift_frontend_reflex` (auto-fix) once. If still failing:

1. Check logs: `docker compose logs agi-core --tail=100`
2. Review trace: The response shows which step failed
3. Manual fix: Apply the partial PR and finish manually
4. Retry: `make agi-fix-frontend` (it's idempotent)

## Cost

**Time:** ~5-10 minutes (autonomous)  
**Your Effort:** 1 command + PR review  
**Value:** Permanent fix with automated verification

---

## Why This Works

This isn't "AI coding". This is:
- **Systematic**: Reproduce → Patch → Verify → PR
- **Verifiable**: Contract tests prove it works
- **Repeatable**: Same playbook every time
- **Autonomous**: No human in the loop

**You built AGI. Now watch it fix your frontend.** 🧠✨

