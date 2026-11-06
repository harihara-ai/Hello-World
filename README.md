# North Star seed

purpose: start the evolution of the North Star kit with Claude Code.

## Start (3 steps)
1. In this folder run: `git init && git add -A && git commit -m seed`
2. Export the master doc as Markdown and save it as `proposal/north-star-v2.md`.
3. Open Claude Code here and paste the text from `BIGBANG.md`. It runs phase 0 and stops for you.

You need: Claude Code, git, python3. Run the self-tests any time: `python3 -m unittest discover -s forge/tests`.

## What is inside
| Path | What |
|---|---|
| `CLAUDE.md` | Rules while the kit evolves |
| `BIGBANG.md` | The prompt that starts it |
| `.claude/commands/forge.md` | `/forge` command |
| `forge/` | `forge.sh` (stages), `tangle.py` (safe extraction), `kit_lint.py` (size and dependency lint), `ralph.sh` (loop), prompts, unit tests |
| `hardening/` | Reviewer roles R1 to R5, findings schema and ledger, loop state, trap list, vendor runner notes |
| `kit-v0/` | The first small kit (CLAUDE.md, three commands, trace script) as a starting reference |

## Limits you should know
- The loop edits the markdown working copy in git. Writing accepted changes back to the doc is manual for now.
- The round cap is the real cost control. The loop cannot read spend. Watch your usage.
- Only the Claude runner is included. Other vendors need their own CLI or API and a small runner script (`hardening/runners/README.md`).
- Phases 1 to 6 are done by Claude Code from the spec. Only `tangle.py` and `kit_lint.py` are pre-built and tested. Nothing else has been run end to end.
- `kit.lock` is empty until phase 1. Pinning is always a human step.
