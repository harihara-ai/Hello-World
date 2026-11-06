purpose: how to add a vendor runner for the multi-vendor swarm (option B).

A runner is a small script `hardening/runners/<vendor>.sh` that takes a role file and a round number and writes `hardening/rounds/N/R<k>-<vendor>.md`.
Contract: `runner.sh ROLE_FILE ROUND` reads the proposal and modules, calls that vendor's CLI or API, and writes the findings in schema format. It must not edit proposal files.
Keys come from environment variables on the machine that runs the loop. Never commit keys.
The Claude runner is the default (`claude -p`). Add other vendors here when you have their CLI or API access, then list them in hardening/state.md.
