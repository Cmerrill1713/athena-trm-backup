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

all: install preflight test demo
	@echo ""
	@echo "🎉 Orchestrator ready to use!"

clean:
	@rm -rf __pycache__ */__pycache__ */*/__pycache__
	@rm -rf .pytest_cache
	@rm -rf memory/*.db
	@echo "✅ Cleaned artifacts"
