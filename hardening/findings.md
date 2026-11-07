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
| H01 | 3 | blocker | INSTALL.md CI | RC-B overlay hides PR edits and runs PR-added kit files; pathspec fails when policy files are absent | accept | approved kit in its own worktree; --repo is the PR checkout; --base merge-base | open |
| H02 | 3 | blocker | coverage, gate_check | RC-C baseline_total and report path come from the PR (R2-3-03, R1-3-06, R3-3-02) | accept | --coverage-report (repeatable) and --baseline-report or --baseline-total flags only | open |
| H03 | 3 | blocker | coverage | pragma: no cover on added code passes (R2-3-04) | accept | coverage-ignore markers on added lines fail; coverage config files join PROTECTED | open |
| H04 | 3 | blocker | gate_check done | RC-D approved plan re-read from the PR (R2-3-06) | accept | owner chose two PRs: plan PR merged by a human = G1 approval; done reads the plan from the base commit (also closes G27) | open |
| H05 | 3 | blocker | new gate red_check | RC-E tests with no asserts pass all gates (R2-3-05) | accept | owner chose red_check: changed tests run against base production code in CI | open |
| H06 | 3 | major | gate_check | planted .pyc loaded by gate_check itself; zero gates ran and passed (R2-3-02, R2-2-04) | accept | set pycache prefix before imports; fail if a floor gate did not run; tangle --check and package reject __pycache__ | open |
| H07 | 3 | major | INSTALL, gate_check | no rule for the change name or PRs without a change folder (R1-3-04, R4-3-03) | accept | --change auto: one change folder from the diff; none and production code changed = fail | open |
| H08 | 3 | major | INSTALL | base is the target tip, not the merge-base; CI artifacts count as changes (R1-3-03, R2-3-07, R3-3-04) | accept | recipe computes merge-base; reports written outside the checkout | open |
| H09 | 3 | major | state.sh, genie.md | bootstrapped never true after G16; Genie re-runs bootstrap (R1-3-05) | accept | bootstrapped = index.json exists; Genie stops at the bootstrap PR | open |
| H10 | 3 | major | cov_import | multi-module and container paths do not match (R3-3-01, R3-3-05) | accept | several reports merged; match by longest unique path suffix | open |
| H11 | 3 | major | coverage | file types the tool never measures count as 0% (R3-3-06) | accept | count a missing file only when the report measures that extension | open |
| H12 | 3 | major | diff_scope | '*.*' scan passes (R2-2-08 residue) | accept | a glob with no literal name part is too broad | open |
| H13 | 3 | minor | tangle | kit/gates, kit/scripts, policy.yml not high-risk (R2-3-08) | accept | the enforcement code is high-risk at pin time | open |
| H14 | 3 | minor | kitconst | *test.* matches Contest.php (R3-3-08) | accept | Test/Spec suffix matched case-sensitively on the file name | open |
| H15 | 3 | minor | CLAUDE.md | 'raise freely' contradicts protected policy; CI note duplicated (R4-3-04, -05) | accept | reword; keep CI note in INSTALL only | open |
| H16 | 3 | minor | router.md | hotfix fast-track and docs wording outdated (R1-3-07) | accept | match G23 and the gate table | open |
| H17 | 3 | minor | spec_lint | '- Errors: none' fails (G21 residue) | accept | strip bullet | open |
| H18 | 3 | minor | coverage | mtime stale check can false-alarm after touch or rebase (R3-3-07, low confidence) | reject | CI writes fresh reports; the check only guards local runs | closed |
