"""Skill-selection manipulation tooling.

Implements the core idea of "Implicit Manipulation for Skill Selection in
LLM Agents with Semantic Matching" (arXiv 2609.02035): an attacker can bias
which skill an agent selects using benign-looking metadata and description
changes, without any overtly malicious instruction. Used to probe risks in
skill libraries, routers, and agent configuration.

Original tooling, not a reproduction of the paper's code.
"""

from .metadata_fuzzer import SkillMetadataFuzzer

__all__ = ["SkillMetadataFuzzer"]
