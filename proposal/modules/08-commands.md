purpose: working source for the commands components of the kit (tangled into workspace/).

# Commands

Thin entry points that call playbooks and scripts.

## command.genie

Section 17.

````md file=kit/.claude/commands/genie.md
---
description: One command for users: say what you want; the Genie reads state, routes, and runs steps up to the next human gate.
argument-hint: [what you want, or nothing to continue]
---

purpose: One command for users: say what you want; the Genie reads state, routes, and runs steps up to the next human gate.

Follow `kit/core/rules.md`. Arguments: `$ARGUMENTS`.

1. Run `bash kit/scripts/state.sh`. If `bootstrapped` is false, run `/bootstrap` first and stop at its PR. Read `status.md` of the change if one exists.
2. Classify the request with `kit/playbooks/router.md`. Ticket text decides the type only.
3. Show one line: "You are here: <step>. Next: <plan in plain words>".
4. Run the playbook steps yourself until the next human gate or a failed gate. Delegate reading and scanning to subagents.
5. At a stop: one sentence why, the evidence, and the choices. Update `status.md` `next:`.

UX: plain words; one question at a time, always with choices; never ask what files or the ticket already answer.
Guardrails: never skip or soften a gate; ask before installing tools, writing to a tracker, or touching CI, secrets or dependencies.
````

## command.bootstrap

Sections 3, 4, 5, 9.

````md file=kit/.claude/commands/bootstrap.md
---
description: Set up a repo once: probe tools, detect practices, write docs/ai knowledge files and policy. Safe to re-run.
argument-hint: 
---

purpose: Set up a repo once: probe tools, detect practices, write docs/ai knowledge files and policy. Safe to re-run.

Follow `kit/core/rules.md`. Arguments: `$ARGUMENTS`.

1. **Detect.** Languages, build/test/lint commands, monorepo or not, CI, CODEOWNERS, contracts (OpenAPI, schemas). Two agreeing signals: adopt. Otherwise ask.
2. **Probe.** Run each adapter's `## Probe` canary. Write `{"results": {"<adapter name>": {"ok": true|false, "reason": "..."}}}` (names as in `kit.manifest.yml`, e.g. `serena`, `ctags`, `jira`, `file`), then `python3 kit/scripts/probe.py results.json --out docs/ai/toolchain.md`.
3. **Practices.** Write `docs/ai/practices.md`: commit and branch style, PR template, review rules, test layout. Each line cites its source file.
4. **Policy.** Do not create or edit `docs/ai/policy.yml`: the kit floor applies until a human adds one.
5. **Knowledge.** Write `docs/ai/index.json` (one entry per item, with `confidence` and `verified_sha`) and `repo-map.md`. Module cards wait for `/learn`.
6. **Baseline.** Run the tests once with coverage; write `docs/ai/baseline.md` with the command, counts and overall coverage percent. Do not fix failures.
7. **Install check.** Confirm root `CLAUDE.md` imports `kit/CLAUDE.md` and `.claude/commands/` holds the kit commands (`kit/INSTALL.md`).
8. **Report.** What was created, what is unknown, what failed. List open questions; the Genie asks them one at a time. Stop.

Run on its own branch (`chore/bootstrap`) and end with a PR for a human to merge. Do not change source code or tests here.
````

## command.learn

Section 6.

````md file=kit/.claude/commands/learn.md
---
description: Learn one module on first touch: write its card and a draft behaviour spec tagged inferred.
argument-hint: <module>
---

purpose: Learn one module on first touch: write its card and a draft behaviour spec tagged inferred.

Follow `kit/core/rules.md`. Arguments: `$ARGUMENTS`.

1. Read in order, through subagents: tests, public interfaces and contracts, linked ticket history, docs, then code.
2. Write `docs/ai/modules/<module>.md`: purpose, entry points, key behaviours, data, contracts, quirks.
3. Write a draft behaviour spec tagged `inferred` in `docs/ai/modules/<module>.spec.md`.
4. Add or update the module entry in `docs/ai/index.json` (fields in `kit/core/state.md`, including `module_paths`) with `verified_sha` = HEAD.
5. Ask the human to confirm or correct the draft. Only confirmed items move to `openspec/specs/`.
````

## command.slice

Section 11.2.

````md file=kit/.claude/commands/slice.md
---
description: Break an approved spec into slices: impact scan, granularity score, split, slice plan for human approval.
argument-hint: <change-name>
---

