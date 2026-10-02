# SEED

> Propose a change. Test it against reality. Keep it only if measurably better.
> The thing being measured can never edit the measuring.

This file and `judge/` are frozen. Only humans edit them. The Judge refuses to
score if their hash changes (see `judge.sha256`).

## Loop
0. Baseline: Judge scores plain Claude Code (no harness).
1. Observer -> Builder -> harness v0. Judge scores v0.
2. Repeat up to N generations:
   a. Evolver reads train failures and proposes ONE small change.
   b. Judge scores the new harness.
   c. Keep it if train improves and held-out does not drop. Otherwise revert.
   d. Log everything to `log.jsonl`.
3. Stop when N is reached, the budget is hit, or 3 generations bring no gain.

## Gates
- Gate 0: baseline is 0% or 100%: the tasks are bad. Stop.
- Gate 1: v0 scores below baseline: fix the seed prompts, not the harness. Stop.
- Gate 2: a task gives different results across repeated runs: drop it.
