"""Own sandbox for agentic-AI red teaming.

A self-contained harness: a tool-using agent runs inside a jailed filesystem
environment, against any OpenAI-compatible model backend (Grok via xAI,
Ollama, LM Studio, vLLM), while the toolkit watches every step.

Modules:
  backends      - pluggable model backends (OpenAI-compatible HTTP, stdlib only)
  environments  - jailed tool environment (files, inbox, simulated outbox)
  agent         - ReAct-style tool-calling agent with a text tool protocol
  runner        - case runner wiring StageTracker, TrajectoryLogger,
                  ConsequenceVerifier into one assessed result
  quickstart    - zero-key smoke demo using the MockBackend

There is no Grok-CLI hookup on this machine; Grok is reached through xAI's
OpenAI-compatible API (set XAI_API_KEY), or use Ollama for a fully free setup.
"""

from .backends import (
    ModelBackend,
    OpenAICompatibleBackend,
    MockBackend,
    grok_backend,
    ollama_backend,
)
from .environments import SandboxEnvironment
from .agent import ToolAgent
from .goals import AttackGoal, email_contains, file_contains
from .runner import run_case

__all__ = [
    "ModelBackend",
    "OpenAICompatibleBackend",
    "MockBackend",
    "grok_backend",
    "ollama_backend",
    "SandboxEnvironment",
    "ToolAgent",
    "AttackGoal",
    "email_contains",
    "file_contains",
    "run_case",
]
