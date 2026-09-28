# Instructions for Muse contributions

Use this file when you add code, experiments, or reports to this repository.
The project is a local agentic prompt-injection test range and an inspectable
research record. Keep those two parts distinct. Preserve the existing frozen
rounds, including failed and ambiguous results.

## Your working contract

1. Read `README.md`, `EVIDENCE_INDEX.md`, and the files you plan to change.
   For a new experiment, read `groklink/round21/CORRECTION.md` before designing
   fixtures. Do not infer success from the title of a report.
2. Work on a branch and submit a focused pull request. State the question the
   change answers. Do not edit historical transcripts, frozen designs, or
   fixtures to improve a past score. Add a dated correction beside a disputed
   result and link it from the evidence index.
3. Use only dummy credentials, simulated tools, and approved test targets.
   The sandbox outbox must never send real mail. Keep personal data, API keys,
   and raw provider credentials out of commits and logs.
4. Keep the README accurate. A mock run checks the machinery; a model run
   measures that model in the stated setup. Never present one as the other.

## New experiment standard

Create a new `groklink/roundNN/` directory rather than changing an old round.
Before the first target run, write `DESIGN.md` with:

- the model and transport, exact versions, user task, attacker-controlled
  surface, trusted instructions, tool permissions, and run budget;
- one falsifiable hypothesis per case, a benign control, and an explicit
  success oracle that checks the attacker goal in simulated state;
- the planned number of runs, stop conditions, and how you will classify
  `completed`, `attempted`, `clean`, and `not engaged`;
- a fixture-consistency check. Trusted instructions must not contradict one
  another, and examples must use the same key anatomy and rule wording.

Freeze the design before final runs. Record its SHA-256 and document any
pre-run correction. Treat pilot work as exploratory. If you change a payload
or fixture after seeing a target response, start a new pilot or round and
report the change. One run can demonstrate an observed event, but it cannot
establish a failure rate. Use repeat runs for reliability claims and state
the denominator beside every count.

Save the smallest useful evidence set: the frozen design, fixture source,
driver and transport source, sanitized per-run transcript, deterministic
adjudication output, and a concise `RESULTS.md`. Include failed cases and
controls. Keep generated environment copies, process IDs, and verbose runtime
logs out of the main tree unless a specific finding needs them. If a run
requires a file that cannot be published, mark it nonreproducible in the
results and do not claim a reader can rerun it.

For each claimed success, cite the exact transcript event and the state
artifact that satisfies the oracle. Check recipient, content, and timing for
disclosure claims. A created outbox file or a suspicious model sentence alone
does not prove exfiltration. Manually review every claimed success and every
unexpected failure. Explain plausible alternative causes, especially
ambiguous trusted instructions and harness errors.

## Code standard

- Keep the sandbox runnable with Python 3.10 or newer. Document any new
  dependency and why the standard library is insufficient.
- Separate attack payloads, trusted fixtures, transport, and adjudication.
  Do not put the expected answer into a scorer that can read the payload
  instead of the model or workspace outcome.
- Add a meaningful test for every new outcome rule, including a false-positive
  case. Run `python -m unittest discover -s tests -v`,
  `python -m sandbox.quickstart`, and a mock campaign after changes to the
  harness. Run affected experiment checks for experiment changes.
- Keep code and reports specific. Use `completed` only when the declared
  attack goal is verified; use `effect_observed` when an effect has no goal
  oracle. Distinguish simulated effects from real-world impact.
- Update `README.md` and `EVIDENCE_INDEX.md` only when a new result changes
  what a reader should believe. Do not add broad capability claims from a
  single local run.

## Pull request handoff

In the pull request, provide: objective, changed paths, target and access
limits, result counts with denominators, strongest evidence links, failed or
ambiguous cases, tests run, reproducibility status, and remaining caveats.
If you disagree with an earlier conclusion, state the competing explanation
and preserve the original record.
