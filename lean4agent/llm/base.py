"""Base interface for LLM providers."""

from abc import ABC, abstractmethod
from typing import Optional


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
            prompt: Input prompt
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text
        """
        pass

    def _extract_tactic(self, response: str) -> str:
        """Extract clean tactic from LLM response.

        Args:
            response: Raw LLM response

        Returns:
            Cleaned tactic string
        """
        tactic = response.strip()
        
        # Remove common prefixes
        if tactic.startswith("Next Tactic:"):
            tactic = tactic[12:].strip()
        
        # Take only first line
        if "\n" in tactic:
            tactic = tactic.split("\n")[0].strip()
        
        return tactic

    def _build_proof_step_prompt(self, theorem: str, current_state: str) -> str:
        """Build standard prompt for proof step generation.

        Args:
            theorem: The theorem to prove
            current_state: Current proof state

        Returns:
            Formatted prompt string
        """
        return f"""Given the following Lean 4 theorem and current proof state, generate the next proof step (tactic).

Theorem:
{theorem}

Current State:
{current_state}

Generate only the next tactic to apply. Do not include explanations or multiple steps.

Next Tactic:"""

    @abstractmethod
    def generate_proof_step(self, theorem: str, current_state: str, **kwargs) -> str:
        """Generate next proof step given current state.

        Args:
            theorem: The theorem to prove
            current_state: Current proof state
            **kwargs: Additional parameters

        Returns:
            Next proof step (tactic)
        """
        pass
