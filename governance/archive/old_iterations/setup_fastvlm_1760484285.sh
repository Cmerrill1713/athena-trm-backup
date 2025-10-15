#!/usr/bin/env bash
# Setup FastVLM - clone, install, download models

set -euo pipefail

FASTVLM_DIR="${FASTVLM_DIR:-$(pwd)/ml-fastvlm}"
MODEL_VARIANT="${MODEL_VARIANT:-1.5b}"  # 0.5b, 1.5b, or 7b

echo "🚀 FastVLM Setup Script"
echo "======================="
echo ""
echo "📁 Install directory: $FASTVLM_DIR"
echo "🤖 Model variant: $MODEL_VARIANT"
echo ""

# Step 1: Clone repository
if [ -d "$FASTVLM_DIR" ]; then
    echo "✅ FastVLM repository already exists"
else
    echo "📥 Cloning Apple FastVLM repository..."
    git clone https://github.com/apple/ml-fastvlm.git "$FASTVLM_DIR"
    echo "✅ Repository cloned"
fi

cd "$FASTVLM_DIR"

# Step 2: Create virtual environment
if [ -d ".venv" ]; then
    echo "✅ Virtual environment already exists"
else
    echo "🐍 Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
fi

echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Step 3: Install FastVLM
echo "📦 Installing FastVLM package..."
pip install -q -e .
echo "✅ FastVLM installed"

# Step 4: Download model checkpoints
if [ -f "get_models.sh" ]; then
    echo "📥 Downloading model checkpoints (this may take a while)..."
    echo "   Variant: fastvlm_${MODEL_VARIANT}_stage3"
    bash get_models.sh
    echo "✅ Models downloaded"
else
    echo "⚠️  get_models.sh not found - you may need to download models manually"
    echo "   See: https://github.com/apple/ml-fastvlm#model-zoo"
fi

# Step 5: Quick test
echo ""
echo "🧪 Running quick smoke test..."
if [ -d "checkpoints/fastvlm_${MODEL_VARIANT}_stage3" ]; then
    echo "✅ Model checkpoint found: checkpoints/fastvlm_${MODEL_VARIANT}_stage3"
    
    # Test if predict.py exists
    if [ -f "predict.py" ]; then
        echo "✅ predict.py found"
    else
        echo "❌ predict.py not found"
        exit 1
    fi
else
    echo "⚠️  Model checkpoint not found"
    echo "   Expected: checkpoints/fastvlm_${MODEL_VARIANT}_stage3"
    echo "   Available checkpoints:"
    ls -1 checkpoints/ 2>/dev/null || echo "   (none)"
fi

echo ""
echo "✅ FastVLM setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Export environment variables:"
echo "      export FASTVLM_ROOT='$FASTVLM_DIR'"
echo "      export FASTVLM_MODEL='checkpoints/fastvlm_${MODEL_VARIANT}_stage3'"
echo ""
echo "   2. Start the server:"
echo "      cd $(dirname $(dirname $(realpath $0)))"
echo "      python3 fastvlm_server.py"
echo ""
echo "   3. Test the endpoint:"
echo "      curl http://127.0.0.1:8811/health"
echo ""

