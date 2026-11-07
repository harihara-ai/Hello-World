# Install the kit into a repo

purpose: the one place that says where kit files go in a target repo and what a human must protect.

1. Copy `kit/` to the repo root as `kit/`, and `kit.manifest.yml` to the root.
2. Copy `kit/.claude/commands/*.md` to `.claude/commands/` (Claude Code reads commands only there).
3. Add the line `@kit/CLAUDE.md` to the root `CLAUDE.md` (create it if missing). Claude Code loads the root file.
4. Needs `python3` (3.8 or later) and `git`. Nothing is installed; no hooks are added.
5. Add to `CODEOWNERS` so a human reviews them: `docs/ai/policy.yml`, `docs/ai/policy-signoff.json`, `kit/`, `.claude/`, `CLAUDE.md`.
   `gate.diff_scope` already fails any AI change that touches these; CODEOWNERS stops the same change arriving another way.
6. Open Claude Code and run `/bootstrap`, then `/genie`.

Upgrade: replace `kit/` and `kit.manifest.yml` in one human PR, then run `/refresh`.
