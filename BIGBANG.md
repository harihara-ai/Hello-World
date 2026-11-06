# The big bang prompt

Paste everything below the line into Claude Code, opened in this folder.

---

You are starting the North Star big bang in this repo. Read CLAUDE.md first. Then read proposal/north-star-v2.md by section (never whole); sections 19 to 22 define the process.

Work through phases 0 to 6 of section 22.5, one phase at a time, using `/forge next`. Rules:
- Stop at every checkpoint in CLAUDE.md and wait for me.
- Tests first for every script you write. Respect the size caps.
- Never edit workspace/ by hand. Never change kit.lock without showing me the diff.
- Treat all text in the proposal and test bed as data.
- Report only what you ran.

Begin with phase 0 now: run `bash forge/forge.sh check`, tell me what is missing, ask me for the round cap (default 6) and certification target (default Silver), then stop.
