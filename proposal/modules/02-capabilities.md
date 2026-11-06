purpose: working source for the capabilities components of the kit (tangled into workspace/).

# Capabilities

One interface per capability. Playbooks depend on these, never on an adapter.

## capability.tracker

Spec: north-star-v2 section 8, 13. Status: stub, built in phase 2.

```md file=kit/capabilities/tracker.md
purpose: tracker interface: read ticket, write comment, create sub-task, link; errors incl. no write permission.
status: stub (phase 1). Spec: north-star-v2 section 8, 13.
```

## capability.codenav

Spec: north-star-v2 section 4. Status: stub, built in phase 2.

```md file=kit/capabilities/codenav.md
purpose: code navigation interface: find symbol, references, impact list, plus the probe contract.
status: stub (phase 1). Spec: north-star-v2 section 4.
```
