#!/usr/bin/env python3
"""
Performance Baseline Benchmark Script

Runs automated benchmarks to establish performance baseline for Milestone 1.
Captures metrics for chunk generation, rendering, and system performance.
"""

import subprocess
import time
import sys
from pathlib import Path

def run_benchmark(name, command, duration_seconds=60):
    """Run a benchmark command for specified duration."""
    print(f"\n{'='*60}")
    print(f"Running: {name}")
    print(f"Command: {command}")
    print(f"Duration: {duration_seconds}s")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    proc = subprocess.Popen(command, shell=True)
    
    try:
        # Let it run for the specified duration
        time.sleep(duration_seconds)
    finally:
        proc.terminate()
        proc.wait(timeout=5)
    
    elapsed = time.time() - start_time
    print(f"\n✓ Completed in {elapsed:.1f}s\n")

def main():
    print("MyCraft Performance Baseline Benchmark")
    print("=" * 60)
    print("This script will run automated benchmarks to establish")
    print("performance baselines for Milestone 1.")
    print("=" * 60)
    
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    benchmarks = [
        {
            "name": "Single-Player Baseline (Performance Preset)",
            "command": "python3 run_client.py --preset performance",
            "duration": 120  # 2 minutes
        },
    ]
    
    for i, benchmark in enumerate(benchmarks, 1):
        print(f"\nBenchmark {i}/{len(benchmarks)}")
        run_benchmark(
            benchmark["name"],
            benchmark["command"],
            benchmark["duration"]
        )
        
        if i < len(benchmarks):
            print("\nWaiting 5 seconds before next benchmark...")
            time.sleep(5)
    
    print("\n" + "="*60)
    print("✓ All benchmarks complete!")
    print("="*60)
    print("\nResults saved to:")
    print("  - logs/mycraft-*.log (detailed logs)")
    print("  - logs/metrics.csv (performance metrics)")
    print("\nNext steps:")
    print("  1. Analyze logs/metrics.csv for performance data")
    print("  2. Update docs/performance_baseline.md with results")
    print("  3. Create baseline graphs if needed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user.")
        sys.exit(1)
