# Testing Guide for Multi-Step Proof Generation

This guide explains how to test the lean4agent toolkit with real Lean 4 and LLM integration to generate multi-step proofs.

## Prerequisites

Before running these tests, ensure you have:

1. **Lean 4** installed and available in PATH
   ```bash
   lean --version
   ```

2. **LLM Provider** set up (choose one):
   - **Ollama** with BFS-Prover-V2 model:
     ```bash
     ollama pull bfs-prover-v2:32b
     ollama serve
     ```
   - **OpenAI API** with valid API key:
     ```bash
     export OPENAI_API_KEY="your-api-key"
     ```

3. **Package installed**:
   ```bash
   pip install -e .
   ```

## Test 1: Simple Proof (Expected 2-3 steps)

```python
from lean4agent import Lean4Agent, Config

# Configure agent
config = Config(
    llm_provider="ollama",  # or "openai"
    ollama_model="bfs-prover-v2:32b",
    max_iterations=20,
    temperature=0.7
)

agent = Lean4Agent(config)

# Simple theorem
theorem = "simple_proof : True"

result = agent.generate_proof(theorem, verbose=True)

if result.success:
    print("\n✓ Proof successful!")
    print(f"Steps: {len(result.proof_steps)}")
    print("\nGenerated proof:")
    print(result.get_proof_code())
```

**Expected output:**
- 1-2 proof steps
- Completion with `trivial` or `rfl`

## Test 2: Multi-Step Proof (Expected 4-5 steps)

This is the main test for coverage verification.

```python
from lean4agent import Lean4Agent, Config

config = Config(
    llm_provider="ollama",
    ollama_model="bfs-prover-v2:32b",
    max_iterations=30,
    temperature=0.7
)

agent = Lean4Agent(config)

# Theorem requiring multiple steps
theorem = "add_zero (n : Nat) : n + 0 = n"

print("=" * 70)
print("Testing Multi-Step Proof Generation")
print("=" * 70)
print(f"\nTheorem: {theorem}")
print("\nStarting proof generation...\n")

result = agent.generate_proof(theorem, verbose=True)

print("\n" + "=" * 70)
print("Results")
print("=" * 70)
print(f"Success: {result.success}")
print(f"Iterations: {result.iterations}")
print(f"Total steps: {len(result.proof_steps)}")

if result.success:
    print("\nProof steps:")
    for i, step in enumerate(result.proof_steps, 1):
        print(f"  {i}. {step.tactic}")
    
    print("\nComplete proof:")
    print(result.get_proof_code())
else:
    print(f"\nError: {result.error}")
```

**Expected characteristics:**
- 4-5 proof steps minimum
- May use induction
- Should demonstrate iterative LLM interaction
- Each step verified by Lean 4

## Test 3: Complex Proof (Expected 5+ steps)

For more thorough coverage testing:

```python
from lean4agent import Lean4Agent, Config

config = Config(
    llm_provider="ollama",
    ollama_model="bfs-prover-v2:32b",
    max_iterations=50,
    temperature=0.7
)

agent = Lean4Agent(config)

# More complex theorem
theorem = "add_comm (a b : Nat) : a + b = b + a"

result = agent.generate_proof(theorem, verbose=True)

# Analyze results
if result.success:
    print(f"\n✓ Successfully proved in {result.iterations} steps")
    print(f"\nProof complexity metrics:")
    print(f"  - Total tactics: {len(result.proof_steps)}")
    print(f"  - Success rate: {sum(1 for s in result.proof_steps if s.success)}/{len(result.proof_steps)}")
    
    # Count tactic types
    tactics = [step.tactic.split()[0] for step in result.proof_steps]
    print(f"  - Tactic variety: {len(set(tactics))} unique tactics")
    
    print(f"\nGenerated proof:\n{result.get_proof_code()}")
```

**Expected output:**
- 5+ proof steps
- Mix of tactics (induction, simp, rw, etc.)
- Demonstrates hypothesis management

## Capturing Screenshots

To capture proof generation output for documentation:

1. **Run test with output redirection:**
   ```bash
   python test_script.py 2>&1 | tee proof_output.log
   ```

2. **Take terminal screenshot** showing:
   - Configuration
   - Iterative proof process
   - Each step with state transitions
   - Final generated proof
   - Success metrics

3. **Verify coverage:**
   - Minimum 4-5 steps completed
   - All steps show ✓ success
   - Valid Lean 4 syntax in output
   - State tracking visible

## Success Criteria

A successful test demonstrates:

✓ **Multi-step generation** - At least 4-5 proof steps  
✓ **Iterative LLM calls** - Separate LLM invocation per step  
✓ **State management** - Proof state updates after each tactic  
✓ **Lean 4 integration** - Valid syntax and verification  
✓ **Completion detection** - Recognizes when proof is done  
✓ **Error handling** - Graceful handling of failed tactics  

## Troubleshooting

**Issue:** Proof fails or times out
- Increase `max_iterations`
- Try simpler theorems first
- Check Lean 4 is working: `lean --version`
- Verify LLM is responding

**Issue:** LLM generates invalid tactics
- Adjust `temperature` (try 0.5 for more conservative)
- Check model is appropriate for Lean 4
- Verify model is properly loaded in Ollama

**Issue:** Proof completes but with fewer than 4 steps
- Try more complex theorems (e.g., involving induction)
- Test with theorems requiring hypothesis rewriting
- Use theorems with multiple cases

## Example Test Script

Save as `test_multi_step_proof.py`:

```python
#!/usr/bin/env python3
"""Test multi-step proof generation for coverage verification."""

from lean4agent import Lean4Agent, Config

def main():
    config = Config(
        llm_provider="ollama",
        ollama_model="bfs-prover-v2:32b",
        max_iterations=30
    )
    
    agent = Lean4Agent(config)
    
    # Test theorem requiring multiple steps
    theorem = "add_zero (n : Nat) : n + 0 = n"
    
    print("Testing Multi-Step Proof Generation")
    print("=" * 70)
    print(f"Theorem: {theorem}\n")
    
    result = agent.generate_proof(theorem, verbose=True)
    
    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    
    if result.success:
        steps = len(result.proof_steps)
        print(f"✓ PASS - Generated {steps}-step proof")
        
        if steps >= 4:
            print("✓ Coverage requirement met (4+ steps)")
        else:
            print(f"⚠ Coverage requirement not met ({steps} < 4 steps)")
        
        print(f"\nProof:\n{result.get_proof_code()}")
    else:
        print(f"✗ FAIL - {result.error}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
```

Run with:
```bash
python test_multi_step_proof.py
```
