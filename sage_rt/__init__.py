"""SAGE-RT black-box red-teaming module.

Taxonomy-driven framework for automated risk discovery against agentic AI
systems, based on arXiv 2609.09647 ("Black-Box Red Teaming of Agentic AI:
A Taxonomy-Driven Framework for Automated Risk Discovery").

The framework organizes adversarial testing around seven risk domains,
generates adversarial scenarios per domain, and executes them against a
target agent through a black-box harness: the target is treated as an
opaque callable, with only observable inputs (prompts) and outputs
(response text plus declared tool calls).

Quick start::

    from sage_rt import taxonomy, scenario_generator, blackbox_harness

    scenarios = scenario_generator.generate_scenarios(
        "prompt_injection_indirect", n=5,
        target_description="a customer-support agent with web search and email tools",
        seed=42,
    )

    harness = blackbox_harness.BlackBoxHarness()
    harness.register_target(my_agent_callable)
    results = harness.run_campaign(scenarios)
"""

from . import taxonomy
from . import scenario_generator
from . import blackbox_harness
from .blackbox_harness import BlackBoxHarness

__all__ = ["taxonomy", "scenario_generator", "blackbox_harness", "BlackBoxHarness"]

__version__ = "0.1.0"
