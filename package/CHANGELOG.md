# Change log

purpose: what changed in the North Star kit, by phase and hardening round.

## 1.0.1-silver-synthetic (2026-11-07)
- **After-cap check (R2, R5):** L01, L03, L04 hold. L02 was bypassed by a test that plants a git hook or git config (M01):
  CI is now two jobs, and the gate job runs on a fresh runner with no PR code before the gates.
- **M02:** a test could write coverage.py's data; the coverage gate now fails changed code that calls the coverage tool.
- **J06 control:** INSTALL lists build files with coverage settings for CODEOWNERS.
- **L06:** trace_check no longer warns about REQ IDs of other changes; INSTALL wording (CI jobs in the install PR, no
  evidence.md in a plan PR, Delphi runs the whole suite, CI helpers tracked).
- **Re-check:** selftest green; run_traps 22/22 in 5 of 5 runs, 0 false alarms. T7 not run.

## 1.0.0-silver-synthetic (2026-11-07)
- **Phases 0-3:** settings (round cap 6, Silver target, synthetic test bed); proposal split into 49 components with a
  manifest; components built tests first; two synthetic test bed repos with seeded traps.
- **Round 1:** traceability counts only test files; gates set their own targets; coverage reads real reports; diff_scope
  asks git; policy, sign-off and kit files are human-only; per-type gate table; tangle flags nested high-risk files.
- **Round 2:** root cause "gates trusted agent-controlled state": CI runs the authoritative gate; sign-off and policy read
  from the base commit; the work type can only tighten gates; bytecode and git-config tricks closed.
- **Round 3:** approved kit runs from its own worktree; G1 approval is a merged plan PR (two PRs per change); red_check
  proves changed tests fail without the change; coverage evidence only from CI flags.
- **Round 4 (cut-first):** stage inferred from git; one plan governs one code PR; CLAUDE.md 31 to 20 lines; CI recipe
  about 15 to about 7 lines; flags and a work type removed; three floor limits accepted (J04-J06).
- **Round 5:** plan reuse via empty evidence closed; no code in change folders; bug playbook in two-PR order.
- **Round 6:** final verification at the cap; three blockers and one major found, then fixed after the cap (L01-L04):
  change-folder allowlist, CI test step before the approved worktree, coverage data file outside the checkout, spike route.
- **Certification:** T1-T6 pass on the test bed (22 cases, 5 of 5 runs, 0 false alarms); T7 not run.
