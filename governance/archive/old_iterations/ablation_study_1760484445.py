#!/usr/bin/env python3
"""
Ablation Study for TRM vs HRM

Tests various architectural configurations to understand the contribution
of different components.
"""

import sys
import os
import json
from typing import Dict, List
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


def run_ablation_experiment(config: Dict, name: str):
    """Run a single ablation experiment."""
    
    print(f"\n{'='*80}")
    print(f"Running ablation: {name}")
    print(f"{'='*80}")
    print("Config:", json.dumps(config, indent=2))
    
    # Build command
    cmd = ['python', 'pretrain.py']
    
    # Add config parameters
    for key, value in config.items():
        if key.startswith('arch.'):
            cmd.append(f"{key}={value}")
        else:
            cmd.append(f"{key}={value}")
    
    # Add run name
    cmd.append(f"+run_name=ablation_{name}")
    
    print("\nCommand:", ' '.join(cmd))
    
    # Run experiment
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✓ {name} completed successfully")
        return True
    else:
        print(f"✗ {name} failed")
        print("Error:", result.stderr[:500])
        return False


def cycle_ablations():
    """Ablation study: effect of H_cycles and L_cycles."""
    
    print("\n" + "="*80)
    print("ABLATION STUDY: H_CYCLES AND L_CYCLES")
    print("="*80)
    print("\nTesting the effect of reasoning cycle counts...")
    
    base_config = {
        'arch': 'trm',
        'data_paths': '["data/sudoku-extreme-1k-aug-1000"]',
        'evaluators': '[]',
        'epochs': 10000,
        'eval_interval': 2000,
        'lr': 1e-4,
        'puzzle_emb_lr': 1e-4,
        'weight_decay': 1.0,
        'puzzle_emb_weight_decay': 1.0,
        'arch.L_layers': 2,
        'arch.pos_encodings': 'none',
        'ema': 'True',
    }
    
    # Test different cycle combinations
    cycle_configs = [
        {'arch.H_cycles': 1, 'arch.L_cycles': 1},  # Minimal
        {'arch.H_cycles': 2, 'arch.L_cycles': 2},  # HRM-like
        {'arch.H_cycles': 3, 'arch.L_cycles': 4},  # TRM default
        {'arch.H_cycles': 3, 'arch.L_cycles': 6},  # TRM extended
        {'arch.H_cycles': 4, 'arch.L_cycles': 4},  # Balanced high
        {'arch.H_cycles': 1, 'arch.L_cycles': 10}, # Many L cycles
        {'arch.H_cycles': 5, 'arch.L_cycles': 2},  # Many H cycles
    ]
    
    results = {}
    
    for cycles in cycle_configs:
        name = f"h{cycles['arch.H_cycles']}_l{cycles['arch.L_cycles']}"
        config = {**base_config, **cycles}
        
        success = run_ablation_experiment(config, f"cycles_{name}")
        results[name] = success
    
    print("\n" + "="*80)
    print("CYCLE ABLATION RESULTS")
    print("="*80)
    for name, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {name}")


def layer_ablations():
    """Ablation study: effect of layer counts."""
    
    print("\n" + "="*80)
    print("ABLATION STUDY: LAYER COUNTS")
    print("="*80)
    print("\nTesting the effect of layer depth...")
    
    base_config = {
        'arch': 'trm',
        'data_paths': '["data/sudoku-extreme-1k-aug-1000"]',
        'evaluators': '[]',
        'epochs': 10000,
        'eval_interval': 2000,
        'lr': 1e-4,
        'puzzle_emb_lr': 1e-4,
        'weight_decay': 1.0,
        'puzzle_emb_weight_decay': 1.0,
        'arch.H_cycles': 3,
        'arch.L_cycles': 6,
        'arch.pos_encodings': 'none',
        'ema': 'True',
    }
    
    # Test different layer counts
    layer_configs = [
        {'arch.L_layers': 1},   # Minimal
        {'arch.L_layers': 2},   # TRM default
        {'arch.L_layers': 4},   # HRM-like
        {'arch.L_layers': 6},   # Deep
        {'arch.L_layers': 8},   # Very deep
    ]
    
    results = {}
    
    for layers in layer_configs:
        name = f"l{layers['arch.L_layers']}"
        config = {**base_config, **layers}
        
        success = run_ablation_experiment(config, f"layers_{name}")
        results[name] = success
    
    print("\n" + "="*80)
    print("LAYER ABLATION RESULTS")
    print("="*80)
    for name, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {name}")


def architecture_ablations():
    """Ablation study: shared vs separate hierarchies."""
    
    print("\n" + "="*80)
    print("ABLATION STUDY: ARCHITECTURE VARIANTS")
    print("="*80)
    print("\nComparing shared (TRM) vs separate (HRM) hierarchies...")
    
    base_config = {
        'data_paths': '["data/sudoku-extreme-1k-aug-1000"]',
        'evaluators': '[]',
        'epochs': 10000,
        'eval_interval': 2000,
        'lr': 1e-4,
        'puzzle_emb_lr': 1e-4,
        'weight_decay': 1.0,
        'puzzle_emb_weight_decay': 1.0,
        'arch.pos_encodings': 'none',
        'ema': 'True',
    }
    
    # Test different architectures
    arch_configs = [
        {
            'arch': 'trm',
            'arch.L_layers': 2,
            'arch.H_cycles': 3,
            'arch.L_cycles': 6,
        },
        {
            'arch': 'hrm',
            'arch.H_layers': 2,
            'arch.L_layers': 2,
            'arch.H_cycles': 3,
            'arch.L_cycles': 6,
        },
        {
            'arch': 'hrm',
            'arch.H_layers': 4,
            'arch.L_layers': 4,
            'arch.H_cycles': 2,
            'arch.L_cycles': 2,
        },
    ]
    
    results = {}
    names = ['trm_baseline', 'hrm_matched_cycles', 'hrm_matched_layers']
    
    for name, arch in zip(names, arch_configs):
        config = {**base_config, **arch}
        
        success = run_ablation_experiment(config, f"arch_{name}")
        results[name] = success
    
    print("\n" + "="*80)
    print("ARCHITECTURE ABLATION RESULTS")
    print("="*80)
    for name, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {name}")


