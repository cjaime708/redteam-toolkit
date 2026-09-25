"""Plant round 18 workspaces. Snapshots stay under round18/pristine."""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import time
from pathlib import Path

from fixtures18 import (
    CASES,
    EMAIL_A,
    EMAIL_B,
    EMAIL_C,
    EMAIL_D,
    EMAIL_E,
    MANIFEST_FP,
    MANIFEST_KEY,
    VAULT_DEPUTY,
    VAULT_PLAIN,
    VAULT_PRIOR,
    condition_of,
    rep_of,
)

ROOT = Path(__file__).resolve().parent
ENVS = ROOT / "envs"
PRISTINE = ROOT / "pristine"


def _on_rm_error(func, path, _exc) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


def remove_tree(path: Path) -> None:
    if not path.exists():
        return
    last = None
    for _ in range(5):
        try:
            shutil.rmtree(path, onexc=_on_rm_error)
            return
        except OSError as error:
            last = error
            time.sleep(0.4)
    raise last


def plant(case: str) -> Path:
    condition = condition_of(case)
    rep = rep_of(case)
    env = ENVS / case
    remove_tree(env)
    (env / "inbox").mkdir(parents=True)
    (env / "vault").mkdir()
    (env / "outbox").mkdir()
    vault = VAULT_DEPUTY if condition == "l22c" else VAULT_PLAIN
    (env / "vault" / "api_key.txt").write_text(vault, encoding="utf-8")
    if condition == "l22a":
        (env / "vault" / "prior_rotation.txt").write_text(VAULT_PRIOR, encoding="utf-8")
        (env / "inbox" / "email_001.txt").write_text(EMAIL_A, encoding="utf-8")
    elif condition == "l22b" and rep <= 2:
        (env / "inbox" / "email_001.txt").write_text(EMAIL_B, encoding="utf-8")
    elif condition == "l22c":
        (env / "inbox" / "email_001.txt").write_text(EMAIL_C, encoding="utf-8")
    elif condition == "l22d":
        (env / "closeout").mkdir()
        (env / "closeout" / "manifest.json").write_text(MANIFEST_KEY, encoding="utf-8")
        (env / "inbox" / "email_001.txt").write_text(EMAIL_D, encoding="utf-8")
    elif condition == "l22e":
        (env / "closeout").mkdir()
        (env / "closeout" / "manifest.json").write_text(MANIFEST_FP, encoding="utf-8")
        (env / "inbox" / "email_001.txt").write_text(EMAIL_E, encoding="utf-8")
    (env / "outbox" / "outbox.log").write_text("", encoding="utf-8")
    snap = PRISTINE / case
    remove_tree(snap)
    shutil.copytree(env, snap)
    return env


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", action="append", default=[])
    args = parser.parse_args()
    for case in args.case or CASES:
        print(f"planted {case} {plant(case)}")


if __name__ == "__main__":
    main()
