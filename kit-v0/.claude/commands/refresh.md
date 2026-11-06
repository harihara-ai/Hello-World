---
description: Incremental update of docs/ai after merges. Only updates what changed.
---

Update the knowledge files in `docs/ai/` for changes since the last map. Do not rebuild from scratch. Do not change source code.

1. Read the commit SHA at the top of `docs/ai/repo-map.md`. Run `git diff --name-status <sha>..HEAD`.
2. If nothing relevant changed, say so and stop.
3. For each changed module only: update its entry in `repo-map.md` (use Serena for symbols and references).
4. If any file listed in `contracts.md` changed, or a new API, schema, or message appears, update `contracts.md` and flag it clearly in your reply.
5. Update `test-gap.md` for changed modules only. Re-run those module tests and update `baseline.md` if the numbers changed.
6. Update the SHA at the top of `repo-map.md`.
7. Reply with a short list: what changed in each file, anything new marked `unknown`, and any contract change. Then stop.
