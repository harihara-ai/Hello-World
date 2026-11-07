# North Star kit

purpose: what is in the North Star kit package, how to install it, and what its certification does and does not mean.

**Status: Silver on the synthetic test bed, accepted with conditions (2026-11-07). Not cleared for production use
until a pilot on two real repos passes.** Details: `hardening/evidence/EVIDENCE.md`.

## What it is
A small kit that makes Claude Code work on a repo through specs, slices and deterministic gates. A human approves
each plan by merging its PR, and CI runs the gates on every PR with the approved kit from the target branch.

## Install
Follow `workspace/kit/INSTALL.md`: copy `kit/`, the commands and the root `CLAUDE.md` line, protect the paths in
`kit/scripts/kitconst.py` with CODEOWNERS, add the CI job, then run `/bootstrap` and `/genie`.

## Contents
| Path | What |
| --- | --- |
| `workspace/kit/` | The kit: core rules, capabilities, adapters, gates, scripts, playbooks, commands, templates |
| `workspace/kit.manifest.yml` | Registry of the 49 components |
| `workspace/tests/` | The kit's own tests: unit, contract, mutation (`bash workspace/tests/run.sh`) |
| `kit.lock` | sha256 of every generated file, pinned by a human |
| `forge/` | Tangle, lint, the stages and their tests, to rebuild and re-check the kit |
| `hardening/testbed/` | Two synthetic repos with 22 seeded trap cases (`python3 -I -B hardening/testbed/run_traps.py`) |
| `hardening/roles/`, `hardening/findings.schema.md` | The reviewer harness, to run the loop again |
| `hardening/findings.md` | The findings ledger from six hardening rounds |
| `hardening/evidence/` | RED and GREEN logs per round and the evidence pack |
| `CHANGELOG.md` | What changed, by phase and round |

## Known limits (short)
- The gates cannot prove that tests for new code assert the right thing, that edited tests were not weakened, or that
  coverage settings in general build files were not loosened. AI test review, PR review and mutation testing cover these.
- Everything was tested on synthetic repos, fixture coverage reports and a hand-run CI recipe.
- Hardening stopped at the round cap; the last four fixes were not reviewed by the reviewer swarm.
