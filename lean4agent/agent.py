"""Main Lean4Agent class for proof generation."""

from typing import Optional, List, Dict, Any
from lean4agent.config import Config
from lean4agent.llm import LLMInterface, OllamaInterface, OpenAIInterface
from lean4agent.lean import LeanClient


class ProofStep:
    """Represents a single proof step."""

    def __init__(self, tactic: str, state: str, success: bool):
        """Initialize proof step.

        Args:
            tactic: The tactic applied
            state: Resulting proof state
            success: Whether tactic application succeeded
        """
        self.tactic = tactic
        self.state = state
        self.success = success

    def __repr__(self) -> str:
        return f"ProofStep(tactic='{self.tactic}', success={self.success})"


class ProofResult:
    """Result of proof generation attempt."""

    def __init__(
        self,
        success: bool,
        theorem: str,
        proof_steps: List[ProofStep],
        complete_proof: Optional[str] = None,
        error: Optional[str] = None,
        iterations: int = 0,
        valid_steps_count: Optional[int] = None,
    ):
        """Initialize proof result.

        Args:
            success: Whether proof generation succeeded
            theorem: The theorem statement
            proof_steps: List of proof steps attempted
            complete_proof: Complete proof code if successful
            error: Error message if failed
            iterations: Number of iterations taken
            valid_steps_count: Number of valid steps before failure
        """
        self.success = success
        self.theorem = theorem
        self.proof_steps = proof_steps
        self.complete_proof = complete_proof
        self.error = error
        self.iterations = iterations
        self.valid_steps_count = (
            valid_steps_count
            if valid_steps_count is not None
            else sum(1 for s in proof_steps if s.success)
        )

    def __repr__(self) -> str:
        return (
            f"ProofResult(success={self.success}, "
            f"iterations={self.iterations}, "
            f"steps={len(self.proof_steps)}, "
            f"valid_steps={self.valid_steps_count})"
        )

    def get_proof_code(self) -> str:
        """Get the complete proof code.

        Returns:
            Complete Lean 4 proof code
        """
        if self.complete_proof:
            return self.complete_proof

        # Construct from steps
        if not self.theorem.strip().startswith("theorem"):
            code = f"theorem {self.theorem} := by\n"
        else:
            code = f"{self.theorem} := by\n"

        for step in self.proof_steps:
            if step.success:
                code += f"  {step.tactic}\n"

        return code

    def get_proof_status_summary(self) -> str:
        """Get a summary of proof validation status.

        Returns:
            Human-readable summary of which steps were valid/invalid
        """
        if self.success:
            return f"Proof completed successfully with {self.valid_steps_count} valid steps."

        summary = f"Proof failed after {self.iterations} iterations.\n"
        summary += (
            f"Valid steps: {self.valid_steps_count} out of {len(self.proof_steps)} attempted.\n"
        )

        if self.valid_steps_count > 0:
            summary += "\nValid steps:\n"
            valid_count = 0
            for i, step in enumerate(self.proof_steps, 1):
                if step.success:
                    valid_count += 1
                    summary += f"  {valid_count}. {step.tactic}\n"

        # Find first failing step
        for i, step in enumerate(self.proof_steps, 1):
            if not step.success:
                summary += f"\nFirst invalid step at position {i}:\n"
                summary += f"  Tactic: {step.tactic}\n"
                if step.state:
                    summary += f"  Error/State: {step.state}\n"
                break

        return summary


