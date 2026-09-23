"""AgentDrift-inspired trajectory logging and labeling.

Based on arXiv 2609.06972 ("AgentDrift: A Step-Labeled Benchmark of
Injection-Hijacked LLM Agent Trajectories"): ordered tool-call
trajectories labeled per step as injection entry, compromised steps,
resisted attacks, or legitimate-but-suspicious content.

Submodules:
    logger   -- TrajectoryLogger (record + JSONL save/load)
    labeler  -- label_trajectory with heuristics + manual overrides
    synthetic-- deterministic synthetic labeled trajectory generator
"""

from .logger import TrajectoryLogger
from .labeler import label_trajectory, LABELS
from .synthetic import generate_synthetic_trajectories

__all__ = [
    "TrajectoryLogger",
    "label_trajectory",
    "LABELS",
    "generate_synthetic_trajectories",
]
