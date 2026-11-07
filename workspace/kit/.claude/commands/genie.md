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
