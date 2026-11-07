purpose: loop state read at the start of every round.

round: 6 (frozen at f571848; final verification, round cap)
phase: 6 (packaged: dist/northstar-kit.zip; Silver on synthetic test bed, accepted with conditions)
certification_target: Silver
round_cap: 6
trap_score: 21/21 cases (critical 16/16, other 5/5, false alarms 0) on pinned workspace
trap_target: all critical, 95 percent others
new_findings_threshold: 2 per round
open_blockers: 0. After-cap check: L01, L03, L04 hold; L02 bypass M01 fixed (two CI jobs) and pinned; not run on a hosted CI
open_majors: deferred G19 (symbol-level scope), G20 (no-coverage stacks), F17; G18 in part
consecutive_clean_rounds: 0 (round 6 had 3 blockers; cap reached)
doc_revision_synced: synced 2026-11-07 (sections 3, 8, 10.2, 10.4, 10.6, 11.2, 11.3, 22.4)
notes: phase 0 confirmed (round cap 6, Silver, synthetic test bed, no budget cap; ralph.sh has no budget check). Keep governance minimal. Phase 1 approved and pinned (43 stubs). Phase 2 built in source: 44 components + tests, 86 tests green on scratch tangle, lint clean; phase 2 pinned. Phase 3 test bed built (hardening/testbed, 14 cases). Owner (round 4): avoid heavier governance; prefer cuts.
