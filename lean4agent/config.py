"""Configuration management for Lean4Agent."""

import os
from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv


class Config(BaseModel):
    """Configuration for Lean4Agent.

    Attributes:
        llm_provider: LLM provider to use ('ollama' or 'openai')
        ollama_url: URL for Ollama API
        ollama_model: Model name for Ollama (required when using ollama)
        openai_api_key: OpenAI API key
        openai_model: OpenAI model name (required when using openai)
        openai_base_url: Base URL for OpenAI API (for OpenAI-compatible APIs)
        lean_project_path: Path to Lean project for dependencies (e.g., mathlib)
        max_iterations: Maximum number of proof generation iterations
        temperature: Temperature for LLM generation
        timeout: Timeout in seconds for API calls
        use_sorry_on_timeout: Whether to generate 'sorry' when max iterations reached
    """

    llm_provider: str = Field(default="ollama", description="LLM provider: 'ollama' or 'openai'")
    ollama_url: str = Field(default="http://localhost:11434", description="Ollama API URL")
    ollama_model: Optional[str] = Field(default=None, description="Ollama model name (required when using ollama)")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_model: Optional[str] = Field(default=None, description="OpenAI model name (required when using openai)")
    openai_base_url: Optional[str] = Field(
        default=None, description="OpenAI API base URL (for OpenAI-compatible APIs)"
    )
    lean_project_path: Optional[Path] = Field(
        default=None, description="Path to Lean project for dependencies (e.g., mathlib)"
    )
    max_iterations: int = Field(default=50, description="Maximum proof generation iterations")
    temperature: float = Field(default=0.7, description="LLM temperature")
    timeout: int = Field(default=30, description="API timeout in seconds")
    use_sorry_on_timeout: bool = Field(
        default=True, description="Use 'sorry' when max iterations reached"
    )

    @classmethod
    def from_env(cls, **kwargs) -> "Config":
        """Create configuration from environment variables.

        Loads .env file if present and reads environment variables.
        Additional kwargs can override environment variables.

        Returns:
            Config instance
        """
        load_dotenv()

        config_dict = {}

        # Load from environment variables
        if os.getenv("LLM_PROVIDER"):
            config_dict["llm_provider"] = os.getenv("LLM_PROVIDER")
        if os.getenv("OLLAMA_URL"):
            config_dict["ollama_url"] = os.getenv("OLLAMA_URL")
        if os.getenv("OLLAMA_MODEL"):
            config_dict["ollama_model"] = os.getenv("OLLAMA_MODEL")
        if os.getenv("OPENAI_API_KEY"):
            config_dict["openai_api_key"] = os.getenv("OPENAI_API_KEY")
        if os.getenv("OPENAI_MODEL"):
            config_dict["openai_model"] = os.getenv("OPENAI_MODEL")
        if os.getenv("OPENAI_BASE_URL"):
            config_dict["openai_base_url"] = os.getenv("OPENAI_BASE_URL")
        if os.getenv("LEAN_PROJECT_PATH"):
            config_dict["lean_project_path"] = Path(os.getenv("LEAN_PROJECT_PATH"))
        if os.getenv("MAX_ITERATIONS"):
            config_dict["max_iterations"] = int(os.getenv("MAX_ITERATIONS"))
        if os.getenv("TEMPERATURE"):
            config_dict["temperature"] = float(os.getenv("TEMPERATURE"))
        if os.getenv("TIMEOUT"):
            config_dict["timeout"] = int(os.getenv("TIMEOUT"))
        if os.getenv("USE_SORRY_ON_TIMEOUT"):
            config_dict["use_sorry_on_timeout"] = os.getenv("USE_SORRY_ON_TIMEOUT").lower() in (
                "true",
                "1",
                "yes",
            )

        # Override with kwargs
        config_dict.update(kwargs)

        return cls(**config_dict)

    def validate_config(self) -> None:
        """Validate configuration settings.

        Raises:
            ValueError: If configuration is invalid
        """
        if self.llm_provider not in ["ollama", "openai"]:
            raise ValueError(f"Invalid LLM provider: {self.llm_provider}")

        if self.llm_provider == "openai":
            if not self.openai_api_key:
                raise ValueError("OpenAI API key is required when using 'openai' provider")
            if not self.openai_model:
                raise ValueError("OpenAI model name is required when using 'openai' provider")
        
        if self.llm_provider == "ollama":
            if not self.ollama_model:
                raise ValueError("Ollama model name is required when using 'ollama' provider")

        if self.max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")

        if not (0 <= self.temperature <= 2):
            raise ValueError("temperature must be between 0 and 2")
