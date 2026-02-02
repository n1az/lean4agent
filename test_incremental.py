"""Test incremental proof generation to verify REPL environment handling."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lean4agent import Lean4Agent, Config

# Configure with your model
config = Config(
    llm_provider="ollama",
    ollama_model="zeyu-zheng/BFS-Prover-V2-7B:q8_0",
    max_iterations=10
)

agent = Lean4Agent(config)

# Test simple proof
theorem = "theorem test_increment : 2 + 2 = 4"

print("Testing incremental proof generation...")
print(f"Theorem: {theorem}\n")
print("=" * 60)

result = agent.generate_proof(theorem, verbose=True)

print("\n" + "=" * 60)
if result.success:
    print("✅ SUCCESS! Proof completed:")
    print(result.get_proof_code())
else:
    print(f"❌ FAILED: {result.error}")
    if result.complete_proof:
        print("\nPartial proof:")
        print(result.complete_proof)
