# 🚀 Quick Start Guide - Multi-Project Workspace

## TL;DR

```bash
# Health check all projects
bash ~/Documents/GitHub/workspace_doctor.sh

# Work on a specific project
cd ~/Documents/GitHub/AI-Projects/universal-ai-tools
make install    # One-time setup
make test       # Run tests
make lint       # Check code quality
```

---

## 📁 Project Quick Links

### 🐍 Python Projects (Python 3.11)

| Project | Path | Status | Quick Start |
|---------|------|--------|-------------|
| **universal-ai-tools** | `AI-Projects/universal-ai-tools` | ✅ Ready | `cd AI-Projects/universal-ai-tools && make test` |
| **TinyRecursiveModels** | `TinyRecursiveModels` | ✅ Ready | `cd TinyRecursiveModels && make test` |
| **pydantic-ai** | `pydantic-ai` | ℹ️ Own Setup | `cd pydantic-ai && uv pip install -e .[dev]` |

### 📦 Node Projects

| Project | Path | Quick Start |
|---------|------|-------------|
| **A2A Types** | `A2A/types` | `cd A2A/types && npm install` |

---

## 🔨 Common Commands (Python)

All Python projects with Makefiles support:

```bash
make help      # Show available commands
make venv      # Create Python 3.11 virtual environment
make install   # Install dependencies
make test      # Run pytest
make lint      # Run ruff linter
make fmt       # Format code with ruff
make clean     # Remove venv and cache files
```

---

## 🩺 Workspace Health Check

```bash
# Run from anywhere
bash ~/Documents/GitHub/workspace_doctor.sh
```

**Checks:**
- Python version & venv status
- Installed tools (pytest, ruff, pip)
- Dependencies presence
- Node/npm versions

---

## 🐛 Troubleshooting

### Issue: `pytest not found`
```bash
cd <project-directory>
make install
```

### Issue: `ImportError` or `ModuleNotFoundError`
```bash
# Activate venv and install missing package
cd <project-directory>
.venv/bin/pip install <package-name>
```

### Issue: NumPy deprecated warnings
✅ **Fixed!** NumPy compatibility issues resolved in `entropy-regularization-framework`

### Issue: MLX not available
```bash
cd ~/Documents/GitHub/TinyRecursiveModels
.venv/bin/pip install mlx mlx-lm
```

---

## 📊 Workspace Status (Current)

### ✅ Fully Configured
- universal-ai-tools (Python 3.11 + pytest + ruff)
- TinyRecursiveModels (Python 3.11 + MLX + pytest)

### ℹ️ External Setup
- pydantic-ai (uses UV monorepo setup)
- A2A types (Node/TypeScript)

### 📝 Optional
- FastVLM models (install `timm` if needed)
- pydantic-ai testing (install `pytest-inline-snapshot` if needed)

---

## 🎯 Development Workflow

### Starting a new task:

1. **Check workspace health:**
   ```bash
   bash ~/Documents/GitHub/workspace_doctor.sh
   ```

2. **Navigate to project:**
   ```bash
   cd ~/Documents/GitHub/<project-path>
   ```

3. **Ensure dependencies are current:**
   ```bash
   make install
   ```

4. **Run tests before making changes:**
   ```bash
   make test
   ```

5. **Make your changes**

6. **Format and lint:**
   ```bash
   make fmt && make lint
   ```

7. **Run tests again:**
   ```bash
   make test
   ```

---

## 🔗 Related Files

- 📄 Full summary: `WORKSPACE_SETUP_COMPLETE.md`
- 🩺 Health checker: `workspace_doctor.sh`
- ⚙️ Project configs: `*/pyproject.toml`, `*/Makefile`

---

**Last Updated:** October 11, 2025  
**Python Version:** 3.11.13  
**Key Tools:** pytest 8.4.2, ruff 0.14.0, MLX 0.29.2

