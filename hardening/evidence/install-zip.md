purpose: fix plan item 5 (G24), install by "unzip into the repo, then /bootstrap": RED, GREEN and the walk-through.

# Install zip (2026-11-07)

Python 3.13.18, git 2.43.0; coverage.py and pytest installed to the session scratchpad (not the repo).

## Tests first (`forge/tests/test_package.py`)
Copies forge, proposal/modules, workspace, package and kit.lock to a temp dir and runs `forge.sh package` there.
- RED (before the forge.sh change): 5 tests, `FAILED (errors=3)`: `test_install_zip_has_repo_root_paths_only`,
  `test_install_zip_matches_workspace_and_lock`, `test_install_zip_never_holds_a_root_claude_md`
  (`FileNotFoundError: dist/northstar-kit-install.zip`). The full package tests passed.
- GREEN: `python3 -I -m unittest discover -s forge/tests`: 30 tests OK (25 old, 5 new).

## Change
- `forge/forge.sh package`: one `add()` helper (reused for both zips) and a second zip,
  `dist/northstar-kit-install.zip`: `kit/`, `kit.manifest.yml`, `.claude/commands/*.md`, nothing else; no root
  `CLAUDE.md`. `dist/northstar-kit.zip` (full package) unchanged in layout.
- `kit/INSTALL.md` (source `proposal/modules/01-core.md`, core.install): Files 5 steps to 3 (unzip; CLAUDE.md line,
  .gitignore, CODEOWNERS, CI jobs; human merge, then /bootstrap). Upgrade: delete `kit/`, unzip the new zip.

## Scratch pin (scratchpad, before the human pin)
`PINNED 70 files. added=0 changed=1 removed=0`, `changed: kit/INSTALL.md HIGH-RISK`; lint `OK: 49 components clean`;
only `kit/INSTALL.md` differs from `workspace/`. Install zip from the scratch kit: 58 entries.

## Walk-through (synthetic repo, two-job recipe simulated as in `after-cap-check.md`)
Harness in the scratchpad: `mk.sh` (bare origin; app with `subtotal`, a root `CLAUDE.md` and an own
`.claude/commands/mine.md`; install per the new Files 1-3; first baseline), `code.sh` (merge plan, clean code PR with
CART-3 from the test bed), `ci2.sh` (tests job, then gate job with own dir, own HOME, fresh clone, report as artifact).
| Step | Expected | Actual |
| --- | --- | --- |
| unzip at root | root CLAUDE.md and own command kept | `root CLAUDE.md untouched by unzip`, `own command kept` |
| plan PR | ready passes | `stage ready`, `pass true`, gate job exit 0 |
| clean code PR (CART-3) | done passes | `stage done pass True`, all 6 gates True, exit 0 |
| t0 control: `src/extra.py` out of scope | blocked | `outside_scan`, `unmatched_file`, `changed_lines`, exit 1 |

Not run: `/bootstrap` itself (agent-driven); a hosted CI (session B); unzip on Windows or with a GUI tool; an upgrade
over an installed kit (delete `kit/`, unzip again).
