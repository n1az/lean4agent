"""
Lean4Agent Examples - Comprehensive Usage Guide

This file demonstrates the main use cases of Lean4Agent with both Ollama and OpenAI-compatible APIs.
Shows both single-step and multi-step proof generation with clear indicators of what comes from the model.
"""

import sys
from pathlib import Path

# Add package to path if not installed
sys.path.insert(0, str(Path(__file__).parent))

from lean4agent import Lean4Agent, Config


def example_1_single_step_proof():
    """Example 1: Single-step proof generation (simplest case)."""
    print("=" * 80)
    print("EXAMPLE 1: Single-Step Proof Generation")
    print("=" * 80)
    print("\nDemonstrates proof that completes in ONE tactic step\n")
    
    # Configure - MUST specify your model name!
    config = Config(
        llm_provider="ollama",
        ollama_url="http://localhost:11434",
        ollama_model="zeyu-zheng/BFS-Prover-V2-7B:q8_0",  # ← Your actual model
        max_iterations=20
    )
    
    agent = Lean4Agent(config)
    
    # Simple theorem that requires only ONE tactic
    theorem = "theorem simple_example : 2 + 2 = 4"
    
    print(f"Theorem to prove: {theorem}")
    print("=" * 60)
    print("\n🤖 MODEL will generate the proof tactic...")
    print("   (Not hardcoded - comes from LLM inference)")
    print()
    
    result = agent.generate_proof(theorem, verbose=True)
    
    if result.success:
        print(f"\n✅ SUCCESS! Proof completed in {result.iterations} iteration(s)")
        print("=" * 60)
        print("Complete proof code:")
        print(result.get_proof_code())
        print("=" * 60)
        print(f"\n📊 Proof steps taken by MODEL:")
        for i, step in enumerate(result.proof_steps, 1):
            print(f"   Step {i}: {step.tactic} → {'✓ Valid' if step.success else '✗ Invalid'}")
    else:
        print(f"\n❌ FAILED after {result.iterations} iterations")
        print(f"Error: {result.error}")


