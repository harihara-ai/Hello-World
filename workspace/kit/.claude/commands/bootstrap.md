---
description: Set up a repo once: probe tools, detect practices, write docs/ai knowledge files and policy. Safe to re-run.
argument-hint: 
---

purpose: Set up a repo once: probe tools, detect practices, write docs/ai knowledge files and policy. Safe to re-run.

Follow `CLAUDE.md` and `kit/core/rules.md`. Arguments: `$ARGUMENTS`.

1. **Detect.** Languages, build/test/lint commands, monorepo or not, CI, CODEOWNERS, contracts (OpenAPI, schemas). Two agreeing signals: adopt. Otherwise ask.
2. **Probe.** Run each adapter `## Probe` canary. Write results as JSON, then `python3 kit/scripts/probe.py results.json --out docs/ai/toolchain.md`.
3. **Practices.** Write `docs/ai/practices.md`: commit and branch style, PR template, review rules, test layout. Each line cites its source file.
4. **Policy.** Copy `kit/core/policy.yml` to `docs/ai/policy.yml` if missing. Never lower a value.
5. **Knowledge.** Write `docs/ai/index.json` (one entry per item, with `confidence` and `verified_sha`) and `repo-map.md`. Module cards wait for `/learn`.
6. **Baseline.** Run the tests once; write `docs/ai/baseline.md`. Do not fix failures.
7. **Report.** What was created, what is unknown, what failed, up to 5 questions. Stop.

Do not change source code or tests here.
