# NeuroForge Orchestrator Makefile
# Agent-agnostic capability routing

PY=python3

.PHONY: install preflight test demo all clean help

help:
	@echo "NeuroForge Orchestrator - Capability-First Routing"
	@echo ""
	@echo "Targets:"
	@echo "  make install    - Install dependencies"
	@echo "  make preflight  - Run preflight checks"
	@echo "  make test       - Run test suite"
	@echo "  make demo       - Run demo execution"
	@echo "  make all        - Run everything"
	@echo "  make clean      - Clean artifacts"
	@echo ""

install:
	@echo "📦 Installing orchestrator dependencies..."
	@$(PY) -m pip install -q -r requirements.txt
	@echo "✅ Dependencies installed"

preflight:
	@bash preflight.sh

test:
	@echo "🧪 Running tests..."
	@$(PY) -m pytest tests/ -v
	@echo "✅ Tests passed"

demo:
	@echo "🎬 Running demo..."
	@$(PY) -c "from router import run_capability; import json; result = run_capability('summarize', {'id':'DEMO','subject':'Example','body':'Hello world'}, {'max_tokens':256}); print(json.dumps(result, indent=2, default=str))"

api:
	@echo "🚀 Starting API server on :8765..."
	@$(PY) -m uvicorn api:app --reload --port 8765

all: install preflight test demo
	@echo ""
	@echo "🎉 Orchestrator ready to use!"
	@echo ""
	@echo "Run 'make api' to start REST API on :8765"

rotate:
	@echo "🔄 Rotating telemetry..."
	@TELEMETRY_DB=./state/telemetry.sqlite DAYS_TO_KEEP=14 MAX_ROWS=50000 \
		python3 tools/telemetry_rotate.py

backup:
	@echo "🔐 Creating encrypted backup..."
	@BACKUP_PASSPHRASE="$(BACKUP_PASSPHRASE)" bash scripts/snapshot_backup.sh

restore:
	@echo "🔓 Restoring from backup..."
	@BACKUP_PASSPHRASE="$(BACKUP_PASSPHRASE)" bash scripts/snapshot_restore.sh "$(FILE)"

dmg-smoke:
	@echo "🧪 Running DMG smoke test..."
	@bash ci/dmg_smoke.sh

clean:
	@rm -rf __pycache__ */__pycache__ */*/__pycache__
	@rm -rf .pytest_cache
	@rm -rf state/
	@echo "✅ Cleaned artifacts"
