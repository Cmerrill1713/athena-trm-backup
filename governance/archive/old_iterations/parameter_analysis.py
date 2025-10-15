#!/usr/bin/env python3
"""
Parameter Analysis Script for TRM vs HRM

Analyzes and compares the parameter counts and computational complexity
of TRM and HRM architectures.
"""

import torch
from typing import Dict, Any
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from models.recursive_reasoning.trm import TinyRecursiveReasoningModel_ACTV1, TinyRecursiveReasoningModel_ACTV1Config
from models.recursive_reasoning.hrm import HierarchicalReasoningModel_ACTV1, HierarchicalReasoningModel_ACTV1Config


def count_parameters(model: torch.nn.Module) -> Dict[str, int]:
    """Count parameters in a model."""
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    # Break down by component
    component_params = {}
    for name, module in model.named_modules():
        if len(list(module.children())) == 0:  # Leaf module
            params = sum(p.numel() for p in module.parameters())
            if params > 0:
                component_params[name] = params
    
    return {
        'total': total_params,
        'trainable': trainable_params,
        'components': component_params
    }


def compute_flops(model_type: str, config: Dict[str, Any]) -> Dict[str, float]:
    """
    Estimate FLOPs for forward pass.
    
    Simplified estimation based on:
    - Attention: 2 * L^2 * d (QK^T + softmax*V)
    - FFN: 2 * L * d * (expansion * d)
    """
    L = config['seq_len']
    d = config['hidden_size']
    e = config['expansion']
    
    if model_type == 'trm':
        # TRM: Uses L_level for both H and L updates
        L_layers = config['L_layers']
        H_cycles = config['H_cycles']
        L_cycles = config['L_cycles']
        
        # Per layer: attention + FFN
        flops_per_layer = 2 * L * L * d + 2 * L * d * (e * d)
        
        # Total iterations: H_cycles * (L_cycles + 1)
        # L_cycles for z_L updates, 1 for z_H update per H_cycle
        total_iterations = H_cycles * (L_cycles + 1)
        
        total_flops = total_iterations * L_layers * flops_per_layer
        
    else:  # hrm
        # HRM: Separate H_level and L_level
        H_layers = config['H_layers']
        L_layers = config['L_layers']
        H_cycles = config['H_cycles']
        L_cycles = config['L_cycles']
        
        flops_per_layer = 2 * L * L * d + 2 * L * d * (e * d)
        
        # Total: H_cycles * (L_cycles * L_layers + H_layers)
        L_iterations = H_cycles * L_cycles * L_layers
        H_iterations = H_cycles * H_layers
        
        total_flops = (L_iterations + H_iterations) * flops_per_layer
    
    return {
        'total_flops': total_flops,
        'flops_per_layer': flops_per_layer,
        'gflops': total_flops / 1e9
    }


