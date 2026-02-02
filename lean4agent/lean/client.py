"""Lean 4 client for proof verification and state management."""

from typing import Optional, Dict, Any, List
from pathlib import Path
from .repl import LeanREPL


class LeanClient:
    """Client for interacting with Lean 4.

    This client manages Lean 4 proof verification and state extraction
    using lean-repl-py for persistent REPL communication.
    """

    def __init__(self, project_path: Optional[Path] = None):
        """Initialize Lean client.

        Args:
            project_path: Path to Lean project for dependencies (e.g., mathlib).
                         If None, uses standalone Lean.
        """
        self.project_path = project_path
        self.repl = LeanREPL(project_path=project_path)
        self.repl.start()
            
    def close(self) -> None:
        """Explicitly close the REPL and clean up resources."""
        if self.repl:
            self.repl.stop()
            
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
            
    def __del__(self):
        """Cleanup REPL on deletion."""
        self.close()

    def verify_proof(self, code: str) -> Dict[str, Any]:
        """Verify a Lean 4 proof.

        Args:
            code: Complete Lean 4 code to verify

        Returns:
            Dictionary with verification results:
                - success: bool - whether verification succeeded
                - error: Optional[str] - error message if failed
                - output: str - full output from Lean
        """
        return self.repl.check_proof(code)

    def get_initial_state(self, theorem: str) -> str:
        """Get the initial proof state for a theorem.

        Args:
            theorem: The theorem statement

        Returns:
            Initial proof state string
        """
        # For a new theorem, the initial state is the goal
        return f"Goal: {theorem}"

    def apply_tactic(
        self, theorem: str, current_proof: List[str], new_tactic: str
    ) -> Dict[str, Any]:
        """Apply a tactic to the current proof state.

        Args:
            theorem: The theorem statement (original name preserved)
            current_proof: List of tactics applied so far
            new_tactic: New tactic to apply

        Returns:
            Dictionary with:
                - success: bool - whether tactic was valid
                - complete: bool - whether proof is complete
                - state: str - resulting proof state or error
                - error: Optional[str] - error message if invalid
                - proof: List[str] - updated proof if successful
        """
        result = self.repl.check_tactic_incremental(
            theorem=theorem,
            current_tactics=current_proof,
            new_tactic=new_tactic
        )
        
        # Add updated proof list to result
        if result["success"]:
            result["proof"] = current_proof + [new_tactic]
        else:
            result["proof"] = current_proof
        
        return {
            "success": result["success"],
            "complete": result["complete"],
            "state": result["state"],
            "error": result.get("error"),
            "proof": result.get("proof", current_proof)
        }

    def check_tactics_batch(
        self, theorem: str, current_proof: List[str], candidate_tactics: List[str]
    ) -> List[Dict[str, Any]]:
        """Check multiple candidate tactics in batch.

        Args:
            theorem: The theorem statement
            current_proof: List of tactics applied so far
            candidate_tactics: List of tactics to check

        Returns:
            List of results for each tactic
        """
        return self.repl.check_tactics_batch(
            theorem=theorem,
            current_tactics=current_proof,
            candidate_tactics=candidate_tactics
        )
