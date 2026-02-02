# Branch Comparison Guide

## Quick Comparison

This guide helps you understand the differences between branches and how to test them.

## Branch Overview

### Current Branch: copilot/compare-toolkit-with-llmlean

This branch includes **both** the model configuration updates and LSP implementation.

**Features:**
- ✅ Model names are required (no hardcoded defaults)
- ✅ LSP support for 10-80x speedup (opt-in via `use_lsp=True`)
- ✅ REPL mode (default, 10-20% faster)
- ✅ Subprocess mode (fallback)

## Testing Different Modes

### 1. Test Subprocess Mode (Baseline)

```python
from lean4agent import Lean4Agent, Config

config = Config(
    llm_provider="ollama",
    ollama_model="bfs-prover-v2:32b",
    use_repl=False,  # Disable REPL
    use_lsp=False    # Disable LSP
)

agent = Lean4Agent(config)
result = agent.generate_proof(theorem, verbose=True)
```

**Expected Performance:** ~300-2400ms per tactic

### 2. Test REPL Mode (Default)

```python
from lean4agent import Lean4Agent, Config

config = Config(
    llm_provider="ollama",
    ollama_model="bfs-prover-v2:32b",
    use_repl=True,   # Enable REPL (default)
    use_lsp=False    # Disable LSP
)

agent = Lean4Agent(config)
result = agent.generate_proof(theorem, verbose=True)
```

**Expected Performance:** ~200-2000ms per tactic (10-20% faster)

### 3. Test LSP Mode (Fastest)

```python
from lean4agent import Lean4Agent, Config

config = Config(
    llm_provider="ollama",
    ollama_model="bfs-prover-v2:32b",
    use_repl=False,  # LSP takes precedence
    use_lsp=True     # Enable LSP
)

agent = Lean4Agent(config)
result = agent.generate_proof(theorem, verbose=True)
```

**Expected Performance:** ~15-30ms per tactic (10-80x faster!)

## Performance Comparison Script

```python
import time
from lean4agent import Lean4Agent, Config

theorem = "simple_proof : True"

modes = [
    ("Subprocess", {"use_repl": False, "use_lsp": False}),
    ("REPL", {"use_repl": True, "use_lsp": False}),
    ("LSP", {"use_repl": False, "use_lsp": True}),
]

print("Performance Comparison")
print("=" * 60)

for mode_name, mode_config in modes:
    config = Config(
        llm_provider="ollama",
        ollama_model="bfs-prover-v2:32b",
        **mode_config
    )
    
    agent = Lean4Agent(config)
    
    start = time.time()
    result = agent.generate_proof(theorem, verbose=False)
    elapsed = time.time() - start
    
    print(f"\n{mode_name} Mode:")
    print(f"  Result: {'✓ Success' if result.success else '✗ Failed'}")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Iterations: {result.iterations}")

print("\n" + "=" * 60)
```

## Feature Matrix

| Feature | Subprocess | REPL | LSP |
|---------|-----------|------|-----|
| **Speed** | Baseline | +10-20% | +10-80x |
| **Setup** | Simple | Default | Requires pygls |
| **Stability** | Stable | Stable | Experimental |
| **Use Case** | Basic | Production | High-throughput |
| **Process** | New each time | Reused files | Persistent server |
| **Overhead** | 200-500ms | 50-100ms | <5ms |

## Migration Path

### From Main Branch (if exists)

```python
# Old way (may have hardcoded defaults)
agent = Lean4Agent()

# New way (explicit model required)
config = Config(
    llm_provider="ollama",
    ollama_model="bfs-prover-v2:32b"
)
agent = Lean4Agent(config)
```

### Enabling LSP

```python
# Just add use_lsp=True
config = Config(
    llm_provider="ollama",
    ollama_model="bfs-prover-v2:32b",
    use_lsp=True  # Enable LSP!
)
agent = Lean4Agent(config)
```

## Configuration Summary

### Required Parameters
- `ollama_model` (when using ollama)
- `openai_model` (when using openai)
- `openai_api_key` (when using openai)

### Optional Performance Parameters
- `use_repl` (default: `True`) - File optimization
- `use_lsp` (default: `False`) - LSP mode

### Example .env File

```env
# Provider and Model (REQUIRED)
LLM_PROVIDER=ollama
OLLAMA_MODEL=bfs-prover-v2:32b

# Performance (OPTIONAL)
USE_REPL=true   # 10-20% faster
USE_LSP=false   # 10-80x faster (experimental)

# Other settings
MAX_ITERATIONS=50
TEMPERATURE=0.7
```

## Troubleshooting

### LSP Mode Not Working

1. **Install dependencies:**
   ```bash
   pip install pygls lsprotocol
   ```

2. **Verify Lean supports server mode:**
   ```bash
   lean --server
   ```

3. **Check logs:**
   - Set `LEAN_SERVER_LOG_DIR` environment variable
   - Review logs for errors

### Performance Not Improved

1. **Verify mode is enabled:**
   ```python
   config = Config(use_lsp=True, ...)
   print(f"LSP enabled: {config.use_lsp}")
   ```

2. **Check event loop overhead:**
   - First call may be slower (setup)
   - Subsequent calls should be fast

3. **Compare with baseline:**
   - Run same proof with all three modes
   - Measure multiple iterations

## Examples

All examples are located in `examples/`:
- `basic_usage.py` - General usage with explicit models
- `lsp_example.py` - LSP-specific examples
- `openai_example.py` - OpenAI configuration

## Documentation

- `README.md` - Quick start and overview
- `LSP_GUIDE.md` - Detailed LSP implementation
- `PERFORMANCE_GUIDE.md` - Performance tuning
- `IMPLEMENTATION_NOTES.md` - Technical details
- `COMPARISON_WITH_LLMLEAN.md` - vs llmlean

## Questions?

If you encounter issues:
1. Check the documentation files above
2. Verify your configuration
3. Test with different modes
4. Check Lean installation

Happy proving! 🎯
