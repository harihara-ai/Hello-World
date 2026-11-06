---
description: Break an approved spec into slices: impact scan, granularity score, split, slice plan for human approval.
argument-hint: <change-name>
---

purpose: Break an approved spec into slices: impact scan, granularity score, split, slice plan for human approval.

Follow `CLAUDE.md` and `kit/core/rules.md`. Arguments: `$ARGUMENTS`.

1. List requirements and scenarios from `spec.md`.
2. Impact scan each requirement with capability.codenav `impact`. Write `impact.md` and `inputs/diff_scope.json`.
3. Measure each candidate slice and write `inputs/granularity.json`, then run `gate_check.py ready`.
4. Split any slice the gate marks split, preferring: by scenario, thin vertical slice, by contract, by data variant, by risk (spike). Never by technical layer alone.
5. Order by dependency. Add Slice 0 (characterization only) for untested code in scope.
6. Write `slices.md` and ask the human to approve the plan.
