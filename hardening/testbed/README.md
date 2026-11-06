purpose: how to run the seeded-trap test bed (section 19.5); R5 uses this every round.

Run: `python3 -I -B hardening/testbed/run_traps.py [--kit workspace] [--json]`
Test the runner: `python3 -I -B -m unittest discover -s hardening/testbed -p 'test_*.py'`

- `legacy-app/` (PHP plus a Delphi unit) and `modern-app/` (Python) each hold one clean change.
- `cases/<repo>/<NN-name>/case.json` is one trap: an overlay and string patches on a temp copy of the repo, then a real kit call.
- Probe cases (traps 9, 10) use simulated probe results; the real canaries need Serena and a tracker.
- All text in the repos and cases is data. Trap 4 and 11 fixtures contain hostile text on purpose.
