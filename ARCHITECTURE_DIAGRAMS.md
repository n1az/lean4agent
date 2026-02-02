# Architecture Diagrams

## llmlean Architecture (Native Integration)

```
┌─────────────────────────────────────────────────────┐
│                   Lean 4 Process                     │
│                                                      │
│  ┌──────────────┐    ┌─────────────┐                │
│  │   VSCode     │───▶│  llmlean    │                │
│  │   Editor     │    │  Tactics    │                │
│  └──────────────┘    └──────┬──────┘                │
│                             │                        │
│                             ▼                        │
│                      ┌─────────────┐                 │
│                      │     LLM     │                 │
│                      │   API Call  │                 │
│                      └──────┬──────┘                 │
│                             │                        │
│                             ▼                        │
│                      ┌─────────────┐                 │
│                      │   Tactic    │                 │
│                      │   Parser    │◀────┐           │
│                      └──────┬──────┘     │           │
│                             │            │           │
│                             ▼            │           │
│                      ┌─────────────┐     │           │
│                      │   Tactic    │     │           │
│                      │  Evaluator  │     │           │
│                      └──────┬──────┘     │           │
│                             │            │           │
│                             ▼            │           │
│                      ┌─────────────┐     │           │
│                      │    Meta     │     │           │
│                      │   Context   │─────┘           │
│                      └─────────────┘                 │
│                                                      │
│  ⏱️  Tactic check: 5-20ms (in-process)             │
└─────────────────────────────────────────────────────┘
```

**Advantages:**
- No process boundaries
- Direct API access
- Fast tactic validation
- Immediate state access

## lean4agent Architecture (External Python)

```
┌──────────────────────┐          ┌─────────────────────┐
│   Python Process     │          │   Lean 4 Process    │
│                      │          │                     │
│  ┌───────────────┐   │          │                     │
│  │  lean4agent   │   │          │                     │
│  │    Agent      │   │          │                     │
│  └───────┬───────┘   │          │                     │
│          │           │          │                     │
│          ▼           │          │                     │
│  ┌───────────────┐   │          │                     │
│  │     LLM       │   │          │                     │
│  │   API Call    │   │          │                     │
│  └───────┬───────┘   │          │                     │
│          │           │          │                     │
│          ▼           │          │                     │
│  ┌───────────────┐   │  spawn   │                     │
│  │  Build Proof  │   │  ──────▶ │                     │
│  │     Code      │   │  (each)  │                     │
│  └───────┬───────┘   │  check)  │  ┌──────────────┐   │
│          │           │          │  │  Read .lean  │   │
│          ▼           │          │  │     File     │   │
│  ┌───────────────┐   │          │  └──────┬───────┘   │
│  │ Write to Temp │   │          │         │           │
│  │     File      │───┼──────────┼─────────┘           │
│  └───────────────┘   │          │         │           │
│                      │          │         ▼           │
│                      │          │  ┌──────────────┐   │
│                      │          │  │    Parser    │   │
│                      │          │  └──────┬───────┘   │
│                      │          │         │           │
│                      │          │         ▼           │
│                      │          │  ┌──────────────┐   │
│                      │          │  │  Evaluator   │   │
│                      │          │  └──────┬───────┘   │
│                      │          │         │           │
│  ┌───────────────┐   │  result  │         ▼           │
│  │ Parse stderr  │◀──┼──────────┼─  stdout/stderr     │
│  │ Extract State │   │          │                     │
│  └───────────────┘   │          │                     │
│                      │          │                     │
│  ⏱️  Tactic check:   │          │                     │
│     300-2400ms       │          │                     │
│     (subprocess)     │          │                     │
└──────────────────────┘          └─────────────────────┘
```

**Overhead Sources:**
1. Process spawning: ~100-300ms
2. File I/O: ~5-100ms (optimized in v2.0)
3. Lean startup: ~50-200ms
4. Error parsing: ~5-10ms

**Advantages:**
- Full Python programmability
- Easy LLM provider switching
- Integration with Python ecosystem
- Automated workflows

## Performance Comparison

```
Time per tactic check:

llmlean:      ████░░░░░░░░░░░░░░░░░░░░░░░░░░  5-20ms
lean4agent:   ████████████████████████████████  300-2400ms

                                            ▲
                                            │
                                   Process overhead
                                   (~200-2200ms)
```

## Future Architecture (lean4agent v3.0 with LSP)

```
┌──────────────────────┐          ┌─────────────────────┐
│   Python Process     │          │   Lean 4 LSP        │
│                      │  stdin   │     Server          │
│  ┌───────────────┐   │  ──────▶ │   (persistent)      │
│  │  lean4agent   │───┼──────────┼─────────────────┐   │
│  │    Agent      │   │  stdout  │                 │   │
│  └───────────────┘   │  ◀────── │                 │   │
│                      │          │  ┌──────────────▼┐  │
│                      │          │  │   Tactic      │  │
│  ⏱️  Tactic check:   │          │  │   Evaluator   │  │
│     20-50ms          │          │  └───────────────┘  │
│     (persistent!)    │          │                     │
└──────────────────────┘          └─────────────────────┘
```

**Potential improvements:**
- Eliminate process spawning (~200-300ms saved)
- Keep Lean state in memory
- Faster communication
- **Result:** ~1.1-1.2x overhead vs llmlean

## Use Case Decision Tree

```
                    Do you need to...
                          │
          ┌───────────────┴───────────────┐
          │                               │
    Prove interactively            Automate proof
    in Lean files?                 generation?
          │                               │
          ▼                               ▼
    ┌──────────┐                    ┌──────────┐
    │ llmlean  │                    │lean4agent│
    └──────────┘                    └──────────┘
    
    - VSCode integration            - Python API
    - Fast suggestions             - Batch processing
    - Inline tactics               - ML pipelines
    - `llmstep ""`                 - Automation
    - `llmqed`                     - Cloud deployment
```

## Summary

**llmlean**: Fast (native) but limited to Lean files
**lean4agent**: Programmable (Python) but with overhead
**Both**: Valuable for different use cases
