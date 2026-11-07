# Playbook: chore and refactor (no behaviour change)

purpose: steps for a chore or refactor where behaviour must stay identical.

1. **Goal and non-goal.** Write both in `spec.md` (Type: chore or refactor). No new requirement.
2. **Pin behaviour.** Characterization tests for every unit the impact scan lists. Green before any change; commit them alone, prefixed `CHAR:`.
3. **Measure before.** Record size, complexity or coupling of the touched files in `evidence.md`.
4. **Change.** Small steps, characterization tests green after each.
5. **Measure after.** Record the same numbers. A refactor must improve at least one and worsen none.
6. **Done.** `gate_check.py done`. `gate.diff_scope` must show only files in scope. Any test edit is explained in the PR.
