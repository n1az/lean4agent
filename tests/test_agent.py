"""Tests for Lean4Agent main functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from lean4agent import Lean4Agent, Config
from lean4agent.agent import ProofStep, ProofResult


def test_proof_step_creation():
    """Test ProofStep creation."""
    step = ProofStep(tactic="rfl", state="complete", success=True)

    assert step.tactic == "rfl"
    assert step.state == "complete"
    assert step.success is True


def test_proof_result_creation():
    """Test ProofResult creation."""
    steps = [ProofStep("rfl", "complete", True)]
    result = ProofResult(
        success=True,
        theorem="test : 1 = 1",
        proof_steps=steps,
        complete_proof="theorem test : 1 = 1 := by\n  rfl\n",
        iterations=1,
    )

    assert result.success is True
    assert result.theorem == "test : 1 = 1"
    assert len(result.proof_steps) == 1
    assert result.iterations == 1


def test_proof_result_get_proof_code():
    """Test ProofResult.get_proof_code method."""
    steps = [ProofStep("intro x", "state1", True), ProofStep("rfl", "complete", True)]
    result = ProofResult(
        success=True, theorem="test (x : Nat) : x = x", proof_steps=steps, iterations=2
    )

    code = result.get_proof_code()
    assert "theorem test (x : Nat) : x = x := by" in code
    assert "intro x" in code
    assert "rfl" in code


def test_lean4agent_initialization():
    """Test Lean4Agent initialization with config."""
    config = Config(llm_provider="ollama", ollama_model="test-model")

    with patch("lean4agent.agent.LeanClient"):
        agent = Lean4Agent(config)
        assert agent.config.llm_provider == "ollama"


def test_lean4agent_initialization_from_env():
    """Test Lean4Agent initialization from environment."""
    with patch("lean4agent.agent.LeanClient"):
        with patch.object(Config, "from_env") as mock_from_env:
            mock_from_env.return_value = Config(llm_provider="ollama", ollama_model="test-model")
            agent = Lean4Agent()
            mock_from_env.assert_called_once()


def test_lean4agent_create_ollama_interface():
    """Test LLM interface creation for Ollama."""
    config = Config(llm_provider="ollama", ollama_model="test-model")

    with patch("lean4agent.agent.LeanClient"):
        agent = Lean4Agent(config)
        from lean4agent.llm import OllamaInterface

        assert isinstance(agent.llm, OllamaInterface)


def test_lean4agent_invalid_provider():
    """Test error on invalid LLM provider."""
    config = Config(llm_provider="invalid")

    with patch("lean4agent.agent.LeanClient"):
        with pytest.raises(ValueError):
            config.validate_config()


def test_lean4agent_generate_proof_success():
    """Test successful proof generation."""
    config = Config(llm_provider="ollama", ollama_model="test-model")

    with patch("lean4agent.agent.LeanClient") as MockLeanClient:
        # Mock LeanClient
        mock_lean = MockLeanClient.return_value
        mock_lean.get_initial_state.return_value = "⊢ 1 = 1"
        mock_lean.apply_tactic.return_value = {
            "success": True,
            "proof": ["rfl"],
            "state": "complete",
            "complete": True,
            "error": None,
        }

        agent = Lean4Agent(config)

        # Mock LLM
        agent.llm.generate_proof_step = Mock(return_value="rfl")

        result = agent.generate_proof("test : 1 = 1")

        assert result.success is True
        assert result.iterations == 1
        assert len(result.proof_steps) == 1
        assert result.proof_steps[0].tactic == "rfl"


def test_lean4agent_generate_proof_max_iterations():
    """Test proof generation reaching max iterations."""
    config = Config(llm_provider="ollama", ollama_model="test-model", max_iterations=3)

    with patch("lean4agent.agent.LeanClient") as MockLeanClient:
        mock_lean = MockLeanClient.return_value
        mock_lean.get_initial_state.return_value = "⊢ goal"
        mock_lean.apply_tactic.return_value = {
            "success": True,
            "proof": ["step"],
            "state": "⊢ goal",
            "complete": False,
            "error": None,
        }

        agent = Lean4Agent(config)
        agent.llm.generate_proof_step = Mock(return_value="step")

        result = agent.generate_proof("test : goal")

        assert result.success is False
        assert result.iterations == 3
        assert "Max iterations" in result.error


def test_lean4agent_verify_proof():
    """Test proof verification."""
    config = Config(llm_provider="ollama", ollama_model="test-model")

    with patch("lean4agent.agent.LeanClient") as MockLeanClient:
        mock_lean = MockLeanClient.return_value
        mock_lean.verify_proof.return_value = {"success": True, "error": None, "output": "verified"}

        agent = Lean4Agent(config)
        result = agent.verify_proof("theorem test : 1 = 1 := by rfl")

        assert result["success"] is True
        mock_lean.verify_proof.assert_called_once()


def test_proof_result_valid_steps_count():
    """Test ProofResult tracks valid steps count."""
    steps = [
        ProofStep("intro x", "state1", True),
        ProofStep("bad_tactic", "error", False),
        ProofStep("rfl", "complete", True),
    ]
    result = ProofResult(success=False, theorem="test : goal", proof_steps=steps, iterations=3)

    assert result.valid_steps_count == 2


def test_proof_result_get_proof_status_summary():
    """Test proof status summary generation."""
    steps = [
        ProofStep("intro x", "state1", True),
        ProofStep("bad_tactic", "error: unknown tactic", False),
        ProofStep("rfl", "complete", True),
    ]
    result = ProofResult(
        success=False,
        theorem="test : goal",
        proof_steps=steps,
        error="Max iterations reached",
        iterations=3,
        valid_steps_count=2,
    )

    summary = result.get_proof_status_summary()
    assert "Valid steps: 2" in summary
    assert "intro x" in summary
    assert "First invalid step" in summary
    assert "bad_tactic" in summary


def test_lean4agent_sorry_on_timeout():
    """Test that 'sorry' is added when max iterations reached."""
    config = Config(llm_provider="ollama", ollama_model="test-model", max_iterations=2, use_sorry_on_timeout=True)

    with patch("lean4agent.agent.LeanClient") as MockLeanClient:
        mock_lean = MockLeanClient.return_value
        mock_lean.get_initial_state.return_value = "⊢ goal"
        mock_lean.apply_tactic.return_value = {
            "success": True,
            "proof": ["step1"],
            "state": "⊢ goal",
            "complete": False,
            "error": None,
        }

        agent = Lean4Agent(config)
        agent.llm.generate_proof_step = Mock(return_value="step1")

        result = agent.generate_proof("test : goal")

        assert result.success is False
        assert result.complete_proof is not None
        assert "sorry" in result.complete_proof
        assert "step1" in result.complete_proof


def test_lean4agent_no_sorry_when_disabled():
    """Test that 'sorry' is not added when disabled."""
    config = Config(llm_provider="ollama", ollama_model="test-model", max_iterations=2, use_sorry_on_timeout=False)

    with patch("lean4agent.agent.LeanClient") as MockLeanClient:
        mock_lean = MockLeanClient.return_value
        mock_lean.get_initial_state.return_value = "⊢ goal"
        mock_lean.apply_tactic.return_value = {
            "success": True,
            "proof": ["step1"],
            "state": "⊢ goal",
            "complete": False,
            "error": None,
        }

        agent = Lean4Agent(config)
        agent.llm.generate_proof_step = Mock(return_value="step1")

        result = agent.generate_proof("test : goal")

        assert result.success is False
        # When sorry is disabled, complete_proof should be None
        assert result.complete_proof is None
