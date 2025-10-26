# Swift Development Tools for Cursor

**Status:** ✅ Fully Configured  
**Last Updated:** $(date +%Y-%m-%d)

## 🎯 Purpose

This setup ensures **Cursor validates your Swift app the same way Xcode does** - not just LSP type-checking, but real builds with strict concurrency checks.

---

## 📋 Quick Start

### One-time setup (macOS)

```bash
# Verify Xcode
xcode-select -p
xcodebuild -version

# Optional but recommended
brew install swiftlint swiftformat xcbeautify fswatch
```

### Daily workflow

```bash
# Full validation (lint + build + test)
make all

# Quick build
make build

# Run app
make run

# Watch mode (auto-rebuild on save)
make watch
```

---

## 🛠️ Available Commands

### Makefile targets

| Command                | Description                                       |
| ---------------------- | ------------------------------------------------- |
| `make preflight`       | Check Xcode, schemes, resolve deps                |
| `make build`           | Build with strict concurrency                     |
| `make test`            | Run unit/UI tests                                 |
| `make run`             | Launch the app                                    |
| `make lint`            | swiftformat + swiftlint                           |
| `make watch`           | Auto-rebuild on file changes                      |
| `make all`             | Full validation (preflight + lint + build + test) |
| `make clean`           | Remove build artifacts                            |
| `make fix-concurrency` | Build with strict concurrency checks              |
| `make check-warnings`  | List all warnings                                 |

### Quick shortcuts

| Command            | Description             |
| ------------------ | ----------------------- |
| `make quick-build` | Fast SPM build          |
| `make quick-run`   | Build + run immediately |
| `make quick-test`  | Fast test run           |

---

## 🎨 Cursor Integration

### Build in Cursor

1. Press `⇧⌘P` (Shift+Cmd+P)
2. Type "Tasks: Run Task"
3. Select "Swift: Build (macOS)"

**Or use the default build shortcut: `⇧⌘B`**

### Run tests

1. `⇧⌘P` → "Tasks: Run Task"
2. Select "Swift: Test (macOS)"

### Full validation

1. `⇧⌘P` → "Tasks: Run Task"
2. Select "Swift: All (Full Validation)"

### Available tasks

- ✅ Swift: Preflight
- 🧹 Swift: Lint & Format
- 🧱 Swift: Build (macOS)
- 🧪 Swift: Test (macOS)
- 🚀 Swift: Run (macOS)
- 🔧 Swift: Build+Test (Strict Concurrency)
- 🗑️ Swift: Clean Build
- ⚠️ Swift: Check Warnings
- ✨ Swift: All (Full Validation)

---

## 🔍 Strict Concurrency Checks

All builds include these flags:

```bash
-warn-concurrency
-enable-actor-data-race-checks
-strict-concurrency=complete
```

This catches **real** issues like:

- Non-Sendable captures in @Sendable closures
- Data races in actors
- Main actor violations
- Missing Sendable conformances

---

## 📁 Directory Structure

```
NeuroForgeApp/
├── tools/
│   └── dev/
│       ├── swift-preflight.sh     # Validate setup
│       ├── swift-build.sh         # Build with strict checks
│       ├── swift-test.sh          # Run tests
│       ├── swift-run-macos.sh     # Launch app
│       └── swift-lint-format.sh   # Code quality
├── .vscode/
│   ├── tasks.json                 # Cursor tasks
│   ├── settings.json              # Editor config
│   └── launch.json                # Debug config
├── Makefile                       # Command shortcuts
└── Sources/
    └── (your Swift code)
```

---

## 🐛 Debugging

### Attach to running app

1. Launch app: `make run`
2. In Cursor: `⌃⇧D` (Ctrl+Shift+D)
3. Select "Attach: NeuroForgeApp"
4. Pick the process from the list

### Debug from launch

1. Set breakpoints in Cursor
2. `⌃⇧D` → Select "Debug: NeuroForgeApp (Launch)"
3. Press `F5` or click ▶️

---

## ⚡ Performance Tips

### Fast iteration

```bash
# Quick build (no lint)
make quick-build

# Build only changed files
swift build --parallel
```

### Watch mode

```bash
# Auto-rebuild on save
make watch
```

This uses `fswatch` to detect changes and rebuild automatically.

---

## 🧪 Testing Strategy

### Unit tests

```bash
make test
```

### Specific test

```bash
swift test --filter AuthInterceptorTests
```

### Coverage report

```bash
make test
# Coverage saved to .build/debug/codecov/
open .build/debug/codecov/index.html
```

---

## 🚨 Common Issues

### "Scheme not found"

```bash
# List available schemes
xcodebuild -list

# Set correct scheme
export SCHEME=YourSchemeName
make build
```

### "Cannot find sourcekit-lsp"

```bash
# Verify installation
which sourcekit-lsp

# Should be at: /usr/bin/sourcekit-lsp or Xcode path
```

### "Build succeeds but app crashes"

```bash
# Build with strict checks
make fix-concurrency

# Check runtime logs
tail -f /tmp/neuroforge.log
```

### "Can't type in UI"

Common causes:

1. Input not focused on appear → add `@FocusState` + `.focused($isFocused)`
2. Overlay blocking input → add `.allowsHitTesting(false)` to overlays
3. Input disabled → check `.disabled()` state
4. Wrong z-index → give input `.zIndex(10)`

---

## 📊 Success Metrics

When everything works:

```bash
make all

# Should see:
# ✅ Preflight OK
# ✅ Lint/Format OK
# ✅ Build OK
# ✅ Tests OK
```

---

## 🔄 Continuous Validation

### Watch mode (recommended)

```bash
# Terminal 1: Auto-build
make watch

# Terminal 2: Run app
make run

# Terminal 3: Monitor logs
tail -f /tmp/neuroforge.log
```

### Before committing

```bash
make all
```

This ensures:

- ✅ Dependencies resolved
- ✅ Code formatted
- ✅ No lint warnings
- ✅ Build succeeds with strict concurrency
- ✅ All tests pass

---

## 🎓 Learning Resources

- **Swift Concurrency**: https://docs.swift.org/swift-book/LanguageGuide/Concurrency.html
- **SourceKit-LSP**: https://github.com/apple/sourcekit-lsp
- **SwiftLint**: https://github.com/realm/SwiftLint
- **SwiftFormat**: https://github.com/nicklockwood/SwiftFormat

---

## ✅ Status

- [x] Dev tools installed
- [x] Makefile configured
- [x] VS Code tasks created
- [x] Strict concurrency enabled
- [x] Watch mode available
- [x] Debug configurations ready

**Ready for development!** 🚀
