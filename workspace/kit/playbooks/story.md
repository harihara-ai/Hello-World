# Playbook: story (also NFR)

purpose: steps for a story, enhancement or NFR, from ticket to merged PR.

1. **Intake.** `read_ticket` (capability.tracker). Save the text to `ticket.md`. Create branch `feature/<KEY>-<slug>` and the change folder.
2. **Learn if needed.** If a touched module has no card in `docs/ai/modules/`, run `/learn <module>`.
3. **Spec.** Draft `spec.md` from `kit/templates/spec.md`. Concrete values, one behaviour per scenario, an error case per requirement. NFRs carry a number.
4. **Slice and G1.** `/slice` (impact scan, slice plan, `gate_check.py ready`). Untested code in scope gets Slice 0 (characterization only). The human approves spec and plan; record it in `status.md`.
5. **Build.** `/implement` per slice, in order.
6. **G4.** Run the tests with coverage, point `inputs/coverage.json` at the report, then `gate_check.py done`. Write the trace table into the PR (`kit/templates/pr.md`).
7. **Hand over.** Open the PR, `comment` on the ticket with REQ IDs and the PR link. The human reviews and merges.

Stop signals: a failed gate after 3 attempts, files outside the impact scan, or a diff over the slice cap. Go back to step 4.
