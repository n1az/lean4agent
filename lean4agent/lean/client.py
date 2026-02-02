"""Lean 4 client for proof verification and state management."""

import subprocess
import tempfile
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from .repl import LeanREPL


class LeanClient:
    """Client for interacting with Lean 4.

    This client manages Lean 4 proof verification and state extraction.
    """

    def __init__(self, lean_executable: str = "lean", use_repl: bool = True):
        """Initialize Lean client.

        Args:
            lean_executable: Path to lean executable (default: 'lean')
            use_repl: Whether to use persistent REPL for better performance (default: True)
        """
        self.lean_executable = lean_executable
        self.use_repl = use_repl
        self.repl: Optional[LeanREPL] = None
        self._verify_lean_installation()
        
        # Start REPL if enabled
        if self.use_repl:
            self.repl = LeanREPL(lean_executable)
            self.repl.start()

    def _verify_lean_installation(self) -> None:
        """Verify that Lean 4 is installed.

        Raises:
            RuntimeError: If Lean 4 is not found
        """
        try:
            result = subprocess.run(
                [self.lean_executable, "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("Lean executable found but returned error")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise RuntimeError(
                f"Lean 4 not found. Please install Lean 4 and ensure it's in PATH. Error: {e}"
            )
            
    def __del__(self):
        """Cleanup REPL on deletion."""
        if self.repl:
            self.repl.stop()

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
        # Use REPL if available
        if self.repl:
            return self.repl.check_proof(code)
            
        # Fall back to subprocess method
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lean", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            result = subprocess.run(
                [self.lean_executable, temp_file], capture_output=True, text=True, timeout=30
            )

            success = result.returncode == 0
            error = None if success else result.stderr

            return {"success": success, "error": error, "output": result.stdout + result.stderr}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Lean verification timed out", "output": ""}
        finally:
            try:
                os.unlink(temp_file)
            except OSError:
                pass  # Temporary file cleanup - ignore if already deleted

    def apply_tactic(
        self, theorem: str, current_proof: List[str], new_tactic: str
    ) -> Dict[str, Any]:
        """Apply a tactic and get the new proof state.

        Args:
            theorem: The theorem statement
            current_proof: List of tactics applied so far
            new_tactic: New tactic to apply

        Returns:
            Dictionary with:
                - success: bool - whether tactic application succeeded
                - proof: List[str] - updated proof steps
                - state: str - current proof state
                - error: Optional[str] - error message if failed
                - complete: bool - whether proof is complete
        """
        # Use REPL if available for better performance
        if self.repl:
            result = self.repl.check_tactic_incremental(
                theorem, current_proof, new_tactic
            )
            # Convert REPL result to expected format
            if result["success"]:
                return {
                    "success": True,
                    "proof": current_proof + [new_tactic],
                    "state": result["state"],
                    "error": None,
                    "complete": result["complete"]
                }
            else:
                return {
                    "success": False,
                    "proof": current_proof,
                    "state": result["state"],
                    "error": result["error"],
                    "complete": False
                }
        
        # Fall back to original implementation
        # Build the proof code
        proof_lines = current_proof + [new_tactic]

        # Create complete Lean code with proof
        if not theorem.strip().startswith("theorem"):
            code = f"theorem {theorem} := by\n"
        else:
            code = f"{theorem} := by\n"

        for tactic in proof_lines:
            code += f"  {tactic}\n"

        # Verify the proof
        result = self.verify_proof(code)

        # Parse the result
        if result["success"]:
            # Proof is complete
            return {
                "success": True,
                "proof": proof_lines,
                "state": "Proof complete",
                "error": None,
                "complete": True,
            }
        else:
            # Check if it's a partial success (tactic applied but proof incomplete)
            error_msg = result.get("error", "")

            # If error indicates unsolved goals, it's partial success
            if "unsolved goals" in error_msg.lower() or "goals" in error_msg.lower():
                # Extract the goal state from error message
                state = self._extract_goal_state(error_msg)
                return {
                    "success": True,
                    "proof": proof_lines,
                    "state": state,
                    "error": None,
                    "complete": False,
                }
            else:
                # Tactic failed
                return {
                    "success": False,
                    "proof": current_proof,
                    "state": self._extract_goal_state(error_msg) if error_msg else "Unknown state",
                    "error": error_msg,
                    "complete": False,
                }

    def _extract_goal_state(self, error_output: str) -> str:
        """Extract goal state from Lean error output.

        Args:
            error_output: Error output from Lean

        Returns:
            Extracted goal state or the full error if extraction fails
        """
        # Try to extract goals from error message
        lines = error_output.split("\n")

        # Look for goal indicators
        goal_start = -1
        for i, line in enumerate(lines):
            if "⊢" in line or "|-" in line or "goal" in line.lower():
                goal_start = i
                break

        if goal_start >= 0:
            # Return from goal start onwards
            return "\n".join(lines[goal_start:])

        # Return full error if we can't extract
        return error_output
        
    def check_tactics_batch(
        self,
        theorem: str,
        current_proof: List[str],
        candidate_tactics: List[str]
    ) -> List[Dict[str, Any]]:
        """Check multiple tactics in batch and return the first valid one.
        
        This is optimized for BFS-Prover models that generate multiple
        candidate tactics. It checks them efficiently and returns results.
        
        Args:
            theorem: The theorem statement
            current_proof: List of tactics applied so far
            candidate_tactics: List of candidate tactics to check
            
        Returns:
            List of results for each tactic, with:
                - success: bool
                - proof: List[str]
                - state: str
                - error: Optional[str]
                - complete: bool
                - tactic: str
        """
        if self.repl:
            # Use REPL batch checking for better performance
            results = self.repl.check_tactics_batch(
                theorem, current_proof, candidate_tactics
            )
            # Convert to expected format
            converted_results = []
            for result in results:
                if result["success"]:
                    converted_results.append({
                        "success": True,
                        "proof": current_proof + [result["tactic"]],
                        "state": result["state"],
                        "error": None,
                        "complete": result["complete"],
                        "tactic": result["tactic"]
                    })
                else:
                    converted_results.append({
                        "success": False,
                        "proof": current_proof,
                        "state": result["state"],
                        "error": result["error"],
                        "complete": False,
                        "tactic": result["tactic"]
                    })
            return converted_results
        
        # Fall back to sequential checking
        results = []
        for tactic in candidate_tactics:
            result = self.apply_tactic(theorem, current_proof, tactic)
            result["tactic"] = tactic
            results.append(result)
        return results

    def get_initial_state(self, theorem: str) -> str:
        """Get the initial proof state for a theorem.

        Args:
            theorem: The theorem statement

        Returns:
            Initial proof state
        """
        # For a new theorem, the initial state is the theorem itself
        return f"Goal: {theorem}"
