# North Star: how we work in this repo

purpose: north star rules loaded in every session (L0). Short on purpose; details load on demand from kit.manifest.yml.

## Start here
- Say what you want in plain words, or run `/genie`. It reads state with `kit/scripts/state.sh` and picks the next step.
- Read `kit.manifest.yml` first, then load only the component the step needs. Never load whole folders.
- State lives in files: `openspec/changes/<name>/status.md` is where any session resumes.
- New repo: `kit/INSTALL.md`; the Genie runs `/bootstrap` first.

## The floor (never lowered by the AI)
- Rules in `kit/core/rules.md` always apply. If a rule blocks you, stop and ask.
- Gates: `python3 kit/scripts/gate_check.py auto --change openspec/changes/<name>`. A failed gate is never waived.
- Files listed in `PROTECTED` (`kit/scripts/kitconst.py`) are changed only by humans, in their own PR.

## Flow per change (two PRs)
1. Spec from `kit/templates/spec.md`, then `/slice`. Gate `ready` passes; open the plan PR. A human merging it is the approval (G1).
2. On a new branch: `/implement`, one scenario per red-green cycle, evidence in `evidence.md`, at most 3 attempts.
3. Gate `done` passes on the code PR (CI runs it with real coverage and the red check). A human merges; you never do.
4. No code without a requirement, no requirement without a test, nothing the spec does not ask for.
