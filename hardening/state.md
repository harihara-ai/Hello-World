purpose: loop state read at the start of every round.

round: 4 (frozen at 7ce6a0a)
phase: 4
certification_target: Silver
round_cap: 6
trap_score: 20/20 cases (critical 15/15, other 5/5, false alarms 0) on pinned workspace
trap_target: all critical, 95 percent others
new_findings_threshold: 2 per round
open_blockers: 0 (round 3 fixes pinned; round 4 re-checks)
open_majors: deferred G19 (symbol-level scope), G20 (no-coverage stacks), F17; G18 in part
consecutive_clean_rounds: 0 (round 3 had 7 blockers)
doc_revision_synced: not synced (write-back list in findings.md)
notes: phase 0 confirmed (round cap 6, Silver, synthetic test bed, no budget cap; ralph.sh has no budget check). Keep governance minimal. Phase 1 approved and pinned (43 stubs). Phase 2 built in source: 44 components + tests, 86 tests green on scratch tangle, lint clean; phase 2 pinned. Phase 3 test bed built (hardening/testbed, 14 cases). Owner (round 4): avoid heavier governance; prefer cuts.
