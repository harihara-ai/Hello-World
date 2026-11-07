purpose: registry of systemic root causes (hardening/RCA.md step 4), with the findings in each class and the prevention.

# Root causes

## R1: the kit's own workflows are never executed end to end by a test (score 10.5, do first)
Findings: P01 (upgrade PR fails gate), P03 (`/implement` writes `metrics.csv`, the gate refuses it), P05 (quarantine
PR cannot pass before a baseline), M01 (planted hooks between jobs, found by hand), N01 (workflow faked by the PR,
found by a live trial), "agent-driven flows: not run" in the register.
Whys (P03): gate refused `metrics.csv` -> the change-folder allow-list lacks it -> the list and `/implement` were
written in separate modules -> no test runs a command's outputs through the gates -> the kit's tests are unit tests
per component plus attack traps; nothing runs the good path of a playbook -> certification measured blocking bad
changes, not completing good ones (saturated: missing feedback loop).
Prevention (detect at the earliest stage), smallest form: add **good-path cases** to the existing test bed
(`hardening/testbed`, run by `run_traps.py`), each a git fixture that must PASS: upgrade PR, plan PR, code PR with
`metrics.csv`, quarantine PR. No new framework; one Python stack first (JS and Java only if a finding needs them).
Plus one contract test: every file a command says it writes is allowed by the gates.
Score: (6 + 3 likely) x 2.3 (two blockers, four minors) / M 2 = 10.5.
Verify (planned, not run): the suite shows P01, P03 and P05 RED on kit 1.0.4 and GREEN on 1.0.5. Status: open.

## R2: protected files are a hand-kept list per tool (score 4.2)
Findings: P02 (`.c8rc*` missing), J06 (build files hold coverage settings), item 3 list "untested on other stacks".
Whys: `.c8rc` unprotected -> PROTECTED lists tools someone remembered -> new stacks bring new config files ->
bootstrap detects the stack but not its config files -> no check that detected tools' configs are owned (saturated).
Prevention (eliminate + detect): `/bootstrap` derives the config files of each detected test and coverage tool from a
table per tool and fails the install check if CODEOWNERS does not cover them.
Score: (3 + 2 likely) x 1.7 / M 2 = 4.2. Status: open; corrective done (P02 pinned in 1.0.5).

## R3: human setup steps are not verified by the kit (score 3)
Findings: hidden classic branch protection (commons-lang#1), "Actions not enabled" scare, rulesets read by hand each
time, B2 bot-account loss.
Whys: merge blocked -> a classic rule existed -> the owner could not see it on a phone -> INSTALL asks for rules but
nothing reads them back -> no `verify-install` step (saturated: missing feedback loop).
Prevention (detect): a read-only `install_check` that reads rulesets, branch protection, CODEOWNERS and the
required checks through the API and prints what is missing, run at the end of `/bootstrap` and weekly.
Score: (4 + 2 likely) x 1 / M 2 = 3. Status: open.

## R4: the agent's sizing and scope are unmeasured judgement (score 3.5)
Findings: P04 (scan missed a test pinning the bug), F17 (estimates), KOA-1 estimate 37% low, G19.
Whys: a test was missed -> the scan was a ctags lookup the agent chose -> the scan has no required inputs (tests
that assert current values, callers, coverage per file) -> granularity checks the agent's numbers, not measured
ones (saturated: unmeasured judgement).
Prevention (eliminate): the slicer script in `DIRECTION.md` section 2 (measured impact, plan-vs-actual at done).
Score: (4 + 3 likely) x 2 / L 4 = 3.5. Status: open; corrective done (P04 bug playbook step, pinned in 1.0.5).

## Order
By score: R1 10.5, R2 4.2, R4 3.5, R3 3. Run order: R1, then R4 ahead of R2 (it blocks scale step S2, a
dependency override), then R2, then R3. Re-score when a new finding lands.
