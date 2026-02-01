"""Tests for LLM interfaces."""

import pytest
from unittest.mock import Mock, patch
from lean4agent.llm.ollama import OllamaInterface


def test_ollama_interface_init():
    """Test OllamaInterface initialization."""
    interface = OllamaInterface(base_url="http://localhost:11434", model="test-model", timeout=60)

    assert interface.base_url == "http://localhost:11434"
    assert interface.model == "test-model"
    assert interface.timeout == 60


def test_ollama_interface_generate():
    """Test OllamaInterface generate method."""
    interface = OllamaInterface()

    with patch("requests.post") as mock_post:
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"response": "test output"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = interface.generate("test prompt")

        assert result == "test output"
        mock_post.assert_called_once()


def test_ollama_interface_generate_proof_step():
    """Test OllamaInterface generate_proof_step method."""
    interface = OllamaInterface()

    with patch("requests.post") as mock_post:
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"response": "rfl"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = interface.generate_proof_step(theorem="test : 1 = 1", current_state="⊢ 1 = 1")

        assert result == "rfl"
        mock_post.assert_called_once()


def test_ollama_interface_generate_with_temperature():
    """Test generate with temperature parameter."""
    interface = OllamaInterface()

    with patch("requests.post") as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {"response": "output"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        interface.generate("prompt", temperature=0.5)

        # Check that temperature was included in the request
        call_args = mock_post.call_args
        assert call_args[1]["json"]["temperature"] == 0.5


def test_ollama_interface_error_handling():
    """Test error handling in OllamaInterface."""
    interface = OllamaInterface()

    with patch("requests.post") as mock_post:
        mock_post.side_effect = Exception("Connection error")

        with pytest.raises(Exception, match="Ollama API call failed"):
            interface.generate("test")
