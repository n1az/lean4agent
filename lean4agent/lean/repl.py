"""Lean REPL interface using lean-repl-py for proof verification."""

import sys
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from lean_repl_py import LeanREPLHandler

# Configure UTF-8 encoding for all platforms
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
if hasattr(sys.stdin, 'reconfigure'):
    sys.stdin.reconfigure(encoding='utf-8')


class LeanREPL:
    """Lean verification using lean-repl-py REPL interface."""
    
    def __init__(self, project_path: Optional[Path] = None):
        """Initialize the Lean REPL.
        
        Args:
            project_path: Path to Lean project for dependencies.
                         If None, uses standalone Lean.
        """
        self.project_path = project_path
        self.lean_repl_handler: Optional[LeanREPLHandler] = None
        self._current_env: Optional[int] = None
        
    def start(self) -> None:
        """Initialize the Lean REPL handler."""
        if self.project_path:
            self.lean_repl_handler = LeanREPLHandler(project_path=self.project_path)
        else:
            self.lean_repl_handler = LeanREPLHandler()
        self._current_env = None
        
    def stop(self) -> None:
        """Clean up REPL resources."""
        self.lean_repl_handler = None
        self._current_env = None
                
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        
    def _build_theorem_code(self, theorem: str, tactics: List[str]) -> str:
        """Build complete Lean code for a theorem with tactics."""
        if not theorem.strip().startswith("theorem"):
            code = f"theorem {theorem} := by\n"
        else:
            code = f"{theorem} := by\n"
            
        for tactic in tactics:
            code += f"  {tactic}\n"
            
        return code
    
    def _parse_response_errors(self, response: Dict[str, Any]) -> tuple[bool, str]:
        """Parse REPL response for errors.
        
        Returns:
            Tuple of (has_error, error_message)
        """
        error_msg = ""
        
        # Check messages for errors
        if 'messages' in response and response['messages']:
            for msg in response['messages']:
                if hasattr(msg, 'severity') and msg.severity == 'error':
                    error_msg += f"{msg.message}\n" if hasattr(msg, 'message') else str(msg)
        
        # Check for sorry
        if 'sorries' in response and response['sorries']:
            error_msg += "declaration uses 'sorry'\n"
        
        # Check proof state (unsolved goals)
        if 'proofState' in response and response['proofState']:
            proof_states = response['proofState']
            if proof_states and not error_msg:
                error_msg += "unsolved goals\n"
                for ps in proof_states:
                    if hasattr(ps, 'goal'):
                        error_msg += f"{ps.goal}\n"
        
        has_error = bool(error_msg)
        return has_error, error_msg.strip()
    
    def _is_real_error(self, error_msg: str) -> bool:
        """Check if error is a real tactic error vs just unsolved goals."""
        real_error_indicators = [
            "unknown tactic",
            "unknown identifier",
            "type mismatch",
            "has already been declared",
            "expected type",
            "failed to synthesize"
        ]
        return any(indicator in error_msg.lower() for indicator in real_error_indicators)
    
    def _extract_goal_state(self, error_output: str) -> str:
        """Extract goal state from Lean error output."""
        lines = error_output.split("\n")
        
        for i, line in enumerate(lines):
            if "⊢" in line or "|-" in line or "goal" in line.lower():
                return "\n".join(lines[i:])
        
        return error_output
            
    def check_proof(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Check a complete proof.
        
        Args:
            code: Complete Lean 4 code to verify
            timeout: Timeout (unused, kept for API compatibility)
            
        Returns:
            Dictionary with: success, error, output
        """
        if not self.lean_repl_handler:
            return {
                "success": False,
                "error": "REPL handler not initialized",
                "output": ""
            }
        
        try:
            # Set environment if we have one
            if self._current_env is not None:
                self.lean_repl_handler.env = self._current_env
            
            # Send command and receive response
            self.lean_repl_handler.send_command(code)
            response, env = self.lean_repl_handler.receive_json()
            
            # Update environment for next command
            if hasattr(env, 'env_index'):
                self._current_env = env.env_index
            
            # Parse errors
            has_error, error_msg = self._parse_response_errors(response)
            
            return {
                "success": not has_error,
                "error": error_msg if error_msg else None,
                "output": str(response)
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"REPL communication error: {e}",
                "output": ""
            }
            
    def check_tactic_incremental(
        self,
        theorem: str,
        current_tactics: List[str],
        new_tactic: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Check a new tactic incrementally.
        
        Creates a fresh REPL environment to avoid "already declared" errors.
        
        Args:
            theorem: The theorem statement
            current_tactics: List of tactics already applied
            new_tactic: New tactic to check
            timeout: Timeout (unused, kept for API compatibility)
            
        Returns:
            Dictionary with: success, state, error, complete
        """
        # Reset environment to start fresh
        self._current_env = None
        
        # Build proof with current tactics + new tactic
        code = self._build_theorem_code(theorem, current_tactics + [new_tactic])
        result = self.check_proof(code, timeout)
        
        if result["success"]:
            return {
                "success": True,
                "state": "Proof complete",
                "error": None,
                "complete": True
            }
        
        error_msg = result.get("error", "")
        
        # Check if only unsolved goals (no real errors) - tactic is valid
        if "unsolved goals" in error_msg.lower() and not self._is_real_error(error_msg):
            return {
                "success": True,
                "state": self._extract_goal_state(error_msg),
                "error": None,
                "complete": False
            }
        
        # Real error - tactic is invalid
        return {
            "success": False,
            "state": error_msg,
            "error": error_msg,
            "complete": False
        }
                
    def check_tactics_batch(
        self,
        theorem: str,
        current_tactics: List[str],
        candidate_tactics: List[str],
        timeout: int = 30
    ) -> List[Dict[str, Any]]:
        """Check multiple tactics in batch.
        
        Args:
            theorem: The theorem statement
            current_tactics: List of tactics already applied
            candidate_tactics: List of tactics to check
            timeout: Timeout (unused, kept for API compatibility)
            
        Returns:
            List of results for each tactic
        """
        results = []
        for tactic in candidate_tactics:
            result = self.check_tactic_incremental(
                theorem, current_tactics, tactic, timeout
            )
            result["tactic"] = tactic
            results.append(result)
        return results
