"""Basic example of using Lean4Agent with Ollama."""
from lean4agent import Lean4Agent, Config

# Example 1: Using default configuration (Ollama with BFS-Prover-V2)
def example_with_defaults():
    """Example using default Ollama configuration."""
    print("=== Example 1: Using Ollama (default) ===\n")
    
    # Create agent with default config (reads from .env if present)
    agent = Lean4Agent()
    
    # Simple theorem to prove
    theorem = "example_add : 2 + 2 = 4"
    
    # Generate proof
    result = agent.generate_proof(theorem, verbose=True)
    
    if result.success:
        print("\n✓ Proof generation successful!")
        print("\nComplete proof:")
        print(result.get_proof_code())
    else:
        print(f"\n✗ Proof generation failed: {result.error}")


# Example 2: Custom configuration
def example_with_custom_config():
    """Example with custom configuration."""
    print("\n\n=== Example 2: Custom configuration ===\n")
    
    # Create custom config
    config = Config(
        llm_provider="ollama",
        ollama_url="http://localhost:11434",
        ollama_model="bfs-prover-v2:32b",
        max_iterations=30,
        temperature=0.7
    )
    
    agent = Lean4Agent(config)
    
    # Try a simple theorem
    theorem = "test_theorem (a b : Nat) : a + b = b + a"
    
    result = agent.generate_proof(theorem, verbose=True)
    
    if result.success:
        print("\n✓ Proof found!")
        print(result.get_proof_code())
    else:
        print(f"\n✗ Failed: {result.error}")
        print(f"Attempted {len(result.proof_steps)} steps")


# Example 3: Using environment variables
def example_with_env():
    """Example using .env file configuration."""
    print("\n\n=== Example 3: Using .env configuration ===\n")
    
    # This will read from .env file
    config = Config.from_env()
    agent = Lean4Agent(config)
    
    theorem = "simple_example : True"
    result = agent.generate_proof(theorem, verbose=True)
    
    if result.success:
        print("\n✓ Success!")
        print(result.get_proof_code())


if __name__ == "__main__":
    # Note: Make sure Ollama is running and has the model loaded
    # Run: ollama pull bfs-prover-v2:32b
    
    # Run example 1
    try:
        example_with_defaults()
    except Exception as e:
        print(f"Example 1 failed: {e}")
    
    # Uncomment to run other examples:
    # example_with_custom_config()
    # example_with_env()
