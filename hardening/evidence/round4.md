purpose: round 4 fix evidence (RED then GREEN per fix group).

## J13 forge
RED: kit/INSTALL.md not high-risk: 'FAILED (failures=1)'. GREEN: forge tests OK.

## J01-J03, J07-J10, J12, C01-C06 kit
RED (updated tests, round 3 kit):
  FAILED (failures=14)
  OK
  OK
GREEN: unit 163 OK, contract 5 OK, mutation 14 OK.
One test fixture fixed on the way: the {tests} placeholder test ran 'python -I -m unittest <path>', which cannot import by path; '-I' removed in that test only.

## Test bed
Runner passes --baseline-report (fixture evidence/base.xml); ready cases leave the code files out (a plan PR holds no code); clean cases use stage auto; evidence.md and slices.md added to the fixtures.
GREEN (3 runs, scratch tangle): 'score: 20/20 cases; critical 15/15; other 5/5; false alarms 0'.

## Rebuild on scratch lock
70 files tangled identical to dev tree; kit_lint 'OK: 49 components clean'.

## Kit size, one method (find + wc over kit/ py/sh and md/yml)
phase 2 pin 308a9f4: code 710, md/yml 547, files 44. Round 3 pin: 1250, 600, 49. Round 4: 1282, 594, 49.
Correction: the round 3 report gave '1044' lines of code; that number came from a different command and was wrong. The right figure is 1250.
CLAUDE.md (always loaded): 31 lines -> 20.
