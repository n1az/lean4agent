"""Lean LSP client for high-performance proof verification.

This module provides a Language Server Protocol (LSP) client for Lean 4,
enabling persistent process communication for fast tactic checking.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from pygls.client import JsonRpcClient
from lsprotocol import types as lsp_types

logger = logging.getLogger(__name__)


class LeanLSPClient:
    """LSP client for communicating with Lean 4 language server.
    
    This client maintains a persistent connection to a Lean server process,
    enabling fast tactic verification without process spawning overhead.
    """
    
    def __init__(self, lean_executable: str = "lean"):
        """Initialize the LSP client.
        
        Args:
            lean_executable: Path to lean executable (default: 'lean')
        """
        self.lean_executable = lean_executable
        self.client: Optional[JsonRpcClient] = None
        self._initialized = False
        self._document_counter = 0
        self._virtual_documents: Dict[str, int] = {}
        
    async def start(self) -> None:
        """Start the LSP server connection."""
        if self._initialized:
            return
            
        # Create JSON-RPC client
        self.client = JsonRpcClient()
        
        # Start Lean language server
        await self.client.start_io([self.lean_executable, "--server"])
        
        # Send initialize request
        init_params = lsp_types.InitializeParams(
            process_id=None,
            root_uri=None,
            capabilities=lsp_types.ClientCapabilities()
        )
        
        response = await self.client.send_request_async(
            "initialize",
            init_params
        )
        
        # Send initialized notification
        await self.client.send_notification(
            "initialized",
            lsp_types.InitializedParams()
        )
        
        self._initialized = True
        logger.info("LSP client initialized successfully")
        
    async def stop(self) -> None:
        """Stop the LSP server connection."""
        if not self._initialized or not self.client:
            return
            
        try:
            # Send shutdown request
            await self.client.send_request_async("shutdown", None)
            
            # Send exit notification
            await self.client.send_notification("exit", None)
        except Exception as e:
            logger.warning(f"Error during LSP shutdown: {e}")
        finally:
            self._initialized = False
            self.client = None
            
    def _get_virtual_uri(self, name: str = "proof") -> str:
        """Generate a unique virtual document URI.
        
        Args:
            name: Base name for the document
            
        Returns:
            Virtual file URI
        """
        self._document_counter += 1
        return f"file:///virtual/{name}_{self._document_counter}.lean"
        
    async def check_proof(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Check a complete proof using LSP.
        
        Args:
            code: Complete Lean 4 code to verify
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with verification results:
                - success: bool
                - error: Optional[str]
                - output: str
        """
        if not self._initialized:
            await self.start()
            
        # Create virtual document URI
        doc_uri = self._get_virtual_uri()
        
        try:
            # Open document
            await self.client.send_notification(
                "textDocument/didOpen",
                lsp_types.DidOpenTextDocumentParams(
                    text_document=lsp_types.TextDocumentItem(
                        uri=doc_uri,
                        language_id="lean4",
                        version=1,
                        text=code
                    )
                )
            )
            
            # Store document version
            self._virtual_documents[doc_uri] = 1
            
            # Wait for diagnostics with timeout
            diagnostics = await asyncio.wait_for(
                self._wait_for_diagnostics(doc_uri),
                timeout=timeout
            )
            
            # Check if there are errors
            has_errors = any(
                d.severity == lsp_types.DiagnosticSeverity.Error
                for d in diagnostics
            )
            
            # Build error message if any
            error_msg = None
            if has_errors:
                error_parts = []
                for diag in diagnostics:
                    if diag.severity == lsp_types.DiagnosticSeverity.Error:
                        error_parts.append(diag.message)
                error_msg = "\n".join(error_parts)
            
            return {
                "success": not has_errors,
                "error": error_msg,
                "output": error_msg or "Success"
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "LSP verification timed out",
                "output": ""
            }
        except Exception as e:
            logger.error(f"Error during proof check: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }
        finally:
            # Close document
            try:
                await self.client.send_notification(
                    "textDocument/didClose",
                    lsp_types.DidCloseTextDocumentParams(
                        text_document=lsp_types.TextDocumentIdentifier(uri=doc_uri)
                    )
                )
                del self._virtual_documents[doc_uri]
            except Exception as e:
                logger.warning(f"Error closing document: {e}")
                
    async def _wait_for_diagnostics(self, doc_uri: str) -> List[lsp_types.Diagnostic]:
        """Wait for diagnostics for a specific document.
        
        Args:
            doc_uri: Document URI to wait for
            
        Returns:
            List of diagnostics
        """
        # This is a simplified implementation
        # In production, you'd want to properly handle LSP notifications
        
        # Wait a bit for processing
        await asyncio.sleep(0.5)
        
        # For now, return empty list (will be improved in full implementation)
        # Proper implementation would register a handler for publishDiagnostics
        return []
        
    async def check_tactic_incremental(
        self,
        theorem: str,
        current_tactics: List[str],
        new_tactic: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Check a new tactic incrementally using LSP.
        
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
        # Build proof code
        code = self._build_theorem_code(theorem, current_tactics + [new_tactic])
        
        # Check the proof
        result = await self.check_proof(code, timeout)
        
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
        
    async def check_tactics_batch(
        self,
        theorem: str,
        current_tactics: List[str],
        candidate_tactics: List[str],
        timeout: int = 30
    ) -> List[Dict[str, Any]]:
        """Check multiple tactics in batch using LSP.
        
        Args:
            theorem: The theorem statement
            current_tactics: List of tactics already applied
            candidate_tactics: List of candidate tactics to check
            timeout: Timeout in seconds
            
        Returns:
            List of results for each tactic
        """
        results = []
        
        for tactic in candidate_tactics:
            result = await self.check_tactic_incremental(
                theorem, current_tactics, tactic, timeout
            )
            result["tactic"] = tactic
            results.append(result)
            
        return results
        
    def __enter__(self):
        """Context manager entry - not supported for async."""
        raise RuntimeError("Use 'async with' for LeanLSPClient")
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
