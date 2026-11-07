---
description: Set up a repo once: probe tools, detect practices, write docs/ai knowledge files. Safe to re-run.
argument-hint: 
---

purpose: Set up a repo once: probe tools, detect practices, write docs/ai knowledge files. Safe to re-run.

Follow `kit/core/rules.md`. Arguments: `$ARGUMENTS`.

1. **Detect.** Languages, build/test/lint commands, monorepo or not, CI, CODEOWNERS, contracts (OpenAPI, schemas). Two agreeing signals: adopt. Otherwise ask.
2. **Probe.** Run each adapter's `## Probe` canary. Write `{"results": {"<adapter name>": {"ok": true|false, "reason": "..."}}}` (names as in `kit.manifest.yml`, e.g. `serena`, `ctags`, `jira`, `file`), then `python3 kit/scripts/probe.py results.json --out docs/ai/toolchain.md`.
3. **Practices.** Write `docs/ai/practices.md`: commit and branch style, PR template, review rules, test layout. Each line cites its source file.
4. **Policy.** Do not create or edit `docs/ai/policy.yml`: the kit floor applies until a human adds one.
5. **Knowledge.** Write `docs/ai/index.json` (one entry per item, with `confidence` and `verified_sha`) and `repo-map.md`. Module cards wait for `/learn`.
6. **Baseline.** Run the tests once with coverage; write `docs/ai/baseline.md` with the command, counts and overall coverage percent. Do not fix failures.
7. **Install check.** Confirm root `CLAUDE.md` imports `kit/CLAUDE.md` and `.claude/commands/` holds the kit commands (`kit/INSTALL.md`).
8. **Report.** What was created, what is unknown, what failed. List open questions; the Genie asks them one at a time. Stop.

Run on its own branch (`chore/bootstrap`) and end with a PR for a human to merge. Do not change source code or tests here.
