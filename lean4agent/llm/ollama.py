"""Ollama LLM interface."""
import json
import requests
from typing import Optional, Dict, Any
from lean4agent.llm.base import LLMInterface


class OllamaInterface(LLMInterface):
    """Interface for Ollama LLM API."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "bfs-prover-v2:32b",
        timeout: int = 30
    ):
        """Initialize Ollama interface.
        
        Args:
            base_url: Base URL for Ollama API
            model: Model name to use
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
    
    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """Generate text using Ollama.
        
        Args:
            prompt: Input prompt
            temperature: Generation temperature
            max_tokens: Maximum tokens (not used in Ollama)
            **kwargs: Additional parameters
            
        Returns:
            Generated text
            
        Raises:
            requests.RequestException: If API call fails
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if temperature is not None:
            payload["temperature"] = temperature
        
        payload.update(kwargs)
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            raise Exception(f"Ollama API call failed: {str(e)}")
    
    def generate_proof_step(
        self,
        theorem: str,
        current_state: str,
        **kwargs
    ) -> str:
        """Generate next proof step using BFS-Prover-V2 format.
        
        Args:
            theorem: The theorem to prove
            current_state: Current proof state in Lean 4
            **kwargs: Additional parameters
            
        Returns:
            Next proof step (tactic)
        """
        # Format prompt for BFS-Prover-V2
        prompt = f"""Given the following Lean 4 theorem and current proof state, generate the next proof step (tactic).

Theorem:
{theorem}

Current State:
{current_state}

Generate only the next tactic to apply. Do not include explanations or multiple steps.

Next Tactic:"""
        
        response = self.generate(prompt, **kwargs)
        
        # Extract tactic from response (clean up the output)
        tactic = response.strip()
        
        # Remove common prefixes if present
        if tactic.startswith("Next Tactic:"):
            tactic = tactic[len("Next Tactic:"):].strip()
        
        # Take only the first line if multiple lines returned
        if "\n" in tactic:
            tactic = tactic.split("\n")[0].strip()
        
        return tactic
