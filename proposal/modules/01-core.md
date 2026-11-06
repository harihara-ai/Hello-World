purpose: working source for the core components of the kit (tangled into workspace/).

# Core

Rules, glossary, state and policy schema. Core depends on nothing.

## core.claude

Spec: north-star-v2 section 1, 2, 6, 7. Status: stub, built in phase 2.

```md file=kit/CLAUDE.md
purpose: north star rules loaded in every session of a target repo (L0).
status: stub (phase 1). Spec: north-star-v2 section 1, 2, 6, 7.
```

## core.rules

Spec: north-star-v2 section 2, 10.6, 17.4. Status: stub, built in phase 2.

```md file=kit/core/rules.md
purpose: the floor rules: data not instructions, retry cap, no gate waivers, human approvals.
status: stub (phase 1). Spec: north-star-v2 section 2, 10.6, 17.4.
```

## core.glossary

Spec: north-star-v2 section 6, 11.1. Status: stub, built in phase 2.

```md file=kit/core/glossary.md
purpose: shared terms (change, slice, task, floor, REQ ID, confidence tags).
status: stub (phase 1). Spec: north-star-v2 section 6, 11.1.
```

## core.state

Spec: north-star-v2 section 7, 17.1. Status: stub, built in phase 2.

```md file=kit/core/state.md
purpose: schema of status.md, evidence.md, slices.md, metrics.csv and the state.sh JSON.
status: stub (phase 1). Spec: north-star-v2 section 7, 17.1.
```

## core.policy

Spec: north-star-v2 section 10.6, 11.3, 16.2. Status: stub, built in phase 2.

```yaml file=kit/core/policy.yml
# purpose: default floor thresholds; repos may raise, lowering needs a recorded human sign-off.
# status: stub (phase 1). Spec: north-star-v2 section 10.6, 11.3, 16.2.
```
