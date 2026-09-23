"""Adaptive search-based attacker (test-time search over injection payloads).

Implements the core idea of "Rethinking Indirect Prompt Injection as a
Test-Time Search Problem" (arXiv 2609.04495): treat the attacker as an
adaptive search agent with an explicit attack budget. More attacker compute
(budget) should translate into better vulnerability discovery, so every
campaign records and discloses its budget.

Original tooling, not a reproduction of the paper's code.
"""

from .adaptive_search import AdaptiveSearchAttacker

__all__ = ["AdaptiveSearchAttacker"]
