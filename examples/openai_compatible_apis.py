"""Example using OpenAI-compatible APIs (Groq, LMStudio, etc.)."""
from lean4agent import Lean4Agent, Config
import os


def example_groq():
    """Example using Groq API (OpenAI-compatible)."""
    print("=== Using Groq API ===\n")
    
    # Configure for Groq
    config = Config(
        llm_provider="openai",
        openai_api_key=os.getenv("GROQ_API_KEY"),
        openai_base_url="https://api.groq.com/openai/v1",
        openai_model="mixtral-8x7b-32768",
        max_iterations=20,
        temperature=0.7
    )
    
    agent = Lean4Agent(config)
    
    theorem = "simple_add (a b : Nat) : a + b = b + a"
    print(f"Attempting to prove: {theorem}\n")
    
    result = agent.generate_proof(theorem, verbose=True)
    
    if result.success:
        print("\n" + "="*50)
        print("✓ Proof successful!")
        print("="*50)
        print("\n" + result.get_proof_code())
    else:
        print("\n" + "="*50)
        print("✗ Proof failed")
        print("="*50)
        print(f"\n{result.get_proof_status_summary()}")
        
        # Show partial proof with sorry if available
        if result.complete_proof:
            print("\nPartial proof with 'sorry':")
            print(result.complete_proof)


def example_lmstudio():
    """Example using LMStudio (local OpenAI-compatible server)."""
    print("\n\n=== Using LMStudio (local) ===\n")
    
    # Configure for LMStudio
    # LMStudio typically doesn't require an API key
    config = Config(
        llm_provider="openai",
        openai_api_key="not-needed",
        openai_base_url="http://localhost:1234/v1",
        openai_model="local-model",  # Use whatever model you have loaded
        max_iterations=20,
        temperature=0.7,
        use_sorry_on_timeout=True
    )
    
    agent = Lean4Agent(config)
    
    theorem = "test_theorem : True"
    print(f"Attempting to prove: {theorem}\n")
    
    result = agent.generate_proof(theorem, verbose=True)
    
    if result.success:
        print("\n✓ Success!")
        print(result.get_proof_code())
    else:
        print("\n✗ Failed")
        print(result.get_proof_status_summary())


def example_with_env_variables():
    """Example loading OpenAI-compatible API from environment."""
    print("\n\n=== Using Environment Variables ===\n")
    
    # This will read OPENAI_BASE_URL from environment
    # Set in .env file:
    #   OPENAI_BASE_URL=https://api.groq.com/openai/v1
    #   OPENAI_API_KEY=your-key
    #   LLM_PROVIDER=openai
    
    config = Config.from_env()
    agent = Lean4Agent(config)
    
    theorem = "example : 1 + 1 = 2"
    result = agent.generate_proof(theorem, verbose=True)
    
    if result.success:
        print("\n✓ Proof found!")
        print(result.get_proof_code())
    else:
        print(f"\n✗ Failed: {result.error}")
        print(f"\nValid steps: {result.valid_steps_count}")


if __name__ == "__main__":
    print("Examples for using OpenAI-compatible APIs\n")
    print("="*60)
    
    # Example 1: Groq
    if os.getenv("GROQ_API_KEY"):
        try:
            example_groq()
        except Exception as e:
            print(f"Groq example failed: {e}")
    else:
        print("Skipping Groq example (set GROQ_API_KEY to run)")
    
    # Example 2: LMStudio
    # Uncomment to test with LMStudio running locally
    # try:
    #     example_lmstudio()
    # except Exception as e:
    #     print(f"LMStudio example failed: {e}")
    
    # Example 3: Environment variables
    # try:
    #     example_with_env_variables()
    # except Exception as e:
    #     print(f"Environment example failed: {e}")
