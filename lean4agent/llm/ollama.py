"""Ollama LLM interface."""

import requests
from typing import Optional
from lean4agent.llm.base import LLMInterface


class OllamaInterface(LLMInterface):
    """Interface for Ollama LLM API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "bfs-prover-v2:32b",
        timeout: int = 30,
    ):
        """Initialize Ollama interface.

        Args:
            base_url: Base URL for Ollama API
            model: Model name
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
        **kwargs,
    ) -> str:
        """Generate text using Ollama.

        Args:
            prompt: Input prompt
            temperature: Generation temperature
            max_tokens: Maximum tokens (unused in Ollama)
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        url = f"{self.base_url}/api/generate"
        payload = {"model": self.model, "prompt": prompt, "stream": False}

        if temperature is not None:
            payload["temperature"] = temperature

        payload.update(kwargs)

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            raise Exception(f"Ollama API call failed: {str(e)}")

    def generate_proof_step(self, theorem: str, current_state: str, **kwargs) -> str:
        """Generate next proof step.

        Args:
            theorem: The theorem to prove
            current_state: Current proof state
            **kwargs: Additional parameters

        Returns:
            Next proof step (tactic)
        """
        prompt = self._build_proof_step_prompt(theorem, current_state)
        response = self.generate(prompt, **kwargs)
        return self._extract_tactic(response)
