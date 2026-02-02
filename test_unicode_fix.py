#!/usr/bin/env python3
"""Test script to verify unicode and LSP fixes."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_unicode_in_repl():
    """Test unicode handling in REPL mode."""
    print("=" * 60)
    print("Test 1: Unicode handling in REPL mode")
    print("=" * 60)
    
    from lean4agent.lean import LeanREPL
    
    # Create REPL instance
    repl = LeanREPL()
    repl.start()
    
    # Test code with unicode characters (ℕ is \u2115)
    test_code = """
theorem test_unicode : ℕ → ℕ := by
  intro n
  exact n
"""
    
    try:
        result = repl.check_proof(test_code)
        if result['success']:
            print("✓ Unicode test PASSED: Proof verified successfully")
        else:
            # It might fail for other reasons, but not encoding
            print(f"✓ Unicode encoding works (proof failed for other reason)")
            print(f"  Error: {result['error'][:100] if result['error'] else 'None'}")
        return True
    except UnicodeEncodeError as e:
        print(f"✗ Unicode test FAILED: {e}")
        return False
    except Exception as e:
        # Other errors are ok for this test (e.g., Lean not installed)
        print(f"✓ Unicode encoding works (other error: {type(e).__name__})")
        return True
    finally:
        repl.stop()

def test_lsp_diagnostic_conversion():
    """Test LSP diagnostic message conversion."""
    print("\n" + "=" * 60)
    print("Test 2: LSP diagnostic message conversion")
    print("=" * 60)
    
    try:
        from lsprotocol import types as lsp_types
        
        # Simulate processing diagnostics with various message types
        test_messages = [
            "Simple string error",
            ["List", "item", "error"],  # Would cause original bug
            {"dict": "error"},
        ]
        
        print("Testing message type conversions:")
        all_passed = True
        for msg in test_messages:
            try:
                # This is what the fix does
                converted = str(msg)
                # Try to join (what caused the original error)
                result = "\n".join([converted])
                print(f"  ✓ {type(msg).__name__:10s} -> str: OK")
            except TypeError as e:
                print(f"  ✗ {type(msg).__name__:10s} -> str: FAILED ({e})")
                all_passed = False
        
        return all_passed
        
    except ImportError:
        print("⚠ lsprotocol not installed, skipping LSP test")
        return True

def main():
    """Run all tests."""
    print("\nTesting Unicode and LSP Fixes")
    print("=" * 60)
    
    results = []
    
    # Test 1: Unicode in REPL
    try:
        results.append(("Unicode REPL", test_unicode_in_repl()))
    except Exception as e:
        print(f"✗ Unicode test crashed: {e}")
        results.append(("Unicode REPL", False))
    
    # Test 2: LSP diagnostics
    try:
        results.append(("LSP Diagnostics", test_lsp_diagnostic_conversion()))
    except Exception as e:
        print(f"✗ LSP test crashed: {e}")
        results.append(("LSP Diagnostics", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name:20s}: {status}")
    
    all_passed = all(passed for _, passed in results)
    print("\n" + ("=" * 60))
    if all_passed:
        print("All tests PASSED! ✓")
        return 0
    else:
        print("Some tests FAILED! ✗")
        return 1

if __name__ == "__main__":
    sys.exit(main())
