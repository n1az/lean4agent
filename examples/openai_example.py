"""Example using OpenAI API for proof generation."""
from lean4agent import Lean4Agent, Config
import os

def example_openai():
    """Example using OpenAI API."""
    print("=== Using OpenAI API ===\n")
    
    # Create config for OpenAI
    # API key can be set via environment variable OPENAI_API_KEY
    # or passed directly
    config = Config(
        llm_provider="openai",
        openai_api_key=os.getenv("OPENAI_API_KEY"),  # or pass directly
        openai_model="gpt-4",
        max_iterations=20,
        temperature=0.7
    )
    
    agent = Lean4Agent(config)
    
    # Example theorem
    theorem = "commutativity (a b : Nat) : a + b = b + a"
    
    print(f"Attempting to prove: {theorem}\n")
    
    result = agent.generate_proof(theorem, verbose=True)
    
    if result.success:
        print("\n" + "="*50)
        print("✓ Proof generation successful!")
        print("="*50)
        print("\nComplete proof:")
        print(result.get_proof_code())
        print(f"\nIterations used: {result.iterations}")
    else:
        print("\n" + "="*50)
        print("✗ Proof generation failed")
        print("="*50)
        print(f"Error: {result.error}")
        print(f"Attempted {len(result.proof_steps)} steps")
        print("\nSteps attempted:")
        for i, step in enumerate(result.proof_steps[:5], 1):  # Show first 5
            print(f"  {i}. {step.tactic} (success: {step.success})")


if __name__ == "__main__":
    # Make sure OPENAI_API_KEY is set in environment or .env file
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        print("Example: export OPENAI_API_KEY='your-key-here'")
    else:
        example_openai()
