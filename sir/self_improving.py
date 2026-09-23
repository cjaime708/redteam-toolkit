"""Self-improving attacker: learns reusable attack strategies from feedback.

Paper: "SIR: Self-improving Red-teaming for Compute Use Agents"
(arXiv 2608.30207). The attacker maintains a store of strategies; after each
trial it receives binary success feedback and updates per-strategy
statistics. Strategies with high success rates are preferred in later
rounds, so the attacker improves across a campaign instead of starting
from scratch each time.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional


class SelfImprovingAttacker:
    """Strategy store with success-rate learning and JSON persistence."""

    def __init__(self, store_path: Optional[str | Path] = None) -> None:
        self.store_path = Path(store_path) if store_path else None
        # strategy_id -> {pattern, successes, attempts, created_ts, notes}
        self.strategies: Dict[str, Dict] = {}
        if self.store_path and self.store_path.exists():
            self.load(self.store_path)

    # -- strategy management ----------------------------------------------
    def add_strategy(self, pattern: str, notes: str = "",
                     strategy_id: Optional[str] = None) -> str:
        """Register a new reusable attack strategy pattern."""
        sid = strategy_id or f"strat-{uuid.uuid4().hex[:8]}"
        if sid in self.strategies:
            raise ValueError(f"strategy {sid!r} already exists")
        self.strategies[sid] = {
            "pattern": pattern,
            "notes": notes,
            "successes": 0,
            "attempts": 0,
            "created_ts": time.time(),
            "updated_ts": time.time(),
        }
        return sid

    def update_strategy_stats(self, strategy_id: str, success: bool) -> Dict:
        """Record binary trial feedback for a strategy.

        ``success`` should come from verified consequences (e.g. the
        ConsequenceVerifier verdict), not from an LLM judge's opinion.
        """
        if strategy_id not in self.strategies:
            raise KeyError(f"unknown strategy: {strategy_id}")
        s = self.strategies[strategy_id]
        s["attempts"] += 1
        if success:
            s["successes"] += 1
        s["updated_ts"] = time.time()
        return self._with_rate(strategy_id, s)

    def success_rate(self, strategy_id: str) -> Optional[float]:
        s = self.strategies.get(strategy_id)
        if s is None:
            raise KeyError(f"unknown strategy: {strategy_id}")
        if s["attempts"] == 0:
            return None
        return s["successes"] / s["attempts"]

    def _with_rate(self, sid: str, s: Dict) -> Dict:
        out = {"strategy_id": sid, **s}
        out["success_rate"] = (
            s["successes"] / s["attempts"] if s["attempts"] else None
        )
        return out

    def get_best_strategies(self, k: int = 5,
                            min_attempts: int = 1) -> List[Dict]:
        """Top-k strategies by success rate (ties: more attempts first).

        Strategies with zero attempts are ranked last.
        """
        ranked = []
        for sid, s in self.strategies.items():
            rate = s["successes"] / s["attempts"] if s["attempts"] else -1.0
            ranked.append((rate, s["attempts"], sid))
        ranked.sort(key=lambda t: (t[0], t[1]), reverse=True)
        out = []
        for rate, _attempts, sid in ranked[:k]:
            s = self.strategies[sid]
            if s["attempts"] < min_attempts:
                continue
            out.append(self._with_rate(sid, s))
        return out

    def stats(self) -> Dict:
        total_attempts = sum(s["attempts"] for s in self.strategies.values())
        total_successes = sum(s["successes"] for s in self.strategies.values())
        return {
            "n_strategies": len(self.strategies),
            "total_attempts": total_attempts,
            "total_successes": total_successes,
            "overall_success_rate": (
                total_successes / total_attempts if total_attempts else None
            ),
        }

    # -- persistence --------------------------------------------------------
    def save(self, path: Optional[str | Path] = None) -> Path:
        dest = Path(path) if path else self.store_path
        if dest is None:
            raise ValueError("no store path given")
        dest.parent.mkdir(parents=True, exist_ok=True)
        payload = {"strategies": self.strategies, "saved_ts": time.time()}
        with dest.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        self.store_path = dest
        return dest

    def load(self, path: str | Path) -> None:
        p = Path(path)
        with p.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        self.strategies = payload.get("strategies", {})
        self.store_path = p
