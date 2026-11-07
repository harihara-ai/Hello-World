---
description: Learn one module on first touch: write its card and a draft behaviour spec tagged inferred.
argument-hint: <module>
---

purpose: Learn one module on first touch: write its card and a draft behaviour spec tagged inferred.

Follow `kit/core/rules.md`. Arguments: `$ARGUMENTS`.

1. Read in order, through subagents: tests, public interfaces and contracts, linked ticket history, docs, then code.
2. Write `docs/ai/modules/<module>.md`: purpose, entry points, key behaviours, data, contracts, quirks.
3. Write a draft behaviour spec tagged `inferred` in `docs/ai/modules/<module>.spec.md`.
4. Add or update the module entry in `docs/ai/index.json` (fields in `kit/core/state.md`, including `module_paths`) with `verified_sha` = HEAD.
5. Ask the human to confirm or correct the draft. Only confirmed items move to `openspec/specs/`.
