purpose: fix plan item 1, the short R2 and R5 check of the after-cap fixes L01-L04 (not a full round).

# After-cap check (2026-11-07)

Kit at `605ebf3` (lock `97cf6129...`, unchanged). Python 3.13.18, git 2.43.0, coverage.py 7.17.2 and pytest 9.2.0
installed to the session scratchpad (not the repo). Harness in the scratchpad: `mk.sh` (bare origin, app with
`subtotal`, install PR per INSTALL Files 1-5, first baseline, merged CART-3 plan PR), `ci.sh` (the INSTALL CI block
line for line, `set -e`, on a fresh clone, test command pytest `{tests}`), `pr.sh` and `run.sh` (one branch per attack).

## R5: forge and test bed
| Step | Result | Evidence |
| --- | --- | --- |
| forge check, lint | ok | `check ok`; `OK: 49 components clean` |
| forge selftest | ok | `70 files match the lock`; forge 25, unit 169, contract 5, mutation 14 OK |
| run_traps (1 run, not 5) | ok | `score: 22/22 cases; critical 17/17; other 5/5; false alarms 0` |

## R5: INSTALL walk-through
| Case | Expected | Actual |
| --- | --- | --- |
| plan PR CI, unmerged plan (L03: was `.coverage` outside_scan) | ready passes | `stage ready pass True`; `git status` in the job checkout empty |
| a0 clean code PR | done passes | `stage done pass True`, exit 0 |
| e1 empty evidence.md | blocked | `plan:no_evidence` |
| a2 tests call code, assert nothing (L05, limit J04) | passes (accepted limit) | `pass True`, exit 0: limit unchanged |
| a3 tests `pass`, no import | blocked | `red_check:tests_pass_on_base`, `coverage:changed_lines` |
| c3 unrequested `free_shipping()` | blocked | `coverage:overall_drop` |
| c2 second PR, no change folder | blocked | `found none, but code or tests changed: ['src/cart.py']` |
| u4, c2b second PR reusing the merged plan | blocked | `plan:plan_used` |
| s1 spike: docs-only findings PR (L04) | passes | `no change folder: only docs or human-owned files changed`, exit 0 |
| s2 spike findings plus `src/proto.py` | blocked | `found none, but code or tests changed: ['src/proto.py']` |

## R2: round 6 attacks
| Attack | Fix | Actual |
| --- | --- | --- |
| d1 pytest doctest `testing-notes.txt` in the change folder, `subtotal` broken | L01 | test step passed (doctest hid it); gate `diff_scope:code_in_change_folder`, exit 1 |
| k2 `conftest.py` in the change folder | L01 | `code_in_change_folder` |
| n1 `CLAUDE.md` and `.claude/settings.json` in the change folder | L01 | `protected_path` x2, `code_in_change_folder` |
| t0 control: unrequested `src/extra.py`, no plant | - | `diff_scope:outside_scan`, `coverage:overall_drop` |
| t1 round 6 attack: a test rewrites `../approved/kit/gates` | L02 | blocked: the worktree does not exist yet; `outside_scan` |
| t1b a test pre-creates `../approved` | L02 | job stops: `fatal: '../approved' already exists`, exit 128 |
| t2 a test writes `.git/hooks/post-checkout`; `git worktree add` runs it, it rewrites every approved gate to print pass | L02 | **NOT BLOCKED**: all six gates True, exit 0, with `src/extra.py` out of scope |
| t3 a test sets `core.fsmonitor` in `.git/config`; gate_check's own git calls run it | L02 | **NOT BLOCKED**: same, exit 0 |
| t4 a test sets `core.fsmonitor` in `~/.gitconfig` (HOME isolated to the scratchpad) | L02 | **NOT BLOCKED**: same, exit 0 |

L01 holds. L03 holds. L04 holds. L02 holds against its own round 6 attack but not against its root cause: PR code runs
earlier in the same job and can leave behind anything git or the shell later executes (repo hooks, repo or user git
config). t4 shows that a fresh clone in the same job would not be enough either.

```
id: M01
severity: blocker
location: workspace/kit/INSTALL.md "CI is the gate that counts" (one job: tests, then worktree, then gate_check)
evidence: t2, t3, t4 above: out-of-scope src/extra.py, "stage done pass True", all gates True, exit 0
problem: The PR's test step can plant a git hook or git config (repo or user) that runs at `git worktree add` or at
gate_check's own git calls, and rewrites the approved kit before the gates run.
proposed_fix: The step R2-6-02 already proposed: two jobs. The test job runs the PR's tests and keeps the coverage report as
an artifact; the required gate job, on a fresh runner, runs no PR code before gate_check (red_check, the last gate,
is the only step that runs PR tests there). One INSTALL edit; no new gate or flag.
confidence: high
```

Not run: a hosted CI with two jobs (so the proposed fix is unverified); whether PR tests can tamper with the coverage
data or report they produce (the report already comes from a run of PR code); PATH or other user-level plants beyond
`~/.gitconfig`; R2-5-01 u2/u3 (whitespace-only evidence.md) and the untracked `__pycache__` note (a2 of round 6).

## M01 fix (fix plan item 1b): RED then GREEN
Source: `proposal/modules/01-core.md` (core.install), INSTALL "CI is the gate that counts" now has two jobs. Harness:
`attacks.sh` runs the same 9 cases against `ci.sh` (current recipe, one job, one HOME) and `ci2.sh` (tests job, then a
gate job with its own dir, own HOME and a fresh clone; the report passed as an artifact). Fresh origins for each run.

| Case | RED: current recipe | GREEN: two jobs |
| --- | --- | --- |
| plan PR (unmerged plan) | ready pass, exit 0 | ready pass, exit 0 |
| a0 clean code PR | done pass, exit 0 | done pass, exit 0 |
| t0 control, out-of-scope file | outside_scan, exit 1 | outside_scan, exit 1 |
| d1 doctest .txt in change folder | code_in_change_folder, exit 1 | code_in_change_folder, exit 1 |
| t1 test rewrites `../approved` | outside_scan, exit 1 | outside_scan, exit 1 |
| t2 planted `post-checkout` hook | **pass, exit 0** | outside_scan, overall_drop, exit 1 |
| t3 planted `core.fsmonitor` in `.git/config` | **pass, exit 0** | outside_scan, overall_drop, exit 1 |
| t4 planted `core.fsmonitor` in `~/.gitconfig` | **pass, exit 0** | outside_scan, overall_drop, exit 1 |
| s1 spike docs-only PR | pass, exit 0 | pass, exit 0 |

GREEN: approved `diff_scope.py` in the gate job is the real file after t3 (not the planted stub).
Scratch tangle: `PINNED 70 files. added=0 changed=1 removed=0`, `changed: kit/INSTALL.md HIGH-RISK`; only that file
differs from `workspace/`. Not pinned: awaiting the human. Not run: a hosted CI (GitHub/GitLab) with two real jobs and
artifacts; a self-hosted runner; installing test tools "as ../approved declares them" (the harness uses the runner's
tools); the gate job's red_check run is the only PR code there and runs after every other gate (by reading gate_check).
