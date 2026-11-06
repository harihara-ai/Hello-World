purpose: phase 2 RED evidence: kit tests run before any implementation existed (2026-11-06).

command: bash tests/run.sh  (scratch dev tree, tests only, kit/ empty)

Ran 69 tests in 1.114s
FAILED (failures=34, errors=33)

first errors:
ERROR: test_missing_from_a_run_is_flaky (test_flaky.Flaky.test_missing_from_a_run_is_flaky)
ERROR: test_bad_stage (test_gate_check.GateCheck.test_bad_stage)
ERROR: test_clean_change_ready_and_done (test_gate_check.GateCheck.test_clean_change_ready_and_done)
ERROR: test_extra_gates_add_only (test_gate_check.GateCheck.test_extra_gates_add_only)
ERROR: test_gates_follow_policy (test_gate_check.GateCheck.test_gates_follow_policy)
ERROR: test_hostile_ticket_blocks_ready (test_gate_check.GateCheck.test_hostile_ticket_blocks_ready)
ERROR: test_missing_input_fails (test_gate_check.GateCheck.test_missing_input_fails)
ERROR: test_unknown_gate_name_refused (test_gate_check.GateCheck.test_unknown_gate_name_refused)
