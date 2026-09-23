"""Self-improving red-teaming for compute-use agents (SIR-style).

Implements the core ideas of "SIR: Self-improving Red-teaming for Compute
Use Agents" (arXiv 2608.30207):
  1. The attacker learns reusable strategies from trial feedback
     (``self_improving.py``).
  2. Outcomes are scored by verifying actual consequences - filesystem,
     permission, and service effects - instead of relying solely on an
     LLM judge (``verifier.py``).

Original tooling, not a reproduction of the paper's code.
"""

from .self_improving import SelfImprovingAttacker
from .verifier import ConsequenceVerifier

__all__ = ["SelfImprovingAttacker", "ConsequenceVerifier"]
