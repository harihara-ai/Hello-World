purpose: working source for the commands components of the kit (tangled into workspace/).

# Commands

Thin entry points. Each calls playbooks and scripts; the Genie routes through playbook.router.

## command.genie

Spec: north-star-v2 section 17. Status: stub, built in phase 2.

```md file=kit/.claude/commands/genie.md
purpose: one command for users: read state, route, run steps to the next human gate.
status: stub (phase 1). Spec: north-star-v2 section 17.
```

## command.bootstrap

Spec: north-star-v2 section 3, 4, 5, 9. Status: stub, built in phase 2.

```md file=kit/.claude/commands/bootstrap.md
purpose: probe tools, detect practices, write docs/ai index, toolchain, practices and policy.
status: stub (phase 1). Spec: north-star-v2 section 3, 4, 5, 9.
```

## command.learn

Spec: north-star-v2 section 6. Status: stub, built in phase 2.

```md file=kit/.claude/commands/learn.md
purpose: reverse-engineer one module into a card and an inferred behaviour spec.
status: stub (phase 1). Spec: north-star-v2 section 6.
```

## command.slice

Spec: north-star-v2 section 11.2. Status: stub, built in phase 2.

```md file=kit/.claude/commands/slice.md
purpose: impact scan, granularity score, split, slice plan for human approval.
status: stub (phase 1). Spec: north-star-v2 section 11.2.
```

## command.implement

Spec: north-star-v2 section 7, 10.4. Status: stub, built in phase 2.

```md file=kit/.claude/commands/implement.md
purpose: red-green-refactor per task with evidence and a 3-attempt cap.
status: stub (phase 1). Spec: north-star-v2 section 7, 10.4.
```

## command.gate

Spec: north-star-v2 section 10. Status: stub, built in phase 2.

```md file=kit/.claude/commands/gate.md
purpose: run gate_check ready or done, then AI review, then ask for human sign-off.
status: stub (phase 1). Spec: north-star-v2 section 10.
```

## command.safety_net

Spec: north-star-v2 section 16. Status: stub, built in phase 2.

```md file=kit/.claude/commands/safety-net.md
purpose: build a regression foundation for a named scope.
status: stub (phase 1). Spec: north-star-v2 section 16.
```

## command.refresh

Spec: north-star-v2 section 6. Status: stub, built in phase 2.

```md file=kit/.claude/commands/refresh.md
purpose: incremental index and module-card update from git diff since verified_sha.
status: stub (phase 1). Spec: north-star-v2 section 6.
```
