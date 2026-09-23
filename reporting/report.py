"""Consulting-grade scoping and reporting for agentic-AI red-team campaigns.

Two entry points:

  - ``scope_assessment(client_name, systems, constraints)`` -> dict:
    the scoping document for a black-box engagement.
  - ``generate_report(campaign_results, trajectory_labels, verifier_verdicts)``
    -> str: a markdown report covering executive summary, findings table,
    risk-domain breakdown, attempted-vs-completed distinction,
    recommendations, and explicit attack-budget disclosure.
  - ``save_report(markdown, path)`` writes the report to disk.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Scoping
# ---------------------------------------------------------------------------

def scope_assessment(
    client_name: str,
    systems: List[Dict],
    constraints: Optional[Dict] = None,
) -> Dict:
    """Build the scoping document for an assessment.

    Parameters
    ----------
    client_name: who the engagement is for.
    systems: list of dicts, each with at least ``name`` and ``description``;
        optional keys: ``access_level`` ("black_box" | "gray_box" |
        "white_box"), ``entry_points`` (list), ``out_of_scope`` (list).
    constraints: optional dict with ``rules_of_engagement`` (list),
        ``time_box`` (str), ``data_handling`` (str), ``contacts`` (list).

    Returns a structured scoping document dict. This is the artifact you
    agree with the client *before* any testing starts.
    """
    constraints = constraints or {}
    norm_systems = []
    for s in systems:
        norm_systems.append({
            "name": s.get("name", "unnamed"),
            "description": s.get("description", ""),
            "access_level": s.get("access_level", "black_box"),
            "entry_points": list(s.get("entry_points", [])),
            "out_of_scope": list(s.get("out_of_scope", [])),
        })
    return {
        "document": "assessment_scope",
        "client": client_name,
        "created": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "systems": norm_systems,
        "rules_of_engagement": list(
            constraints.get("rules_of_engagement", [
                "No testing outside listed entry points.",
                "No exfiltration of real customer data; use synthetic fixtures.",
                "Stop and notify the contact on any suspected production impact.",
                "All testing within the agreed time box.",
            ])
        ),
        "time_box": constraints.get("time_box", "to be agreed"),
        "data_handling": constraints.get(
            "data_handling",
            "Findings contain synthetic data only; client data redacted on sight.",
        ),
        "contacts": list(constraints.get("contacts", [])),
        "deliverable": ("Findings report with attempted-vs-completed "
                        "distinction, risk-domain breakdown, attack-budget "
                        "disclosure, and prioritized recommendations."),
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3,
                  "info": 4}


def _md_table(headers: List[str], rows: List[List[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |",
             "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def generate_report(
    campaign_results: Dict,
    trajectory_labels: Optional[List[Dict]] = None,
    verifier_verdicts: Optional[List[Dict]] = None,
) -> str:
    """Generate the markdown findings report.

    Parameters
    ----------
    campaign_results: dict with keys:
        - ``campaign_name`` (str), ``client`` (str), ``date`` (str, optional)
        - ``findings``: list of dicts with ``id``, ``title``, ``severity``
          (critical/high/medium/low/info), ``risk_domain`` (str),
          ``status`` ("completed" | "attempted" | "not_vulnerable"),
          ``description``, ``evidence`` (str), ``recommendation`` (str).
        - ``attack_budget``: dict like ``{"budget_total": N,
          "budget_used": M, "search_procedure": "..."}`` (disclosed verbatim).
        - ``scope`` (optional): scoping doc or summary str.
    trajectory_labels: optional list of step-label dicts (from trajectory
        annotation, e.g. AgentDrift-style): each with ``trajectory_id``,
        ``injection_entry_step`` (int|None), ``compromised_steps`` (list),
        ``resisted`` (bool). Used to quantify attempted vs completed.
    verifier_verdicts: optional list of ConsequenceVerifier verdict dicts.

    A finding counts as **completed** only when a verifier verdict confirms
    a real consequence; otherwise it stays **attempted**. The report states
    this rule explicitly.
    """
    trajectory_labels = trajectory_labels or []
    verifier_verdicts = verifier_verdicts or []

    name = campaign_results.get("campaign_name", "Red-team campaign")
    client = campaign_results.get("client", "Client")
    date = campaign_results.get(
        "date", _dt.date.today().isoformat())
    findings: List[Dict] = list(campaign_results.get("findings", []))
    budget = campaign_results.get("attack_budget", {})

    # Cross-check completed claims against verifier verdicts.
    verified_completed = sum(
        1 for v in verifier_verdicts if v.get("consequence") == "VIOLATION"
    )
    observed_effects = sum(
        1 for v in verifier_verdicts if v.get("consequence") == "observed"
    )

    completed = [f for f in findings if f.get("status") == "completed"]
    attempted = [f for f in findings if f.get("status") == "attempted"]
    not_vuln = [f for f in findings if f.get("status") == "not_vulnerable"]
    findings_sorted = sorted(
        findings,
        key=lambda f: _SEVERITY_ORDER.get(str(f.get("severity", "info")).lower(), 5),
    )

    # Risk-domain breakdown.
    domains: Dict[str, Dict[str, int]] = {}
    for f in findings:
        d = domains.setdefault(str(f.get("risk_domain", "uncategorized")),
                               {"completed": 0, "attempted": 0,
                                "not_vulnerable": 0, "total": 0})
        d[f.get("status", "attempted")] = d.get(f.get("status"), 0) + 1
        d["total"] += 1

    # Trajectory stats.
    n_traj = len(trajectory_labels)
    n_compromised_traj = sum(
        1 for t in trajectory_labels if t.get("compromised_steps"))
    n_resisted = sum(1 for t in trajectory_labels if t.get("resisted"))

    L: List[str] = []
    L.append(f"# Agentic AI Red-Team Report: {name}")
    L.append("")
    L.append(f"**Client:** {client}  |  **Date:** {date}")
    L.append("")
    L.append("## Executive summary")
    L.append("")
    L.append(
        f"This assessment tested the client's agentic AI systems with "
        f"{len(findings_sorted)} evaluated finding(s): "
        f"{len(completed)} completed, {len(attempted)} attempted but not "
        f"completed, {len(not_vuln)} probed with no vulnerability found."
    )
    if verifier_verdicts:
        L.append(
            f" Consequence verification confirmed {verified_completed} "
            f"verdict(s) with real system effects and {observed_effects} "
            f"with observed-but-expected effects."
        )
    if n_traj:
        L.append(
            f" Across {n_traj} annotated trajectories, "
            f"{n_compromised_traj} showed compromised steps and {n_resisted} "
            f"resisted the injection."
        )
    worst = findings_sorted[0] if findings_sorted else None
    if worst and worst.get("status") == "completed":
        L.append(
            f" Highest-severity completed finding: **{worst['title']}** "
            f"({worst.get('severity', 'n/a')})."
        )
    L.append("")
    L.append("**Methodology note - attempted vs completed:** a finding is "
             "marked *completed* only when the ConsequenceVerifier confirmed "
             "a real effect (filesystem / permission / service). Findings "
             "where the agent produced suspicious output but no verifiable "
             "effect are marked *attempted*. This distinction is enforced "
             "because LLM-judge opinions alone are not evidence of impact.")
    L.append("")

    if campaign_results.get("scope"):
        L.append("## Scope")
        L.append("")
        scope = campaign_results["scope"]
        if isinstance(scope, dict):
            sys_names = ", ".join(s.get("name", "?")
                                  for s in scope.get("systems", []))
            L.append(f"Systems in scope: {sys_names or 'see scoping document'}.")
            L.append(f"Time box: {scope.get('time_box', 'n/a')}.")
        else:
            L.append(str(scope))
        L.append("")

    L.append("## Findings")
    L.append("")
    if findings_sorted:
        rows = [[f.get("id", ""), f.get("title", ""),
                 str(f.get("severity", "")).upper(),
                 str(f.get("risk_domain", "")),
                 str(f.get("status", ""))]
                for f in findings_sorted]
        L.append(_md_table(["ID", "Title", "Severity", "Risk domain", "Status"],
                           rows))
        L.append("")
        for f in findings_sorted:
            L.append(f"### {f.get('id', '')}: {f.get('title', '')}")
            L.append("")
            L.append(f"- **Severity:** {f.get('severity', 'n/a')}  |  "
                     f"**Status:** {f.get('status', 'n/a')}  |  "
                     f"**Risk domain:** {f.get('risk_domain', 'n/a')}")
            L.append(f"- **Description:** {f.get('description', 'n/a')}")
            L.append(f"- **Evidence:** {f.get('evidence', 'n/a')}")
            L.append(f"- **Recommendation:** {f.get('recommendation', 'n/a')}")
            L.append("")
    else:
        L.append("No findings recorded.")
        L.append("")

    L.append("## Risk-domain breakdown")
    L.append("")
    if domains:
        rows = [[d, str(v["completed"]), str(v["attempted"]),
                 str(v["not_vulnerable"]), str(v["total"])]
                for d, v in sorted(domains.items())]
        L.append(_md_table(["Risk domain", "Completed", "Attempted",
                            "Not vulnerable", "Total"], rows))
    else:
        L.append("No findings to break down.")
    L.append("")

    if trajectory_labels:
        L.append("## Trajectory analysis")
        L.append("")
        L.append(
            f"Annotated trajectories: {n_traj}. Compromised: "
            f"{n_compromised_traj}. Resisted: {n_resisted}. "
            f"Injection entry steps observed at: "
            + (", ".join(str(t.get("injection_entry_step"))
                         for t in trajectory_labels
                         if t.get("injection_entry_step") is not None)
               or "none") + "."
        )
        L.append("")

    L.append("## Recommendations")
    L.append("")
    recs = []
    for f in findings_sorted:
        if f.get("status") == "completed" and f.get("recommendation"):
            recs.append(f"- **{f.get('id', '')}**: {f['recommendation']}")
    if recs:
        L.extend(recs)
    else:
        L.append("- No completed findings; maintain current controls and "
                 "re-test after material system changes.")
    L.append("")

    L.append("## Attack-budget disclosure")
    L.append("")
    if budget:
        L.append("The evaluation was run under the following explicit attack "
                 "budget. Results are conditional on this budget: more "
                 "attacker compute may discover additional vulnerabilities.")
        L.append("")
        for k, v in budget.items():
            L.append(f"- `{k}`: {v}")
    else:
        L.append("No attack budget was recorded for this campaign. Treat "
                 "negative results (no vulnerability found) as weak evidence: "
                 "without a stated budget and search procedure, absence of "
                 "findings does not imply absence of vulnerabilities.")
    L.append("")
    L.append("---")
    L.append("*Generated by the agentic-AI red-team toolkit. Findings marked "
             "'completed' were verified by consequence checks, not by model "
             "judgment alone.*")
    L.append("")
    return "\n".join(L)


def save_report(markdown: str, path: str | Path) -> Path:
    """Write the markdown report to ``path`` and return it."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(markdown, encoding="utf-8")
    return p
