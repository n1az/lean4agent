"""Base interface for LLM providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class LLMInterface(ABC):
    """Abstract base class for LLM interfaces."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Generate text from the LLM.

        Args:
            prompt: Input prompt for the LLM
            temperature: Temperature for generation (optional)
            max_tokens: Maximum tokens to generate (optional)
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text

        Raises:
            Exception: If generation fails
        """
        pass

    @abstractmethod
    def generate_proof_step(self, theorem: str, current_state: str, **kwargs) -> str:
        """Generate next proof step given current state.

        Args:
            theorem: The theorem to prove
            current_state: Current proof state
            **kwargs: Additional parameters

        Returns:
            Next proof step
        """
        pass
