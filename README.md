# SEED: a self-building harness

An implementation of the SEED lean spec v0.1. Point it at a repo and it builds a Claude Code
harness (CLAUDE.md, hooks, skills, scripts) for that repo, then improves the harness one small
change at a time. A change is kept only when the repo's own git history shows it is measurably better.

> Propose a change. Test it against reality. Keep it only if measurably better.
> The thing being measured can never edit the measuring.

It uses only the Python standard library (3.9+), plus `git` and the `claude` CLI.

## Quickstart

```sh
cd /path/to/repo-under-test
python -m seed survey            # needs >= 15 fix-with-test commits
python -m seed init              # creates .seed/; review test_cmd and regression_cmd in .seed/judge/config.json
python -m seed mine              # mines tasks, checks fail-before/pass-after, freezes the judge
python -m seed baseline          # plain Claude Code (Gates 0 and 2)
python -m seed build             # Observer -> Builder -> v0, scored (Gate 1)
python -m seed evolve --generations 5
python -m seed confirm           # the verdict: fresh baseline vs harness on held-out, paired
python -m seed reflect           # writes .seed/seed-proposals.md for a human
python -m seed report
```

Run it from a checkout of this repo (`PYTHONPATH=/path/to/this/repo`), or pass `--repo PATH`.
`python -m seed run` runs baseline, build, evolve, confirm and reflect in one go.

## Layout in the repo under test

```
.seed/
  SEED.md          frozen: the principle and the loop
  judge/           frozen: config.json, tasks.json, hidden/<task>/<test files>
  judge.sha256     hash of judge/ + SEED.md, checked before and after every role and every scoring run
  harness/         mutable, its own git repo: one commit per kept change, reverted with git
  log.jsonl        one line per generation: change, score, cost, kept/reverted, reason
  runs/            per-run evidence: prompt, agent output, diff, hidden-test log
  state.json       money spent, tasks dropped as noisy (Gate 2)
```

`seed init` adds `.seed/` to `.git/info/exclude`, so task checkouts (git worktrees) never contain it.

## How the spec maps to the code

| Spec | Where |
|---|---|
| Mine fix + test commits; hide the tests; the issue text is the commit message | `seed/mine.py` |
| Judge: worktree at the parent, install the harness, `claude -p` with caps, anti-cheat diff check, run hidden tests, regression suite | `seed/judge.py` |
| Headless agent with max turns, max $ per task, timeout | `seed/agent.py` |
| Observer, Builder, Evolver, Reflector prompts | `seed/prompts/*.md` |
| Ratchet: keep if train goes up and held-out does not drop; tie-break on cost, then turns | `loop.is_better` |
| One small change per generation (diff size cap, default 80 lines); an exact repeat of a rejected change is refused without scoring | `loop.run_evolve` |
| Gates 0, 1, 2; caps on generations, $ per generation, total $; stop after 3 generations with no gain | `seed/loop.py`, `seed/config.py` |
| The Evolver sees train failures only; held-out stays unseen | `loop.write_digest` |
| Reflector proposals are never applied automatically | `prompts/reflector.md` |

Notes on choices the spec leaves open:

- **Task validation.** `mine` keeps a task only if its hidden tests fail on the parent commit
  and pass on the fix commit. Use `--no-validate` to skip this check.
- **"Remove the fix."** The task checkout is the parent commit, so the fix is simply not there yet.
- **Test command.** `test_cmd` in `judge/config.json` is a human decision and is frozen with the judge.
  `{tests}` expands to the hidden test paths and `{test_names}` to their basenames
  (for JUnit-style `-Dtest=`). `init` guesses a value from the build files.
- **Fair tasks only.** With `bugfix_only` (the default), `mine` drops feature commits and bug reports
  shorter than `min_issue_words` (default 4), before spending time on validation. A commit counts as a
  feature when its subject starts with add/implement/introduce/new and doesn't also say fix/bug, or when
  the fix defines a new top-level function or class that didn't exist at the parent. On more-itertools,
  this keeps 56 of 88 candidates.
