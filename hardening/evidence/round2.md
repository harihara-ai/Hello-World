purpose: round 2 fix evidence (RED then GREEN per fix group).

## G09-G11 forge
RED: 3 new forge tests (agent-steering files high-risk, fence after reopened comment, byte hashing): 'FAILED (failures=3)'.
GREEN: 'Ran 24 tests ... OK'; tangle.py 199 lines.

## G01-G08, G12-G18, G21 kit
RED (new tests, round 1 kit):
  FAILED (failures=20)
  OK
  OK
GREEN: unit 130 OK, contract 5 OK, mutation 14 OK.

## Test bed
RED: new kit refuses to guess a base without a remote: 'score: 5/19 cases; critical 2/14'. Runner then passes --base <base commit> like CI, and supports committing the agent's work (case 18).
GREEN (3 runs, scratch tangle): 'score: 19/19 cases; critical 14/14; other 5/5; false alarms 0'.

## Forge follow-up
RED: high-risk files refused on every tangle, even after a human pin: 'FAILED (failures=1)'. GREEN: approval checked at --pin only; 25 forge tests OK.

## Rebuild on scratch lock
66 files tangled identical to dev tree; kit_lint 'OK: 47 components clean'.

## Pin and GREEN on workspace (human-approved)
PINNED 66 files. added=0 changed=21 removed=0; HIGH-RISK approved: kit/.claude/commands/bootstrap.md, learn.md, kit/CLAUDE.md.
selftest: lock check OK, forge 25 OK, unit 130 OK, contract 5 OK, mutation 14 OK. Runner unit tests OK. run_traps 19/19, false alarms 0.
