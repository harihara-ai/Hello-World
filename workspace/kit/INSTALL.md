# Install the kit into a repo

purpose: the one place that says where kit files go in a target repo, what a human protects, and how CI enforces the gates.

## Files
1. Copy `kit/` to the repo root as `kit/`, and `kit.manifest.yml` to the root.
2. Copy `kit/.claude/commands/*.md` to `.claude/commands/` (Claude Code reads commands only there).
3. Add the line `@kit/CLAUDE.md` to the root `CLAUDE.md` (create it if missing).
4. Needs `python3` (3.8 or later) and `git`. Nothing is installed; no hooks are added.
   Add `__pycache__/` and `openspec/changes/*/gates-*.json` (local gate output) to `.gitignore`.
5. A human merges this install PR (CI gates start with the next PR). Then run `/bootstrap`; it ends with its own PR.

## What a human protects
Put every pattern in `PROTECTED` in `kit/scripts/kitconst.py` into `CODEOWNERS`. That one list is what
`gate.diff_scope` refuses in an AI change; CODEOWNERS stops the same change arriving another way.

## Two PRs per change
1. Plan PR: `spec.md`, `slices.md`, `inputs/diff_scope.json`, `inputs/granularity.json`. CI runs `ready`; a human
   merges it. That merge is the G1 approval.
2. Code PR, branched after the plan is merged. CI runs `done`, which reads the plan from the base commit and
   fails if the PR changes it.

## CI is the gate that counts
Local runs are early feedback: the agent controls its own working copy. The required CI job runs the approved
kit from the target branch, in its own worktree, against the PR checkout:
```
git fetch origin <target> && BASE=$(git merge-base HEAD origin/<target>)
git worktree add ../approved origin/<target>
<run the tests with coverage; the step must pass; write the report outside the checkout: ../out/coverage.xml>
python3 ../approved/kit/scripts/gate_check.py auto --repo . --change auto --base $BASE \
  --coverage-report ../out/coverage.xml --baseline-report <the target's last coverage report> --test-cmd "<test command>"
```
The gate picks the stage: ready for a plan PR (it may change only its change folder), done for a code PR. A PR
with no change folder passes only if it touches docs or human-owned files. Keep each run's coverage report as an
artifact; the target's latest is the next baseline, so the base is never re-tested. `{tests}` in the test command
is replaced by the changed test files. No coverage tool (Delphi): a signed `min_changed_line_coverage: 0`.
When the install PR merges, run the tests with coverage on the target once and keep that report: it is the first baseline.
`{tests}` examples: pytest `pytest {tests}`; PHPUnit `vendor/bin/phpunit {tests}`. Maven and dotnet take class names, so
use the whole suite there.
Make the job a required check.

Hotfix at night: an admin merges with the check overridden; within 5 working days a retro plan PR adds the spec and an
`evidence.md` naming the merged commit (`kit/playbooks/bug.md`).

## Upgrade
Replace `kit/` and `kit.manifest.yml` in one human PR, copy the commands again (Files, step 2), then run `/refresh`.
