# Install the kit into a repo

purpose: the one place that says where kit files go in a target repo, what a human protects, and how CI enforces the gates.

## Files
1. Copy `kit/` to the repo root as `kit/`, and `kit.manifest.yml` to the root.
2. Copy `kit/.claude/commands/*.md` to `.claude/commands/` (Claude Code reads commands only there).
3. Add the line `@kit/CLAUDE.md` to the root `CLAUDE.md` (create it if missing).
4. Needs `python3` (3.8 or later) and `git`. Nothing is installed; no hooks are added.
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
git fetch origin <target>
BASE=$(git merge-base HEAD origin/<target>)
git worktree add ../approved origin/<target>
GATE="python3 ../approved/kit/scripts/gate_check.py --repo . --change auto --base $BASE"
$GATE ready                                  # plan PRs
<run the tests with coverage on HEAD, writing the report outside the checkout, e.g. ../out/coverage.xml>
<the same on BASE (or reuse the target branch's last report) for ../out/base.xml>
$GATE done --coverage-report ../out/coverage.xml --baseline-report ../out/base.xml --test-cmd "<test command>"
```
`--change auto` finds the PR's one change folder. With none, the job passes only if no production code changed
(install, bootstrap and human kit or policy PRs; CODEOWNERS covers those). Make the job a required check.

## Upgrade
Replace `kit/` and `kit.manifest.yml` in one human PR, copy the commands again (Files, step 2), then run `/refresh`.
