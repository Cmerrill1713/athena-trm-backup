# Quick Start Guide: TRM vs HRM Experiments

This guide will help you quickly get started with comparing TRM and HRM.

## Prerequisites

1. **GPU Required**: At least 1 GPU with 24GB+ VRAM (L40S, A100, H100)
2. **CUDA**: Version 12.0 or later
3. **Python**: 3.10+

## Installation

```bash
cd /Users/christianmerrill/Documents/GitHub/TinyRecursiveModels

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Mac/Linux

# Install dependencies
pip install --upgrade pip wheel setuptools
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
pip install --no-cache-dir --no-build-isolation adam-atan2

# Login to wandb (optional, for experiment tracking)
wandb login
```

## Quick Test (5 minutes)

Run parameter analysis to understand the architectures:

```bash
cd experiments/analysis
python parameter_analysis.py
```

This will show you:
- Parameter counts for TRM vs HRM
- Computational complexity comparison
- Memory requirements
- Key architectural differences

## Small Experiment (12-24 hours)

Run a small-scale comparison on Sudoku:

```bash
# Prepare data
python dataset/build_sudoku_dataset.py \
  --output-dir data/sudoku-extreme-1k-aug-1000 \
  --subsample-size 1000 \
  --num-aug 1000

# Run comparison
./experiments/run_comparison.sh sudoku 1
```

This will:
1. Train TRM on Sudoku (~12 hours on 1 L40S)
2. Train HRM on Sudoku (~12 hours on 1 L40S)
3. Save checkpoints and logs

## Medium Experiment (24-48 hours)

Run on Maze tasks (requires 4 GPUs):

```bash
# Prepare data
python dataset/build_maze_dataset.py

# Run comparison
./experiments/run_comparison.sh maze 4
```

## Full Experiment (3-7 days)

Run on ARC-AGI-1 (requires 4 H100 GPUs):

```bash
# Prepare data
python -m dataset.build_arc_dataset \
  --input-file-prefix kaggle/combined/arc-agi \
  --output-dir data/arc1concept-aug-1000 \
  --subsets training evaluation concept \
  --test-set-name evaluation

# Run comparison (will take ~3 days per model)
./experiments/run_comparison.sh arc1 4
```

## Analyzing Results

After experiments complete:

```bash
# Compare training metrics
cd experiments/analysis
python compare_results.py

# This will:
# 1. Load metrics from both experiments
# 2. Generate comparison plots
# 3. Create summary report in experiments/results/
```

## Manual Experiment

If you want more control, run experiments manually:

```bash
# TRM on Sudoku
python pretrain.py \
  arch=trm \
  data_paths="[data/sudoku-extreme-1k-aug-1000]" \
  evaluators="[]" \
  epochs=10000 \
  eval_interval=2000 \
  arch.L_layers=2 \
  arch.H_cycles=3 \
  arch.L_cycles=6 \
  +run_name="my_trm_experiment" \
  ema=True

# HRM on Sudoku  
python pretrain.py \
  arch=hrm \
  data_paths="[data/sudoku-extreme-1k-aug-1000]" \
  evaluators="[]" \
  epochs=10000 \
  eval_interval=2000 \
  arch.H_layers=4 \
  arch.L_layers=4 \
  arch.H_cycles=2 \
  arch.L_cycles=2 \
  +run_name="my_hrm_experiment" \
  ema=True
```

## Ablation Studies

Run systematic ablations to understand components:

```bash
cd experiments/analysis

# Test effect of cycles
python ablation_study.py cycles

# Test effect of layers
python ablation_study.py layers

# Compare architectures
python ablation_study.py arch

# Run all ablations (takes a long time!)
python ablation_study.py all
```

## Monitoring Experiments

### Using wandb (recommended)

1. Log in to https://wandb.ai
2. Navigate to your project
3. View real-time training curves, metrics, and system usage

### Using checkpoints

```bash
# View saved checkpoints
ls checkpoints/

# Load and inspect checkpoint
python -c "
import torch
state = torch.load('checkpoints/YOUR_RUN/step_10000', map_location='cpu')
print('Keys:', state.keys())
print('Parameters:', sum(p.numel() for p in state.values()))
"
```

## Common Issues

### Out of Memory

- Reduce `global_batch_size` in config
- Use gradient checkpointing
- Use fewer GPUs with smaller batch per GPU

### Slow Training

- Ensure CUDA is properly installed
- Use multiple GPUs: `torchrun --nproc-per-node 4`
- Check GPU utilization: `nvidia-smi -l 1`

### Data Not Found

Make sure to run dataset preparation scripts:
```bash
python dataset/build_sudoku_dataset.py --output-dir data/sudoku-extreme-1k-aug-1000 --subsample-size 1000 --num-aug 1000
```

## Expected Results

Based on the paper:

### Sudoku (1000 examples)
- **TRM**: Near 100% accuracy after 50k epochs
- **HRM**: Similar performance, more parameters

### ARC-AGI-1
- **TRM**: ~45% accuracy (paper result)
- **HRM**: ~40% accuracy (baseline)

### ARC-AGI-2
- **TRM**: ~8% accuracy (paper result)
- **HRM**: Lower baseline

## Next Steps

1. **Read the paper**: [Less is More: Recursive Reasoning with Tiny Networks](https://arxiv.org/abs/2510.04871)
2. **Explore configs**: Check `config/arch/` for different architectures
3. **Modify experiments**: Edit experiment scripts in `experiments/`
4. **Share results**: Contribute findings back to the community

## Getting Help

- Review `experiments/README.md` for detailed documentation
- Check existing issues on GitHub
- Run parameter analysis to understand architectures
- Start with small experiments before scaling up

## Resource Planning

| Experiment | GPUs | Time | VRAM per GPU |
|------------|------|------|--------------|
| Parameter Analysis | 1 | 5 min | 2GB |
| Sudoku (small) | 1 | 12-24 hr | 24GB |
| Maze | 4 | 24-48 hr | 24GB |
| ARC-AGI-1 | 4 | 3-7 days | 40GB |
| ARC-AGI-2 | 4 | 3-7 days | 40GB |

Plan accordingly!