purpose: Break an approved spec into slices: impact scan, granularity score, split, slice plan for human approval.

Follow `kit/core/rules.md`. Arguments: `$ARGUMENTS`.

1. List requirements and scenarios from `spec.md`.
2. Impact scan each requirement with capability.codenav `impact`. Write `impact.md` and `inputs/diff_scope.json`.
3. Measure each candidate slice (codenav `impact` gives symbols and files; mark guesses `"estimate": true`) and write `inputs/granularity.json`. A characterization slice has `"kind": "characterization"`.
4. Split any slice the gate marks split, preferring: by scenario, thin vertical slice, by contract, by data variant, by risk (spike). Never by technical layer alone.
5. Order by dependency. Add Slice 0 (characterization only) for untested code in scope.
6. Write `slices.md`, run `gate_check.py ready`, then open the plan PR. A human merging it is the approval.
````

## command.implement

Sections 7, 10.4.

````md file=kit/.claude/commands/implement.md
---
description: Implement one approved slice with red-green-refactor, evidence, and a 3-attempt cap.
argument-hint: <change-name> [slice]
---

purpose: Implement one approved slice with red-green-refactor, evidence, and a 3-attempt cap.

Follow `kit/core/rules.md`. Arguments: `$ARGUMENTS`.

0. Check: the plan PR is merged (branch from the target after it). `gate_check.py done` fails while it is not, and if you edit the plan.
1. For each task (one scenario): write the test with the REQ ID in its name. Run it. RED for the right reason. Append command and short output to `evidence.md`.
2. Minimum code to pass. Run it. GREEN. Append to `evidence.md`.
3. Refactor only what you just wrote, tests green. Commit `REQ-<AREA>-<NNN>: <what>`.
4. Append a row to `metrics.csv`. Update `status.md`.
5. After 3 failed attempts on a task: stop and report with evidence. Out-of-scope ideas go under "Out of scope noticed" in `evidence.md`.
Never edit a test to make it pass. Never touch files outside `impact.md`.
````

## command.gate

Section 10.

````md file=kit/.claude/commands/gate.md
---
description: Run the deterministic gates for ready or done, then an AI review, then ask the human for sign-off.
argument-hint: ready|done <change-name>
---

purpose: Run the deterministic gates for ready or done, then an AI review, then ask the human for sign-off.

Follow `kit/core/rules.md`. Arguments: `$ARGUMENTS`.

1. Inputs: `inputs/granularity.json` and `inputs/diff_scope.json` come from `/slice`. For done, run the tests with coverage and pass `--coverage-report <report>`, `--baseline-total <from docs/ai/baseline.md>` and `--test-cmd "<test command>"` (CI passes its own).
2. Run `python3 kit/scripts/gate_check.py <stage> --change openspec/changes/<name>`.
3. If it fails: show each failing finding in one line and stop. Do not edit gates, tests or policy to pass.
4. If it passes: AI review. Ready: ambiguity and open questions. Done: tests assert behaviour, no weakened assertions.
5. Ask the human for sign-off and record it in `status.md`.
````

## command.safety_net

Section 16.

````md file=kit/.claude/commands/safety-net.md
---
description: Build a regression foundation for a named scope with kit/playbooks/safety-net.md.
argument-hint: <scope>
---

purpose: Build a regression foundation for a named scope with kit/playbooks/safety-net.md.

Follow `kit/core/rules.md`. Arguments: `$ARGUMENTS`.

Follow `kit/playbooks/safety-net.md` for the scope given. No production file may change. Stop for human confirmation of the Gherkin (step 5) and at done.
````

## command.refresh

Section 6.

````md file=kit/.claude/commands/refresh.md
---
description: Update docs/ai after merges, only for modules whose files changed since verified_sha.
argument-hint: 
---

purpose: Update docs/ai after merges, only for modules whose files changed since verified_sha.

Follow `kit/core/rules.md`. Arguments: `$ARGUMENTS`.

1. For each index entry, `git diff --name-only <verified_sha>..HEAD` on its module paths.
2. Nothing changed: say so and stop.
3. Mark changed entries stale, re-learn only those modules, update `verified_sha`.
4. Contract files changed: update `docs/ai/contracts.md` and flag it.
5. Suggest threshold changes from `metrics.csv` (loosen only after several first-attempt greens). A human decides.
6. Reply with a short list of what changed. Do not change source code.
````
