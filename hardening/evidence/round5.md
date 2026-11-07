purpose: round 5 fix evidence (RED then GREEN per fix group).

## K01, K02, K07-K10 kit
RED (new tests, round 4 kit):
  FAIL: test_match_paths (test_cov_import.CovImport.test_match_paths)
  FAIL: test_untracked_bytecode_from_the_test_step_is_ignored (test_diff_scope.GitMode.test_untracked_bytecode_from_the_test_step_is_ignored)
  FAIL: test_code_planted_in_the_change_folder_fails (test_gate_check_git.GitGateCheck.test_code_planted_in_the_change_folder_fails)
  FAIL: test_empty_evidence_still_marks_the_plan_used (test_gate_check_git.GitGateCheck.test_empty_evidence_still_marks_the_plan_used)
  FAIL: test_moved_file_and_emptied_folder_are_restored (test_red_check.RedCheck.test_moved_file_and_emptied_folder_are_restored)
  FAIL: test_runner_that_finds_no_tests_is_an_error (test_red_check.RedCheck.test_runner_that_finds_no_tests_is_an_error)
  Ran 168 tests in 43.148s
  FAILED (failures=6)
  Ran 5 tests in 0.003s
  OK
  Ran 14 tests in 11.316s
  OK
GREEN: unit 168 OK, contract 5 OK, mutation 14 OK.

## K03-K06, K09, K11 docs
bug.md rewritten to plan PR then code PR; INSTALL: first baseline, ignore lines, {tests} examples, hotfix retro plan; wording fixes.

## Test bed
New case 20 (conftest.py in the change folder). GREEN (3 runs, scratch tangle): 'score: 21/21 cases; critical 16/16; other 5/5; false alarms 0'.

## Rebuild on scratch lock
70 files tangled identical to dev tree; kit_lint 'OK: 49 components clean'. Kit size: code 1297 (+15), md/yml 602 (+8), files 49.
