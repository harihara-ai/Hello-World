purpose: round 1 checkpoint for the human; delete this file to let the loop continue.

Round 1 (frozen a5d992e; Claude-only subagents, option A). Raw: 46 findings, 16 blockers (R1 5, R2 7, R3 3, R4 1); R5 found 0 misses.
Ledger: hardening/findings.md, 31 consolidated items: 24 fixed, 4 fixed in part, 1 deferred (F17), 2 rejected (F28, F31).

Biggest holes closed (all reproduced first, then covered by tests):
- trace_check counted IDs in src/ and any file (F01); Java/C# underscore IDs failed (F02).
- gate inputs could redirect gates or carry NaN (F03, F04); coverage was hand-typed numbers (F05, now reads the report).
- diff_scope trusted listed files and hid renames; no default base (F06). Policy, sign-off and kit files were AI-writable (F07).
- ready ran on an unguarded policy (F08); hostile ticket text blocked a change forever (F09); chores could never pass done (F10).
- commands were not installable where Claude Code reads them (F11); tangle missed nested high-risk files (F12); workspace edits shipped (F13).

Test bed now: 18 cases (4 new adversarial), git mode, rule-level checks. Score on the fixed kit: 18/18, 0 false alarms.

Needs you:
1. Arbitrate any decision in findings.md you disagree with (especially the rejections F28, F31 and the deferral F17).
2. Approve the kit.lock pin: 66 files, added 4, changed 40, removed 0, unchanged 22, no high-risk paths.
3. Forge changed (tangle.py, forge.sh, forge tests) in commit c30c8e3: review that diff too.
4. Doc write-back list at the end of findings.md (proposal/north-star-v2.md is read-only here).
