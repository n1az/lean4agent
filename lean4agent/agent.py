"""Main Lean4Agent class for proof generation."""

from typing import Optional, List, Dict, Any
from lean4agent.config import Config
from lean4agent.llm import LLMInterface, OllamaInterface, OpenAIInterface
from lean4agent.lean import LeanClient


class CheckResult:
    """Result of checking a tactic - similar to llmlean's CheckResult."""
    
    PROOF_DONE = "ProofDone"  # Tactic completes the proof
    VALID = "Valid"           # Tactic is valid but proof not complete
    INVALID = "Invalid"       # Tactic is invalid
    
    def __init__(self, status: str, tactic: str = "", state: str = "", error: str = ""):
        self.status = status
        self.tactic = tactic
        self.state = state
        self.error = error
    
    @property
    def is_proof_done(self) -> bool:
        return self.status == self.PROOF_DONE
    
    @property
    def is_valid(self) -> bool:
        return self.status in (self.PROOF_DONE, self.VALID)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "tactic": self.tactic,
            "state": self.state,
            "error": self.error,
            "is_valid": self.is_valid,
            "is_proof_done": self.is_proof_done
        }
    
    def __repr__(self) -> str:
        return f"CheckResult(status='{self.status}', tactic='{self.tactic}')"


class ProofStep:
    """Represents a single proof step."""

    def __init__(self, tactic: str, state: str, success: bool, complete: bool = False):
        """Initialize proof step.

        Args:
            tactic: The tactic applied
            state: Resulting proof state (goals after tactic or error message)
            success: Whether tactic application succeeded
            complete: Whether this tactic completed the proof
        """
        self.tactic = tactic
        self.state = state
        self.success = success
        self.complete = complete

    @property
    def check_result(self) -> CheckResult:
        """Get the check result for this step (llmlean-style)."""
        if self.complete:
            return CheckResult(CheckResult.PROOF_DONE, self.tactic, self.state)
        elif self.success:
            return CheckResult(CheckResult.VALID, self.tactic, self.state)
        else:
            return CheckResult(CheckResult.INVALID, self.tactic, self.state, self.state)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "tactic": self.tactic,
            "state": self.state,
            "success": self.success,
            "complete": self.complete,
            "check_result": self.check_result.status
        }

    def __repr__(self) -> str:
        return f"ProofStep(tactic='{self.tactic}', success={self.success}, complete={self.complete})"


