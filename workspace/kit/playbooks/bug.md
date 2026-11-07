# Playbook: bug and hotfix

purpose: steps for a bug or production hotfix: a plan PR, then a code PR whose regression test fails first.

1. **Intake.** `read_ticket`. Save `ticket.md`. Branch `fix/<KEY>-<slug>-plan`.
2. **Plan PR.** Spec with a REQ ID for the broken behaviour (`Type: bug` or `hotfix`), a one-slice
   `inputs/granularity.json` and `inputs/diff_scope.json`. `gate_check.py auto` runs ready; a human merges it.
3. **Reproduce.** On `fix/<KEY>-<slug>` from the target: one failing test carrying the REQ ID. Record RED in `evidence.md`.
4. **Fix.** Smallest change that turns the test GREEN. Note the root cause in `evidence.md`.
5. **Done.** `gate_check.py auto` runs done, unchanged for hotfixes; `gate.red_check` confirms the test fails without the fix.
6. **Hotfix merged at night with the check overridden** (`kit/INSTALL.md`): within 5 working days open a retro plan PR with
   the spec and an `evidence.md` that names the merged commit. It passes ready and needs no code PR.
