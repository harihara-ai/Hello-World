# North Star: how we work in this repo

Read this first. These rules always apply. If a rule blocks you, stop and ask. Do not work around it.

## 1. Source of truth
- Specs live in `openspec/` (OpenSpec). `openspec/specs/` = what the system does now. `openspec/changes/<name>/` = a proposed change (proposal, spec deltas, tasks).
- Repo knowledge lives in `docs/ai/` (repo-map, contracts, test-gap, baseline). Facts only. Write "unknown" instead of guessing.
- In a monorepo, the nearest `CLAUDE.md` to the file you are editing wins.

## 2. Modes
- `/bootstrap` : one time per repo. Scans and sets up. Safe to re-run.
- `/implement <change-name>` : per approved spec. Red-green loop. Ends with a PR.
- `/refresh` : after merges. Updates only what changed in `docs/ai/`.
Never write code outside `/implement`, unless the user asks directly.

## 3. Traceability
- Every requirement has an ID: `REQ-<AREA>-<NNN>` (example: `REQ-AUTH-004`). Put it in the requirement title.
- Every test that proves a requirement has the ID in its name or a comment.
- Every commit starts with the ID: `REQ-AUTH-004: reject expired token`.
- The PR lists a table: requirement -> test -> commit.
- Run `scripts/trace_check.sh` before every PR. A requirement with no test is a failure.
- Code with no requirement behind it is not allowed. Ask for a spec change first.

## 4. No over-engineering
- Do the smallest change that makes the failing test pass.
- No feature, option, config flag, or abstraction that the spec does not ask for.
- No new abstraction until the third real use.
- No new dependency without asking.
- Do not refactor code you did not need to touch.
- If you notice something out of scope, do not fix it. Add it to "Out of scope noticed" in the PR.

## 5. Red-green-refactor (mandatory)
1. RED: write one test for one spec scenario. Run it. It must fail, and for the right reason. Record the command and the failure in `openspec/changes/<name>/evidence.md`.
2. GREEN: write the minimum code to pass. Run the test. Record it passing.
3. REFACTOR: clean up only the code you just wrote, with tests green.
4. Never edit a test to make it pass. If a test is wrong, say why and ask.
5. Never skip RED. If you cannot make a test fail first, stop and tell the user.

## 6. Legacy safety
- Before you change existing code that has no tests, write characterization tests that pin its current behaviour (golden master or approval tests). Commit them separately, tagged `CHAR:`. They must pass before your change.
- Do not "fix" behaviour that a characterization test pins unless the spec says so.

## 7. Stop and ask when
- The spec is ambiguous, missing a scenario, or conflicts with the code.
- A change touches a public contract (API, schema, shared library) in `docs/ai/contracts.md`.
- A task needs more than about 300 changed lines. Propose a split.
- You are about to delete code, change a dependency, or touch CI or secrets.

## 8. Done means
- All tests pass, including the baseline from `docs/ai/baseline.md`.
- Lint and Semgrep clean. Trivy clean if dependencies changed.
- `scripts/trace_check.sh` passes.
- `evidence.md` shows RED then GREEN for every requirement.
- PR opened. You do not merge. A human merges.

## 9. Tools (use before reading raw files)
- Serena (MCP) for symbol search, references, and safe edits.
- OpenSpec CLI for spec validation and archive.
- Semgrep and Trivy for scans.
- Use the commands in the repo `CLAUDE.md` addendum (written by `/bootstrap`) for build, test, and lint.
