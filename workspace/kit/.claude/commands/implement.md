---
description: Implement one approved slice with red-green-refactor, evidence, and a 3-attempt cap.
argument-hint: <change-name> [slice]
---

purpose: Implement one approved slice with red-green-refactor, evidence, and a 3-attempt cap.

Follow `CLAUDE.md` and `kit/core/rules.md`. Arguments: `$ARGUMENTS`.

0. Check: G1 passed and the human approval is recorded in `status.md`. If not, stop.
1. For each task (one scenario): write the test with the REQ ID in its name. Run it. RED for the right reason. Append command and short output to `evidence.md`.
2. Minimum code to pass. Run it. GREEN. Append to `evidence.md`.
3. Refactor only what you just wrote, tests green. Commit `REQ-<AREA>-<NNN>: <what>`.
4. Append a row to `metrics.csv`. Update `status.md`.
5. After 3 failed attempts on a task: stop and report with evidence. Out-of-scope ideas go under "Out of scope noticed" in `evidence.md`.
Never edit a test to make it pass. Never touch files outside `impact.md`.