class Lean4Agent:
    """Main agent for generating Lean 4 proofs using LLMs.

    This agent iteratively generates proof steps using an LLM and verifies
    them with Lean 4 until a complete proof is found.
    """

    def __init__(self, config: Optional[Config] = None):
        """Initialize Lean4Agent.

        Args:
            config: Configuration object. If None, loads from environment.
        """
        self.config = config or Config.from_env()
        self.config.validate_config()

        # Initialize LLM interface
        self.llm = self._create_llm_interface()

        # Initialize Lean client
        self.lean_client = LeanClient()

    def _create_llm_interface(self) -> LLMInterface:
        """Create LLM interface based on configuration.

        Returns:
            LLM interface instance

        Raises:
            ValueError: If invalid provider specified
        """
        if self.config.llm_provider == "ollama":
            return OllamaInterface(
                base_url=self.config.ollama_url,
                model=self.config.ollama_model,
                timeout=self.config.timeout,
            )
        elif self.config.llm_provider == "openai":
            return OpenAIInterface(
                api_key=self.config.openai_api_key,
                model=self.config.openai_model,
                base_url=self.config.openai_base_url,
                timeout=self.config.timeout,
            )
        else:
            raise ValueError(f"Unknown LLM provider: {self.config.llm_provider}")

    def generate_proof(
        self, theorem: str, max_iterations: Optional[int] = None, verbose: bool = False
    ) -> ProofResult:
        """Generate proof for a given theorem.

        Args:
            theorem: The theorem statement to prove
            max_iterations: Maximum iterations (overrides config)
            verbose: Whether to print progress

        Returns:
            ProofResult object with generation results
        """
        max_iter = max_iterations or self.config.max_iterations

        if verbose:
            print(f"Starting proof generation for: {theorem}")
            print(f"Max iterations: {max_iter}")

        # Initialize proof state
        current_proof = []
        proof_steps = []
        current_state = self.lean_client.get_initial_state(theorem)

        for iteration in range(max_iter):
            if verbose:
                print(f"\n--- Iteration {iteration + 1} ---")
                print(f"Current state: {current_state}")

            try:
                # Generate next tactic using LLM
                next_tactic = self.llm.generate_proof_step(
                    theorem=theorem,
                    current_state=current_state,
                    temperature=self.config.temperature,
                )

                if verbose:
                    print(f"Generated tactic: {next_tactic}")

                # Apply tactic in Lean
                result = self.lean_client.apply_tactic(
                    theorem=theorem, current_proof=current_proof, new_tactic=next_tactic
                )

                # Record the step
                step = ProofStep(
                    tactic=next_tactic, state=result["state"], success=result["success"]
                )
                proof_steps.append(step)

                if not result["success"]:
                    if verbose:
                        print(f"Tactic failed: {result['error']}")
                    # Continue trying with next tactic
                    continue

                # Update proof state
                current_proof = result["proof"]
                current_state = result["state"]

                if verbose:
                    print(f"New state: {current_state}")

                # Check if proof is complete
                if result["complete"]:
                    if verbose:
                        print(f"\n✓ Proof completed in {iteration + 1} iterations!")

                    # Build complete proof code
                    if not theorem.strip().startswith("theorem"):
                        complete_proof = f"theorem {theorem} := by\n"
                    else:
                        complete_proof = f"{theorem} := by\n"

                    for tactic in current_proof:
                        complete_proof += f"  {tactic}\n"

                    return ProofResult(
                        success=True,
                        theorem=theorem,
                        proof_steps=proof_steps,
                        complete_proof=complete_proof,
                        iterations=iteration + 1,
                    )

            except Exception as e:
                if verbose:
                    print(f"Error in iteration {iteration + 1}: {str(e)}")

                # Record failed step
                step = ProofStep(tactic="", state=str(e), success=False)
                proof_steps.append(step)

        # Max iterations reached without completing proof
        if verbose:
            print(f"\n✗ Failed to complete proof in {max_iter} iterations")

        # Count valid steps
        valid_steps = [s for s in proof_steps if s.success]
        valid_steps_count = len(valid_steps)

        # Generate proof with 'sorry' if enabled and there are valid steps
        complete_proof_with_sorry = None
        if self.config.use_sorry_on_timeout:
            if not theorem.strip().startswith("theorem"):
                complete_proof_with_sorry = f"theorem {theorem} := by\n"
            else:
                complete_proof_with_sorry = f"{theorem} := by\n"

            for step in valid_steps:
                complete_proof_with_sorry += f"  {step.tactic}\n"

            # Add sorry to complete the proof
            complete_proof_with_sorry += "  sorry\n"

            if verbose:
                print(
                    f"\nGenerated proof with {valid_steps_count} valid steps + 'sorry' for incomplete parts"
                )

        return ProofResult(
            success=False,
            theorem=theorem,
            proof_steps=proof_steps,
            complete_proof=complete_proof_with_sorry,
            error=f"Max iterations ({max_iter}) reached without completing proof",
            iterations=max_iter,
            valid_steps_count=valid_steps_count,
        )

    def verify_proof(self, code: str) -> Dict[str, Any]:
        """Verify a Lean 4 proof.

        Args:
            code: Complete Lean 4 code to verify

        Returns:
            Verification result dictionary
        """
        return self.lean_client.verify_proof(code)
