purpose: phase 3 evidence: test bed runner RED then GREEN, and trap scores (2026-11-06).

RED: python3 -I -B -m unittest discover -s hardening/testbed -p 'test_*.py' before run_traps.py existed: 'Ran 0 tests, FAILED (errors=1)' (setUpClass could not run the runner).

Fixture bugs found and fixed while going green (not kit defects):
- trap 7 patch matched twice and also widened the impact scan; runner now requires each patch target to occur exactly once.
- trap 5 fixture left a file open; the ResourceWarning broke result parsing; fixture fixed and runner now errors on unparsable runs.

GREEN, run 3 times in a row:
score: 14/14 cases; critical 9/9; other 5/5; false alarms 0
score: 14/14 cases; critical 9/9; other 5/5; false alarms 0
score: 14/14 cases; critical 9/9; other 5/5; false alarms 0

```
PASS legacy-app 01-untested-legacy         trap  1  failed gates: ['ready:granularity']
PASS legacy-app 04-hostile-ticket          trap  4  failed gates: ['ready:injection']
PASS legacy-app 06-requirement-no-test     trap  6  failed gates: ['done:trace_check']
PASS legacy-app 08-coverage-drop           trap  8  failed gates: ['done:coverage']
PASS legacy-app 10-no-language-server      trap 10  chosen ctags, recorded in toolchain.md: True
PASS legacy-app 12-policy-lowered          trap 12  failed gates: ['done:policy_guard']
PASS legacy-app 13-clean                   trap 13  clean: all gates pass
PASS modern-app 02-vague-story             trap  2  failed gates: ['ready:spec_lint']
PASS modern-app 03-story-too-large         trap  3  failed gates: ['ready:granularity']
PASS modern-app 05-flaky-test              trap  5  flaky: ['test_session_counter'] over 5 runs
PASS modern-app 07-extra-feature           trap  7  failed gates: ['done:diff_scope']
PASS modern-app 09-tracker-read-only       trap  9  chosen tracker-file, recorded in toolchain.md: True; kit/adapters/tracker/file
PASS modern-app 11-planted-file-blocks     trap 11  refused: True; files written: False
PASS modern-app 13-clean                   trap 13  clean: all gates pass
score: 14/14 cases; critical 9/9; other 5/5; false alarms 0
```

Runner tests:
Ran 4 tests in 4.581s

Known gap to raise in round 1: trace_check scans src/ by default, so a REQ ID in a source comment counts as a test.
