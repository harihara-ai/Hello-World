purpose: working source for the playbooks components of the kit (tangled into workspace/).

# Playbooks

Steps for one work item type. The router table maps ticket types to playbooks.

## playbook.router

Spec: north-star-v2 section 8, 17.2, 17.5. Status: stub, built in phase 2.

```md file=kit/playbooks/router.md
purpose: maps tracker types and user intents to playbooks; unknown types ask one question.
status: stub (phase 1). Spec: north-star-v2 section 8, 17.2, 17.5.
```

## playbook.story

Spec: north-star-v2 section 8, 10. Status: stub, built in phase 2.

```md file=kit/playbooks/story.md
purpose: story or enhancement (also NFR with a threshold): spec, G1, slice, implement, G3, G4.
status: stub (phase 1). Spec: north-star-v2 section 8, 10.
```

## playbook.bug

Spec: north-star-v2 section 8. Status: stub, built in phase 2.

```md file=kit/playbooks/bug.md
purpose: bug and hotfix: failing repro test first, REQ ID on the regression test, root cause noted.
status: stub (phase 1). Spec: north-star-v2 section 8.
```

## playbook.no_behaviour_change

Spec: north-star-v2 section 8. Status: stub, built in phase 2.

```md file=kit/playbooks/no-behaviour-change.md
purpose: chore and refactor: characterization tests green before and after; behaviour identical.
status: stub (phase 1). Spec: north-star-v2 section 8.
```

## playbook.safety_net

Spec: north-star-v2 section 16. Status: stub, built in phase 2.

```md file=kit/playbooks/safety-net.md
purpose: regression foundation: inventory, gap, plan, Gherkin, automate, stabilise; no production file changes.
status: stub (phase 1). Spec: north-star-v2 section 16.
```

## playbook.spike

Spec: north-star-v2 section 8. Status: stub, built in phase 2.

```md file=kit/playbooks/spike.md
purpose: spike: question and time box; output is a findings doc, no production code merged.
status: stub (phase 1). Spec: north-star-v2 section 8.
```
