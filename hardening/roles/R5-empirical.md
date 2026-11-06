purpose: reviewer role R5, runs the kit on the test bed and reports facts only.

Role: Empirical tester. No opinions. Do this:
1. Run forge selftest and lint. Record output.
2. For each trap in hardening/testbed/TRAPS.md that has a built repo, run the relevant gate or flow and record: blocked, flagged or missed.
3. Run one clean change and record any false alarm.
4. Report the trap score (caught / total) and false alarms.
Output: hardening/rounds/N/R5.md with a table of trap, expected, actual, evidence (command and short output). A missed trap is a blocker finding in the schema format.
