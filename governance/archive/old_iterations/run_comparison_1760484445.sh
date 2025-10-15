#!/bin/bash
# Run TRM experiments
# This script launches TRM training on various tasks

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}TRM Training Experiments${NC}"
echo -e "${GREEN}=====================================${NC}"

# Check if we're in the right directory
if [ ! -f "pretrain.py" ]; then
    echo -e "${RED}Error: Must run from TinyRecursiveModels root directory${NC}"
    exit 1
fi

# Parse command line arguments
TASK=${1:-"sudoku"}  # Default to sudoku if no argument
NUM_GPUS=${2:-1}     # Default to 1 GPU

echo -e "\n${YELLOW}Configuration:${NC}"
echo "  Task: $TASK"
echo "  GPUs: $NUM_GPUS"

# Check CUDA availability
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${RED}Error: nvidia-smi not found. CUDA required.${NC}"
    exit 1
fi

echo -e "\n${YELLOW}GPU Status:${NC}"
nvidia-smi --query-gpu=index,name,memory.total,memory.free --format=csv

# Function to run experiment
run_experiment() {
    local name=$1
    local arch=$2
    local data=$3
    local extra_args=$4
    
    echo -e "\n${GREEN}======================================${NC}"
    echo -e "${GREEN}Running: $name${NC}"
    echo -e "${GREEN}======================================${NC}"
    
    if [ "$NUM_GPUS" -gt 1 ]; then
        # Multi-GPU training
        torchrun --nproc-per-node $NUM_GPUS \
            --rdzv_backend=c10d \
            --rdzv_endpoint=localhost:0 \
            --nnodes=1 \
            pretrain.py \
            arch=$arch \
            data_paths="[$data]" \
            +run_name="${name}" \
            $extra_args
    else
        # Single GPU training
        python pretrain.py \
            arch=$arch \
            data_paths="[$data]" \
            +run_name="${name}" \
            $extra_args
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $name completed successfully${NC}"
    else
        echo -e "${RED}✗ $name failed${NC}"
        exit 1
    fi
}

# Run experiments based on task
case $TASK in
    "sudoku")
        echo -e "\n${YELLOW}Starting Sudoku experiments (small scale)${NC}"
        echo "Expected runtime: ~12 hours on 1 GPU"
        
        # Prepare data
        if [ ! -d "data/sudoku-extreme-1k-aug-1000" ]; then
            echo -e "${YELLOW}Preparing Sudoku dataset...${NC}"
            python dataset/build_sudoku_dataset.py \
                --output-dir data/sudoku-extreme-1k-aug-1000 \
                --subsample-size 1000 \
                --num-aug 1000
        fi
        
        # TRM on Sudoku
        run_experiment \
            "trm_sudoku_production" \
            "trm" \
            "data/sudoku-extreme-1k-aug-1000" \
            "evaluators='[]' epochs=50000 eval_interval=5000 \
             lr=1e-4 puzzle_emb_lr=1e-4 \
             weight_decay=1.0 puzzle_emb_weight_decay=1.0 \
             arch.L_layers=2 arch.H_cycles=3 arch.L_cycles=6 \
             arch.pos_encodings=none ema=True"
        ;;
        
    "maze")
        echo -e "\n${YELLOW}Starting Maze experiments (medium scale)${NC}"
        echo "Expected runtime: ~24 hours on 4 GPUs"
        
        # Prepare data
        if [ ! -d "data/maze-30x30-hard-1k" ]; then
            echo -e "${YELLOW}Preparing Maze dataset...${NC}"
            python dataset/build_maze_dataset.py
        fi
        
        # TRM on Maze
        run_experiment \
            "trm_maze_production" \
            "trm" \
            "data/maze-30x30-hard-1k" \
            "evaluators='[]' epochs=50000 eval_interval=5000 \
             lr=1e-4 puzzle_emb_lr=1e-4 \
             weight_decay=1.0 puzzle_emb_weight_decay=1.0 \
             arch.L_layers=2 arch.H_cycles=3 arch.L_cycles=4 \
             ema=True"
        ;;
        
    "arc1")
        echo -e "\n${YELLOW}Starting ARC-AGI-1 experiments (full scale)${NC}"
        echo "Expected runtime: ~3 days on 4 H100 GPUs"
        
        # Prepare data
        if [ ! -d "data/arc1concept-aug-1000" ]; then
            echo -e "${YELLOW}Preparing ARC-AGI-1 dataset...${NC}"
            python -m dataset.build_arc_dataset \
                --input-file-prefix kaggle/combined/arc-agi \
                --output-dir data/arc1concept-aug-1000 \
                --subsets training evaluation concept \
                --test-set-name evaluation
        fi
        
        # TRM on ARC-AGI-1 (45% accuracy target)
        run_experiment \
            "trm_arc1_production" \
            "trm" \
            "data/arc1concept-aug-1000" \
            "arch.L_layers=2 arch.H_cycles=3 arch.L_cycles=4 ema=True"
        ;;
        
    "arc2")
        echo -e "\n${YELLOW}Starting ARC-AGI-2 experiments (full scale)${NC}"
        echo "Expected runtime: ~3 days on 4 H100 GPUs"
        
        # Prepare data
        if [ ! -d "data/arc2concept-aug-1000" ]; then
            echo -e "${YELLOW}Preparing ARC-AGI-2 dataset...${NC}"
            python -m dataset.build_arc_dataset \
                --input-file-prefix kaggle/combined/arc-agi \
                --output-dir data/arc2concept-aug-1000 \
                --subsets training2 evaluation2 concept \
                --test-set-name evaluation2
        fi
        
        # TRM on ARC-AGI-2 (8% accuracy target)
        run_experiment \
            "trm_arc2_production" \
            "trm" \
            "data/arc2concept-aug-1000" \
            "arch.L_layers=2 arch.H_cycles=3 arch.L_cycles=4 ema=True"
        ;;
        
    "all")
        echo -e "\n${YELLOW}Running ALL experiments${NC}"
        echo -e "${RED}Warning: This will take weeks!${NC}"
        read -p "Are you sure? (yes/no) " -n 3 -r
        echo
        if [[ ! $REPLY =~ ^yes$ ]]; then
            echo "Cancelled."
            exit 1
        fi
        
        # Run all experiments sequentially
        bash $0 sudoku $NUM_GPUS
        bash $0 maze $NUM_GPUS
        bash $0 arc1 $NUM_GPUS
        bash $0 arc2 $NUM_GPUS
        ;;
        
    *)
        echo -e "${RED}Unknown task: $TASK${NC}"
        echo "Valid tasks: sudoku, maze, arc1, arc2, all"
        exit 1
        ;;
esac

echo -e "\n${GREEN}=====================================${NC}"
echo -e "${GREEN}All experiments completed!${NC}"
echo -e "${GREEN}=====================================${NC}"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Analyze results: python experiments/analysis/parameter_analysis.py"
echo "2. View training curves in wandb"
echo "3. Check checkpoints/ directory for saved models"
echo "4. Integrate with your projects:"
echo "   - MacOS-Agent: see ../MacOS-Agent/trm_integration.py"
echo "   - PydanticAI: see ../pydantic-ai/examples/trm_agent_example.py"

