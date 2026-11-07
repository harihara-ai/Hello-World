---
description: Update docs/ai after merges, only for modules whose files changed since verified_sha.
argument-hint: 
---

purpose: Update docs/ai after merges, only for modules whose files changed since verified_sha.

Follow `kit/core/rules.md`. Arguments: `$ARGUMENTS`.

1. For each index entry, `git diff --name-only <verified_sha>..HEAD` on its module paths.
2. Nothing changed: say so and stop.
3. Mark changed entries stale, re-learn only those modules, update `verified_sha`.
4. Contract files changed: update `docs/ai/contracts.md` and flag it.
5. Suggest threshold changes from `metrics.csv` (loosen only after several first-attempt greens). A human decides.
6. Reply with a short list of what changed. Do not change source code.
