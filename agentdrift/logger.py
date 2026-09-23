"""Trajectory logging for agent tool-call runs (AgentDrift, arXiv 2609.06972).

Records ordered steps as dicts with keys:
    step_id, actor, action, tool, args, observation, timestamp

Save/load as JSONL so trajectories are easy to append to and stream.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


STEP_FIELDS = ("step_id", "actor", "action", "tool", "args", "observation", "timestamp")


class TrajectoryLogger:
    """Record an ordered tool-call trajectory and persist it as JSONL."""

    def __init__(self) -> None:
        self._steps: list[dict] = []

    def record(
        self,
        actor: str,
        action: str,
        tool: str | None = None,
        args: dict | None = None,
        observation: str | None = None,
    ) -> int:
        """Append a step. Returns the step_id (0-based index)."""
        step = {
            "step_id": len(self._steps),
            "actor": actor,
            "action": action,
            "tool": tool,
            "args": args or {},
            "observation": observation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._steps.append(step)
        return step["step_id"]

    @property
    def steps(self) -> list[dict]:
        """Copy of recorded steps in order."""
        return [dict(s) for s in self._steps]

    def clear(self) -> None:
        self._steps.clear()

    def save(self, path: str | Path) -> Path:
        """Write steps as JSONL, one step per line."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for step in self._steps:
                f.write(json.dumps(step, ensure_ascii=False) + "\n")
        return path

    @classmethod
    def load(cls, path: str | Path) -> "TrajectoryLogger":
        """Load steps from a JSONL file into a new logger."""
        logger = cls()
        with Path(path).open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    step = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_no}: invalid JSON") from exc
                if not isinstance(step, dict) or "step_id" not in step:
                    raise ValueError(f"{path}:{line_no}: not a step dict")
                logger._steps.append(step)
        # Re-normalize step_ids to be 0..n-1 in file order.
        for i, step in enumerate(logger._steps):
            step["step_id"] = i
        return logger
