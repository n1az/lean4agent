"""Example using LSP-based Lean client for maximum performance."""
from lean4agent import Lean4Agent, Config

def example_with_lsp():
    """Example using LSP for best performance."""
    print("=== Example: Using LSP Mode (Best Performance) ===\n")
    
    # Create config with LSP enabled
    config = Config(
        llm_provider="ollama",
        ollama_model="bfs-prover-v2:32b",  # Must specify model
        use_lsp=True,  # Enable LSP for maximum performance
        use_repl=False,  # LSP takes precedence
        max_iterations=30,
        temperature=0.7
    )
    
    agent = Lean4Agent(config)
    
    # Simple theorem to prove
    theorem = "example_add : 2 + 2 = 4"
    
    print(f"Proving: {theorem}\n")
    print("Using LSP mode for fast tactic checking...")
    print("Expected: 10-80x faster than subprocess mode\n")
    
    # Generate proof
    result = agent.generate_proof(theorem, verbose=True)
    
    if result.success:
        print("\n✓ Proof generation successful!")
        print("\nComplete proof:")
        print(result.get_proof_code())
        print(f"\nIterations: {result.iterations}")
    else:
        print(f"\n✗ Proof generation failed: {result.error}")
        print(f"Attempted {len(result.proof_steps)} steps")


def example_compare_modes():
    """Compare different verification modes."""
    print("\n\n=== Example: Comparing Verification Modes ===\n")
    
    import time
    
    theorem = "simple_proof : True"
    
    # Test with LSP
    print("1. Testing with LSP mode...")
    config_lsp = Config(
        llm_provider="ollama",
        ollama_model="bfs-prover-v2:32b",
        use_lsp=True
    )
    agent_lsp = Lean4Agent(config_lsp)
    
    start = time.time()
    result_lsp = agent_lsp.generate_proof(theorem, verbose=False)
    time_lsp = time.time() - start
    
    print(f"   Result: {'✓ Success' if result_lsp.success else '✗ Failed'}")
    print(f"   Time: {time_lsp:.2f}s")
    
    # Test with REPL
    print("\n2. Testing with REPL mode...")
    config_repl = Config(
        llm_provider="ollama",
        ollama_model="bfs-prover-v2:32b",
        use_lsp=False,
        use_repl=True
    )
    agent_repl = Lean4Agent(config_repl)
    
    start = time.time()
    result_repl = agent_repl.generate_proof(theorem, verbose=False)
    time_repl = time.time() - start
    
    print(f"   Result: {'✓ Success' if result_repl.success else '✗ Failed'}")
    print(f"   Time: {time_repl:.2f}s")
    
    # Compare
    if time_repl > 0:
        speedup = time_repl / time_lsp
        print(f"\nSpeedup: {speedup:.2f}x faster with LSP")


if __name__ == "__main__":
    # Note: Make sure Ollama is running and has the model loaded
    # Run: ollama pull bfs-prover-v2:32b
    
    print("LSP Mode Example")
    print("=" * 70)
    print()
    print("This example demonstrates the LSP-based Lean client,")
    print("which provides 10-80x faster tactic checking compared to")
    print("traditional subprocess-based verification.")
    print()
    print("=" * 70)
    print()
    
    try:
        example_with_lsp()
        # Uncomment to compare modes:
        # example_compare_modes()
    except Exception as e:
        print(f"Example failed: {e}")
        import traceback
        traceback.print_exc()
