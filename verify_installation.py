#!/usr/bin/env python3
"""
Verification script for lean4agent package.

This script verifies that the package is correctly installed and configured.
"""
import sys

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from lean4agent import Lean4Agent, Config
        from lean4agent.llm import LLMInterface, OllamaInterface, OpenAIInterface
        from lean4agent.lean import LeanClient
        from lean4agent.agent import ProofStep, ProofResult
        print("✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_config():
    """Test configuration creation and validation."""
    print("\nTesting configuration...")
    try:
        from lean4agent import Config
        
        # Test default config
        config = Config()
        assert config.llm_provider == "ollama"
        assert config.ollama_model == "bfs-prover-v2:32b"
        print("✓ Default config created")
        
        # Test custom config
        config = Config(
            llm_provider="ollama",
            max_iterations=100,
            temperature=0.5
        )
        config.validate_config()
        print("✓ Custom config validated")
        
        # Test from_env
        config = Config.from_env()
        print("✓ Config from environment created")
        
        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False


def test_llm_interfaces():
    """Test LLM interface creation."""
    print("\nTesting LLM interfaces...")
    try:
        from lean4agent.llm import OllamaInterface
        
        interface = OllamaInterface()
        assert interface.base_url == "http://localhost:11434"
        assert interface.model == "bfs-prover-v2:32b"
        print("✓ OllamaInterface created")
        
        return True
    except Exception as e:
        print(f"✗ LLM interface test failed: {e}")
        return False


def test_proof_classes():
    """Test proof-related classes."""
    print("\nTesting proof classes...")
    try:
        from lean4agent.agent import ProofStep, ProofResult
        
        # Test ProofStep
        step = ProofStep(tactic="rfl", state="complete", success=True)
        assert step.tactic == "rfl"
        print("✓ ProofStep created")
        
        # Test ProofResult
        result = ProofResult(
            success=True,
            theorem="test : 1 = 1",
            proof_steps=[step],
            iterations=1
        )
        assert result.success is True
        code = result.get_proof_code()
        assert "theorem test : 1 = 1 := by" in code
        print("✓ ProofResult created and code generated")
        
        return True
    except Exception as e:
        print(f"✗ Proof classes test failed: {e}")
        return False


def test_agent_creation():
    """Test agent creation (without actual LLM calls)."""
    print("\nTesting agent creation...")
    try:
        from lean4agent import Lean4Agent, Config
        from unittest.mock import patch
        
        # Create config
        config = Config(llm_provider="ollama")
        
        # Mock LeanClient to avoid requiring Lean installation
        with patch('lean4agent.agent.LeanClient'):
            agent = Lean4Agent(config)
            assert agent.config.llm_provider == "ollama"
            print("✓ Agent created successfully")
        
        return True
    except Exception as e:
        print(f"✗ Agent creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_package_metadata():
    """Test package metadata."""
    print("\nTesting package metadata...")
    try:
        import lean4agent
        
        assert hasattr(lean4agent, '__version__')
        print(f"✓ Package version: {lean4agent.__version__}")
        
        assert hasattr(lean4agent, '__all__')
        print(f"✓ Package exports: {lean4agent.__all__}")
        
        return True
    except Exception as e:
        print(f"✗ Package metadata test failed: {e}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Lean4Agent Package Verification")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_config,
        test_llm_interfaces,
        test_proof_classes,
        test_agent_creation,
        test_package_metadata,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All verification tests passed!")
        print("\nThe lean4agent package is ready to use!")
        print("\nQuick start:")
        print("  from lean4agent import Lean4Agent, Config")
        print("  agent = Lean4Agent()")
        print("  result = agent.generate_proof('theorem test : True')")
        return 0
    else:
        print(f"\n✗ {total - passed} verification test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