- **Regression check.** A run passes only if the hidden tests pass *and* `regression_cmd`
  (the repo's existing suite) stays green. During `mine`, the suite is run on each reference fix;
  if it fails there too (broken or environment-dependent tests), the check is turned off for that task
  and `mine` prints a note. Set `regression_cmd` to null to disable it.
- **Failure categories.** Every run is labelled `PASS`, `CHEATED`, `NO_CHANGE`, `WRONG_FIX`,
  `REGRESSION`, `TIMEOUT` or `NOT_RUN`. The Evolver's input starts with a count by category, and the log
  and report show it. `SETUP_FAILURE` and `JUDGE_ERROR` are problems on the Judge's side: they are reported
  as `invalid` and left out of the pass rate rather than counted against the harness.
- **No blind retries.** Each harness change is fingerprinted by its added and removed lines. A change
  identical to one already rejected is reverted without spending a scoring run.
- **Claim vs. evidence.** Each run records whether the agent's final message claims success.
  `false_claims` counts runs that claimed success while the hidden tests or the suite said otherwise.
  It is reported, but it never enters the keep/revert decision.
- **Tokens and models.** Input tokens (including cache reads and writes), output tokens and model names
  come from `claude -p`'s JSON output and are summed per generation, next to cost and turns.
- **Re-scoring for free.** Each run saves only the agent's own diff. `seed rescore <label>` replays the
  saved diffs on clean checkouts and grades them with the current judge, with no model calls. Use it
  after making the judge stricter.
- **Smoke test.** `seed try <task-id> --max-turns 15 --max-cost 1` runs one capped attempt at one task.
- **Split by time.** By default (`split_mode: "time"`) the newest third of tasks is held out, so held-out
  measures whether the harness generalizes to *later* work, not just to other bugs from the same era.
  `"hash"` gives a random split.
- **Keep margin.** A change is kept only if it nets at least `min_net_flips` (default 2) newly passing
  train tasks, counted task by task. A one-task wobble from run-to-run noise doesn't count as progress.
- **Overfitting guard.** A change whose added lines name code identifiers from training bug reports
  (snake_case, dotted, `called()`, or `quoted` names) is reverted unscored. Names the Observer recorded in
  `facts.md` count as general knowledge, not leaks.
- **Removal trials.** Every `ablate_every` generations (default 3), instead of asking the Evolver for an
  addition, SEED deletes one harness piece: a CLAUDE.md paragraph or a file. It keeps the deletion if the
  score is no worse. Each piece is tried once (again if its content changes). Without this, harnesses only grow.
- **Confirmation is the verdict.** The ratchet keeps whatever scored best, so its logged scores are biased
  upward. `seed confirm` runs plain Claude Code and the final harness fresh, `confirm_runs` times each
  (default 3), on held-out tasks only. It compares pass rates task by task and runs an exact sign test.
  `seed report` shows that verdict, not the ratchet's scores.
- **Gate 2.** The baseline runs each task `baseline_runs` times (default 3). Tasks with mixed
  results are dropped from all later scoring.
- **Roles never touch your working tree.** Observer, Builder and Evolver run in a throwaway
  worktree of HEAD and can write only to `.seed/harness` (enforced by deny rules plus the hash check).

## Isolation: what is and isn't enforced

The frozen judge is protected four ways: it is never inside a task checkout, Claude Code deny rules
block `Read`/`Edit`/`Write` on `.seed/`, it is set read-only with chmod, and its hash is checked
before and after every run (any change stops the run). An agent running with
`--dangerously-skip-permissions` can still reach `.seed/` through `Bash`, and root ignores chmod.
For real runs, use a container, or mount `.seed/judge` from somewhere the agent cannot read,
as the spec suggests.

## Tests

```sh
python -m unittest discover -s tests -v
```

`tests/fake_agent.py` stands in for `claude -p` in every role, so the whole loop runs on a synthetic
repo with no API calls. The suite checks mining, hidden tests, the anti-cheat zero, a fix that passes its
hidden test but breaks the suite (`REGRESSION`), a sabotaging change reverted by the ratchet, an oversized
change rejected, a repeated rejected change refused, Gate 0, and a tampered judge refusing to score.

## Not done yet

- Build-order steps 4 and 5 need real repos: pick repo A and repo B (verify each with `seed survey`),
  then repo C, which needs a characterization-test generation step before the Judge. That step
  is not implemented.
- No real `claude -p` runs have been made. Budget for a run is roughly
  tasks × runs × (generations + 2) × the per-task cap.
- Issue text comes from the commit message only. Linked GitHub issues are not fetched.
