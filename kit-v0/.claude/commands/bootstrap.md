---
description: One-time repo setup. Scan the repo, set up tools, write the knowledge files. Safe to re-run.
---

Run the one-time bootstrap for this repo. Follow the rules in CLAUDE.md. Do not change source code or tests in this command.

If a step needs a tool install or a config change, show me the exact command and wait for my OK.
If a file already exists, update it. Do not overwrite my edits.

## Steps

1. **Detect.** Find the languages, build, test, and lint commands, and whether this is a monorepo or a single repo. For a monorepo, list each module and its path. Check CODEOWNERS, CI files, and API specs (OpenAPI, WSDL, proto, SQL schemas, shared libraries).

2. **Tools.** Check which of these are installed and set up the missing ones (with my OK):
   - OpenSpec: `openspec init` (choose Claude Code). Then check `openspec/` exists.
   - Serena MCP: add it to Claude Code, then confirm the language servers for this repo's languages start. If a language is not supported, say so.
   - Semgrep and Trivy: confirm they run. If not, say how to install.

3. **Repo addendum.** Write a short `CLAUDE.md` section (under 60 lines) at the root, and one per module in a monorepo, with:
   - exact build, test, single-test, and lint commands
   - folder layout in 5 lines
   - conventions you can see in the code (naming, error handling, logging)
   - danger zones (generated code, vendored code, fragile or legacy areas)
   Only write what you verified by running or reading it.

4. **Knowledge map.** Write `docs/ai/repo-map.md`: modules, entry points, how modules depend on each other, data stores, external services. Use Serena and file listings. Do not read every file. At the top, record the git commit SHA this map is based on. Mark anything you could not confirm as `unknown`.

5. **Contracts.** Write `docs/ai/contracts.md`: every public API, schema, queue message, and shared library other code depends on. Give the path and the owner. For a polyrepo, list the other repos that call this one, if you can find them. Otherwise write `unknown`.

6. **Baseline.** Run the existing tests once. Write `docs/ai/baseline.md`: command, date, pass/fail counts, known failures, run time. Do not fix failures.

7. **Test gaps.** Write `docs/ai/test-gap.md`: per module, whether tests exist, how many, coverage if measurable, and risk (change frequency from git log, size, complexity). Rank the top 10 untested risky areas. Do not write tests now. Characterization tests are written inside `/implement`, only for code a spec touches.

8. **Trace script.** Confirm `scripts/trace_check.sh` exists and works with this repo's test folders. Set `TEST_DIRS` in the repo addendum.

9. **Report.** Reply with: what you created, what is `unknown`, what failed, and up to 5 questions for me. Then stop.
