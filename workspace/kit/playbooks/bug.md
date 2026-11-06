# Playbook: bug and hotfix

purpose: steps for a bug or production hotfix: reproduce with a failing test first, then fix.

1. **Intake.** `read_ticket`. Save `ticket.md`. Branch `fix/<KEY>-<slug>`.
2. **Reproduce.** Write one failing test that shows the bug. Record RED in `evidence.md`. No fix before RED.
3. **Spec.** If the behaviour was never specified, add a requirement with a REQ ID. The regression test carries that ID.
4. **G1.** `gate_check.py ready`. A hotfix may skip slicing (one slice) but not the gate.
5. **Fix.** Smallest change that turns the test GREEN. Note the root cause in `evidence.md`.
6. **G4.** `gate_check.py done`, unchanged for hotfixes: the done gate is never relaxed.
7. **Hotfix follow-up.** Add a retro-spec within 5 working days and record it as a `next:` line in `status.md`.
