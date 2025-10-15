#!/bin/bash
# DGM Quick Start Script
# Sets up and runs Darwin Gödel Machine with governance integration

set -e

echo "🧬 Darwin Gödel Machine - Quick Start"
echo "======================================"

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker"
    exit 1
fi

echo "✓ Python: $(python3 --version)"
echo "✓ Docker: $(docker --version)"

# Check API keys
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  ANTHROPIC_API_KEY not set"
    echo "   export ANTHROPIC_API_KEY='your-key'"
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set (optional, using Claude by default)"
fi

# Navigate to project root
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

echo ""
echo "📦 Setting up DGM environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "governance/research/dgm-upstream/venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv governance/research/dgm-upstream/venv
fi

# Activate venv
source governance/research/dgm-upstream/venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r governance/research/dgm-upstream/requirements.txt
pip install -q pyyaml prometheus-client

echo "✓ Dependencies installed"

# Validate constitutional policy
echo ""
echo "🛡️  Validating constitutional policy..."
python3 << 'PYEOF'
import yaml
with open('governance/legislative/self_modification_policy.yaml') as f:
    policy = yaml.safe_load(f)

constraints = policy['constraints']['execution']
mandatory = [c for c in constraints if c['enforcement'] == 'MANDATORY']

print(f"✓ {len(mandatory)} mandatory safety constraints active:")
for c in mandatory:
    print(f"  - {c['rule']}")

print(f"\n✓ Circuit breaker: {policy['guardrails']['evolution_limits']['circuit_breaker_failures']} failure limit")
PYEOF

# Show configuration
echo ""
echo "⚙️  Configuration:"
cat governance/research/dgm/config/dgm_config.yaml | grep -A3 "safety:" | head -4

echo ""
echo "======================================"
echo "🚀 Ready to run DGM!"
echo ""
echo "Options:"
echo "  1. Run pilot experiment (10 generations):"
echo "     python governance/research/dgm/experiments/experiment_runner.py \\"
echo "       governance/research/dgm/experiments/pilot_experiment.yaml"
echo ""
echo "  2. Run orchestrator directly (5 generations):"
echo "     python governance/executive/orchestration/dgm_orchestrator.py"
echo ""
echo "  3. Test verdict validator:"
echo "     python governance/judicial/evaluation/dgm_verdict_validator.py"
echo ""
echo "Select option (1-3) or press Enter to exit:"
read -r option

case $option in
    1)
        echo "🧪 Running pilot experiment..."
        python governance/research/dgm/experiments/experiment_runner.py \
          governance/research/dgm/experiments/pilot_experiment.yaml
        ;;
    2)
        echo "🎯 Running orchestrator..."
        python governance/executive/orchestration/dgm_orchestrator.py
        ;;
    3)
        echo "✅ Testing verdict validator..."
        python governance/judicial/evaluation/dgm_verdict_validator.py
        ;;
    *)
        echo "Exiting. Run this script again when ready."
        ;;
esac

echo ""
echo "✓ DGM session complete!"

