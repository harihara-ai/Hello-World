purpose: the findings ledger, the memory of the hardening loop.

Round 1 (frozen a5d992e, option A: Claude-only subagents). Raw findings: R1 12, R2 12, R3 12, R4 10, R5 0 (46; 16 blockers).
Consolidated below as F-ids; duplicates merged. Decisions by the single editor; human arbitrates at the round 1 checkpoint.

| id | round | severity | location | problem | decision | reason | status |
|---|---|---|---|---|---|---|---|
| F01 | 1 | blocker | gates/trace_check.py | REQ ID in src/ or any file counts as a test (R1-07, R2-01, R3-02) | accept | count IDs only in test files (shared test globs), drop test_dirs input; comment-only links in test files stay a known limit (spec 13) | fixed (pinned round 1) |
| F02 | 1 | blocker | gates/trace_check.py | Java/C#/Delphi names cannot hold '-' (R3-01) | accept | match REQ[-_]AREA[-_]NNN, case-insensitive, normalise | fixed (pinned round 1) |
| F03 | 1 | blocker | scripts/gate_check.py | agent-written inputs redirect spec_lint/trace_check targets (R2-02) | accept | targets come from the change path only | fixed (pinned round 1) |
| F04 | 1 | blocker | scripts/gateio.py, coverage.py | NaN passes numeric floors; empty changed set = 100% (R2-03) | accept | reject NaN/Infinity on input; warn on empty changed set | fixed (pinned round 1) |
| F05 | 1 | blocker | gates/coverage.py | no producer for coverage input; agent hand-writes it (R1-11, R3-03, R3-04) | accept | coverage reads Cobertura/JaCoCo/lcov/clover report plus git diff -U0 itself, instrumented lines only | fixed (pinned round 1) |
| F06 | 1 | blocker | gates/diff_scope.py | no default base; renames hide deletes; changed_files trusted; change folder flagged; .NET test layouts (R1-04, R2-04, R3-12) | accept | gate_check passes base; --no-renames; git wins over changed_files; exempt change folder; more test globs | fixed (pinned round 1) |
| F07 | 1 | blocker | policy_guard.py, diff_scope.py | sign-off, policy and kit files are agent-writable (R1-03, R2-05) | accept | diff_scope fails on protected paths (policy, sign-off, kit/, .claude/, CLAUDE.md): humans change them in their own PR; sign-off binds key to value | fixed (pinned round 1) |
| F08 | 1 | blocker | core/policy.yml, policy_guard.py | ready runs on unguarded policy; raised repo floor can be lowered back (R1-02, R2-06) | accept | policy_guard in both stages; compare to max(kit floor, base-commit policy); drop --policy | fixed (pinned round 1) |
| F09 | 1 | blocker | gate_check.py, injection.py | hostile ticket text blocks the change forever (R1-01) | accept | fetched data (ticket.md, comments/) is flagged as warn; AI-written files fail | fixed (pinned round 1) |
| F10 | 1 | blocker | gate_check.py | one done list cannot fit chore/refactor/spike/tests (R1-05) | accept | fixed per-Type table in gate_check, not editable via policy | fixed (pinned round 1) |
| F11 | 1 | blocker | kit layout | commands and CLAUDE.md are not where Claude Code looks; no install step (R1-09, R4-01, R4-02, R4-04) | accept | kit/INSTALL.md; state.sh reports bootstrapped; Genie runs /bootstrap first | fixed (pinned round 1) |
| F12 | 1 | blocker | forge/tangle.py | high-risk prefixes are root-anchored, so kit/.claude/settings.json etc. need no approval; fences in HTML comments tangled (R2-09) | accept | match high-risk on any segment, mark HIGH-RISK in pin output, skip fences inside comments | fixed (pinned round 1) |
| F13 | 1 | major | forge/forge.sh, tangle.py | hand-edited or planted workspace files run and ship (R2-10) | accept | --check also hashes the outdir; selftest and package call it | fixed (pinned round 1) |
| F14 | 1 | major | gates/injection.py, gate_check.py | unicode tricks, paraphrases, non-md and UTF-16 files, dir names unscanned (R2-07, R2-08) | accept | NFKC, strip Cf, flag mixed scripts, 3 more patterns, scan all files; rules.md calls it a tripwire | fixed (pinned round 1) |
| F15 | 1 | major | gates/spec_lint.py | any digit exempts vague words; banned words hit quoted names; Scenario Outline and error-by-title (R2-11, R3-08, R3-09) | accept | number with unit or comparator; skip backticks and Problem/Out of scope; accept Scenario Outline; error case by Then wording | fixed (pinned round 1) |
| F16 | 1 | major | gates/granularity.py | and/or hard red; characterization slices cannot fit (R3-06) | accept | and/or amber; kind characterization exempt from lines/symbols (spec 11.3 write-back needed) | fixed (pinned round 1) |
| F17 | 1 | major | slice inputs | slice numbers are LLM estimates; untested can be set to none (R3-07) | defer | needs per-file coverage from F05 first; round 2 | open (round 2) |
| F18 | 1 | major | gates/coverage.py | strict total compare; stacks with no coverage tool (R3-05) | accept part | max_total_drop 0.1 (may only fall); no-tool case deferred | fixed in part (pinned round 1) |
| F19 | 1 | major | gates/flaky.py, safety-net | no runs producer, quarantine undefined, failing passes (R3-11) | accept part | quarantine list docs/ai/quarantine.md; converter deferred | fixed in part (pinned round 1) |
| F20 | 1 | major | playbooks/safety-net.md | golden master, scrubbing, seams, bounded scope missing (R3-10) | accept | four lines in the playbook; seams go in their own chore change | fixed (pinned round 1) |
| F21 | 1 | major | playbooks/bug.md | hotfix cannot pass G1 without a slice file (R1-06) | accept | hotfix writes a one-slice plan | fixed (pinned round 1) |
| F22 | 1 | major | CLAUDE.md, commands | ready-before-slice order cannot work (R1-08) | accept | order: spec, slice, gate ready, approve; spec section 3 write-back needed | fixed (pinned round 1) |
| F23 | 1 | major | scripts/probe.py | probe tool names do not match adapters (R1-10) | accept | rank by adapter name | fixed (pinned round 1) |
| F24 | 1 | major | CLAUDE.md, gate.md | policy fallback and input producers unstated (R4-03, R4-05) | accept | one line each | fixed (pinned round 1) |
| F25 | 1 | major | hardening/testbed | test bed scores only seeded phrasing and gate names (R2-12) | accept | expect_rule, git-initialised repos, 4 adversarial cases | fixed (pinned round 1) |
| F26 | 1 | minor | core/state.md | index schema lacks module paths for /refresh (R1-12) | accept | add spec 6 fields | fixed (pinned round 1) |
| F27 | 1 | minor | commands | duplicate purpose line and CLAUDE.md re-read (R4-06) | accept part | drop the CLAUDE.md mention; purpose line kept (lint rule) | fixed in part (pinned round 1) |
| F28 | 1 | minor | commands | remove /safety-net, /refresh (R4-07) | reject | spec 19.6 lists them as deliverables | closed |
| F29 | 1 | minor | bootstrap.md | five questions at once (R4-08) | accept | report unknowns; Genie asks one at a time | fixed (pinned round 1) |
| F30 | 1 | minor | playbooks/story.md | impact scan step duplicates /slice; one big approval (R4-09) | accept part | delete duplicate step; single G1 approval kept (spec 10.2 #11) | fixed in part (pinned round 1) |
| F31 | 1 | minor | adapters | all adapters ship to every repo (R4-10) | reject | manifest loads lazily; spec 19.6 lists all adapters | closed |

Doc write-back needed after round 1 (proposal is read-only here): section 3 order (slice before /gate ready), section 11.3 ('and'/'or' amber; characterization slices skip size), section 10.6 (policy_guard in both stages, protected paths, sign-off bound to value), section 22.4 (high-risk matched at any depth).

Round 2 (frozen 1d47337). Raw findings: R1 8 (2 blockers), R2 10 (6), R3 7 (0), R4 8 (0), R5 2 (0); 35 total, 8 blockers.
Round 1 fixes re-checked: R1 10/11 hold, R2 9/11 attacks closed; F05 (coverage evidence) and F07 (sign-off at ready) do not fully hold.
Root cause RC-A behind every blocker: gates trust local state the agent controls (base ref, change path, evidence files, Type line,
working-tree sign-off, planted bytecode, git config). Root fix: the authoritative gate run is CI on a fresh clone, with kit, policy,
sign-off and base taken from the target branch and coverage produced by CI (spec 10.6). Local runs are early feedback; cheap local
closes below follow the same rule: facts come from the base commit or git, never from files the agent writes.

| id | round | severity | location | problem | decision | reason | status |
|---|---|---|---|---|---|---|---|
| G01 | 2 | blocker | INSTALL.md, gate_check.py | RC-A: no authoritative run; local state decides (R1-2-01..03, R2-2-01, -04, -05, -06) | accept | CI recipe in INSTALL: fresh clone, kit/policy/sign-off from target branch, CI-made coverage report, base = merge-base with target | fixed (pinned round 2) |
| G02 | 2 | blocker | gate_check.py | --change may be any folder; diff_scope then ignores it (R1-2-01) | accept | --change must be openspec/changes/<one name> | fixed (pinned round 2) |
| G03 | 2 | blocker | gate_check.py | base from agent flag, local branch or silent HEAD fallback (R2-2-01) | accept | default only from origin/HEAD, origin/main, origin/master; no remote and no --base = fail | fixed (pinned round 2) |
| G04 | 2 | blocker | gate_check.py, policy_guard | sign-off read from working tree (R2-2-02, F07) | accept | sign-off read from the base commit, like the base policy | fixed (pinned round 2) |
| G05 | 2 | blocker | gate_check.py, kitconst TYPES | Type line in spec.md drops gates (R1-2-05, R2-2-03) | accept | drop lists removed: Type can only tighten (no_production, flaky); a gate passes alone only when it has nothing to check | fixed (pinned round 2) |
| G06 | 2 | blocker | gates/coverage.py | manual numbers pass inside git; stale report passes (R1-2-02, -03, R2-2-06, R3-2-03, F05) | accept | inside git a report is required; report older than changed code fails; no changed code = nothing to check | fixed (pinned round 2) |
| G07 | 2 | blocker | gate_check.py | planted __pycache__ .pyc is loaded by gates (R2-2-04) | accept | gates run with -X pycache_prefix in a temp dir | fixed (pinned round 2) |
| G08 | 2 | blocker | cov_import.py, diff_scope.py | repo git config changes diff output (R2-2-05) | accept | git called with explicit diff flags and no external diff or textconv | fixed (pinned round 2) |
| G09 | 2 | major | kitconst.py, tangle.py, INSTALL.md | protected and high-risk lists drift; agent-steering files unlisted (R2-2-07, R4-2-01) | accept | one PROTECTED list incl. .mcp.json, nested CLAUDE.md, .husky, .vscode, pre-commit, GitLab CI; tangle flags any .claude/ and CLAUDE.md; INSTALL points at the list | fixed (pinned round 2) |
| G10 | 2 | major | forge/tangle.py | --check compares decoded text; CR swap undetected (R2-2-09) | accept | hash bytes | fixed (pinned round 2) |
| G11 | 2 | minor | forge/tangle.py | fence after a closed-then-reopened comment is tangled (R2-2-10) | accept | track comment state across the line | fixed (pinned round 2) |
| G12 | 2 | major | gates/trace_check.py | IDs read from ticket.md; prefixes testREQ_ fail; ids.txt counts (R1-2-07, R3-2-01, F01 leftover) | accept | IDs from spec.md and specs/ only; digit-only lookbehind; test files must be code or .feature | fixed (pinned round 2) |
| G13 | 2 | major | cov_import.py | Cobertura sources ignored; same-name files cross-match (R3-2-02, R3-2-06) | accept | join source roots; exact match first, suffix only if unique; warn on unmatched files | fixed (pinned round 2) |
| G14 | 2 | major | kitconst.py | globs case-sensitive; root Tests/ counts as production (R3-2-05) | accept | case-insensitive match | fixed (pinned round 2) |
| G15 | 2 | major | kitconst.py | docs work cannot touch README.md; tests work cannot add conftest.py (R1-2-06) | accept | *.md and conftest are not production; framework setup is its own chore | fixed (pinned round 2) |
| G16 | 2 | major | bootstrap.md | bootstrap writes protected policy and pollutes the first change (R1-2-04, R4-2-02) | accept | bootstrap does not copy policy (floor applies); runs on its own branch and PR | fixed (pinned round 2) |
| G17 | 2 | major | gates/granularity.py | characterized stays amber after Slice 0 exists (R3-2-04) | accept | green when the plan has a characterization slice | fixed (pinned round 2) |
| G18 | 2 | major | gates/diff_scope.py | impact scan '*' written at done turns scope off (R2-2-08) | accept part | reject bare '*' or '**' scans; plan integrity rests on CI and PR review (G01) | fixed in part (pinned round 2) |
| G19 | 2 | major | diff_scope | unrequested function inside an in-scope file passes (R5-2-01) | defer | needs symbol-level diff via codenav; spec 10.4 #9 is S+A, AI review covers it now | open (round 3) |
| G20 | 2 | major | coverage | stacks with no coverage tool cannot pass done (R3 F18 residue) | defer | needs a signed policy key; decide with pilots | open (later) |
| G21 | 2 | minor | spec_lint.py | 'Errors: None.' and '- none' fail (R3-2-07) | accept | normalise bullets and punctuation | fixed (pinned round 2) |
| G22 | 2 | minor | spec_lint.py | vague words in a heading excused by a nearby number (R5-2-02) | reject | heuristic edge; AI ambiguity review (10.1) covers it; chasing wordings is symptom work | closed |
| G23 | 2 | minor | bug.md | hotfix fast-track missing (R1-2-08) | reject | Type may only tighten gates (G05); a hotfix writes a one-slice plan | closed |
| G24 | 2 | minor | install | six manual steps, two copies of commands (R4-2-04) | defer | package stage (phase 6) ships repo-root layout | open (phase 6) |
| G25 | 2 | minor | core/policy.yml, glossary | sign-off shape undocumented; red/amber, L0 undefined (R4-2-05, -07) | accept | three-line example and glossary rows | fixed (pinned round 2) |
| G26 | 2 | minor | glossary | G1-G4 and ready/done are two vocabularies (R4-2-06) | reject | glossary already maps them; spec uses both | closed |
| G27 | 2 | minor | implement.md | approval in status.md is not proof (R4-2-08) | defer | closed by H04 (approval = merged plan PR) | superseded by H04 |
| G28 | 2 | minor | INSTALL.md, learn.md | upgrade does not re-copy commands; learn does not write module_paths (R1 notes) | accept | one line each | fixed (pinned round 2) |

Doc write-back added in round 2: section 10.6 and 22.4 (CI is the authoritative gate run; base, policy and sign-off from the target branch), section 8 (work type may only tighten gates; no hotfix fast track).

Round 3 (frozen 0465d26). Raw: R1 7 (1 blocker), R2 8 (5), R3 8 (0), R4 5 (0), R5 2 (1); 30 total, 7 blockers. Test bed 19/19 x5, 0 false alarms.
Round 2 fixes re-checked: R1 6/7 hold (G01 not), R2 7/10 attacks closed (R2-2-04, -06, -08 open), R3 4 hold, 2 in part; R4 4/4 hold.
Root causes:
- RC-B: the CI recipe overlays the approved kit and policy onto the PR's working tree, so the PR's own edits to them vanish from the diff
  and files it adds under kit/ run as the gate (R1-3-01, R2-3-01, R5-3-01/02, R3-3-03, R4-3-01). Fix: run the approved kit from a
  separate worktree against the PR checkout, with --base = merge-base.
- RC-C: the PR decides what coverage means (report path, baseline, pragmas, config) (R2-3-03/04, R1-3-06, R3-3-01/02/05/06).
  Fix: CI passes reports and baseline as gate_check flags; coverage config files are protected; added coverage-ignore markers fail.
- RC-D: the approved plan is re-read from the PR, and approval is a note (R2-3-06, earlier G27). Proposed fix: G1 approval = the
  plan PR is merged; done reads spec, Type and impact scan from the base commit and fails if the PR changes them.
- RC-E: nothing proves the tests detect the change (spec 10.4 #1 red then green) (R2-3-05). Proposed fix: red_check runs the changed
  tests against base production code in CI: story/bug must fail there, refactor/chore/tests must pass there.

| id | round | severity | location | problem | decision | reason | status |
|---|---|---|---|---|---|---|---|
| H01 | 3 | blocker | INSTALL.md CI | RC-B overlay hides PR edits and runs PR-added kit files; pathspec fails when policy files are absent | accept | approved kit in its own worktree; --repo is the PR checkout; --base merge-base | fixed (pinned round 3) |
| H02 | 3 | blocker | coverage, gate_check | RC-C baseline_total and report path come from the PR (R2-3-03, R1-3-06, R3-3-02) | accept | --coverage-report (repeatable) and --baseline-report or --baseline-total flags only | fixed (pinned round 3) |
| H03 | 3 | blocker | coverage | pragma: no cover on added code passes (R2-3-04) | accept | coverage-ignore markers on added lines fail; coverage config files join PROTECTED | fixed (pinned round 3) |
| H04 | 3 | blocker | gate_check done | RC-D approved plan re-read from the PR (R2-3-06) | accept | owner chose two PRs: plan PR merged by a human = G1 approval; done reads the plan from the base commit (also closes G27) | fixed (pinned round 3) |
| H05 | 3 | blocker | new gate red_check | RC-E tests with no asserts pass all gates (R2-3-05) | accept | owner chose red_check: changed tests run against base production code in CI | fixed (pinned round 3) |
| H06 | 3 | major | gate_check | planted .pyc loaded by gate_check itself; zero gates ran and passed (R2-3-02, R2-2-04) | accept | set pycache prefix before imports; fail if a floor gate did not run; tangle --check and package reject __pycache__ | fixed (pinned round 3) |
| H07 | 3 | major | INSTALL, gate_check | no rule for the change name or PRs without a change folder (R1-3-04, R4-3-03) | accept | --change auto: one change folder from the diff; none and production code changed = fail | fixed (pinned round 3) |
| H08 | 3 | major | INSTALL | base is the target tip, not the merge-base; CI artifacts count as changes (R1-3-03, R2-3-07, R3-3-04) | accept | recipe computes merge-base; reports written outside the checkout | fixed (pinned round 3) |
| H09 | 3 | major | state.sh, genie.md | bootstrapped never true after G16; Genie re-runs bootstrap (R1-3-05) | accept | bootstrapped = index.json exists; Genie stops at the bootstrap PR | fixed (pinned round 3) |
| H10 | 3 | major | cov_import | multi-module and container paths do not match (R3-3-01, R3-3-05) | accept | several reports merged; match by longest unique path suffix | fixed (pinned round 3) |
| H11 | 3 | major | coverage | file types the tool never measures count as 0% (R3-3-06) | accept | count a missing file only when the report measures that extension | fixed (pinned round 3) |
| H12 | 3 | major | diff_scope | '*.*' scan passes (R2-2-08 residue) | accept | a glob with no literal name part is too broad | fixed (pinned round 3) |
| H13 | 3 | minor | tangle | kit/gates, kit/scripts, policy.yml not high-risk (R2-3-08) | accept | the enforcement code is high-risk at pin time | fixed (pinned round 3) |
| H14 | 3 | minor | kitconst | *test.* matches Contest.php (R3-3-08) | accept | Test/Spec suffix matched case-sensitively on the file name | fixed (pinned round 3) |
| H15 | 3 | minor | CLAUDE.md | 'raise freely' contradicts protected policy; CI note duplicated (R4-3-04, -05) | accept | reword; keep CI note in INSTALL only | fixed (pinned round 3) |
| H16 | 3 | minor | router.md | hotfix fast-track and docs wording outdated (R1-3-07) | accept | match G23 and the gate table | fixed (pinned round 3) |
| H17 | 3 | minor | spec_lint | '- Errors: none' fails (G21 residue) | accept | strip bullet | fixed (pinned round 3) |
| H18 | 3 | minor | coverage | mtime stale check can false-alarm after touch or rebase (R3-3-07, low confidence) | reject | CI writes fresh reports; the check only guards local runs | closed |

Doc write-back added in round 3: section 10.2 #11 and 22.5 (G1 approval = merged plan PR; two PRs per change), section 10.4 #1 (red_check), section 10.6 (CI runs the approved kit from the target branch in its own worktree).

Round 4 (frozen 7ce6a0a; brief: prefer cuts). Raw: R1 6 (2 blockers) + 3 cuts, R2 6 (4), R3 6 (1) + 3 cuts, R4 weight audit 8 (0), R5 2 (1); 8 blockers.
Round 3 fixes re-checked: R1 6/6 hold, R2 6/8 attacks closed, R3 3 hold and 3 in part, R4 H09 holds and H15 in part, R5 20/20 x5, CI block 1.1 s.
Weight audit: 22 concepts (user 7, lead +9, Genie-only 6); 3 human actions per story; CI setup about 15 steps.
Root causes:
- RC-F: the PR picks which checks it gets (which stage, which plan, whether a change folder is needed) (R1-4-01/02, R2-4-03/04, R5-4-01, R4-4-02).
  Fix that also removes steps: gate_check infers the stage from git; a plan PR may change only its change folder; the code PR records evidence.md, and a plan with evidence.md already in the base cannot be reused.
- RC-G: red_check cannot tell why the base run failed (R3-4-01, R2-4-01). Fix the cheap, real part: run base code in the CI checkout itself (deps present), treat a runner that cannot start as an error, optional {tests}.
  Known limit, not closed by more machinery: tests for brand-new code are only proven to touch it.
Limits of the floor, left to AI test review (spec 10.4 #10, type A), human PR review and the ceiling (mutation testing):
tests for new code that assert little (R2-4-01, R2-3-05), weakened assertions in existing tests (R2-4-02), coverage config inside general build files (R2-4-05).

| id | round | severity | location | problem | decision | reason | status |
|---|---|---|---|---|---|---|---|
| J01 | 4 | blocker | gate_check, INSTALL | RC-F stage, plan reuse and folder choice are up to the PR (R1-4-01, R2-4-03, R2-4-04, R5-4-01) | accept | stage auto from git; plan PR may touch only its folder; done needs evidence.md new in this PR | fixed (pinned round 4) |
| J02 | 4 | blocker | gate_check | no change folder passes when only tests changed (R1-4-02) | accept | the no-folder pass covers only protected files and docs | fixed (pinned round 4) |
| J03 | 4 | blocker | red_check | a runner that cannot start in the base worktree counts as red (R3-4-01) | accept | base code is restored inside the checkout (no worktree); exit 126, 127 or timeout is an error | fixed (pinned round 4) |
| J04 | 4 | blocker | red_check | tests for new code pass red_check by failing to load on base (R2-4-01, R2-3-05) | reject | needs per-test JUnit parsing; known limit, covered by AI test review (10.4 #10), PR review and mutation testing (ceiling) | closed (limit, accepted by human after round 4) |
| J05 | 4 | blocker | red_check | weakened assertion in an existing test passes (R2-4-02) | reject | spec 10.4 #10 is an AI check; a deterministic version needs requirement-aware test diffing | closed (limit, accepted by human after round 4) |
| J06 | 4 | major | coverage | coverage exclusion in pyproject.toml (R2-4-05) | reject | general build files cannot be protected; human review of the approved scan; documented limit | closed (limit, accepted by human after round 4) |
| J07 | 4 | major | coverage, diff_scope | binary file crashes coverage; committed bytecode is ignored by diff_scope (R2-4-06) | accept | skip binary files; added bytecode fails | fixed (pinned round 4) |
| J08 | 4 | major | red_check | whole suite on base: unrelated failure fakes red (R3-4-02) | accept | optional {tests} placeholder in --test-cmd | fixed (pinned round 4) |
| J09 | 4 | major | coverage | no coverage tool (Delphi) can never pass (R3-4-03, G20) | accept | a signed min_changed_line_coverage of 0 means no report is needed | fixed (pinned round 4) |
| J10 | 4 | major | cov_import | lone file-name match inherits another module's coverage (R3-4-04) | accept | need two shared path segments unless the report path is a bare name | fixed (pinned round 4) |
| J11 | 4 | major | INSTALL | hotfix at night needs two merges; break-glass undocumented (R3-4-05) | accept | three lines: admin merge, then the plan and gates within 5 working days | fixed (pinned round 4) |
| J12 | 4 | major | state.sh, glossary | change name from branch breaks with two PRs (R1-4-03) | accept | match the change folder whose name the branch contains; glossary: one spec, two PRs | fixed (pinned round 4) |
| J13 | 4 | minor | tangle | kit/INSTALL.md not high-risk (R2-3-08) | accept | add to high-risk names | fixed (pinned round 4) |
| J14 | 4 | minor | commands | bootstrap says policy; implement points at impact.md, gate step 5 asks a redundant sign-off (R1-4-04, -05, -C3) | accept | fix wording; remove step | fixed (pinned round 4) |
| C01 | 4 | cut | red_check | head run duplicates CI's coverage run (R3-4-C1) | accept | remove; the CI test step must pass | fixed (pinned round 4) |
| C02 | 4 | cut | red_check | behaviour_changed base run for refactors (R3-4-C2) | accept | remove; refactor safety = existing tests green on head | fixed (pinned round 4) |
| C03 | 4 | cut | coverage | stale_report mtime check (R3-4-C3, H18) | accept | remove; reports come from CI | fixed (pinned round 4) |
| C04 | 4 | cut | gate_check | --baseline-total keeps an agent-typed number (R1-4-C2) | accept | remove; baseline is a report (CI reuses the target's last one, no extra run: R4-4-01 in part) | fixed (pinned round 4) |
| C05 | 4 | cut | kitconst, router | Type docs duplicates the no-folder path (R1-4-C1) | accept | remove the type; docs-only PRs need no change folder | fixed (pinned round 4) |
| C06 | 4 | cut | gate_check | --also flag (R4-4-05) | accept | remove | fixed (pinned round 4) |
| C07 | 4 | cut | CLAUDE.md, router.md, state.md | duplicates in always-loaded text; unmeasurable metrics columns (R4-4-03, -04, -06) | accept | trim | fixed (pinned round 4) |
| C08 | 4 | cut | glossary | G1-G4 beside ready/done (R4-4-07) | reject | spec uses both; glossary maps them (G26) | closed |
| C09 | 4 | add | INSTALL | script to print CODEOWNERS lines (R4-4-08) | reject | adds a script; the lead copies one list | closed |
| J15 | 4 | minor | kitconst | FooTests/ folder, Spec model class (R3-4-06) | reject | wider globs re-open production misclassification (R3-3-08); rename or list in the scan | closed |
| J16 | 4 | minor | testbed | change folder lacks slices.md (R5-4-02) | accept | add one | fixed (pinned round 4) |

Round 5 (frozen 57e537d; verification only). Raw: R1 1 blocker, 2 major; R2 2 blockers; R3 2 major; R4 1 major; R5 0 (1 minor). Not clean.
Round 4 fixes re-checked: R1 12/15 hold (hotfix flows fail), R2 4/5 attacks closed, R3 J03 J08 J09 J11 C01-C03 hold, R4 cuts landed (21 concepts, lead setup ~10 steps), R5 20/20 x5, INSTALL walk-through green, CI ~1 s.

| id | round | severity | location | problem | decision | reason | status |
|---|---|---|---|---|---|---|---|
| K01 | 5 | blocker | gate_check, changectx | an empty evidence.md lets a plan be reused (R2-5-01) | accept | "used" = evidence.md exists in base (git cat-file -e); done needs a non-empty evidence.md | fixed (pinned round 5) |
| K02 | 5 | blocker | diff_scope | the change folder skips the scan and the protected list; conftest.py, CLAUDE.md, settings planted there pass (R2-5-02) | accept | protected check before the exemption; code files in a change folder always fail | fixed (pinned round 5) |
| K03 | 5 | blocker | playbooks/bug.md | still one PR with the test before G1; fails CI (R1-5-01) | accept | rewrite to plan PR, then code PR with the failing repro test first | fixed (pinned round 5) |
| K04 | 5 | major | INSTALL, bug.md | after a night admin merge no follow-up can pass (R1-5-02) | accept | retro plan PR with spec and evidence.md pointing at the merged commit; passes ready, no code PR | fixed (pinned round 5) |
| K05 | 5 | major | story.md, diff_scope message | no way to change a merged plan (R1-5-03) | accept | a new change folder; message and stop signals say so | fixed (pinned round 5) |
| K06 | 5 | major | INSTALL | no first baseline report (R4-5-01) | accept | the install PR's CI run on the target keeps the first report artifact; doc only | fixed (pinned round 5) |
| K07 | 5 | major | red_check | moving a class or emptying a folder crashes the restore (R3-5-01) | accept | create folders before writing; tolerate a missing backup | fixed (pinned round 5) |
| K08 | 5 | major | cov_import | repo-root files never match container paths (R3-5-02) | accept | one shared segment is enough when the repo path has one segment | fixed (pinned round 5) |
| K09 | 5 | minor | diff_scope, INSTALL | untracked __pycache__ from CI's own test step and gates-*.json would fail or be committed (R2 note, R5-5-01) | accept | bytecode check covers tracked files only; INSTALL lists the two ignore lines | fixed (pinned round 5) |
| K10 | 5 | minor | red_check | runner that finds no tests (pytest exit 5) reads as red (R3-5-04) | accept | exit 5 is a runner error | fixed (pinned round 5) |
| K11 | 5 | minor | commands, templates, state.md | leftover wording: bootstrap policy, gate sign-off, impact.md, docs type, old branch rule, G1 undefined (R1 N1-N3, R4 minors, R3-5-03) | accept | fix wording; one {tests} example line per stack | fixed (pinned round 5) |

Round 6 (frozen f571848; final verification; round cap). Raw: R1 0 blockers, 1 major; R2 2 blockers; R3 0; R4 0; R5 2 blockers (one is accepted limit J04). Not clean.
Round 5 fixes re-checked: R1 12/13 hold (spike flow fails), R2 3/5 closed, R3 5/5 hold, R4 R4-5-01 closed, R5 21/21 x5, walk-through green with COVERAGE_FILE outside the checkout.
Hardening stopped at the round cap (6) with the items below open. Stop rule (2 clean rounds in a row) was never met.

| id | round | severity | location | problem | decision | reason | status |
|---|---|---|---|---|---|---|---|
| L01 | 6 | blocker | diff_scope | non-code files in the change folder still run (pytest collects test*.txt doctests) (R2-6-01) | accept | allowlist in kitconst.CHANGE_FOLDER_FILES; test bed case 21 | fixed after cap, pinned; R2/R5 check holds (evidence/after-cap-check.md) |
| L02 | 6 | blocker | INSTALL CI recipe | the PR's tests run after the approved worktree exists and can rewrite the approved kit (R2-6-02) | accept | INSTALL: tests run first, worktree created after them, set -e | fixed with M01 (two CI jobs); R2 attacks t1-t4 blocked |
| L03 | 6 | blocker | INSTALL | coverage.py's .coverage data file lands in the checkout and fails diff_scope on every PR (R5-6-01) | accept | COVERAGE_FILE outside the checkout; .coverage in .gitignore | fixed after cap, pinned; R5 walk-through holds |
| L04 | 6 | major | playbooks/spike.md | spike mixes spec and findings in one PR; fails CI (R1-6-01) | accept | docs-only findings PR route | fixed after cap, pinned; R5 walk-through holds |
| L05 | 6 | blocker | red_check, coverage | tests that run new code but assert nothing pass (R5-6-02) | limit | same root cause as accepted limit J04 | closed (limit J04) |
| L06 | 6 | minor | INSTALL, trace_check | test step result not enforced by the gate; flaky baseline; orphan_id warnings pile up; Delphi {tests} example; untracked helpers removed during base run (R1 N1-N3, R3-6-01..03, R4 minors, R5-6-03) | open | wording and small fixes | open (cap) |
| M01 | after-cap check | blocker | INSTALL CI recipe | the PR's test step plants a git hook or git config (repo or ~/.gitconfig) that rewrites the approved kit at `git worktree add` or at gate_check's git calls (t2-t4) | accept | two jobs: tests in one, gate job on a fresh runner runs no PR code before gate_check (R2-6-02's own proposal) | fixed, pinned (human-approved); RED/GREEN t2-t4 in evidence/after-cap-check.md |

Doc write-back done (2026-11-07, owner go-ahead): proposal/north-star-v2.md sections 3, 8, 10.2 #11, 10.4 #1, 10.6, 11.2 step 7, 11.3 and 22.4 now match the kit. The round 3 note's '22.5' was misplaced: the two-PR flow went into 10.2 and 11.2 instead. Round 4 cuts changed no spec promise.
