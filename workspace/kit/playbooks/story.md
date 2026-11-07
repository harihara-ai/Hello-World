# Playbook: story (also NFR)

purpose: steps for a story, enhancement or NFR, from ticket to merged PR.

1. **Intake.** `read_ticket` (capability.tracker). Save the text to `ticket.md`. Create branch `feature/<KEY>-<slug>` and the change folder.
2. **Learn if needed.** If a touched module has no card in `docs/ai/modules/`, run `/learn <module>`.
3. **Spec.** Draft `spec.md` from `kit/templates/spec.md`. Concrete values, one behaviour per scenario, an error case per requirement. NFRs carry a number.
4. **Slice and G1.** `/slice` (impact scan, slice plan, `gate_check.py ready`). Untested code in scope gets Slice 0 (characterization only). Open the plan PR; the human merging it is the approval.
5. **Build.** On a new branch from the target, `/implement` per slice, in order. Each changed test must fail without the change (`gate.red_check`).
6. **G4.** `gate_check.py done` with the coverage report and test command (see `/gate`). Write the trace table into the PR (`kit/templates/pr.md`).
7. **Hand over.** Open the PR, `comment` on the ticket with REQ IDs and the PR link. The human reviews and merges.

Stop signals: a failed gate after 3 attempts, files outside the impact scan, or a diff over the slice cap.
A merged plan cannot change: plan the rest in a new change folder (`<name>-2`) and its own plan PR.
