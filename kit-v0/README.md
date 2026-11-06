# North Star kit for Claude Code

Spec-driven AI development for any repo. Plain files, no lock-in.

## What is in the kit
| File | Purpose |
|---|---|
| `CLAUDE.md` | Always-on rules: traceability, no over-engineering, red-green, legacy safety |
| `.claude/commands/bootstrap.md` | `/bootstrap` : one time per repo |
| `.claude/commands/implement.md` | `/implement <change>` : per approved spec |
| `.claude/commands/refresh.md` | `/refresh` : after merges |
| `scripts/trace_check.sh` | Fails if a requirement has no test |

## OSS tools it uses
- **OpenSpec** (spec workflow, delta specs, archive): `npm install -g @fission-ai/openspec@latest` (Node 20.19+)
- **Serena** (symbol-level search and edits over MCP, uses language servers): runs with `uvx`
- **Semgrep** (code scan), **Trivy** (dependency scan)
- Your own test runner and linter per language

Spec Kit (github/spec-kit) is the main alternative to OpenSpec. OpenSpec is lighter and handles changes to existing code well, so it is the default here.

## Setup (once per repo)
1. Copy the kit into the repo root (merge with any existing `CLAUDE.md`).
2. `chmod +x scripts/trace_check.sh`
3. Open Claude Code in the repo and run `/bootstrap`. Review its report.

## Daily flow
1. Write or generate the change with OpenSpec (proposal, spec deltas with `REQ-` IDs, tasks). **You review and approve.**
2. `/implement <change-name>`
3. **You review and merge the PR.**
4. `openspec archive <change-name>`, then `/refresh`.

## One-time vs incremental
- One-time: `/bootstrap` (tools, repo addendum, repo map, contracts, baseline, test gaps)
- Incremental: `/refresh` (only what changed), characterization tests (only for code a spec touches), each `/implement` run

## Polyrepo notes
- Run `/bootstrap` in each repo.
- `docs/ai/contracts.md` is the link between repos. Keep the callers list up to date.
- A change that touches a contract needs a spec in every repo affected. Claude Code stops and asks first.

## Monorepo notes
- Add a short `CLAUDE.md` per module. The nearest one wins.
- Keep `TEST_DIRS` set to cover all modules' test folders.

## Limits to know
- The kit does not replace review. Humans approve at two points: the spec and the merge.
- Trace check proves a test mentions the ID, not that the test is good. Read the tests in the PR.
- Command names in OpenSpec have changed between versions. Use the ones `openspec init` installs.
