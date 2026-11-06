purpose: the findings ledger, the memory of the hardening loop.

Round 1 (frozen a5d992e, option A: Claude-only subagents). Raw findings: R1 12, R2 12, R3 12, R4 10, R5 0 (46; 16 blockers).
Consolidated below as F-ids; duplicates merged. Decisions by the single editor; human arbitrates at the round 1 checkpoint.

| id | round | severity | location | problem | decision | reason | status |
|---|---|---|---|---|---|---|---|
| F01 | 1 | blocker | gates/trace_check.py | REQ ID in src/ or any file counts as a test (R1-07, R2-01, R3-02) | accept | count IDs only in test files (shared test globs), drop test_dirs input; comment-only links in test files stay a known limit (spec 13) | fixed, pending pin |
| F02 | 1 | blocker | gates/trace_check.py | Java/C#/Delphi names cannot hold '-' (R3-01) | accept | match REQ[-_]AREA[-_]NNN, case-insensitive, normalise | fixed, pending pin |
| F03 | 1 | blocker | scripts/gate_check.py | agent-written inputs redirect spec_lint/trace_check targets (R2-02) | accept | targets come from the change path only | fixed, pending pin |
| F04 | 1 | blocker | scripts/gateio.py, coverage.py | NaN passes numeric floors; empty changed set = 100% (R2-03) | accept | reject NaN/Infinity on input; warn on empty changed set | fixed, pending pin |
| F05 | 1 | blocker | gates/coverage.py | no producer for coverage input; agent hand-writes it (R1-11, R3-03, R3-04) | accept | coverage reads Cobertura/JaCoCo/lcov/clover report plus git diff -U0 itself, instrumented lines only | fixed, pending pin |
| F06 | 1 | blocker | gates/diff_scope.py | no default base; renames hide deletes; changed_files trusted; change folder flagged; .NET test layouts (R1-04, R2-04, R3-12) | accept | gate_check passes base; --no-renames; git wins over changed_files; exempt change folder; more test globs | fixed, pending pin |
| F07 | 1 | blocker | policy_guard.py, diff_scope.py | sign-off, policy and kit files are agent-writable (R1-03, R2-05) | accept | diff_scope fails on protected paths (policy, sign-off, kit/, .claude/, CLAUDE.md): humans change them in their own PR; sign-off binds key to value | fixed, pending pin |
| F08 | 1 | blocker | core/policy.yml, policy_guard.py | ready runs on unguarded policy; raised repo floor can be lowered back (R1-02, R2-06) | accept | policy_guard in both stages; compare to max(kit floor, base-commit policy); drop --policy | fixed, pending pin |
| F09 | 1 | blocker | gate_check.py, injection.py | hostile ticket text blocks the change forever (R1-01) | accept | fetched data (ticket.md, comments/) is flagged as warn; AI-written files fail | fixed, pending pin |
| F10 | 1 | blocker | gate_check.py | one done list cannot fit chore/refactor/spike/tests (R1-05) | accept | fixed per-Type table in gate_check, not editable via policy | fixed, pending pin |
| F11 | 1 | blocker | kit layout | commands and CLAUDE.md are not where Claude Code looks; no install step (R1-09, R4-01, R4-02, R4-04) | accept | kit/INSTALL.md; state.sh reports bootstrapped; Genie runs /bootstrap first | fixed, pending pin |
| F12 | 1 | blocker | forge/tangle.py | high-risk prefixes are root-anchored, so kit/.claude/settings.json etc. need no approval; fences in HTML comments tangled (R2-09) | accept | match high-risk on any segment, mark HIGH-RISK in pin output, skip fences inside comments | fixed, pending pin |
| F13 | 1 | major | forge/forge.sh, tangle.py | hand-edited or planted workspace files run and ship (R2-10) | accept | --check also hashes the outdir; selftest and package call it | fixed, pending pin |
| F14 | 1 | major | gates/injection.py, gate_check.py | unicode tricks, paraphrases, non-md and UTF-16 files, dir names unscanned (R2-07, R2-08) | accept | NFKC, strip Cf, flag mixed scripts, 3 more patterns, scan all files; rules.md calls it a tripwire | fixed, pending pin |
| F15 | 1 | major | gates/spec_lint.py | any digit exempts vague words; banned words hit quoted names; Scenario Outline and error-by-title (R2-11, R3-08, R3-09) | accept | number with unit or comparator; skip backticks and Problem/Out of scope; accept Scenario Outline; error case by Then wording | fixed, pending pin |
| F16 | 1 | major | gates/granularity.py | and/or hard red; characterization slices cannot fit (R3-06) | accept | and/or amber; kind characterization exempt from lines/symbols (spec 11.3 write-back needed) | fixed, pending pin |
| F17 | 1 | major | slice inputs | slice numbers are LLM estimates; untested can be set to none (R3-07) | defer | needs per-file coverage from F05 first; round 2 | open (round 2) |
| F18 | 1 | major | gates/coverage.py | strict total compare; stacks with no coverage tool (R3-05) | accept part | max_total_drop 0.1 (may only fall); no-tool case deferred | fixed in part, pending pin |
| F19 | 1 | major | gates/flaky.py, safety-net | no runs producer, quarantine undefined, failing passes (R3-11) | accept part | quarantine list docs/ai/quarantine.md; converter deferred | fixed in part, pending pin |
| F20 | 1 | major | playbooks/safety-net.md | golden master, scrubbing, seams, bounded scope missing (R3-10) | accept | four lines in the playbook; seams go in their own chore change | fixed, pending pin |
| F21 | 1 | major | playbooks/bug.md | hotfix cannot pass G1 without a slice file (R1-06) | accept | hotfix writes a one-slice plan | fixed, pending pin |
| F22 | 1 | major | CLAUDE.md, commands | ready-before-slice order cannot work (R1-08) | accept | order: spec, slice, gate ready, approve; spec section 3 write-back needed | fixed, pending pin |
| F23 | 1 | major | scripts/probe.py | probe tool names do not match adapters (R1-10) | accept | rank by adapter name | fixed, pending pin |
| F24 | 1 | major | CLAUDE.md, gate.md | policy fallback and input producers unstated (R4-03, R4-05) | accept | one line each | fixed, pending pin |
| F25 | 1 | major | hardening/testbed | test bed scores only seeded phrasing and gate names (R2-12) | accept | expect_rule, git-initialised repos, 4 adversarial cases | fixed, pending pin |
| F26 | 1 | minor | core/state.md | index schema lacks module paths for /refresh (R1-12) | accept | add spec 6 fields | fixed, pending pin |
| F27 | 1 | minor | commands | duplicate purpose line and CLAUDE.md re-read (R4-06) | accept part | drop the CLAUDE.md mention; purpose line kept (lint rule) | fixed in part, pending pin |
| F28 | 1 | minor | commands | remove /safety-net, /refresh (R4-07) | reject | spec 19.6 lists them as deliverables | closed |
| F29 | 1 | minor | bootstrap.md | five questions at once (R4-08) | accept | report unknowns; Genie asks one at a time | fixed, pending pin |
| F30 | 1 | minor | playbooks/story.md | impact scan step duplicates /slice; one big approval (R4-09) | accept part | delete duplicate step; single G1 approval kept (spec 10.2 #11) | fixed in part, pending pin |
| F31 | 1 | minor | adapters | all adapters ship to every repo (R4-10) | reject | manifest loads lazily; spec 19.6 lists all adapters | closed |

Doc write-back needed after round 1 (proposal is read-only here): section 3 order (slice before /gate ready), section 11.3 ('and'/'or' amber; characterization slices skip size), section 10.6 (policy_guard in both stages, protected paths, sign-off bound to value), section 22.4 (high-risk matched at any depth).
