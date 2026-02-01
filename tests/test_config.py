"""Tests for Lean4Agent configuration."""
import os
import pytest
from lean4agent.config import Config


def test_config_defaults():
    """Test default configuration values."""
    config = Config()
    
    assert config.llm_provider == "ollama"
    assert config.ollama_url == "http://localhost:11434"
    assert config.ollama_model == "bfs-prover-v2:32b"
    assert config.openai_model == "gpt-4"
    assert config.max_iterations == 50
    assert config.temperature == 0.7
    assert config.timeout == 30


def test_config_custom_values():
    """Test configuration with custom values."""
    config = Config(
        llm_provider="openai",
        openai_api_key="test-key",
        max_iterations=100,
        temperature=0.5
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
    config = Config(max_iterations=0)
    
    with pytest.raises(ValueError, match="max_iterations must be at least 1"):
        config.validate_config()


def test_config_validation_invalid_temperature():
    """Test validation with invalid temperature."""
    config = Config(temperature=3.0)
    
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
        llm_provider="openai",
        openai_api_key="override-key",
        max_iterations=200
    )
    
    assert config.llm_provider == "openai"
    assert config.openai_api_key == "override-key"
    assert config.max_iterations == 200
