"""MMPIBench-inspired multimodal prompt-injection module.

Based on arXiv 2609.09404 ("An Experimental Evaluation of Multimodal
Prompt Injection Attacks on Agentic AI Frameworks"): injection payloads
travel across modalities (text, visual carriers, audio carriers) and
must be tracked from perception through planning to tool calls, so that
an *attempted* unsafe action can be distinguished from a *completed*
one.

Submodules:
    carriers           -- injection carriers per modality
    trajectory_tracker -- stage-by-stage run tracking
"""

from .carriers import (
    Carrier,
    TextCarrier,
    VisualCarrier,
    AudioCarrier,
    Carriers,
)
from .trajectory_tracker import StageTracker

__all__ = [
    "Carrier",
    "TextCarrier",
    "VisualCarrier",
    "AudioCarrier",
    "Carriers",
    "StageTracker",
]
