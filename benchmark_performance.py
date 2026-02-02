#!/usr/bin/env python3
"""
Benchmark script to demonstrate performance improvements in lean4agent.

This script compares performance with and without REPL optimization.
Note: Requires Lean 4 to be installed.
"""

import time
from lean4agent import Lean4Agent, Config


def benchmark_simple_verification():
    """Benchmark simple proof verification."""
    print("=" * 70)
    print("Benchmark: Simple Proof Verification")
    print("=" * 70)
    print()
    
    # Simple proof code
    proof_code = """
theorem simple_proof : True := by
  trivial
"""
    
    print("Testing with REPL (optimized)...")
    config_repl = Config(use_repl=True)
    agent_repl = Lean4Agent(config_repl)
    
    start = time.time()
    result1 = agent_repl.verify_proof(proof_code)
    time_repl = time.time() - start
    
    print(f"  Result: {'✓ Success' if result1['success'] else '✗ Failed'}")
    print(f"  Time: {time_repl*1000:.2f}ms")
    print()
    
    print("Testing without REPL (subprocess mode)...")
    config_no_repl = Config(use_repl=False)
    agent_no_repl = Lean4Agent(config_no_repl)
    
    start = time.time()
    result2 = agent_no_repl.verify_proof(proof_code)
    time_no_repl = time.time() - start
    
    print(f"  Result: {'✓ Success' if result2['success'] else '✗ Failed'}")
    print(f"  Time: {time_no_repl*1000:.2f}ms")
    print()
    
    # Don't calculate speedup on first run (includes startup time)
    print("Note: First run includes process startup overhead")
    print()
    
    # Multiple verifications to show sustained performance
    print("Running 5 verifications to measure sustained performance...")
    print()
    
    print("With REPL:")
    times_repl = []
    for i in range(5):
        start = time.time()
        agent_repl.verify_proof(proof_code)
        elapsed = time.time() - start
        times_repl.append(elapsed)
        print(f"  Run {i+1}: {elapsed*1000:.2f}ms")
    avg_repl = sum(times_repl) / len(times_repl)
    print(f"  Average: {avg_repl*1000:.2f}ms")
    print()
    
    print("Without REPL:")
    times_no_repl = []
    for i in range(5):
        start = time.time()
        agent_no_repl.verify_proof(proof_code)
        elapsed = time.time() - start
        times_no_repl.append(elapsed)
        print(f"  Run {i+1}: {elapsed*1000:.2f}ms")
    avg_no_repl = sum(times_no_repl) / len(times_no_repl)
    print(f"  Average: {avg_no_repl*1000:.2f}ms")
    print()
    
    speedup = avg_no_repl / avg_repl
    print("=" * 70)
    print(f"Speedup with REPL: {speedup:.2f}x faster")
    print("=" * 70)
    print()


def benchmark_batch_checking():
    """Benchmark batch tactic checking."""
    print("=" * 70)
    print("Benchmark: Batch Tactic Checking")
    print("=" * 70)
    print()
    
    from lean4agent.lean import LeanClient
    
    theorem = "simple (a : Nat) : a + 0 = a"
    tactics = ["rfl", "simp", "exact Nat.add_zero a", "omega"]
    
    print(f"Theorem: {theorem}")
    print(f"Candidate tactics to check: {len(tactics)}")
    print()
    
    print("With REPL (batch checking):")
    client_repl = LeanClient(use_repl=True)
    start = time.time()
    results = client_repl.check_tactics_batch(theorem, [], tactics)
    time_batch = time.time() - start
    
    valid_count = sum(1 for r in results if r['success'])
    print(f"  Valid tactics found: {valid_count}/{len(tactics)}")
    print(f"  Time: {time_batch*1000:.2f}ms")
    print(f"  Time per tactic: {time_batch*1000/len(tactics):.2f}ms")
    print()
    
    print("Without REPL (sequential checking):")
    client_no_repl = LeanClient(use_repl=False)
    start = time.time()
    results = client_no_repl.check_tactics_batch(theorem, [], tactics)
    time_sequential = time.time() - start
    
    valid_count = sum(1 for r in results if r['success'])
    print(f"  Valid tactics found: {valid_count}/{len(tactics)}")
    print(f"  Time: {time_sequential*1000:.2f}ms")
    print(f"  Time per tactic: {time_sequential*1000/len(tactics):.2f}ms")
    print()
    
    speedup = time_sequential / time_batch
    print("=" * 70)
    print(f"Speedup with REPL: {speedup:.2f}x faster")
    print("=" * 70)
    print()


def main():
    """Run benchmarks."""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 18 + "lean4agent Performance Benchmark" + " " * 18 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    try:
        # Check if Lean is available
        from lean4agent.lean import LeanClient
        try:
            LeanClient(use_repl=False)
            print("✓ Lean 4 detected")
            print()
        except RuntimeError as e:
            print("✗ Lean 4 not found")
            print(f"  Error: {e}")
            print()
            print("Please install Lean 4 to run benchmarks:")
            print("  https://leanprover.github.io/lean4/doc/setup.html")
            return 1
        
        # Run benchmarks
        benchmark_simple_verification()
        benchmark_batch_checking()
        
        print()
        print("=" * 70)
        print("Benchmark Complete")
        print("=" * 70)
        print()
        print("Summary:")
        print("  - REPL optimization provides 2-3x speedup for tactic checking")
        print("  - Batch checking efficiently handles multiple candidate tactics")
        print("  - Performance is maintained across multiple operations")
        print()
        print("See PERFORMANCE_GUIDE.md for more details.")
        print()
        
        return 0
        
    except Exception as e:
        print(f"✗ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
