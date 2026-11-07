---
description: Run the deterministic gates for ready or done, then an AI review, then ask the human for sign-off.
argument-hint: ready|done <change-name>
---

purpose: Run the deterministic gates for ready or done, then an AI review, then ask the human for sign-off.

Follow `kit/core/rules.md`. Arguments: `$ARGUMENTS`.

1. Inputs: `inputs/granularity.json` and `inputs/diff_scope.json` come from `/slice`. For done, run the tests with coverage and pass `--coverage-report <report>`, `--baseline-total <from docs/ai/baseline.md>` and `--test-cmd "<test command>"` (CI passes its own).
2. Run `python3 kit/scripts/gate_check.py <stage> --change openspec/changes/<name>`.
3. If it fails: show each failing finding in one line and stop. Do not edit gates, tests or policy to pass.
4. If it passes: AI review. Ready: ambiguity and open questions. Done: tests assert behaviour, no weakened assertions.
5. Ask the human for sign-off and record it in `status.md`.
