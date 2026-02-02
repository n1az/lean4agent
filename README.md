# Lean4Agent

**LLM-based Agentic Toolkit for Solving Math Problems Using Lean 4**

Lean4Agent is a Python toolkit that leverages Large Language Models (LLMs) to automatically generate proofs for mathematical theorems in Lean 4. It supports multiple LLM providers including Ollama (with BFS-Prover-V2) and OpenAI's API.

## Features

- 🤖 **Agentic Proof Generation**: Iteratively generates proof steps until a complete proof is found
- 🔌 **Multiple LLM Providers**: Support for Ollama and OpenAI API
- 🎯 **BFS-Prover-V2 Support**: Optimized for single-state proof generation models
- ⚙️ **Easy Configuration**: Simple setup with environment variables or configuration objects
- 📦 **Pip Installable**: Install as a package and use in your projects
- 🔍 **Proof Verification**: Built-in Lean 4 integration for verifying proofs
- ⚡ **Performance Optimized**: Reusable temp files for reduced I/O overhead (~10-20% faster)

## Installation

### Prerequisites

- Python 3.8 or higher
- Lean 4 installed and available in PATH ([Installation Guide](https://leanprover.github.io/lean4/doc/setup.html))
- For Ollama: Ollama installed and running ([Ollama](https://ollama.ai/))
- For OpenAI: OpenAI API key

### Install from source

```bash
git clone https://github.com/n1az/lean4agent.git
cd lean4agent
pip install -e .
```

### Install with OpenAI support

```bash
pip install -e ".[openai]"
```

### Install for development

```bash
pip install -e ".[dev]"
```

## Quick Start

### Using Ollama (Default)

```python
from lean4agent import Lean4Agent, Config

# Create agent with default configuration
agent = Lean4Agent()

# Define a theorem to prove
theorem = "example_theorem (a b : Nat) : a + b = b + a"

# Generate proof
result = agent.generate_proof(theorem, verbose=True)

if result.success:
    print("✓ Proof found!")
    print(result.get_proof_code())
else:
    print(f"✗ Failed: {result.error}")
```

### Using OpenAI API

```python
from lean4agent import Lean4Agent, Config

# Configure for OpenAI
config = Config(
    llm_provider="openai",
    openai_api_key="your-api-key",
    openai_model="gpt-4"
)

agent = Lean4Agent(config)
result = agent.generate_proof(theorem, verbose=True)
```

### Using OpenAI-Compatible APIs (Groq, LMStudio, etc.)

You can use any OpenAI-compatible API by specifying a custom base URL:

```python
from lean4agent import Lean4Agent, Config

# Configure for Groq
config = Config(
    llm_provider="openai",
    openai_api_key="your-groq-api-key",
    openai_base_url="https://api.groq.com/openai/v1",
    openai_model="mixtral-8x7b-32768"
)

# Or configure for LMStudio
config = Config(
    llm_provider="openai",
    openai_api_key="not-needed",  # LMStudio doesn't require API key
    openai_base_url="http://localhost:1234/v1",
    openai_model="local-model"
)

agent = Lean4Agent(config)
result = agent.generate_proof(theorem, verbose=True)
```

### Using Environment Variables

Create a `.env` file:

```env
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=bfs-prover-v2:32b
MAX_ITERATIONS=50
TEMPERATURE=0.7

# For OpenAI-compatible APIs
# OPENAI_BASE_URL=https://api.groq.com/openai/v1
# OPENAI_API_KEY=your-key
```

Then use in your code:

```python
from lean4agent import Lean4Agent, Config

# Automatically loads from .env
config = Config.from_env()
agent = Lean4Agent(config)
```

## Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `llm_provider` | LLM provider: 'ollama' or 'openai' | `'ollama'` |
| `ollama_url` | Ollama API URL | `'http://localhost:11434'` |
| `ollama_model` | Ollama model name | `'bfs-prover-v2:32b'` |
| `openai_api_key` | OpenAI API key | `None` |
| `openai_model` | OpenAI model name | `'gpt-4'` |
| `openai_base_url` | OpenAI API base URL (for compatible APIs) | `None` |
| `max_iterations` | Maximum proof generation iterations | `50` |
| `temperature` | LLM generation temperature | `0.7` |
| `timeout` | API request timeout (seconds) | `30` |
| `use_sorry_on_timeout` | Add 'sorry' when max iterations reached | `True` |
| `use_repl` | Use persistent Lean REPL for better performance | `True` |

## Advanced Usage

### Custom Configuration

```python
from lean4agent import Lean4Agent, Config

config = Config(
    llm_provider="ollama",
    ollama_url="http://localhost:11434",
    ollama_model="bfs-prover-v2:32b",
    max_iterations=100,
    temperature=0.5,
    timeout=60
)

agent = Lean4Agent(config)
```

### Accessing Proof Steps

```python
result = agent.generate_proof(theorem)

print(f"Iterations: {result.iterations}")
print(f"Steps attempted: {len(result.proof_steps)}")

for i, step in enumerate(result.proof_steps, 1):
    print(f"{i}. {step.tactic} (success: {step.success})")
```

### Understanding Proof Validation Status

When a proof fails, you can get detailed feedback about which steps were valid:

```python
result = agent.generate_proof(theorem, verbose=True)

if not result.success:
    # Get human-readable summary
    print(result.get_proof_status_summary())
    
    # Shows:
    # - Total number of valid vs invalid steps
    # - List of valid steps that were applied
    # - First invalid step and why it failed
    
    # Check if partial proof with 'sorry' was generated
    if result.complete_proof:
        print("\nPartial proof with 'sorry':")
        print(result.complete_proof)
```

### Disabling 'sorry' on Timeout

If you don't want the agent to generate proofs with 'sorry' when max iterations is reached:

```python
config = Config(
    llm_provider="ollama",
    use_sorry_on_timeout=False
)

agent = Lean4Agent(config)
result = agent.generate_proof(theorem)

# If proof fails, result.complete_proof will be None instead of containing 'sorry'
```

### Verifying Existing Proofs

```python
proof_code = """
theorem example : 2 + 2 = 4 := by
  rfl
"""

verification = agent.verify_proof(proof_code)
print(f"Valid: {verification['success']}")
```

## Examples

See the `examples/` directory for more examples:

- `basic_usage.py` - Basic usage with Ollama
- `openai_example.py` - Using OpenAI API

Run examples:

```bash
python examples/basic_usage.py
python examples/openai_example.py
```

## How It Works

1. **Initialize**: Agent is configured with LLM provider and Lean 4 client
2. **Start REPL**: Persistent Lean process for fast tactic checking (optional, enabled by default)
3. **Generate Tactic**: LLM generates the next proof step based on current state
4. **Apply & Verify**: Tactic is applied in Lean 4 and verified incrementally
5. **Iterate**: Process repeats until proof is complete or max iterations reached
6. **Return Result**: Complete proof or error information is returned

### Performance Optimizations

Lean4Agent v2.0 includes performance improvements:

- **Optimized File Handling**: Reuses temporary files to reduce I/O overhead
- **Batch Checking**: Supports checking multiple candidate tactics efficiently
- **~10-20% Speedup**: Multi-step proofs are faster through reduced file system overhead

**Future improvements**: True process persistence via Lean LSP could provide 2-3x additional speedup.

See [PERFORMANCE_GUIDE.md](PERFORMANCE_GUIDE.md) for details.

### Comparison with llmlean

Lean4Agent provides similar functionality to llmlean but as a Python library:

- **llmlean**: Native Lean integration, used within Lean files via `llmstep` and `llmqed` tactics
- **lean4agent**: Python API for programmatic proof generation and automation

See [COMPARISON_WITH_LLMLEAN.md](COMPARISON_WITH_LLMLEAN.md) for detailed comparison.

### BFS-Prover-V2 Integration

BFS-Prover-V2 is a specialized model for Lean proof generation that produces single proof steps. Lean4Agent handles the iteration:

- Sends current proof state to the model
- Receives single tactic suggestion
- Applies tactic in Lean 4
- Updates state and repeats

## API Reference

### Lean4Agent

Main class for proof generation.

```python
agent = Lean4Agent(config: Optional[Config] = None)
```

**Methods:**

- `generate_proof(theorem: str, max_iterations: Optional[int] = None, verbose: bool = False) -> ProofResult`
- `verify_proof(code: str) -> Dict[str, Any]`

### Config

Configuration management.

```python
config = Config(
    llm_provider: str = "ollama",
    ollama_url: str = "http://localhost:11434",
    ollama_model: str = "bfs-prover-v2:32b",
    openai_api_key: Optional[str] = None,
    openai_model: str = "gpt-4",
    openai_base_url: Optional[str] = None,
    max_iterations: int = 50,
    temperature: float = 0.7,
    timeout: int = 30,
    use_sorry_on_timeout: bool = True
)
```

**Methods:**

- `from_env(**kwargs) -> Config` - Load from environment variables
- `validate_config() -> None` - Validate configuration

### ProofResult

Result object from proof generation.

**Attributes:**

- `success: bool` - Whether proof was completed
- `theorem: str` - The theorem statement
- `proof_steps: List[ProofStep]` - All proof steps attempted
- `complete_proof: Optional[str]` - Complete proof code (may contain 'sorry' on timeout)
- `error: Optional[str]` - Error message if failed
- `iterations: int` - Number of iterations used
- `valid_steps_count: int` - Number of valid steps before failure

**Methods:**

- `get_proof_code() -> str` - Get complete Lean 4 proof code
- `get_proof_status_summary() -> str` - Get detailed summary of proof validation status

## Requirements

- Python >= 3.8
- Lean 4
- requests >= 2.28.0
- pydantic >= 2.0.0
- python-dotenv >= 1.0.0
- openai >= 1.0.0 (optional, for OpenAI support)

## Troubleshooting

### Lean 4 Not Found

Make sure Lean 4 is installed and in your PATH:

```bash
lean --version
```

### Ollama Connection Issues

Ensure Ollama is running:

```bash
ollama serve
```

And the model is available:

```bash
ollama pull bfs-prover-v2:32b
```

### OpenAI API Errors

Verify your API key is correct and you have sufficient credits.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Citation

If you use Lean4Agent in your research, please cite:

```bibtex
@software{lean4agent,
  title = {Lean4Agent: LLM-based Agentic Toolkit for Lean 4},
  author = {Lean4Agent Contributors},
  year = {2024},
  url = {https://github.com/n1az/lean4agent}
}
```

## Acknowledgments

- Lean 4 theorem prover team
- BFS-Prover-V2 model developers
- OpenAI for API access
- Ollama for local LLM infrastructure
