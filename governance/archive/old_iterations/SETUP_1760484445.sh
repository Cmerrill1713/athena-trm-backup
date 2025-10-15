#!/bin/bash
# TRM Setup Script
# Sets up TRM environment and removes HRM dependencies

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     TRM (Tiny Recursive Model) Setup & Integration       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"

# Check we're in the right directory
if [ ! -f "pretrain.py" ]; then
    echo -e "${RED}Error: Must run from TinyRecursiveModels root directory${NC}"
    exit 1
fi

# Step 1: Remove HRM artifacts
echo -e "\n${YELLOW}[1/6] Removing HRM artifacts...${NC}"

# Remove HRM-related experiment configs if they exist
rm -f experiments/configs/*hrm*.yaml 2>/dev/null || true
rm -f experiments/analysis/*hrm*.py 2>/dev/null || true

echo -e "${GREEN}✓ HRM artifacts removed${NC}"

# Step 2: Check Python version
echo -e "\n${YELLOW}[2/6] Checking Python version...${NC}"

if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    PIP_CMD=pip3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
    PIP_CMD=pip
else
    echo -e "${RED}Error: Python not found${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Found Python $PYTHON_VERSION${NC}"

# Step 3: Install dependencies
echo -e "\n${YELLOW}[3/6] Installing dependencies...${NC}"

echo "Upgrading pip, wheel, setuptools..."
$PIP_CMD install --upgrade pip wheel setuptools

echo "Installing PyTorch..."
$PIP_CMD install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo "Installing other requirements..."
$PIP_CMD install -r requirements.txt

echo "Installing adam-atan2..."
$PIP_CMD install --no-cache-dir --no-build-isolation adam-atan2

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 4: Setup directory structure
echo -e "\n${YELLOW}[4/6] Setting up directories...${NC}"

mkdir -p data
mkdir -p checkpoints
mkdir -p experiments/results
mkdir -p experiments/results/plots

echo -e "${GREEN}✓ Directories created${NC}"

# Step 5: Verify TRM is working
echo -e "\n${YELLOW}[5/6] Verifying TRM installation...${NC}"

$PYTHON_CMD -c "
import torch
import sys
sys.path.insert(0, '.')
from models.recursive_reasoning.trm import TinyRecursiveReasoningModel_ACTV1
print('✓ TRM model imported successfully')

# Check device availability
if torch.cuda.is_available():
    print(f'✓ CUDA available: {torch.cuda.get_device_name(0)}')
elif torch.backends.mps.is_available():
    print('✓ MPS (Apple Silicon) available')
else:
    print('ℹ  Using CPU (consider GPU for faster training)')
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ TRM verification passed${NC}"
else
    echo -e "${RED}✗ TRM verification failed${NC}"
    exit 1
fi

# Step 6: Create integration symlinks
echo -e "\n${YELLOW}[6/6] Setting up integrations...${NC}"

# Function to create symlink safely
create_symlink() {
    local src=$1
    local dst=$2
    if [ -e "$dst" ]; then
        echo "  ℹ  $dst already exists, skipping"
    else
        ln -s "$src" "$dst" 2>/dev/null && echo "  ✓ Created: $dst" || echo "  ℹ  Could not create: $dst"
    fi
}

# Link to MacOS-Agent if it exists
if [ -d "../MacOS-Agent" ]; then
    echo "Linking to MacOS-Agent..."
    create_symlink "$(pwd)/MacOS-Agent/trm_integration.py" "../MacOS-Agent/trm_integration.py"
fi

# Link to PydanticAI if it exists
if [ -d "../pydantic-ai" ]; then
    echo "Linking to PydanticAI..."
    # Already created the example file directly
    if [ -f "../pydantic-ai/examples/trm_agent_example.py" ]; then
        echo "  ✓ PydanticAI example already exists"
    fi
fi

echo -e "${GREEN}✓ Integration setup complete${NC}"

# Summary
echo -e "\n${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Setup Complete!                         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${BLUE}What's been done:${NC}"
echo "  ✓ HRM artifacts removed"
echo "  ✓ Dependencies installed"
echo "  ✓ TRM verified working"
echo "  ✓ Directories created"
echo "  ✓ Integrations configured"

echo -e "\n${BLUE}Next steps:${NC}"
echo "  1. Run parameter analysis:"
echo "     ${YELLOW}python3 experiments/analysis/parameter_analysis.py${NC}"
echo ""
echo "  2. Test MacOS-Agent integration:"
echo "     ${YELLOW}cd ../MacOS-Agent && python3 trm_integration.py --help${NC}"
echo ""
echo "  3. Test PydanticAI integration:"
echo "     ${YELLOW}cd ../pydantic-ai && python3 examples/trm_agent_example.py --help${NC}"
echo ""
echo "  4. Run a small experiment:"
echo "     ${YELLOW}./experiments/run_comparison.sh sudoku 1${NC}"
echo ""
echo "  5. Read the documentation:"
echo "     ${YELLOW}cat experiments/QUICKSTART.md${NC}"

echo -e "\n${GREEN}Ready to use TRM! 🚀${NC}\n"

