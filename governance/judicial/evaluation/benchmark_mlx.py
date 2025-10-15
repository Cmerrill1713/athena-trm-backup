#!/usr/bin/env python3
"""
TRM Benchmark: PyTorch vs MLX

Comprehensive performance comparison on Apple Silicon.
"""

import os
import time
from typing import Dict, List

import numpy as np
import psutil

# Suppress warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

print("="*80)
print("TRM Benchmark: PyTorch vs MLX on Apple Silicon")
print("="*80)

# Test configurations
configs = [
    {
        'name': 'Tiny (128 hidden)',
        'hidden_size': 128,
        'seq_len': 64,
        'vocab_size': 1000,
    },
    {
        'name': 'Small (256 hidden)',
        'hidden_size': 256,
        'seq_len': 128,
        'vocab_size': 5000,
    },
    {
        'name': 'Medium (512 hidden)',
        'hidden_size': 512,
        'seq_len': 256,
        'vocab_size': 10000,
    },
]

results = []


def get_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


def benchmark_pytorch(config: Dict, num_iterations: int = 10):
    """Benchmark PyTorch version."""
    print(f"\n{'='*80}")
    print(f"PyTorch: {config['name']}")
    print(f"{'='*80}")

    try:
        import torch

        from models.recursive_reasoning.trm import TinyRecursiveReasoningModel_ACTV1

        # Create config
        model_config = {
            'batch_size': 1,
            'seq_len': config['seq_len'],
            'vocab_size': config['vocab_size'],
            'num_puzzle_identifiers': 100,
            'hidden_size': config['hidden_size'],
            'expansion': 4,
            'num_heads': max(1, config['hidden_size'] // 64),
            'H_cycles': 1,
            'L_cycles': 2,
            'L_layers': 2,
            'H_layers': 0,
            'pos_encodings': 'rope',
            'halt_max_steps': 3,
            'halt_exploration_prob': 0.0,
            'puzzle_emb_ndim': config['hidden_size'],
            'mlp_t': False,
            'puzzle_emb_len': 16,
            'no_ACT_continue': True,
        }

        # Determine device
        if torch.backends.mps.is_available():
            device = torch.device('mps')
            device_name = "Apple MPS"
        elif torch.cuda.is_available():
            device = torch.device('cuda')
            device_name = f"CUDA ({torch.cuda.get_device_name(0)})"
        else:
            device = torch.device('cpu')
            device_name = "CPU"

        print(f"Device: {device_name}")

        # Create model
        print("Creating model...")
        mem_before = get_memory_usage()

        model = TinyRecursiveReasoningModel_ACTV1(model_config)
        model.to(device)
        model.eval()

        mem_after = get_memory_usage()
        mem_usage = mem_after - mem_before

        # Count parameters
        params = sum(p.numel() for p in model.parameters())
        print(f"Parameters: {params:,}")
        print(f"Memory: {mem_usage:.1f} MB")

        # Create dummy input
        inputs = {
            'inputs': torch.randint(0, config['vocab_size'], (1, config['seq_len'])).to(device),
            'puzzle_identifiers': torch.tensor([0]).to(device),
        }

        # Warm-up
        print("Warming up...")
        with torch.no_grad():
            carry = model.initial_carry(inputs)
            for _ in range(3):
                carry, outputs = model(carry, inputs)

        # Benchmark
        print(f"Benchmarking ({num_iterations} iterations)...")
        latencies = []

        with torch.no_grad():
            for i in range(num_iterations):
                carry = model.initial_carry(inputs)

                start = time.time()
                for _ in range(3):  # 3 reasoning steps
                    carry, outputs = model(carry, inputs)

                # Sync if using GPU
                if device.type in ['cuda', 'mps']:
                    if device.type == 'cuda':
                        torch.cuda.synchronize()
                    elif device.type == 'mps':
                        torch.mps.synchronize()

                latency = (time.time() - start) * 1000
                latencies.append(latency)

                if i == 0:
                    print(f"  First run (cold): {latency:.1f}ms")

        # Statistics
        latencies = latencies[1:]  # Remove first (cold start)
        mean_latency = np.mean(latencies)
        std_latency = np.std(latencies)
        min_latency = np.min(latencies)
        max_latency = np.max(latencies)

        print("\nResults:")
        print(f"  Mean: {mean_latency:.1f}ms ± {std_latency:.1f}ms")
        print(f"  Min:  {min_latency:.1f}ms")
        print(f"  Max:  {max_latency:.1f}ms")

        return {
            'framework': 'PyTorch',
            'device': device_name,
            'config': config['name'],
            'params': params,
            'memory_mb': mem_usage,
            'mean_latency_ms': mean_latency,
            'std_latency_ms': std_latency,
            'min_latency_ms': min_latency,
            'max_latency_ms': max_latency,
        }

    except Exception as e:
        print(f"❌ PyTorch benchmark failed: {e}")
        return None


def benchmark_mlx(config: Dict, num_iterations: int = 10):
    """Benchmark MLX version."""
    print(f"\n{'='*80}")
    print(f"MLX: {config['name']}")
    print(f"{'='*80}")

    try:
        import mlx.core as mx

        from models.recursive_reasoning.trm_mlx import TRMMLX, count_parameters

        # Create config
        model_config = {
            'batch_size': 1,
            'seq_len': config['seq_len'],
            'vocab_size': config['vocab_size'],
            'num_puzzle_identifiers': 100,
            'hidden_size': config['hidden_size'],
            'expansion': 4,
            'num_heads': max(1, config['hidden_size'] // 64),
            'H_cycles': 1,
            'L_cycles': 2,
            'L_layers': 2,
            'pos_encodings': 'rope',
            'halt_max_steps': 3,
            'puzzle_emb_ndim': config['hidden_size'],
        }

        print("Device: Apple Silicon (MLX)")

        # Create model
        print("Creating model...")
        mem_before = get_memory_usage()

        model = TRMMLX(model_config)

        mem_after = get_memory_usage()
        mem_usage = mem_after - mem_before

        # Count parameters
        params = count_parameters(model)
        print(f"Parameters: {params:,}")
        print(f"Memory: {mem_usage:.1f} MB")

        # Create dummy input
        inputs = mx.random.randint(0, config['vocab_size'], (1, config['seq_len']))
        puzzle_ids = mx.array([0])

        # Warm-up
        print("Warming up...")
        for _ in range(3):
            outputs = model(inputs, puzzle_ids, max_steps=3)
            mx.eval(outputs['logits'])

        # Benchmark
        print(f"Benchmarking ({num_iterations} iterations)...")
        latencies = []

        for i in range(num_iterations):
            start = time.time()
            outputs = model(inputs, puzzle_ids, max_steps=3)
            mx.eval(outputs['logits'])  # Force evaluation
            latency = (time.time() - start) * 1000
            latencies.append(latency)

            if i == 0:
                print(f"  First run (cold): {latency:.1f}ms")

        # Statistics
        latencies = latencies[1:]  # Remove first (cold start)
        mean_latency = np.mean(latencies)
        std_latency = np.std(latencies)
        min_latency = np.min(latencies)
        max_latency = np.max(latencies)

        print("\nResults:")
        print(f"  Mean: {mean_latency:.1f}ms ± {std_latency:.1f}ms")
        print(f"  Min:  {min_latency:.1f}ms")
        print(f"  Max:  {max_latency:.1f}ms")

        return {
            'framework': 'MLX',
            'device': 'Apple Silicon',
            'config': config['name'],
            'params': params,
            'memory_mb': mem_usage,
            'mean_latency_ms': mean_latency,
            'std_latency_ms': std_latency,
            'min_latency_ms': min_latency,
            'max_latency_ms': max_latency,
        }

    except Exception as e:
        print(f"❌ MLX benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def print_comparison_table(results: List[Dict]):
    """Print comparison table."""
    print("\n" + "="*80)
    print("BENCHMARK RESULTS SUMMARY")
    print("="*80)

    # Group by config
    configs_map = {}
    for r in results:
        if r:
            config_name = r['config']
            if config_name not in configs_map:
                configs_map[config_name] = {}
            configs_map[config_name][r['framework']] = r

    # Print comparison
    for config_name, frameworks in configs_map.items():
        print(f"\n{config_name}")
        print("-" * 80)

        pytorch = frameworks.get('PyTorch')
        mlx = frameworks.get('MLX')

        if pytorch:
            print(f"PyTorch ({pytorch['device']}):")
            print(f"  Latency: {pytorch['mean_latency_ms']:.1f}ms ± {pytorch['std_latency_ms']:.1f}ms")
            print(f"  Memory:  {pytorch['memory_mb']:.1f} MB")
            print(f"  Params:  {pytorch['params']:,}")

        if mlx:
            print("MLX (Apple Silicon):")
            print(f"  Latency: {mlx['mean_latency_ms']:.1f}ms ± {mlx['std_latency_ms']:.1f}ms")
            print(f"  Memory:  {mlx['memory_mb']:.1f} MB")
            print(f"  Params:  {mlx['params']:,}")

        if pytorch and mlx:
            speedup = pytorch['mean_latency_ms'] / mlx['mean_latency_ms']
            mem_reduction = (pytorch['memory_mb'] - mlx['memory_mb']) / pytorch['memory_mb'] * 100

            print("\nMLX Improvement:")
            print(f"  ⚡ Speed:  {speedup:.1f}x faster")
            print(f"  💾 Memory: {mem_reduction:.1f}% less")


def main():
    """Run benchmarks."""
    import argparse

    parser = argparse.ArgumentParser(description='Benchmark TRM: PyTorch vs MLX')
    parser.add_argument('--iterations', type=int, default=10,
                       help='Number of iterations per test')
    parser.add_argument('--pytorch', action='store_true',
                       help='Benchmark PyTorch only')
    parser.add_argument('--mlx', action='store_true',
                       help='Benchmark MLX only')

    args = parser.parse_args()

    run_pytorch = args.pytorch or (not args.pytorch and not args.mlx)
    run_mlx = args.mlx or (not args.pytorch and not args.mlx)

    results = []

    for config in configs:
        if run_pytorch:
            result = benchmark_pytorch(config, args.iterations)
            if result:
                results.append(result)

        if run_mlx:
            result = benchmark_mlx(config, args.iterations)
            if result:
                results.append(result)

    # Print summary
    print_comparison_table(results)

    print("\n" + "="*80)
    print("Benchmark complete!")
    print("="*80)


if __name__ == "__main__":
    main()

