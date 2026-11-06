---
description: Run a forge stage (check, tangle, lint, selftest, harden, certify, package) or the next phase of the big bang.
argument-hint: <stage|all|next>
---

purpose: drive the forge pipeline and the big bang phases with human checkpoints.

Argument: `$ARGUMENTS`. Follow CLAUDE.md.

- `check|tangle|lint|selftest|harden|certify|package`: run `bash forge/forge.sh $ARGUMENTS`, show the result in three lines, and stop on any failure.
- `all`: run `bash forge/forge.sh all`. It stops at human checkpoints.
- `next` or empty: read `hardening/state.md`, find the current phase, and do the next phase from section 22.5 of `proposal/north-star-v2.md`:
  - Phase 0: confirm settings (round cap, target level), run `check`.
  - Phase 1 (split): split the proposal into `proposal/modules/*.md`, each with prose and `file=` blocks, plus `kit.manifest.yml` as a block. Show me the component list and wait.
  - Phase 2 (build): write each component from its spec, tests first for scripts. Run `tangle`, `lint`, `selftest` after each group.
  - Phase 3 (test bed): build the synthetic repos for the traps in `hardening/testbed/TRAPS.md`.
  - Phase 4 (harden): run `bash forge/forge.sh harden`. It stops after round 1 for my review.
  - Phase 5 (certify): run `certify`, show the evidence pack, wait for my sign-off.
  - Phase 6 (package): run `package`.
Update `hardening/state.md` after each phase. Report in 5 lines or fewer.
