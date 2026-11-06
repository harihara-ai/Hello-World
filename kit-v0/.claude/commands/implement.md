---
description: Implement one approved OpenSpec change with red-green-refactor, traceability, and a PR.
argument-hint: <change-name>
---

Implement the change `openspec/changes/$ARGUMENTS/`. Follow every rule in CLAUDE.md.

## Step 0: Check before starting
- The change folder exists with a proposal, spec deltas, and tasks.
- Run `openspec validate $ARGUMENTS`. It must pass.
- Every requirement has a `REQ-<AREA>-<NNN>` ID and at least one scenario.
- I have clearly approved this spec in this chat or in the change folder.
If any item is missing, list what is missing and stop. Do not guess.

## Step 1: Impact scan (no code yet)
Use Serena to find the symbols and files each requirement will touch. Write `openspec/changes/$ARGUMENTS/impact.md`:
- files and symbols affected
- public contracts touched (check `docs/ai/contracts.md`)
- affected code that has no tests
Stop and ask me if a public contract is touched or the scope looks bigger than the spec.

## Step 2: Characterization tests (only if needed)
For affected code with no tests, write characterization tests that pin current behaviour. Run them. They must pass. Commit separately with the prefix `CHAR:`.

## Step 3: Red-green loop, one task at a time
For each task in `tasks.md`, in order:
1. RED: write a test for one scenario. Put the REQ ID in the test name. Run it. Confirm it fails for the right reason. Append command and failure output (short) to `evidence.md`.
2. GREEN: write the minimum code to pass. Run it. Append the passing result to `evidence.md`.
3. REFACTOR: tidy only what you just wrote. Run the tests again.
4. Commit: `REQ-<AREA>-<NNN>: <what changed>`.
5. Tick the task in `tasks.md`.
Keep changes small. If something is unclear or out of scope, stop and ask. Note out-of-scope findings in `evidence.md` under "Out of scope noticed". Do not fix them.

## Step 4: Verify
Run in order and fix only what your change broke:
1. Full test suite vs `docs/ai/baseline.md`
2. Lint
3. Semgrep
4. Trivy, only if dependencies changed
5. `scripts/trace_check.sh $ARGUMENTS`
6. Read your own diff. Remove anything the spec did not ask for.

## Step 5: Spec drift
If the final behaviour differs from the spec, do not edit the spec yourself. Show me the difference and ask.

## Step 6: Pull request
Open a PR. The description has:
- Summary (3 lines)
- Trace table: requirement | test | commit
- RED/GREEN evidence (link to `evidence.md`)
- Out of scope noticed
- Verify results
Do not merge. After a human merges, I will run `openspec archive $ARGUMENTS`, then `/refresh`.
