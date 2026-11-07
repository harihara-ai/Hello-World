# Install the kit into a repo

purpose: the one place that says where kit files go in a target repo, what a human protects, and how CI enforces the gates.

## Files
1. Copy `kit/` to the repo root as `kit/`, and `kit.manifest.yml` to the root.
2. Copy `kit/.claude/commands/*.md` to `.claude/commands/` (Claude Code reads commands only there).
3. Add the line `@kit/CLAUDE.md` to the root `CLAUDE.md` (create it if missing).
4. Needs `python3` (3.8 or later) and `git`. Nothing is installed; no hooks are added.
5. Open Claude Code and run `/bootstrap` on its own branch; a human merges its PR. Then use `/genie`.

## What a human protects
Put every pattern in `PROTECTED` in `kit/scripts/kitconst.py` into `CODEOWNERS`. That one list is what
`gate.diff_scope` refuses in an AI change; CODEOWNERS stops the same change arriving another way.

## CI is the gate that counts
A local `gate_check` run is early feedback: the agent controls its own working copy. The authoritative run is
a CI job on every PR, with nothing taken from the PR branch except the change itself:
1. Fresh clone; fetch the target branch.
2. `git checkout origin/<target> -- kit kit.manifest.yml docs/ai/policy.yml docs/ai/policy-signoff.json`
   (the kit, policy and sign-off as approved, not as the PR left them).
3. Run the test suite with coverage; CI writes the report path into `inputs/coverage.json`.
4. `python3 kit/scripts/gate_check.py done --change openspec/changes/<name> --base origin/<target>`
5. Make the job a required check. The human still reviews `spec.md`, `slices.md` and the impact scan in the PR.

## Upgrade
Replace `kit/` and `kit.manifest.yml` in one human PR, copy the commands again (step 2), then run `/refresh`.
