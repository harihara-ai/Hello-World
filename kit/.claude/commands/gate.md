---
description: Run the deterministic gates (ready or done, picked from git), then an AI review; the human merge is the sign-off.
argument-hint: ready|done <change-name>
---

purpose: Run the deterministic gates (ready or done, picked from git), then an AI review; the human merge is the sign-off.

Follow `kit/core/rules.md`. Arguments: `$ARGUMENTS`.

1. Inputs: `inputs/granularity.json` and `inputs/diff_scope.json` come from `/slice`. For done, run the tests with coverage and pass `--coverage-report <report>`, `--baseline-report <target's last report>` and `--test-cmd "<test command>"` (CI passes its own).
2. Run `python3 kit/scripts/gate_check.py auto --change openspec/changes/<name>` (it picks ready or done).
3. If it fails: show each failing finding in one line and stop. Do not edit gates, tests or policy to pass.
4. If it passes: AI review. Ready: ambiguity and open questions. Done: tests assert behaviour, no weakened assertions
   (the gates cannot prove this; see `kit/core/rules.md` rule 10). Then open the PR; the human merge is the sign-off.
