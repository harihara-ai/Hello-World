# Playbook: story (also NFR)

purpose: steps for a story, enhancement or NFR, from ticket to merged PR.

1. **Intake.** `read_ticket` (capability.tracker). Save the text to `ticket.md`. Create branch `feature/<KEY>-<slug>` and the change folder.
2. **Learn if needed.** If a touched module has no card in `docs/ai/modules/`, run `/learn <module>`.
3. **Spec.** Draft `spec.md` from `kit/templates/spec.md`. Concrete values, one behaviour per scenario, an error case per requirement. NFRs carry a number.
4. **Impact scan.** codenav `impact` per requirement. Write `impact.md` and `inputs/diff_scope.json` (`impact_scan` globs).
5. **Slice.** `/slice`: write `slices.md` and `inputs/granularity.json`. Untested code in scope gets Slice 0 (characterization only).
6. **G1.** `gate_check.py ready`. Fix and re-run until green. Then the human approves spec and slice plan. Record the approval in `status.md`.
7. **Build.** `/implement` per slice, in order.
8. **G4.** Write `inputs/coverage.json` from the coverage tool, then `gate_check.py done`. Write the trace table into the PR (`kit/templates/pr.md`).
9. **Hand over.** Open the PR, `comment` on the ticket with REQ IDs and the PR link. The human reviews and merges.

Stop signals: a failed gate after 3 attempts, files outside the impact scan, or a diff over the slice cap. Go back to step 5.