class ProofResult:
    """Result of proof generation attempt.
    
    This class provides llmlean-compatible output formats for integration
    with other tools and for JSON serialization.
    """

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
            success: Whether proof generation succeeded (proof complete)
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
    
    @property
    def has_sorry(self) -> bool:
        """Check if the proof contains 'sorry'."""
        if self.complete_proof:
            return "sorry" in self.complete_proof
        return False
    
    @property
    def is_valid_no_sorry(self) -> bool:
        """Check if proof is valid without sorry (like kimina-lean-server)."""
        return self.success and not self.has_sorry
    
    @property
    def is_valid_with_sorry(self) -> bool:
        """Check if proof is valid (may contain sorry for incomplete parts)."""
        return self.success or (self.valid_steps_count > 0 and self.complete_proof is not None)

    def get_valid_tactics(self) -> List[str]:
        """Get list of valid tactics only.
        
        Returns:
            List of tactic strings that were successfully applied
        """
        return [step.tactic for step in self.proof_steps if step.success]
    
    def get_suggestions(self) -> List[Dict[str, Any]]:
        """Get llmlean-style suggestions list.
        
        Returns a list of suggestions similar to llmlean's format:
        [{"tactic": "...", "status": "ProofDone"|"Valid"|"Invalid"}, ...]
        """
        return [step.to_dict() for step in self.proof_steps]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary with all proof result information
        """
        return {
            "success": self.success,
            "theorem": self.theorem,
            "iterations": self.iterations,
            "valid_steps_count": self.valid_steps_count,
            "total_steps": len(self.proof_steps),
            "has_sorry": self.has_sorry,
            "is_valid_no_sorry": self.is_valid_no_sorry,
            "is_valid_with_sorry": self.is_valid_with_sorry,
            "error": self.error,
            "complete_proof": self.complete_proof,
            "valid_tactics": self.get_valid_tactics(),
            "steps": self.get_suggestions()
        }

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
        self.lean_client = LeanClient(project_path=self.config.lean_project_path)

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

                # Apply tactic in Lean (keeps original theorem name)
                result = self.lean_client.apply_tactic(
                    theorem=theorem, current_proof=current_proof, new_tactic=next_tactic
                )

                # Record the step with complete flag
                step = ProofStep(
                    tactic=next_tactic, 
                    state=result["state"], 
                    success=result["success"],
                    complete=result.get("complete", False)
                )
                proof_steps.append(step)

                if not result["success"]:
                    if verbose:
                        print(f"Tactic failed: {result['error']}")
                    # Don't update current_state - keep previous goal for next iteration
                    continue

                # Tactic succeeded - update proof state
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

    def suggest_tactic(
        self, 
        theorem: str, 
        current_proof: Optional[List[str]] = None,
        num_suggestions: int = 1,
        prefix: str = "",
        verbose: bool = False
    ) -> List[CheckResult]:
        """Generate next-tactic suggestions (llmstep-like functionality).
        
        This is similar to llmlean's `llmstep` tactic - it generates
        suggestions for the next tactic given the current proof state.
        
        Args:
            theorem: The theorem statement
            current_proof: List of tactics already applied (empty for start)
            num_suggestions: Number of suggestions to generate
            prefix: Optional prefix that tactics should start with
            verbose: Whether to print progress
            
        Returns:
            List of CheckResult objects with tactic suggestions and their validity
        """
        current_proof = current_proof or []
        
        # Get current state from Lean
        if current_proof:
            # Apply current proof to get state
            result = self.lean_client.apply_tactic(
                theorem=theorem,
                current_proof=current_proof[:-1] if current_proof else [],
                new_tactic=current_proof[-1] if current_proof else ""
            )
            if current_proof and result["success"]:
                current_state = result["state"]
            else:
                current_state = self.lean_client.get_initial_state(theorem)
        else:
            current_state = self.lean_client.get_initial_state(theorem)
        
        suggestions = []
        seen_tactics = set()
        
        for i in range(num_suggestions):
            try:
                # Generate tactic with some temperature variation
                temp = self.config.temperature + (i * 0.1)  # Increase temp for variety
                next_tactic = self.llm.generate_proof_step(
                    theorem=theorem,
                    current_state=current_state,
                    temperature=min(temp, 2.0),
                )
                
                # Apply prefix filter
                if prefix and not next_tactic.strip().startswith(prefix):
                    continue
                
                # Skip duplicates
                if next_tactic in seen_tactics:
                    continue
                seen_tactics.add(next_tactic)
                
                # Check the tactic
                result = self.lean_client.apply_tactic(
                    theorem=theorem,
                    current_proof=current_proof,
                    new_tactic=next_tactic
                )
                
                if result["complete"]:
                    status = CheckResult.PROOF_DONE
                elif result["success"]:
                    status = CheckResult.VALID
                else:
                    status = CheckResult.INVALID
                
                suggestions.append(CheckResult(
                    status=status,
                    tactic=next_tactic,
                    state=result["state"],
                    error=result.get("error", "")
                ))
                
                if verbose:
                    print(f"Suggestion {len(suggestions)}: {next_tactic} ({status})")
                    
            except Exception as e:
                if verbose:
                    print(f"Error generating suggestion: {e}")
        
        # Sort suggestions: ProofDone first, then Valid, then Invalid
        suggestions.sort(key=lambda x: (
            0 if x.status == CheckResult.PROOF_DONE else
            1 if x.status == CheckResult.VALID else 2
        ))
        
        return suggestions
    
    def get_valid_suggestions(
        self,
        theorem: str,
        current_proof: Optional[List[str]] = None,
        num_suggestions: int = 5,
        prefix: str = "",
        verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """Get only valid tactic suggestions (for integration with other tools).
        
        Returns a list of valid suggestions as dictionaries.
        
        Args:
            theorem: The theorem statement
            current_proof: List of tactics already applied
            num_suggestions: Maximum number of suggestions to try
            prefix: Optional prefix filter
            verbose: Whether to print progress
            
        Returns:
            List of dicts with valid suggestions:
            [{"tactic": "...", "status": "ProofDone"|"Valid", "state": "..."}]
        """
        suggestions = self.suggest_tactic(
            theorem=theorem,
            current_proof=current_proof,
            num_suggestions=num_suggestions,
            prefix=prefix,
            verbose=verbose
        )
        
        return [s.to_dict() for s in suggestions if s.is_valid]
    
    def check_tactic(
        self,
        theorem: str,
        tactic: str,
        current_proof: Optional[List[str]] = None
    ) -> CheckResult:
        """Check if a single tactic is valid.
        
        Args:
            theorem: The theorem statement
            tactic: The tactic to check
            current_proof: List of tactics already applied
            
        Returns:
            CheckResult with the tactic's validity status
        """
        current_proof = current_proof or []
        
        result = self.lean_client.apply_tactic(
            theorem=theorem,
            current_proof=current_proof,
            new_tactic=tactic
        )
        
        if result["complete"]:
            status = CheckResult.PROOF_DONE
        elif result["success"]:
            status = CheckResult.VALID
        else:
            status = CheckResult.INVALID
        
        return CheckResult(
            status=status,
            tactic=tactic,
            state=result["state"],
            error=result.get("error", "")
        )
    
    def check_tactics_batch(
        self,
        theorem: str,
        tactics: List[str],
        current_proof: Optional[List[str]] = None
    ) -> List[CheckResult]:
        """Check multiple tactics in batch.
        
        Args:
            theorem: The theorem statement
            tactics: List of tactics to check
            current_proof: List of tactics already applied
            
        Returns:
            List of CheckResult for each tactic
        """
        current_proof = current_proof or []
        
        results = self.lean_client.check_tactics_batch(
            theorem=theorem,
            current_proof=current_proof,
            candidate_tactics=tactics
        )
        
        check_results = []
        for r in results:
            if r.get("complete", False):
                status = CheckResult.PROOF_DONE
            elif r.get("success", False):
                status = CheckResult.VALID
            else:
                status = CheckResult.INVALID
            
            check_results.append(CheckResult(
                status=status,
                tactic=r.get("tactic", ""),
                state=r.get("state", ""),
                error=r.get("error", "")
            ))
        
        return check_results
