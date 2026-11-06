purpose: working source for the scripts components of the kit (tangled into workspace/).

# Scripts

Helpers used by commands and gates.

## script.gate_check

Spec: north-star-v2 section 10.6. Status: stub, built in phase 2.

```python file=kit/scripts/gate_check.py
# purpose: runs the gates listed in policy.yml for ready or done and merges their JSON.
# status: stub (phase 1). Spec: north-star-v2 section 10.6.
```

## script.state

Spec: north-star-v2 section 17.1. Status: stub, built in phase 2.

```bash file=kit/scripts/state.sh
# purpose: prints the Genie state JSON (branch, ticket key, change folder, last gate, readiness).
# status: stub (phase 1). Spec: north-star-v2 section 17.1.
```

## script.probe

Spec: north-star-v2 section 4, 5. Status: stub, built in phase 2.

```python file=kit/scripts/probe.py
# purpose: picks a tool per capability from probe results using the ranked fallbacks; writes toolchain.md.
# status: stub (phase 1). Spec: north-star-v2 section 4, 5.
```