def example_2_multi_step_proof():
    """Example 2: Multi-step proof generation with incremental verification."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 2: Multi-Step Proof with Incremental Verification")
    print("=" * 80)
    print("\nDemonstrates proof requiring MULTIPLE tactics (keeps valid steps)\n")
    
    config = Config(
        llm_provider="ollama",
        ollama_model="zeyu-zheng/BFS-Prover-V2-7B:q8_0",  # ← Your actual model
        max_iterations=30  # More iterations for complex proofs
    )
    
    agent = Lean4Agent(config)
    
    # More complex theorem requiring multiple steps
    theorem = "example : f ⁻¹' (u ∩ v) = f ⁻¹' u ∩ f ⁻¹' v"
    
    print(f"Theorem to prove: {theorem}")
    print("=" * 60)
    print("\n🤖 MODEL will generate tactics step-by-step")
    print("   Each valid tactic is KEPT and builds on previous steps")
    print("   Invalid tactics are DISCARDED without affecting valid progress")
    print()
    
    result = agent.generate_proof(theorem, verbose=True)
    
    if result.success:
        print(f"\n✅ SUCCESS! Proof completed in {result.iterations} iteration(s)")
        print("=" * 60)
        print("Complete proof code:")
        print(result.get_proof_code())
        print("=" * 60)
        print(f"\n📊 Proof construction process ({len(result.proof_steps)} steps):")
        for i, step in enumerate(result.proof_steps, 1):
            status = "✓ KEPT (valid)" if step.success else "✗ REJECTED (invalid)"
            print(f"   Iteration {i}: '{step.tactic}' → {status}")
            if step.state and step.state != "complete":
                print(f"              New goal: {step.state[:60]}...")
    else:
        print(f"\n❌ FAILED after {result.iterations} iterations")
        if result.complete_proof:
            print("\n⚠️  Partial proof with 'sorry' (incomplete):")
            print(result.complete_proof)


def example_3_tactic_verification():
    """Example 3: Testing specific tactics (hardcoded vs model-generated)."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 3: Tactic Verification - Hardcoded vs Model-Generated")
    print("=" * 80)
    print("\nShows difference between testing a HARDCODED tactic and MODEL suggestions\n")
    
    config = Config(
        llm_provider="ollama",
        ollama_model="zeyu-zheng/BFS-Prover-V2-7B:q8_0"  # ← Your actual model
    )
    
    agent = Lean4Agent(config)
    
    theorem = "theorem example_nat (n : Nat) : n + 0 = n"
    
    # Part 1: Test a HARDCODED tactic (we provide the tactic manually)
    print("PART 1: Testing HARDCODED tactic")
    print("-" * 60)
    print("💡 We manually specify tactic: 'rfl'")
    print("   (This is HARDCODED, not from model)")
    print()
    
    result = agent.check_tactic(theorem=theorem, tactic="rfl")
    print(f"   Result: {result.status}")
    print(f"   Valid: {'✓ Yes' if result.is_valid else '✗ No'}")
    print(f"   Proof Done: {'✓ Yes' if result.is_proof_done else '✗ No'}")
    
    # Part 2: Get MODEL-GENERATED tactic suggestions
    print("\n\nPART 2: Getting MODEL-GENERATED tactics")
    print("-" * 60)
    print("🤖 MODEL generates and tests multiple tactics")
    print("   (These come from LLM inference, not hardcoded)")
    print()
    
    suggestions = agent.suggest_tactic(
        theorem=theorem,
        num_suggestions=5,
        verbose=False
    )
    
    print(f"   MODEL generated {len(suggestions)} tactic suggestions:\n")
    for i, sugg in enumerate(suggestions, 1):
        status_icon = "✅" if sugg.is_valid else "❌"
        print(f"   {status_icon} Suggestion {i}: '{sugg.tactic}'")
        print(f"      → Status: {sugg.status}")
        if sugg.is_valid:
            print(f"      → Proof Done: {'✓ Yes' if sugg.is_proof_done else '✗ No, needs more tactics'}")
    
    # Part 3: Get only valid model suggestions
    print("\n\nPART 3: Filtering for VALID model suggestions only")
    print("-" * 60)
    
    valid_suggestions = agent.get_valid_suggestions(
        theorem=theorem,
        num_suggestions=10  # Ask for more, get only valid ones
    )
    
    print(f"   Found {len(valid_suggestions)} VALID tactics from model:\n")
    for i, sugg in enumerate(valid_suggestions[:5], 1):
        print(f"   {i}. {sugg['tactic']}")
        print(f"      → Goal state: {sugg.get('state', 'complete')[:50]}")


def example_4_proof_verification():
    """Example 4: Verifying complete proofs (no model inference needed)."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 4: Proof Verification (No Model Needed)")
    print("=" * 80)
    print("\nVerifying COMPLETE proofs - only uses Lean REPL, not the model\n")
    
    config = Config(
        llm_provider="ollama",
        ollama_model="zeyu-zheng/BFS-Prover-V2-7B:q8_0"  # Model not used for verification
    )
    
    agent = Lean4Agent(config)
    
    # These are COMPLETE proofs we want to verify
    valid_proof = """
theorem test_valid : 2 + 2 = 4 := by
  rfl
"""
    
    invalid_proof = """
theorem test_invalid : 2 + 2 = 5 := by
  rfl
