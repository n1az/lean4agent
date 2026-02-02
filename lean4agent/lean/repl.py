"""Persistent Lean REPL for improved performance.

This module provides a persistent Lean process that can handle multiple
tactic checks without the overhead of process spawning.

Note: The current implementation still uses temporary files and subprocess.run()
for each check, which doesn't provide the full benefits of a persistent REPL.
A future version could use Lean's server mode or LSP for true persistence.
"""

import subprocess
import tempfile
import os
import json
import re
from typing import Optional, Dict, Any, List
from pathlib import Path


class LeanREPL:
    """A manager for Lean verification with optimized file handling.
    
    This class optimizes Lean verification by reusing a temporary directory
    and file across multiple checks, reducing file I/O overhead.
    
    Note: While called "REPL", this implementation still spawns a new Lean
    process for each check. Future versions could implement true process
    persistence using Lean's server mode or LSP.
    """
    
    def __init__(self, lean_executable: str = "lean"):
        """Initialize the REPL.
        
        Args:
            lean_executable: Path to lean executable
        """
        self.lean_executable = lean_executable
        self.temp_dir: Optional[Path] = None
        self.lean_file: Optional[Path] = None
        
    def start(self) -> None:
        """Initialize the temporary directory for Lean file reuse.
        
        Note: Does not start a persistent process yet, just sets up
        the temporary directory to reduce file I/O overhead.
        """
        # Create a temporary directory for the Lean file
        self.temp_dir = Path(tempfile.mkdtemp())
        self.lean_file = self.temp_dir / "check.lean"
        
        # Initialize with empty file
        self.lean_file.write_text("")
        
    def stop(self) -> None:
        """Clean up temporary resources."""
        if self.temp_dir and self.temp_dir.exists():
            try:
                if self.lean_file and self.lean_file.exists():
                    self.lean_file.unlink()
                self.temp_dir.rmdir()
            except OSError:
                pass
                
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
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with verification results:
                - success: bool
                - error: Optional[str]
                - output: str
        """
        # Write code to file with explicit UTF-8 encoding
        self.lean_file.write_text(code, encoding='utf-8')
        
        try:
            # Run lean on the file with UTF-8 encoding
            result = subprocess.run(
                [self.lean_executable, str(self.lean_file)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace any encoding errors with placeholder
                timeout=timeout
            )
            
            success = result.returncode == 0
            error = None if success else result.stderr
            
            return {
                "success": success,
                "error": error,
                "output": result.stdout + result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Lean verification timed out",
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
        
        Args:
            theorem: The theorem statement
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
        # Build proof code using helper
        code = self._build_theorem_code(theorem, current_tactics + [new_tactic])
        
        # Check the proof
        result = self.check_proof(code, timeout)
        
        if result["success"]:
            # Proof is complete
            return {
                "success": True,
                "state": "Proof complete",
                "error": None,
                "complete": True
            }
        else:
            error_msg = result.get("error", "")
            
            # Check if it's partial success (unsolved goals)
            if "unsolved goals" in error_msg.lower() or "goals" in error_msg.lower():
                state = self._extract_goal_state(error_msg)
                return {
                    "success": True,
                    "state": state,
                    "error": None,
                    "complete": False
                }
            else:
                # Tactic failed
                return {
                    "success": False,
                    "state": self._extract_goal_state(error_msg) if error_msg else "Unknown state",
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
        """Check multiple tactics in batch and return results for all.
        
        This is useful when you have multiple LLM-generated tactics and want
        to check which ones are valid.
        
        Args:
            theorem: The theorem statement
            current_tactics: List of tactics already applied
            candidate_tactics: List of tactics to check
            timeout: Timeout in seconds
            
        Returns:
            List of dictionaries, one for each candidate tactic, with:
                - success: bool
                - state: str
                - error: Optional[str]
                - complete: bool
                - tactic: str (the checked tactic)
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
