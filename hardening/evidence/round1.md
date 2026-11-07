purpose: round 1 fix evidence (RED then GREEN per fix group).

## F12, F13 forge
RED: 3 new forge tests failed (nested high-risk paths, fence in HTML comment, workspace tampering): 'Ran 21 tests ... FAILED (failures=3)'.
GREEN: 'Ran 21 tests ... OK'; forge.sh selftest now starts with 'OK: 62 files match the lock'.

## F01-F10, F14-F16, F18, F23 gates
RED (scratch dev tree, new tests, old gates):
  unit: FAILED (failures=41, errors=1)
  OK
  FAILED (failures=2)
GREEN after fixes: unit 110 OK, contract 5 OK, mutation 14 OK (one mutation fixture moved its vague word into Outcome, per F15).

## F11 state.sh
RED: test_state 'FAILED (errors=2)'; GREEN: OK.

## F25 test bed
RED: runner tests for rule checks and git mode: 'FAILED (failures=2)' against the pinned workspace.
Runner on the round 1 kit (scratch tangle): 'score: 18/18 cases; critical 13/13; other 5/5; false alarms 0'.
Runner unit tests run against workspace/, so their GREEN is recorded after the pin.

## Rebuild on scratch lock
tangle 66 files, identical to dev tree (diff -r); kit_lint 'OK: 47 components clean'; kit tests unit 111, contract 5, mutation 14 all OK.

## Pin and GREEN on workspace (2026-11-07, human-approved)
PINNED 66 files. added=4 changed=40 removed=0 (no HIGH-RISK). selftest: lock check OK, forge 21 OK, unit 111 OK, contract 5 OK, mutation 14 OK.
Runner unit tests on workspace: OK. run_traps: 18/18 cases; critical 13/13; other 5/5; false alarms 0.
