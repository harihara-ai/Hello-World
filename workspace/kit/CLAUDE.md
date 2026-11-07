# North Star: how we work in this repo

purpose: north star rules loaded in every session (L0). Short on purpose; details load on demand from kit.manifest.yml.

## Start here
- Say what you want in plain words, or run `/genie`. It reads state with `kit/scripts/state.sh` and picks the next step.
- New repo: follow `kit/INSTALL.md`, then `/bootstrap`. The Genie runs `/bootstrap` first when `bootstrapped` is false.
- Read `kit.manifest.yml` first, then load only the component the step needs. Never load whole folders.
- State lives in files: `openspec/changes/<name>/status.md` is where any session resumes.

## The floor (never lowered by the AI)
- Rules in `kit/core/rules.md` always apply. If a rule blocks you, stop and ask.
- Gates: `python3 kit/scripts/gate_check.py ready|done --change openspec/changes/<name>`. A failed gate is never waived.
- Thresholds live in `docs/ai/policy.yml` (the kit floor `kit/core/policy.yml` applies when it is missing).
  Only humans change policy, sign-off, `kit/`, `.claude/` and `CLAUDE.md`, in their own PR; `gate.diff_scope` fails if you do.

## Flow per change
1. Ticket to spec: `kit/templates/spec.md`.
2. Slice: `/slice` scores every slice (red, or two ambers, means split), then gate `ready` must pass.
   Open the plan PR. A human merging it is the approval; the code goes in a second PR (`kit/INSTALL.md`).
3. Build: `/implement`, one scenario per red-green cycle, evidence in `evidence.md`, at most 3 attempts.
4. Done: gate `done` passes on the code PR (CI runs it with real coverage and the red check), then a human reviews and merges. You never merge.

## Knowledge
- `docs/ai/index.json` is always loaded. Module cards load when a spec touches the module.
- Tag derived facts `observed`, `inferred` or `confirmed`. Only `confirmed` becomes a spec.
- `/refresh` after merges updates only what changed.

## Smallest sufficient change
- No code without a requirement. No requirement without a test.
- No feature, flag or abstraction the spec does not ask for. Note out-of-scope ideas; do not build them.
