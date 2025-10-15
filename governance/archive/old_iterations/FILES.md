# MCP Store File Reference

Quick reference for all MCP Store files and their purposes.

## 📁 Core Service Files

```
services/mcp_store/
├── app.py                         # FastAPI application (main service)
├── mcp_server.py                  # MCP protocol wrapper
├── mcp_enhanced_server.js         # Enhanced JS MCP server with auto-logging
├── requirements.txt               # Python dependencies
└── Dockerfile                     # Production container build
```

## 📚 Documentation

```
services/mcp_store/
├── README.md                      # Complete API & usage documentation
├── QUICK_START.md                 # 5-minute setup guide
├── MIGRATION_GUIDE.md             # Integration patterns for all languages
└── FILES.md                       # This file
```

## 🔧 Setup & Testing

```
services/mcp_store/
├── init_weaviate_schema.sh        # One-time Weaviate schema setup
├── test_integration.sh            # End-to-end integration tests
└── .env.example                   # Environment variable template
```

## 🐳 Infrastructure

```
AI-Projects/universal-ai-tools/
├── docker-compose.mcp-store.yml   # MCP Store + dependencies
├── mcp-config.json                # Local MCP server config
└── mcp-config-docker.json         # Docker MCP server config
```

## 🛠️ Build & Deploy

```
Repository Root/
├── Makefile                       # Added mcp-store-* targets
├── MCP_STORE_COMPLETE.md          # Implementation summary
└── scripts/
    └── validate_with_mcp_store.sh # Example validation script
```

## 🔑 Key Files by Use Case

### Just Getting Started
1. **QUICK_START.md** - Follow this first
2. **docker-compose.mcp-store.yml** - Deploy config
3. **init_weaviate_schema.sh** - Run once for setup

### Integrating Your Services
1. **MIGRATION_GUIDE.md** - Language-specific examples
2. **mcp_enhanced_server.js** - Drop-in wrapper
3. **validate_with_mcp_store.sh** - Shell script example

### Understanding the System
1. **README.md** - Complete documentation
2. **app.py** - Service implementation
3. **MCP_STORE_COMPLETE.md** - Architecture overview

### Deployment & Operations
1. **Dockerfile** - Container build
2. **docker-compose.mcp-store.yml** - Orchestration
3. **Makefile** - Operational commands

### Testing & Validation
1. **test_integration.sh** - Full test suite
2. **validate_with_mcp_store.sh** - Real-world usage
3. **init_weaviate_schema.sh** - Schema verification

## 📊 File Sizes

```bash
$ du -sh services/mcp_store/*
 12K    app.py
4.0K    Dockerfile
 12K    MIGRATION_GUIDE.md
 12K    mcp_enhanced_server.js
4.0K    mcp_server.py
8.0K    QUICK_START.md
8.0K    README.md
4.0K    requirements.txt
4.0K    init_weaviate_schema.sh
4.0K    test_integration.sh
```

## 🔗 Dependencies

### Python (`requirements.txt`)
- fastapi==0.115.0
- uvicorn==0.30.6
- psycopg[binary]==3.2.1
- weaviate-client==4.7.3
- redis==5.0.7
- python-dateutil==2.9.0.post0
- mcp==0.1.0
- requests==2.32.3

### Infrastructure (Docker)
- postgres:15-alpine
- redis:7-alpine
- semitechnologies/weaviate:latest
- python:3.11-slim (base image)

## 🎯 Quick Commands

```bash
# View all files
ls -lah services/mcp_store/

# Check file sizes
du -sh services/mcp_store/*

# Search for usage
grep -r "MCPSTORE" services/mcp_store/

# Count lines
wc -l services/mcp_store/*.{py,js,sh,md}

# View structure
tree services/mcp_store/
```

## 📝 File Purposes

| File | Purpose | When to Use |
|------|---------|-------------|
| `app.py` | Core FastAPI service | Modify to add features |
| `mcp_server.py` | MCP protocol wrapper | Use from orchestrator |
| `mcp_enhanced_server.js` | Auto-logging wrapper | Replace existing MCP server |
| `requirements.txt` | Python deps | Update dependencies |
| `Dockerfile` | Container build | Production deployment |
| `README.md` | Full docs | Learn API & features |
| `QUICK_START.md` | Setup guide | First-time setup |
| `MIGRATION_GUIDE.md` | Integration | Add to your services |
| `init_weaviate_schema.sh` | Schema setup | One-time initialization |
| `test_integration.sh` | Test suite | Verify installation |
| `.env.example` | Config template | Set environment vars |

## 🔍 Finding Code

### Search for API endpoints
```bash
grep -n "^@app\." services/mcp_store/app.py
```

### Find all MCP tools
```bash
grep -n "@tool()" services/mcp_store/mcp_server.py
```

### View all Make targets
```bash
grep "^mcp-store-" Makefile
```

## 📦 What Each File Does

### `app.py` - The Core Service
- FastAPI application on port 8411
- `/health` - Health check endpoint
- `POST /v1/store/results` - Write validation results
- `GET /v1/store/results/{id}` - Retrieve by ID
- `GET /v1/store/results` - List with filters
- Connects to Postgres, Weaviate, Redis

### `mcp_server.py` - MCP Wrapper
- Exposes 4 MCP tools:
  - `store_write` - Write result
  - `store_get` - Get by ID
  - `store_list` - List with filters
  - `store_health` - Health check
- Calls HTTP API under the hood

### `mcp_enhanced_server.js` - Enhanced Wrapper
- Wraps existing test tools
- Auto-stores results in MCP Store
- Adds latency measurements
- Tools: `test_llm_router`, `test_hrm_mlx`, `test_fastvlm`, `test_go_service`

### `init_weaviate_schema.sh` - Schema Setup
- Creates `ValidationResult` class in Weaviate
- Defines 7 properties (agent, service, status, etc.)
- Idempotent (safe to run multiple times)

### `test_integration.sh` - Test Suite
- Writes PASS and FAIL results
- Retrieves by ID
- Lists with filters
- Verifies all endpoints
- Exit code 0 = success

## 🚀 Getting Started Checklist

- [ ] Read `QUICK_START.md`
- [ ] Run `make mcp-store-full`
- [ ] Run `make mcp-store-init-schema`
- [ ] Run `./test_integration.sh`
- [ ] Read `MIGRATION_GUIDE.md`
- [ ] Try example integrations
- [ ] Update your validation scripts

## 📞 Where to Look

| Question | File |
|----------|------|
| How do I start it? | `QUICK_START.md` |
| What's the API? | `README.md` |
| How do I integrate? | `MIGRATION_GUIDE.md` |
| Is it working? | `test_integration.sh` |
| How do I deploy? | `docker-compose.mcp-store.yml` |
| What's the architecture? | `MCP_STORE_COMPLETE.md` |

---

**Location:** `/Users/christianmerrill/Documents/GitHub/AI-Projects/universal-ai-tools/services/mcp_store/`  
**Owner:** NeuroForge Platform  
**Status:** ✅ Complete & Ready

