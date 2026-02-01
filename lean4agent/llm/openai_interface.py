"""OpenAI LLM interface."""
from typing import Optional
from lean4agent.llm.base import LLMInterface

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIInterface(LLMInterface):
    """Interface for OpenAI API."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        base_url: Optional[str] = None,
        timeout: int = 30
    ):
        """Initialize OpenAI interface.
        
        Args:
            api_key: OpenAI API key
            model: Model name to use
            base_url: Base URL for OpenAI API (optional, for OpenAI-compatible APIs)
            timeout: Request timeout in seconds
            
        Raises:
            ImportError: If openai package is not installed
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI package is not installed. "
                "Install it with: pip install openai"
            )
        
        client_kwargs = {"api_key": api_key, "timeout": timeout}
        if base_url:
            client_kwargs["base_url"] = base_url
        
        self.client = OpenAI(**client_kwargs)
        self.model = model
        self.timeout = timeout
        self.base_url = base_url
    
    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """Generate text using OpenAI.
        
        Args:
            prompt: Input prompt
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Generated text
            
        Raises:
            Exception: If API call fails
        """
        try:
            messages = [{"role": "user", "content": prompt}]
            
            params = {
                "model": self.model,
                "messages": messages,
            }
            
            if temperature is not None:
                params["temperature"] = temperature
            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            
            params.update(kwargs)
            
            response = self.client.chat.completions.create(**params)
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API call failed: {str(e)}")
    
    def generate_proof_step(
        self,
        theorem: str,
        current_state: str,
        **kwargs
    ) -> str:
        """Generate next proof step.
        
        Args:
            theorem: The theorem to prove
            current_state: Current proof state in Lean 4
            **kwargs: Additional parameters
            
        Returns:
            Next proof step (tactic)
        """
        prompt = f"""Given the following Lean 4 theorem and current proof state, generate the next proof step (tactic).

Theorem:
{theorem}

Current State:
{current_state}

Generate only the next tactic to apply. Do not include explanations or multiple steps.

Next Tactic:"""
        
        response = self.generate(prompt, **kwargs)
        
        # Extract tactic from response
        tactic = response.strip()
        
        # Remove common prefixes if present
        if tactic.startswith("Next Tactic:"):
            tactic = tactic[len("Next Tactic:"):].strip()
        
        # Take only the first line if multiple lines returned
        if "\n" in tactic:
            tactic = tactic.split("\n")[0].strip()
        
        return tactic