def compare_architectures():
    """Compare TRM and HRM architectures."""
    
    # Common config
    base_config = {
        'batch_size': 768,
        'seq_len': 900,  # 30x30 grid
        'vocab_size': 16,
        'num_puzzle_identifiers': 1000,
        'hidden_size': 512,
        'expansion': 4,
        'num_heads': 8,
        'pos_encodings': 'rope',
        'halt_max_steps': 16,
        'halt_exploration_prob': 0.1,
        'puzzle_emb_ndim': 512,
    }
    
    # TRM config
    trm_config = {
        **base_config,
        'H_layers': 0,  # Uses L_level
        'L_layers': 2,
        'H_cycles': 3,
        'L_cycles': 6,
        'mlp_t': False,
        'puzzle_emb_len': 16,
        'no_ACT_continue': True,
    }
    
    # HRM config
    hrm_config = {
        **base_config,
        'H_layers': 4,
        'L_layers': 4,
        'H_cycles': 2,
        'L_cycles': 2,
        'mlp_t': False,
    }
    
    print("=" * 80)
    print("TRM vs HRM Architecture Comparison")
    print("=" * 80)
    
    # Create models
    print("\nCreating models...")
    with torch.device('cuda'):
        trm_model = TinyRecursiveReasoningModel_ACTV1(trm_config)
        hrm_model = HierarchicalReasoningModel_ACTV1(hrm_config)
    
    # Parameter analysis
    print("\n" + "=" * 80)
    print("PARAMETER ANALYSIS")
    print("=" * 80)
    
    trm_params = count_parameters(trm_model)
    hrm_params = count_parameters(hrm_model)
    
    print(f"\nTRM:")
    print(f"  Total Parameters:     {trm_params['total']:,}")
    print(f"  Trainable Parameters: {trm_params['trainable']:,}")
    
    print(f"\nHRM:")
    print(f"  Total Parameters:     {hrm_params['total']:,}")
    print(f"  Trainable Parameters: {hrm_params['trainable']:,}")
    
    print(f"\nParameter Ratio (HRM/TRM): {hrm_params['total'] / trm_params['total']:.2f}x")
    print(f"Parameter Difference: {hrm_params['total'] - trm_params['total']:,}")
    
    # Computational complexity
    print("\n" + "=" * 80)
    print("COMPUTATIONAL COMPLEXITY")
    print("=" * 80)
    
    trm_flops = compute_flops('trm', trm_config)
    hrm_flops = compute_flops('hrm', hrm_config)
    
    print(f"\nTRM:")
    print(f"  Total FLOPs:    {trm_flops['gflops']:.2f} GFLOPs")
    print(f"  Configuration:  {trm_config['H_cycles']} H_cycles × {trm_config['L_cycles']} L_cycles")
    print(f"                  {trm_config['L_layers']} L_layers (shared for H and L)")
    
    print(f"\nHRM:")
    print(f"  Total FLOPs:    {hrm_flops['gflops']:.2f} GFLOPs")
    print(f"  Configuration:  {hrm_config['H_cycles']} H_cycles × {hrm_config['L_cycles']} L_cycles")
    print(f"                  {hrm_config['H_layers']} H_layers + {hrm_config['L_layers']} L_layers")
    
    print(f"\nFLOPs Ratio (HRM/TRM): {hrm_flops['gflops'] / trm_flops['gflops']:.2f}x")
    
    # Architecture differences
    print("\n" + "=" * 80)
    print("KEY ARCHITECTURAL DIFFERENCES")
    print("=" * 80)
    
    print("\n1. HIERARCHY DESIGN:")
    print("   TRM: Shared L_level module for both H and L updates")
    print("   HRM: Separate H_level and L_level modules")
    
    print("\n2. LAYER DISTRIBUTION:")
    print(f"   TRM: {trm_config['L_layers']} layers (shared)")
    print(f"   HRM: {hrm_config['H_layers']} H-layers + {hrm_config['L_layers']} L-layers")
    
    print("\n3. CYCLE PATTERN:")
    print(f"   TRM: {trm_config['H_cycles']} H_cycles × {trm_config['L_cycles']} L_cycles")
    print(f"        Total reasoning iterations: {trm_config['H_cycles'] * (trm_config['L_cycles'] + 1)}")
    print(f"   HRM: {hrm_config['H_cycles']} H_cycles × {hrm_config['L_cycles']} L_cycles")
    print(f"        Total reasoning iterations: {hrm_config['H_cycles'] * (hrm_config['L_cycles'] + 1)}")
    
    print("\n4. ACT HALTING:")
    print("   TRM: Simplified (no_ACT_continue=True)")
    print("   HRM: Standard Q-learning with halt/continue actions")
    
    print("\n5. GRADIENT FLOW:")
    print("   TRM: Gradient only on final H_cycle iteration")
    print("   HRM: Gradient only on final H_cycle iteration")
    
    # Memory estimation
    print("\n" + "=" * 80)
    print("MEMORY ESTIMATION (per batch)")
    print("=" * 80)
    
    batch_size = base_config['batch_size']
    seq_len = base_config['seq_len']
    hidden_size = base_config['hidden_size']
    bytes_per_param = 2  # bfloat16
    
    # Model parameters
    trm_param_memory = trm_params['total'] * bytes_per_param / (1024**2)
    hrm_param_memory = hrm_params['total'] * bytes_per_param / (1024**2)
    
    # Activations (rough estimate)
    activation_memory = batch_size * seq_len * hidden_size * bytes_per_param / (1024**2)
    
    print(f"\nTRM:")
    print(f"  Model Parameters: {trm_param_memory:.1f} MB")
    print(f"  Activations:      ~{activation_memory:.1f} MB")
    print(f"  Total (approx):   {trm_param_memory + activation_memory:.1f} MB")
    
    print(f"\nHRM:")
    print(f"  Model Parameters: {hrm_param_memory:.1f} MB")
    print(f"  Activations:      ~{activation_memory:.1f} MB")
    print(f"  Total (approx):   {hrm_param_memory + activation_memory:.1f} MB")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print("\nTRM Advantages:")
    print(f"  ✓ {((hrm_params['total'] - trm_params['total']) / hrm_params['total'] * 100):.1f}% fewer parameters")
    print(f"  ✓ Simpler architecture (shared hierarchy)")
    print(f"  ✓ Potentially easier to train")
    print(f"  ✓ More cycles for iterative refinement")
    
    print("\nHRM Advantages:")
    print(f"  ✓ Explicit hierarchy separation")
    print(f"  ✓ More expressive (separate H/L modules)")
    print(f"  ✓ Biologically motivated design")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    compare_architectures()