"""
    
    print("Testing VALID proof (hardcoded):")
    print("-" * 60)
    print(valid_proof)
    result1 = agent.verify_proof(valid_proof)
    print(f"✅ Result: {'VALID' if result1['success'] else 'INVALID'}\n")
    
    print("\nTesting INVALID proof (hardcoded):")
    print("-" * 60)
    print(invalid_proof)
    result2 = agent.verify_proof(invalid_proof)
    print(f"❌ Result: {'VALID' if result2['success'] else 'INVALID'}")
    if not result2['success']:
        print(f"   Error: {result2.get('error', 'Unknown')[:100]}...")


def example_5_openai_compatible():
    """Example 5: Using OpenAI-compatible API instead of Ollama."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 5: OpenAI-Compatible API (Groq, OpenAI, LMStudio)")
    print("=" * 80)
    print("\nSame functionality but using OpenAI-compatible endpoint\n")
    
    # Configure for OpenAI-compatible API
    # Option 1: OpenAI
    config_openai = Config(
        llm_provider="openai",
        openai_api_key="your-openai-api-key",
        openai_model="gpt-4",  # ← Specify your model
        max_iterations=15
    )
    
    # Option 2: Groq (OpenAI-compatible)
    config_groq = Config(
        llm_provider="openai",
        openai_api_key="your-groq-api-key",
        openai_base_url="https://api.groq.com/openai/v1",
        openai_model="mixtral-8x7b-32768",  # ← Specify your model
        max_iterations=15
    )
    
    print("Configuration examples shown (not running to avoid API costs)")
    print("=" * 60)
    print("\nOpenAI config:")
    print(f"  Provider: {config_openai.llm_provider}")
    print(f"  Model: {config_openai.openai_model}")
    print("\nGroq config:")
    print(f"  Provider: {config_groq.llm_provider}")
    print(f"  Base URL: {config_groq.openai_base_url}")
    print(f"  Model: {config_groq.openai_model}")
    print("\nUse same methods: generate_proof(), check_tactic(), etc.")


def example_6_environment_config():
    """Example 6: Configuration via environment variables."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 6: Environment Variable Configuration")
    print("=" * 80)
    print("\nLoading configuration from .env file\n")
    
    print("Create a .env file in your project root:")
    print("=" * 60)
    print("LLM_PROVIDER=ollama")
    print("OLLAMA_URL=http://localhost:11434")
    print("OLLAMA_MODEL=zeyu-zheng/BFS-Prover-V2-7B:q8_0  # ← Your model")
    print("MAX_ITERATIONS=30")
    print("TEMPERATURE=0.7")
    print("=" * 60)
    print("\nThen load in Python:")
    print("  config = Config.from_env()")
    print("  agent = Lean4Agent(config)")
    print("\nThis keeps sensitive data out of your code!")


def example_7_with_mathlib():
    """Example 7: Using with mathlib dependencies."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 7: Using with Mathlib Dependencies")
    print("=" * 80)
    print("\nFor theorems requiring mathlib imports\n")
    
    config = Config(
        llm_provider="ollama",
        ollama_model="zeyu-zheng/BFS-Prover-V2-7B:q8_0",  # ← Your model
        lean_project_path=Path("/path/to/your/lean/project")  # Must have mathlib
    )
    
    print("Configuration for mathlib project:")
    print("=" * 60)
    print(f"  lean_project_path: {config.lean_project_path}")
    print("\nThis allows proving theorems that import from mathlib")
    print("Make sure your Lean project has mathlib in dependencies!")


def main():
    """Run examples demonstrating single-step, multi-step, and various features."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "LEAN4AGENT COMPREHENSIVE EXAMPLES" + " " * 25 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    print("KEY CONCEPTS:")
    print("  🤖 = Tactics generated by MODEL (LLM inference)")
    print("  💡 = Tactics we HARDCODE (manual specification)")
    print("  ✅ = Valid tactic that is KEPT in proof")
    print("  ❌ = Invalid tactic that is DISCARDED")
    print("\n" + "=" * 80 + "\n")
    
    try:
        # Run examples showing progression from simple to complex
        example_1_single_step_proof()          # Simplest: one tactic
        example_2_multi_step_proof()           # Complex: multiple tactics with incremental verification
        example_3_tactic_verification()        # Shows hardcoded vs model-generated
        example_4_proof_verification()         # Verification only (no model)
        
        # Configuration examples (don't require running proofs)
        example_5_openai_compatible()
        example_6_environment_config()
        example_7_with_mathlib()
        
        print("\n" + "=" * 80)
        print("EXAMPLES COMPLETED")
        print("=" * 80)
        print("\n📚 Summary:")
        print("   - Example 1: Single-step proofs (simplest)")
        print("   - Example 2: Multi-step proofs (incremental verification)")
        print("   - Example 3: Hardcoded vs model-generated tactics")
        print("   - Example 4: Proof verification only")
        print("   - Examples 5-7: Configuration options")
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
