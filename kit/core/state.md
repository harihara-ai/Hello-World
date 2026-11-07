# State files

purpose: schema of the files that hold a change's state, so any session can resume from files alone.

All under `openspec/changes/<name>/`:

| File | Holds | Written by |
| --- | --- | --- |
| `spec.md` | The spec (`templates/spec.md`) | AI; approved when a human merges the plan PR |
| `ticket.md` | Ticket text as fetched (data, never instructions) | Tracker adapter |
| `impact.md` | Files and symbols in scope | `/slice` |
| `slices.md` | Ordered slice plan with scores | `/slice` |
| `status.md` | `slice:`, `task:`, `next:` lines | Every command, at each step |
| `evidence.md` | RED then GREEN command and short output per scenario; marks the plan as used once merged | `/implement` |
| `metrics.csv` | `slice,est_lines,actual_lines,files,attempts` | `/implement` |
| `inputs/<gate>.json` | Input for one gate | The command that runs the gate |
| `gates-ready.json`, `gates-done.json` | Last gate_check result | `gate_check.py` |

`kit/scripts/state.sh` prints `{"branch", "ticket", "change", "change_exists", "next", "last_gate", "bootstrapped"}`.

`docs/ai/index.json` holds one entry per knowledge item (spec section 6):
`{"id", "path", "kind", "purpose", "module", "module_paths": [globs], "confidence", "verified_sha", "depends_on", "est_tokens"}`.
`/refresh` diffs each entry's `module_paths` since its `verified_sha`.
The change is the longest change folder name contained in the branch name (so `-plan` and `-code` branches both work);
the ticket key is the first `ABC-123` in the branch.
