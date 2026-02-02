"""Tests for Lean4Agent configuration."""

import os
import pytest
from lean4agent.config import Config


def test_config_defaults():
    """Test default configuration values."""
    config = Config()

    assert config.llm_provider == "ollama"
    assert config.ollama_url == "http://localhost:11434"
    assert config.ollama_model is None  # No default model
    assert config.openai_model is None  # No default model
    assert config.max_iterations == 50
    assert config.temperature == 0.7
    assert config.timeout == 30


def test_config_custom_values():
    """Test configuration with custom values."""
    config = Config(
        llm_provider="openai", openai_api_key="test-key", max_iterations=100, temperature=0.5
    )

    assert config.llm_provider == "openai"
    assert config.openai_api_key == "test-key"
    assert config.max_iterations == 100
    assert config.temperature == 0.5


def test_config_validation_invalid_provider():
    """Test validation with invalid provider."""
    config = Config(llm_provider="invalid")

    with pytest.raises(ValueError, match="Invalid LLM provider"):
        config.validate_config()


def test_config_validation_missing_openai_key():
    """Test validation with OpenAI but no API key."""
    config = Config(llm_provider="openai")

    with pytest.raises(ValueError, match="OpenAI API key is required"):
        config.validate_config()


def test_config_validation_invalid_iterations():
    """Test validation with invalid max_iterations."""
    config = Config(ollama_model="test-model", max_iterations=0)

    with pytest.raises(ValueError, match="max_iterations must be at least 1"):
        config.validate_config()


def test_config_validation_invalid_temperature():
    """Test validation with invalid temperature."""
    config = Config(ollama_model="test-model", temperature=3.0)

    with pytest.raises(ValueError, match="temperature must be between 0 and 2"):
        config.validate_config()


def test_config_from_env(monkeypatch):
    """Test loading configuration from environment variables."""
    # Set environment variables
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("MAX_ITERATIONS", "100")
    monkeypatch.setenv("TEMPERATURE", "0.5")

    config = Config.from_env()

    assert config.llm_provider == "openai"
    assert config.openai_api_key == "test-key"
    assert config.max_iterations == 100
    assert config.temperature == 0.5


def test_config_from_env_with_overrides(monkeypatch):
    """Test that kwargs override environment variables."""
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("MAX_ITERATIONS", "50")

    config = Config.from_env(
        llm_provider="openai", openai_api_key="override-key", max_iterations=200
    )

    assert config.llm_provider == "openai"
    assert config.openai_api_key == "override-key"
    assert config.max_iterations == 200


def test_config_openai_base_url():
    """Test configuration with custom OpenAI base URL."""
    config = Config(
        llm_provider="openai",
        openai_api_key="test-key",
        openai_base_url="https://api.groq.com/openai/v1",
    )

    assert config.openai_base_url == "https://api.groq.com/openai/v1"


def test_config_use_sorry_on_timeout():
    """Test use_sorry_on_timeout configuration."""
    config_default = Config()
    assert config_default.use_sorry_on_timeout is True

    config_disabled = Config(use_sorry_on_timeout=False)
    assert config_disabled.use_sorry_on_timeout is False


def test_config_from_env_openai_base_url(monkeypatch):
    """Test loading OpenAI base URL from environment variables."""
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.lmstudio.ai/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    config = Config.from_env()

    assert config.openai_base_url == "https://api.lmstudio.ai/v1"


def test_config_from_env_use_sorry_on_timeout(monkeypatch):
    """Test loading use_sorry_on_timeout from environment variables."""
    monkeypatch.setenv("USE_SORRY_ON_TIMEOUT", "false")

    config = Config.from_env()

    assert config.use_sorry_on_timeout is False
