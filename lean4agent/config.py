"""Configuration management for Lean4Agent."""

import os
from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv


class Config(BaseModel):
    """Configuration for Lean4Agent."""

    llm_provider: str = Field(default="ollama", description="LLM provider: 'ollama' or 'openai'")
    ollama_url: str = Field(default="http://localhost:11434", description="Ollama API URL")
    ollama_model: Optional[str] = Field(default=None, description="Ollama model name")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_model: Optional[str] = Field(default=None, description="OpenAI model name")
    openai_base_url: Optional[str] = Field(default=None, description="OpenAI API base URL")
    lean_project_path: Optional[Path] = Field(default=None, description="Lean project path")
    max_iterations: int = Field(default=50, description="Maximum proof iterations")
    temperature: float = Field(default=0.7, description="LLM temperature")
    timeout: int = Field(default=30, description="API timeout in seconds")
    use_sorry_on_timeout: bool = Field(default=True, description="Use 'sorry' when max iterations reached")

    @classmethod
    def from_env(cls, **kwargs) -> "Config":
        """Create configuration from environment variables.

        Returns:
            Config instance
        """
        load_dotenv()
        config_dict = {}

        # Load from environment
        env_mappings = {
            "LLM_PROVIDER": "llm_provider",
            "OLLAMA_URL": "ollama_url",
            "OLLAMA_MODEL": "ollama_model",
            "OPENAI_API_KEY": "openai_api_key",
            "OPENAI_MODEL": "openai_model",
            "OPENAI_BASE_URL": "openai_base_url",
            "LEAN_PROJECT_PATH": "lean_project_path",
            "MAX_ITERATIONS": "max_iterations",
            "TEMPERATURE": "temperature",
            "TIMEOUT": "timeout",
            "USE_SORRY_ON_TIMEOUT": "use_sorry_on_timeout",
        }

        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                if config_key == "lean_project_path":
                    config_dict[config_key] = Path(value)
                elif config_key in ("max_iterations", "timeout"):
                    config_dict[config_key] = int(value)
                elif config_key == "temperature":
                    config_dict[config_key] = float(value)
                elif config_key == "use_sorry_on_timeout":
                    config_dict[config_key] = value.lower() in ("true", "1", "yes")
                else:
                    config_dict[config_key] = value

        # Override with kwargs
        config_dict.update(kwargs)
        return cls(**config_dict)

    def validate_config(self) -> None:
        """Validate configuration settings."""
        if self.llm_provider not in ["ollama", "openai"]:
            raise ValueError(f"Invalid LLM provider: {self.llm_provider}")

        if self.llm_provider == "openai":
            if not self.openai_api_key:
                raise ValueError("OpenAI API key required when using 'openai' provider")
            if not self.openai_model:
                raise ValueError("OpenAI model name required when using 'openai' provider")
        
        if self.llm_provider == "ollama" and not self.ollama_model:
            raise ValueError("Ollama model name required when using 'ollama' provider")

        if self.max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")

        if not (0 <= self.temperature <= 2):
            raise ValueError("temperature must be between 0 and 2")
