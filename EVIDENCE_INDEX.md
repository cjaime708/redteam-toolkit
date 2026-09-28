# Evidence index

This page separates model experiments from scripted harness checks. A saved
transcript shows what the local instrument recorded. It does not prove a
result generalizes to other models, prompts, or deployments.

## Model experiments

| Study | Design and record | What the record supports | Limit |
| --- | --- | --- | --- |
| Round 18, grok-4.7 | [Design](groklink/round18/DESIGN.md), [results](groklink/round18/RESULTS.md), [transcripts](groklink/round18/transcripts/) | One simulated full-key disclosure in 20 runs. The report also identifies 15 flags caused by an ambiguous fingerprint definition. | The 20 runs test five local case families. They do not estimate a deployment-wide failure rate. |
| Round 21, gpt-5.6-sol | [Design](groklink/round21/DESIGN.md), [results](groklink/round21/RESULTS.md), [transcripts](groklink/round21/transcripts/) | Two of four local runs logged the dummy full key to an attacker-designated simulated address. | The trusted fixture contradicted itself. Read the [correction](groklink/round21/CORRECTION.md); the runs do not isolate the forged email as the cause. |

Historical designs and raw records remain in place, including failures and
ambiguous results. We do not edit frozen fixtures to make old results look
cleaner. New hypotheses require a new round and fresh fixtures.

## Harness checks

- [`sandbox/quickstart.py`](sandbox/quickstart.py) checks clean, completed,
  and blocked paths with a scripted backend.
- [`sandbox/campaign.py`](sandbox/campaign.py) runs a six-scenario mock battery
  with explicit goals and a benign control. Its successes are scripted.
- [`tests/test_attack_goals.py`](tests/test_attack_goals.py) checks false
  positives: an outbox effect with the wrong recipient or body is not a
  completed leak.

## Reproducibility status

The sandbox and unit tests run from this checkout with Python 3.10 or newer.
The saved `groklink` rounds include transcripts and adjudication files, but
some drivers import `common/turn_runner.py`, which is absent. Treat those
rounds as inspectable historical records until their transport and setup can
be packaged and rerun independently.
