# Change log

purpose: what changed in the North Star kit, by phase and hardening round.

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
