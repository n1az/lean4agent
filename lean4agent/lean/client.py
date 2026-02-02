"""Lean 4 client for proof verification and state management."""

import subprocess
import tempfile
import os
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
from .repl import LeanREPL
from .lsp_client import LeanLSPClient


class LeanClient:
    """Client for interacting with Lean 4.

    This client manages Lean 4 proof verification and state extraction.
    Supports both subprocess-based and LSP-based communication.
    """

    def __init__(
        self, 
        lean_executable: str = "lean", 
        use_repl: bool = True,
        use_lsp: bool = False
    ):
        """Initialize Lean client.

        Args:
            lean_executable: Path to lean executable (default: 'lean')
            use_repl: Whether to use persistent REPL for better performance (default: True)
            use_lsp: Whether to use LSP server for best performance (default: False)
        """
        self.lean_executable = lean_executable
        self.use_repl = use_repl
        self.use_lsp = use_lsp
        self.repl: Optional[LeanREPL] = None
        self.lsp_client: Optional[LeanLSPClient] = None
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        
        self._verify_lean_installation()
        
        # Start REPL if enabled and not using LSP
        if self.use_lsp:
            # Initialize LSP client (will be started when needed)
            self.lsp_client = LeanLSPClient(lean_executable)
        elif self.use_repl:
            self.repl = LeanREPL(lean_executable)
            self.repl.start()
            
    def _get_event_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop for async operations."""
        if self._event_loop is None:
            try:
                self._event_loop = asyncio.get_event_loop()
            except RuntimeError:
                self._event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._event_loop)
        return self._event_loop

    def _verify_lean_installation(self) -> None:
        """Verify that Lean 4 is installed.

        Raises:
            RuntimeError: If Lean 4 is not found
        """
        try:
            result = subprocess.run(
                [self.lean_executable, "--version"], 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                errors='replace',
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("Lean executable found but returned error")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise RuntimeError(
                f"Lean 4 not found. Please install Lean 4 and ensure it's in PATH. Error: {e}"
            )
            
    def close(self) -> None:
        """Explicitly close the REPL/LSP and clean up resources.
        
        This method provides deterministic cleanup. It's recommended to use
        this explicitly or use the client as a context manager.
        """
        if self.lsp_client:
            loop = self._get_event_loop()
            loop.run_until_complete(self.lsp_client.stop())
            self.lsp_client = None
        if self.repl:
            self.repl.stop()
            self.repl = None
            
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
            
    def __del__(self):
        """Cleanup REPL/LSP on deletion.
        
        Note: __del__ is not guaranteed to be called. Use close() or
        context manager for deterministic cleanup.
        """
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
        # Use LSP if available
        if self.lsp_client:
            loop = self._get_event_loop()
            return loop.run_until_complete(self.lsp_client.check_proof(code))
            
        # Use REPL if available
        if self.repl:
            return self.repl.check_proof(code)
            
        # Fall back to subprocess method
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lean", delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_file = f.name

        try:
            result = subprocess.run(
                [self.lean_executable, temp_file], 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                errors='replace',
                timeout=30
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
        # Use LSP if available (highest performance)
        if self.lsp_client:
            loop = self._get_event_loop()
            result = loop.run_until_complete(
                self.lsp_client.check_tactic_incremental(
                    theorem, current_proof, new_tactic
                )
            )
            # Convert LSP result to expected format
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
        # Use LSP if available (best performance)
        if self.lsp_client:
            loop = self._get_event_loop()
            results = loop.run_until_complete(
                self.lsp_client.check_tactics_batch(
                    theorem, current_proof, candidate_tactics
                )
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
