"""Lean4Agent - LLM based agentic toolkit to solve math problems using Lean 4."""

__version__ = "0.1.0"

from lean4agent.agent import Lean4Agent
from lean4agent.config import Config

__all__ = ["Lean4Agent", "Config"]
