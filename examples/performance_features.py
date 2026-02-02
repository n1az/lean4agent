#!/usr/bin/env python3
"""
Example: Performance Optimization Usage

This example demonstrates the new performance features in lean4agent v2.0,
including persistent REPL and batch tactic checking.

Prerequisites:
- Lean 4 installed and in PATH
- lean4agent package installed
"""

from lean4agent import Lean4Agent, Config
from lean4agent.lean import LeanClient
import time


def example_repl_optimization():
    """Demonstrate REPL optimization for faster proof generation."""
    print("=" * 70)
    print("Example 1: REPL Optimization")
    print("=" * 70)
    print()
    
    print("The persistent REPL keeps a Lean process alive throughout")
    print("proof generation, eliminating process spawning overhead.")
    print()
    
    # Using REPL (default, optimized)
    print("Creating agent with REPL (default)...")
    agent = Lean4Agent()  # use_repl=True by default
    print("✓ REPL started and ready")
    print()
    
    # Example theorem
    theorem = "simple_proof : True"
    print(f"Theorem: {theorem}")
    print()
    
    # Generate proof
    print("Generating proof...")
    start = time.time()
    result = agent.generate_proof(theorem, verbose=False)
    elapsed = time.time() - start
    
    print(f"✓ Proof generated in {elapsed:.2f}s")
    print(f"  Success: {result.success}")
    print(f"  Iterations: {result.iterations}")
    print()
    
    print("Key benefit: Each tactic check takes ~20ms instead of ~400ms")
    print("              without REPL (2-3x speedup for multi-step proofs)")
    print()


def example_batch_checking():
    """Demonstrate batch tactic checking."""
    print("=" * 70)
    print("Example 2: Batch Tactic Checking")
    print("=" * 70)
    print()
    
    print("Batch checking allows you to test multiple candidate tactics")
    print("efficiently, useful when working with models that generate")
    print("multiple suggestions.")
    print()
    
    # Create client
    client = LeanClient(use_repl=True)
    
    # Theorem to prove
    theorem = "example (a : Nat) : a + 0 = a"
    print(f"Theorem: {theorem}")
    print()
    
    # Multiple candidate tactics (some valid, some not)
    candidates = [
        "rfl",                    # Valid
        "simp",                   # Valid
        "exact Nat.add_zero a",   # Valid
        "omega",                  # Valid
        "invalid_tactic",         # Invalid
        "apply add_comm",         # Invalid for this theorem
    ]
    
    print(f"Checking {len(candidates)} candidate tactics...")
    print()
    
    # Check all tactics
    start = time.time()
    results = client.check_tactics_batch(theorem, [], candidates)
    elapsed = time.time() - start
    
    print("Results:")
    for i, result in enumerate(results, 1):
        status = "✓" if result["success"] else "✗"
        tactic = result["tactic"]
        print(f"  {i}. {status} {tactic}")
    
    print()
    valid_count = sum(1 for r in results if r["success"])
    print(f"Found {valid_count}/{len(candidates)} valid tactics")
    print(f"Time: {elapsed:.2f}s ({elapsed/len(candidates):.3f}s per tactic)")
    print()
    
    # Use first valid tactic
    for result in results:
        if result["success"]:
            print(f"Using first valid tactic: {result['tactic']}")
            print(f"  Proof complete: {result['complete']}")
            break
    print()


def example_reuse_agent():
    """Demonstrate efficient agent reuse for multiple proofs."""
    print("=" * 70)
    print("Example 3: Efficient Agent Reuse")
    print("=" * 70)
    print()
    
    print("When proving multiple theorems, reuse the same agent instance")
    print("to keep the REPL alive and maximize performance.")
    print()
    
    # Create single agent instance
    agent = Lean4Agent()
    
    # Multiple theorems
    theorems = [
        "proof1 : True",
        "proof2 : True ∧ True",
        "proof3 : ∀ x : Nat, x = x",
    ]
    
    print(f"Proving {len(theorems)} theorems...")
    print()
    
    start = time.time()
    for i, theorem in enumerate(theorems, 1):
        result = agent.generate_proof(theorem, verbose=False)
        status = "✓" if result.success else "✗"
        print(f"  {i}. {status} {theorem}")
        print(f"      Iterations: {result.iterations}")
    
    elapsed = time.time() - start
    
    print()
    print(f"Total time: {elapsed:.2f}s")
    print(f"Average: {elapsed/len(theorems):.2f}s per proof")
    print()
    
    print("Key benefit: REPL stays alive across all proofs, no startup overhead")
    print()


def example_configuration():
    """Demonstrate configuration options."""
    print("=" * 70)
    print("Example 4: Configuration Options")
    print("=" * 70)
    print()
    
    print("You can configure performance settings via Config:")
    print()
    
    # Example 1: Optimize for speed
    print("1. Optimized for speed (REPL enabled):")
    config_fast = Config(
        use_repl=True,        # Enable REPL (default)
        max_iterations=30,    # Moderate limit
        temperature=0.5,      # More focused
    )
    print(f"   use_repl: {config_fast.use_repl}")
    print(f"   max_iterations: {config_fast.max_iterations}")
    print()
    
    # Example 2: Legacy mode
    print("2. Legacy mode (no REPL, for compatibility):")
    config_legacy = Config(
        use_repl=False,       # Disable REPL
    )
    print(f"   use_repl: {config_legacy.use_repl}")
    print()
    
    # Example 3: From environment
    print("3. Load from environment (.env file):")
    print("   USE_REPL=true")
    print("   MAX_ITERATIONS=50")
    config_env = Config.from_env()
    print(f"   use_repl: {config_env.use_repl}")
    print()
    
    print("See PERFORMANCE_GUIDE.md for tuning recommendations")
    print()


def main():
    """Run examples."""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "lean4agent Performance Features Example" + " " * 14 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    try:
        # Check if Lean is available
        from lean4agent.lean import LeanClient
        try:
            LeanClient(use_repl=False)
            print("✓ Lean 4 detected")
            print()
        except RuntimeError:
            print("✗ Lean 4 not found")
            print()
            print("This example requires Lean 4 to be installed.")
            print("Install from: https://leanprover.github.io/lean4/doc/setup.html")
            print()
            print("However, you can still see the configuration options:")
            print()
            example_configuration()
            return 1
        
        # Run examples
        example_repl_optimization()
        example_batch_checking()
        example_reuse_agent()
        example_configuration()
        
        print("=" * 70)
        print("Examples Complete")
        print("=" * 70)
        print()
        print("Key Takeaways:")
        print("  1. REPL optimization provides 2-3x speedup")
        print("  2. Batch checking efficiently handles multiple candidates")
        print("  3. Reuse agent instances for best performance")
        print("  4. Configuration is flexible and easy")
        print()
        print("For more details:")
        print("  - PERFORMANCE_GUIDE.md - Tuning and optimization tips")
        print("  - COMPARISON_WITH_LLMLEAN.md - vs llmlean comparison")
        print("  - benchmark_performance.py - Performance benchmarks")
        print()
        
        return 0
        
    except Exception as e:
        print(f"✗ Example failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