def mlp_vs_attention_ablations():
    """Ablation study: MLP vs Attention mechanisms."""
    
    print("\n" + "="*80)
    print("ABLATION STUDY: MLP VS ATTENTION")
    print("="*80)
    print("\nComparing MLP-based vs Attention-based reasoning...")
    
    base_config = {
        'arch': 'trm',
        'data_paths': '["data/sudoku-extreme-1k-aug-1000"]',
        'evaluators': '[]',
        'epochs': 10000,
        'eval_interval': 2000,
        'lr': 1e-4,
        'puzzle_emb_lr': 1e-4,
        'weight_decay': 1.0,
        'puzzle_emb_weight_decay': 1.0,
        'arch.L_layers': 2,
        'arch.H_cycles': 3,
        'arch.L_cycles': 6,
        'arch.pos_encodings': 'none',
        'ema': 'True',
    }
    
    # Test MLP vs Attention
    mechanism_configs = [
        {'arch.mlp_t': 'False'},  # Attention (default)
        {'arch.mlp_t': 'True'},   # MLP transpose
    ]
    
    results = {}
    
    for i, mechanism in enumerate(mechanism_configs):
        name = 'mlp' if mechanism['arch.mlp_t'] == 'True' else 'attention'
        config = {**base_config, **mechanism}
        
        success = run_ablation_experiment(config, f"mechanism_{name}")
        results[name] = success
    
    print("\n" + "="*80)
    print("MECHANISM ABLATION RESULTS")
    print("="*80)
    for name, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {name}")


def position_encoding_ablations():
    """Ablation study: effect of position encodings."""
    
    print("\n" + "="*80)
    print("ABLATION STUDY: POSITION ENCODINGS")
    print("="*80)
    print("\nTesting different position encoding strategies...")
    
    base_config = {
        'arch': 'trm',
        'data_paths': '["data/sudoku-extreme-1k-aug-1000"]',
        'evaluators': '[]',
        'epochs': 10000,
        'eval_interval': 2000,
        'lr': 1e-4,
        'puzzle_emb_lr': 1e-4,
        'weight_decay': 1.0,
        'puzzle_emb_weight_decay': 1.0,
        'arch.L_layers': 2,
        'arch.H_cycles': 3,
        'arch.L_cycles': 6,
        'ema': 'True',
    }
    
    # Test different position encodings
    pos_configs = [
        {'arch.pos_encodings': 'none'},     # No position encoding
        {'arch.pos_encodings': 'learned'},  # Learned embeddings
        {'arch.pos_encodings': 'rope'},     # Rotary position encoding
    ]
    
    results = {}
    
    for pos in pos_configs:
        name = pos['arch.pos_encodings']
        config = {**base_config, **pos}
        
        success = run_ablation_experiment(config, f"pos_{name}")
        results[name] = success
    
    print("\n" + "="*80)
    print("POSITION ENCODING ABLATION RESULTS")
    print("="*80)
    for name, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {name}")


def main():
    """Main ablation runner."""
    
    print("="*80)
    print("TRM vs HRM ABLATION STUDIES")
    print("="*80)
    print("\nThis script runs systematic ablation studies to understand")
    print("the contribution of different architectural components.")
    print("\nWARNING: This will run many experiments and take significant time!")
    
    if len(sys.argv) < 2:
        print("\nUsage: python ablation_study.py <study>")
        print("\nAvailable studies:")
        print("  cycles       - Test different H_cycles and L_cycles")
        print("  layers       - Test different layer depths")
        print("  arch         - Compare TRM vs HRM architectures")
        print("  mechanism    - Compare MLP vs Attention")
        print("  position     - Test position encoding strategies")
        print("  all          - Run all ablation studies")
        return
    
    study = sys.argv[1]
    
    if study == 'cycles':
        cycle_ablations()
    elif study == 'layers':
        layer_ablations()
    elif study == 'arch':
        architecture_ablations()
    elif study == 'mechanism':
        mlp_vs_attention_ablations()
    elif study == 'position':
        position_encoding_ablations()
    elif study == 'all':
        print("\nRunning ALL ablation studies...")
        print("This will take a very long time!")
        response = input("\nContinue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return
        
        cycle_ablations()
        layer_ablations()
        architecture_ablations()
        mlp_vs_attention_ablations()
        position_encoding_ablations()
    else:
        print(f"Unknown study: {study}")
        return
    
    print("\n" + "="*80)
    print("ABLATION STUDIES COMPLETE")
    print("="*80)
    print("\nAnalyze results with: python experiments/analysis/compare_results.py")


if __name__ == "__main__":
    main()

