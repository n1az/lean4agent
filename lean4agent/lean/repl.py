"""Lean REPL interface using lean-repl-py for proof verification.

This module provides a persistent Lean REPL that handles multiple tactic checks
without process spawning or temp file overhead, using lean-repl-py.
"""

import sys
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from lean_repl_py import LeanREPLHandler, LeanREPLEnvironment

# Ensure UTF-8 encoding for all platforms (subprocess pipe communication)
# This is needed because lean-repl-py uses subprocess.Popen with text=True,
# which defaults to system encoding (cp1252 on Windows, varies on Linux/Mac)
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Reconfigure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
if hasattr(sys.stdin, 'reconfigure'):
    sys.stdin.reconfigure(encoding='utf-8')


class LeanREPL:
    """Manager for Lean verification using lean-repl-py REPL interface.
    
    Provides persistent Lean process communication via stdin/stdout with no temp files.
    """
    
    def __init__(self, project_path: Optional[Path] = None):
        """Initialize the Lean REPL.
        
        Args:
            project_path: Path to Lean project for dependencies (e.g., mathlib).
                         If None, uses standalone Lean with no external dependencies.
        """
        self.project_path = project_path
        self.lean_repl_handler: Optional[LeanREPLHandler] = None
        self._current_env: Optional[int] = None
        
    def start(self) -> None:
        """Initialize the Lean REPL handler.
        
        UTF-8 encoding is already set at module level to ensure proper
        subprocess communication for all platforms.
        """
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
        """Build complete Lean code for a theorem with tactics.
        
        Args:
            theorem: The theorem statement
            tactics: List of tactics to apply
            
        Returns:
            Complete Lean code
        """
        if not theorem.strip().startswith("theorem"):
            code = f"theorem {theorem} := by\n"
        else:
            code = f"{theorem} := by\n"
            
        for tactic in tactics:
            code += f"  {tactic}\n"
            
        return code
            
    def check_proof(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Check a complete proof.
        
        Args:
            code: Complete Lean 4 code to verify
            timeout: Timeout in seconds (unused, kept for API compatibility)
            
        Returns:
            Dictionary with verification results:
                - success: bool
                - error: Optional[str]
                - output: str
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
            
            # Send command to Lean REPL
            self.lean_repl_handler.send_command(code)
            response, env = self.lean_repl_handler.receive_json()
            
            # Update environment for next command
            if hasattr(env, 'env_index'):
                self._current_env = env.env_index
            
            # Parse response for errors
            has_error = False
            error_msg = ""
            
            # Check messages for errors
            if 'messages' in response and response['messages']:
                for msg in response['messages']:
                    if hasattr(msg, 'severity') and msg.severity == 'error':
                        has_error = True
                        error_msg += f"{msg.message}\n" if hasattr(msg, 'message') else str(msg)
            
            # Check for sorry
            if 'sorries' in response and response['sorries']:
                has_error = True
                error_msg += "declaration uses 'sorry'\n"
            
            # Check proof state (unsolved goals)
            if 'proofState' in response and response['proofState']:
                proof_states = response['proofState']
                if proof_states and not has_error:
                    # Unsolved goals without other errors means partial success
                    error_msg += "unsolved goals\n"
                    for ps in proof_states:
                        if hasattr(ps, 'goal'):
                            error_msg += f"{ps.goal}\n"
            
            success = not has_error
            
            return {
                "success": success,
                "error": error_msg.strip() if error_msg else None,
                "output": str(response)
            }
                
        except UnicodeEncodeError as e:
            return {
                "success": False,
                "error": f"Unicode encoding error (Windows UTF-8 issue): {e}. Try setting PYTHONIOENCODING=utf-8",
                "output": ""
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
        """Check a new tactic incrementally without redeclaring the theorem.
        
        This creates a fresh REPL environment for each check to avoid 
        "already declared" errors, while keeping the original theorem name.
        
        Args:
            theorem: The theorem statement (original name preserved)
            current_tactics: List of tactics already applied
            new_tactic: New tactic to check
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with:
                - success: bool
                - state: str
                - error: Optional[str]
                - complete: bool
        """
        # Reset environment to start fresh (avoids "already declared" errors)
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
        else:
            error_msg = result.get("error", "")
            
            # Check if there are actual errors (not just unsolved goals)
            has_real_error = False
            if error_msg:
                # Real errors: unknown tactic, type mismatch, etc.
                real_error_indicators = [
                    "unknown tactic",
                    "unknown identifier",
                    "type mismatch",
                    "has already been declared",
                    "expected type",
                    "failed to synthesize"
                ]
                for indicator in real_error_indicators:
                    if indicator in error_msg.lower():
                        has_real_error = True
                        break
            
            # If only "unsolved goals" (no real errors), tactic is valid but proof incomplete
            if "unsolved goals" in error_msg.lower() and not has_real_error:
                state = self._extract_goal_state(error_msg)
                return {
                    "success": True,
                    "state": state,
                    "error": None,
                    "complete": False
                }
            else:
                # Real error - tactic is invalid
                return {
                    "success": False,
                    "state": error_msg,  # Keep original goal, not error
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
            timeout: Timeout in seconds
            
        Returns:
            List of dictionaries with results for each tactic
        """
        results = []
        
        for tactic in candidate_tactics:
            result = self.check_tactic_incremental(
                theorem, current_tactics, tactic, timeout
            )
            result["tactic"] = tactic
            results.append(result)
            
        return results
        
    def _extract_goal_state(self, error_output: str) -> str:
        """Extract goal state from Lean error output.
        
        Args:
            error_output: Error output from Lean
            
        Returns:
            Extracted goal state
        """
        lines = error_output.split("\n")
        
        # Look for goal indicators
        goal_start = -1
        for i, line in enumerate(lines):
            if "⊢" in line or "|-" in line or "goal" in line.lower():
                goal_start = i
                break
                
        if goal_start >= 0:
            return "\n".join(lines[goal_start:])
            
        return error_output
