# 🎯 GO, RUST, PYTHON FOCUSED CLEANUP

**Goal:** Keep only Go, Rust, and Python code. Archive Swift and Node.js projects.

---

## ✅ KEEP (Target Languages)

### 🟦 GO

- **ollama-source/** (693MB) ✅ KEEP
  - Your Ollama fork with Athena branding
  - Full Go codebase
  - Active development (you're working on llama_test.go)

### 🟧 RUST

- **Root Cargo.toml** ✅ KEEP
- **governance/observability/** (Rust monitoring code) ✅ KEEP
  - metrics.rs, gpu_monitor.rs, etc.

### 🟨 PYTHON

- **agi_core/** (884KB) ✅ KEEP
- **services/** (101MB) ✅ KEEP - All backend services
  - router, rag-gateway, mcp-ecosystem, kokoro, llm_gateway, etc.
- **governance/** (4.6GB) ✅ KEEP - Core governance system
- **backend/** (11MB) ✅ KEEP
- **monitoring/** (108KB) ✅ KEEP
- **orchestrator/** (28KB) ✅ KEEP
- **common/** (40KB) ✅ KEEP
- **scripts/** (1.7MB) ✅ KEEP
- **pydantic-ai/** (36MB) ✅ KEEP - Python experiments
- **fastvlm/** (5GB) ✅ KEEP - Python + vision models
- **tests/** (108KB) ✅ KEEP - Test suites
- **tools/** (12MB) ✅ KEEP - Python tools

### Other (Keep)

- **ui/** (112KB) ✅ KEEP - HTML/JS web UIs (lightweight, no framework)
- **config/** ✅ KEEP - Configurations
- **docker-compose.yml** ✅ KEEP - Stack definition
- **Makefile\*** ✅ KEEP - Build automation

---

## ❌ ARCHIVE (Non-Target Languages)

### Swift Projects → Move to `archive/swift-projects/`

- **NeuroForgeApp/** (656MB, 8,872 files)
  - Full Swift macOS app
  - Governance integration, chat UI
  - **Decision:** Archive if superseded by web UI
- **assistant-broker/** (36KB)
  - Swift package
  - **Decision:** Archive if not used

### Node.js/TypeScript → Move to `archive/nodejs-projects/`

- **athena-macapp-ui/** (553MB with node_modules)

  - Electron app with TypeScript/React
  - **Decision:** Archive if superseded by web UI

- **athena-desktop-ui/** (12KB)

  - Minimal Node app
  - **Decision:** Archive - too minimal to keep

- **athena-voice-control/** (44KB)
  - Bash scripts + JSON
  - **Decision:** Review - might have useful voice commands

### Large Historical Data → Move out of git

- **archive/** (15GB, 290K files)

  - Already archived content
  - **Decision:** Move to external storage

- **AI-Projects/** (12GB, 285K files)
  - "Universal AI Tools" project
  - **Decision:** Make separate repository or move to external storage

### Completed Research → Archive

- **TinyRecursiveModels/** (282MB)
  - Research project with completion docs
  - **Decision:** Move to `archive/research/`

---

## 📊 SPACE SAVINGS

| Action                        | Space Saved | Files Removed   |
| ----------------------------- | ----------- | --------------- |
| Archive Swift projects        | 656MB       | 8,872           |
| Archive Node.js projects      | 565MB       | 33,840          |
| Move archive/ to external     | 15GB        | 290K            |
| Move AI-Projects/ to external | 12GB        | 285K            |
| Archive TinyRecursiveModels   | 282MB       | 6,128           |
| Remove build artifacts        | 500MB       | 200+            |
| **TOTAL**                     | **~29GB**   | **~625K files** |

---

## 🚀 EXECUTION PLAN

### Phase 1: Archive Non-Target Languages (SAFE)

```bash
cd /Users/christianmerrill/Documents/GitHub

# Create archive structure
mkdir -p archive/2025-10-26-language-cleanup/swift-projects
mkdir -p archive/2025-10-26-language-cleanup/nodejs-projects
mkdir -p archive/2025-10-26-language-cleanup/research

# Move Swift projects
git mv NeuroForgeApp archive/2025-10-26-language-cleanup/swift-projects/
git mv assistant-broker archive/2025-10-26-language-cleanup/swift-projects/

# Move Node.js projects
git mv athena-macapp-ui archive/2025-10-26-language-cleanup/nodejs-projects/
git mv athena-desktop-ui archive/2025-10-26-language-cleanup/nodejs-projects/

# Move completed research
git mv TinyRecursiveModels archive/2025-10-26-language-cleanup/research/

git commit -m "chore: archive Swift and Node.js projects - focus on Go/Rust/Python"
```

### Phase 2: Move Large Historical Data (SAFE)

```bash
# Move to external storage (data preserved!)
mkdir -p ~/athena-external-archives/$(date +%Y-%m-%d)

# Move archive/ (15GB of old backups)
mv archive/ ~/athena-external-archives/$(date +%Y-%m-%d)/archive-old/

# Move AI-Projects/ (separate project)
mv AI-Projects/ ~/athena-external-archives/$(date +%Y-%m-%d)/

# Update git
git add archive/ AI-Projects/
git commit -m "chore: move large archives to external storage"
```

### Phase 3: Clean Build Artifacts (SAFE)

```bash
# Update .gitignore
cat >> .gitignore << 'IGNORE'
# Build artifacts
logs/
state/
artifacts/
snapshots/
backups/
.pytest_cache/
.ruff_cache/

# Dependencies
node_modules/
.build/
.swiftpm/

# Large models
*.bin
*.gguf
*.safetensors
IGNORE

# Remove from git (regenerable files)
git rm -r --cached logs/ state/ artifacts/ snapshots/ backups/
git commit -m "chore: remove build artifacts from git"
```

---

## 🎯 FINAL STRUCTURE

After cleanup, your repo will be:

```
athena-trm-backup/
├── ollama-source/          # Go - Ollama fork
├── agi_core/               # Python - AGI service
├── services/               # Python - Backend services
├── governance/             # Python + Rust - Governance system
├── backend/                # Python - Backend utilities
├── monitoring/             # Python - Monitoring
├── ui/                     # HTML/JS - Web UIs (lightweight)
├── config/                 # Configs
├── scripts/                # Python - Operational scripts
├── tests/                  # Test suites
├── tools/                  # Python tools
├── docker-compose.yml      # Stack definition
├── Makefile*               # Build automation
├── Cargo.toml              # Rust workspace
└── requirements*.txt       # Python dependencies
```

**Languages:** Go, Rust, Python only  
**Estimated Size:** ~8-10GB (down from 35-50GB)  
**Reduction:** 70-80% smaller!

---

## ✅ VERIFICATION CHECKLIST

After cleanup:

- [ ] Go code compiles: `cd ollama-source && go build`
- [ ] Rust code compiles: `cargo build`
- [ ] Python services work: `docker-compose up`
- [ ] Web UI accessible: `http://localhost:8080`
- [ ] No Swift code remains in main repo
- [ ] No Node.js projects in main repo
- [ ] Archive folders moved to external storage
- [ ] Repository size < 10GB

---

## 🔄 IF YOU NEED SWIFT/NODE.JS LATER

All archived code is preserved:

- **In git:** `archive/2025-10-26-language-cleanup/`
- **External:** `~/athena-external-archives/2025-10-26/`

You can:

```bash
# Restore from git archive
git mv archive/2025-10-26-language-cleanup/swift-projects/NeuroForgeApp .

# Or copy from external storage
cp -r ~/athena-external-archives/2025-10-26/archive-old/NeuroForgeApp .
```

---

## 🤔 DECISION POINTS

Before executing, confirm:

1. **NeuroForgeApp** - Do you still need the Swift macOS app? Or is web UI enough?
2. **athena-macapp-ui** - Is the Electron app still used? Or superseded?
3. **AI-Projects/** - Is this a separate project that should be its own repo?
4. **archive/** - Okay to move to external storage? (You can always restore)

---

**Ready to execute?** Start with Phase 1 (archive non-target languages) and we'll verify before moving to Phase 2.
