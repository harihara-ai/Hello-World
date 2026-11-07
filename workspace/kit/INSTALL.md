# Install the kit into a repo

purpose: the one place that says where kit files go in a target repo, what a human protects, and how CI enforces the gates.

## Files
1. Copy `kit/` to the repo root as `kit/`, and `kit.manifest.yml` to the root.
2. Copy `kit/.claude/commands/*.md` to `.claude/commands/` (Claude Code reads commands only there).
3. Add the line `@kit/CLAUDE.md` to the root `CLAUDE.md` (create it if missing).
4. Needs `python3` (3.8 or later) and `git`. Nothing is installed; no hooks are added.
   Add `__pycache__/`, `.coverage` and `openspec/changes/*/gates-*.json` (local and test output) to `.gitignore`.
5. Add the CI jobs (below) in this same PR. A human merges it (CI gates start with the next PR). Then run `/bootstrap`; it ends with its own PR.

## What a human protects
Put every pattern in `PROTECTED` in `kit/scripts/kitconst.py` into `CODEOWNERS`. That one list is what
`gate.diff_scope` refuses in an AI change; CODEOWNERS stops the same change arriving another way.
Also list the build files that can hold coverage or test settings: `pyproject.toml`, `setup.cfg`, `tox.ini`, `pom.xml`,
`build.gradle*`, `package.json`, `*.csproj`. They are not in `PROTECTED` (a change may need them), so a human reviews each change.

## Two PRs per change
1. Plan PR: `spec.md`, `slices.md`, `inputs/diff_scope.json`, `inputs/granularity.json`, never `evidence.md` (it marks
   the plan as implemented). CI runs `ready`; a human
   merges it. That merge is the G1 approval.
2. Code PR, branched after the plan is merged. CI runs `done`, which reads the plan from the base commit and
   fails if the PR changes it.

## CI is the gate that counts
Local runs are early feedback: the agent controls its own working copy. CI has two jobs, so PR code never runs
before the gates (a test can plant a git hook or git config that rewrites the kit on the same runner):
1. **tests**: run the PR's tests with coverage; the step must pass. Keep the report as an artifact.
2. **gate**, after tests, on a fresh runner (hosted runners are; a self-hosted one must be ephemeral). It runs the
   approved kit from the target branch in its own worktree and no PR code before `gate_check.py`: install test tools
   as `../approved` declares them, never from files the PR changed. Only `red_check`, the last gate, runs PR tests.
```
# tests job
set -e
COVERAGE_FILE=../out/.coverage <run the tests with coverage, writing the report to ../out/coverage.xml>
<keep ../out/coverage.xml as this run's artifact>
# gate job
set -e
git fetch origin <target> && BASE=$(git merge-base HEAD origin/<target>)
git worktree add ../approved origin/<target>
<install the test tools from ../approved; fetch the tests job's report to ../out/coverage.xml>
python3 -I ../approved/kit/scripts/gate_check.py auto --repo . --change auto --base $BASE \
  --coverage-report ../out/coverage.xml --baseline-report <the target's last coverage report> --test-cmd "<test command>"
```
The gate picks the stage: ready for a plan PR (it may change only its change folder), done for a code PR. A PR
with no change folder passes only if it touches docs or human-owned files. Keep each run's coverage report as an
artifact; the target's latest is the next baseline, so the base is never re-tested. `{tests}` in the test command
is replaced by the changed test files. No coverage tool (Delphi): a signed `min_changed_line_coverage: 0`.
When the install PR merges, run the tests with coverage on the target once and keep that report: it is the first baseline
(a flaky test there is quarantined first: `kit/playbooks/safety-net.md`).
`{tests}` examples: pytest `pytest {tests}`; PHPUnit `vendor/bin/phpunit {tests}`. Maven and dotnet take class names and
Delphi (DUnit, DUnitX) takes no file list, so use the whole suite there. Keep CI helper scripts tracked or outside the
checkout: the red check treats an untracked file as added code and removes it for the base run.
Make both jobs required checks.

Hotfix at night: an admin merges with the check overridden; within 5 working days a retro plan PR adds the spec and an
`evidence.md` naming the merged commit (`kit/playbooks/bug.md`).

## Upgrade
Replace `kit/` and `kit.manifest.yml` in one human PR, copy the commands again (Files, step 2), then run `/refresh`.
