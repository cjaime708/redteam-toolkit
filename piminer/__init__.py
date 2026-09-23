"""Transferable attack-strategy library (PIMiner-style).

Implements the core idea of "Agent Against Agent: An Agentic System for
Automatic Prompt Injection Red Teaming" (arXiv 2608.05108): develop a
library of attack strategies on one set of targets and transfer it to
unseen target models. The library is pre-seeded with transferable
strategies; each records the target types it works best against and its
known limitations so consultants can judge transferability honestly.

Original tooling, not a reproduction of the paper's code.
"""

from .strategy_library import StrategyLibrary, AttackStrategy

__all__ = ["StrategyLibrary", "AttackStrategy"]
