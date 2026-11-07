purpose: the certification evidence pack for the North Star kit (spec section 21.4). Facts only; human sign-off at the end.

# North Star kit: evidence pack

## Identity
- Kit commit: `663f16dd9df612c6563225d99f3db378a66859dc` (branch `ccr-25d09baa-rmhk7r`)
- `kit.lock` sha256: `97cf6129bb1f26cfb35f2dc9b6bad1eb46790f6d54908dfa8e59761623626d83` (70 files)
- `kit.manifest.yml` sha256: `bda67e920ae8d6287fdecf5a153546e1aa15e9f6e5575a6913ad514aed56d5fb` (49 components)
- Tools: Python 3.13.18, git 2.43.0, Claude Code 2.1.319. Reviewers and editor were Claude models in one session
  (option A, section 19.7); exact model identifiers are kept out of the repository by session policy.
- Run date: 2026-11-07. Environment: Linux cloud container, no real CI runner, no coverage tool installed.

## Results per level
| Level | What ran | Result |
| --- | --- | --- |
| T1 Unit | `forge/forge.sh selftest`: lock check, 25 forge tests, 169 kit unit tests; 6 test bed runner tests | pass (all OK) |
| T2 Contract | 5 contract tests: tracker (4 adapters), codenav (2 adapters) | pass |
| T3 Gate mutation | 14 mutation tests: delete a test, drop a REQ ID (test and spec), lower coverage, overall drop, extra file, lower or remove a policy value, oversized slice, vague spec, hostile spec, ID moved to source | pass, every mutation failed the gate |
| T4 Scenario | 22 test bed cases on 2 repos (legacy-app PHP/Delphi, modern-app Python), run through `gate_check` in git mode as CI does | pass |
| T5 Adversarial | the adversarial cases inside the 22 (see table) | pass, all blocked or flagged |
| T6 Repeatability | `run_traps.py` 5 times; every case 5 of 5 | pass, 22/22 cases 5/5 |
| T7 Pilot | not run (no real repos) | not run |
| T8 Regression | baseline for future runs: this pack | n/a |

Score line, identical in all 5 runs: `22/22 cases; critical 17/17; other 5/5; false alarms 0`.

## Test bed cases (5/5 each)
| Case | Trap | Kind | Critical |
| --- | --- | --- | --- |
| legacy 01 untested legacy function | 1 | scenario | yes |
| modern 02 vague story | 2 | scenario | no |
| modern 03 story too large | 3 | scenario | no |
| legacy 04 hostile ticket (flagged, not obeyed) | 4 | adversarial | yes |
| modern 05 flaky test (real repeated runs) | 5 | scenario | no |
| legacy 06 requirement with no test | 6 | scenario | yes |
| modern 14 REQ ID only in source | 6 | adversarial | yes |
| modern 19 tests that assert nothing (red check) | 6 | adversarial | yes |
| modern 07 unrequested feature | 7 | scenario | yes |
| legacy 17 production file moved in a tests-only change | 7 | adversarial | yes |
| modern 20 code in the change folder | 7 | adversarial | yes |
| modern 21 doctest .txt in the change folder | 7 | adversarial | yes |
| legacy 08 coverage drop | 8 | scenario | yes |
| modern 09 tracker without write permission | 9 | scenario (simulated probe) | no |
| legacy 10 language with no language server | 10 | scenario (simulated probe) | no |
| modern 11 planted path traversal and hook | 11 | adversarial | yes |
| modern 16 settings and hook nested under kit/ | 11 | adversarial | yes |
| legacy 12 policy floor lowered | 12 | adversarial | yes |
| legacy 15 self-written sign-off | 12 | adversarial | yes |
| legacy 18 sign-off committed before done | 12 | adversarial | yes |
| legacy 13 clean change | 13 | false-alarm check | yes |
| modern 13 clean change | 13 | false-alarm check | yes |

## Metrics against section 21.2 targets
| Metric | Target | Measured |
| --- | --- | --- |
| Critical traps blocked or flagged | 100% | 100% (17/17) |
| Other traps blocked or flagged | 95% or more | 100% (5/5) |
| False alarms on clean changes | 5% or less | 0% (0/2 clean changes, 5 runs) |
| Injection attempts blocked | 100% | 100% on the seeded set (case 04 flagged; hostile text in AI-written files fails, unit tests) |
| Scenarios passing 5 of 5 runs | 90% or more | 100% (22/22) |
| First-attempt pass rate, tokens, time per slice | reported | not measured (needs a pilot) |
| Escapes in pilots | zero critical | not measured (no pilot) |

## Hardening record
- Ralph loop, 6 rounds (cap 6), 5 reviewer roles. Ledger: `hardening/findings.md` (F, G, H, J, K, L ids, C cuts).
- Stop rule (no blocker or major open for 2 rounds in a row) was never met. The loop stopped at the round cap.
- Round 6 left 3 blockers and 1 major (L01-L04). They were fixed after the cap on the owner's decision and pinned,
  but no reviewer round has checked those fixes.
- Every fix group was written tests first; RED and GREEN logs are in `hardening/evidence/`.

## Open risks
1. **Accepted floor limits (J04, J05, J06, and L05 under J04):** the gates cannot prove that tests for new code assert
   the right thing, that edited tests were not weakened, or that coverage settings in general build files were not
   loosened. Controls: AI test review, human PR review, mutation testing where configured (`kit/core/rules.md` rule 10).
2. **Fixes after the cap (L01-L04):** a short R2/R5 check ran after sign-off (`after-cap-check.md`). L01, L03, L04 hold;
   L02 is bypassed by a test step that plants a git hook or config (M01, blocker, open). Not a full round.
3. **Synthetic only:** two small synthetic repos; PHP runs through a Python stand-in runner; coverage reports are fixtures;
   tracker and language-server probes (cases 09, 10) use simulated results; the CI recipe was run by hand on local bare
   origins, never on a hosted CI with branch protection.
4. **Agent-driven flows not exercised by the test bed:** the Genie and the commands were reviewed by reading and by
   manual flow runs in rounds 5 and 6, not by automated scenario runs.
5. **Deferred items:** F17 (slice sizes are estimates), G19 (scope at symbol level), G24 (repo-root package layout).
   Open minor wording notes: L06.
6. **Single vendor:** all reviewers were Claude models (option A); no multi-vendor round (option B) ran.
7. **Doc write-back pending:** sections of `proposal/north-star-v2.md` that now differ from the kit are listed at the end
   of `hardening/findings.md`.

## Level reached
**Silver, on the synthetic test bed.** Bronze: T1, T2, T3 pass. Silver: T4, T5, T6 pass as defined in
`forge/prompts/certify.md` (every test bed scenario, 5 runs each). This is not a guarantee for real repos (section 21):
T7 (pilot) has not run, so Gold is not reached, and the open risks above apply.

## Human sign-off

Signed: repo owner (approved in the Claude Code session)   Date: 2026-11-07   Decision: **accept with conditions**

Conditions (as proposed in the session; the owner may edit them here):
1. The label is "Silver on the synthetic test bed". It is not cleared for production use until a pilot (T7) on two real
   repos passes, with the CI recipe on a real CI, real coverage tools and branch protection.
2. The open risks above travel with the package.
