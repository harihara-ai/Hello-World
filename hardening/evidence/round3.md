purpose: round 3 fix evidence (RED then GREEN per fix group).

## H06, H13 forge
RED: planted __pycache__ accepted by --check; gates/, scripts/, policy.yml not high-risk: 'FAILED (failures=2)'.
GREEN: forge tests OK; package skips __pycache__; tangle.py 198 lines.

## H01-H05, H07-H12, H14, H17 kit
RED (new tests, round 2 kit):
  FAILED (failures=34, errors=4)
  OK
  OK
GREEN: unit 157 OK, contract 5 OK, mutation 14 OK (gate_check split into gate_check.py 158 + changectx.py 76 lines).

## Test bed
Runner passes CI flags (--coverage-report, --baseline-total, --test-cmd) from testbed.json and applies plan patches before the base commit (patch_base). New case 19: tests that assert nothing.
PHP is not installed: legacy-app/tests/run_tests.py is a stand-in runner (fixture).
GREEN (3 runs, scratch tangle): 'score: 20/20 cases; critical 15/15; other 5/5; false alarms 0'.
Runner unit tests read workspace/: their GREEN is recorded after the pin. A dedicated runner test for the new flags was not added (covered by the cases).

## Rebuild on scratch lock
70 files tangled identical to dev tree; kit_lint 'OK: 49 components clean'.
