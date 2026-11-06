purpose: working source for the gates components of the kit (tangled into workspace/).

# Gates

Each gate is one deterministic check: JSON in, JSON out, exit 0 pass, 1 fail.

## gate.spec_lint

Spec: north-star-v2 section 10.1, 10.2. Status: stub, built in phase 2.

```python file=kit/gates/spec_lint.py
# purpose: G1 spec checks: REQ IDs, Given/When/Then with an error case, test levels, banned vague words, size.
# status: stub (phase 1). Spec: north-star-v2 section 10.1, 10.2.
```

## gate.granularity

Spec: north-star-v2 section 11.3. Status: stub, built in phase 2.

```python file=kit/gates/granularity.py
# purpose: scores a slice green/amber/red per section 11.3; any red or two ambers means split.
# status: stub (phase 1). Spec: north-star-v2 section 11.3.
```

## gate.trace

Spec: north-star-v2 section 10.4 #6. Status: stub, built in phase 2.

```bash file=kit/gates/trace_check.sh
# purpose: every REQ ID in the specs appears in at least one test (ported from kit-v0).
# status: stub (phase 1). Spec: north-star-v2 section 10.4 #6.
```

## gate.diff_scope

Spec: north-star-v2 section 10.4 #9, 16.5. Status: stub, built in phase 2.

```python file=kit/gates/diff_scope.py
# purpose: flags changed files outside the impact scan, and production files in a safety-net change.
# status: stub (phase 1). Spec: north-star-v2 section 10.4 #9, 16.5.
```

## gate.coverage

Spec: north-star-v2 section 10.4 #5. Status: stub, built in phase 2.

```python file=kit/gates/coverage.py
# purpose: changed-line coverage at or above threshold and no drop in overall coverage.
# status: stub (phase 1). Spec: north-star-v2 section 10.4 #5.
```

## gate.policy_guard

Spec: north-star-v2 section 10.6. Status: stub, built in phase 2.

```python file=kit/gates/policy_guard.py
# purpose: refuses a policy.yml change that lowers a threshold without a recorded human sign-off.
# status: stub (phase 1). Spec: north-star-v2 section 10.6.
```

## gate.injection

Spec: north-star-v2 section 17.4, 21.1 T5. Status: stub, built in phase 2.

```python file=kit/gates/injection.py
# purpose: flags hostile instructions in ticket, spec, comment or file-name text.
# status: stub (phase 1). Spec: north-star-v2 section 17.4, 21.1 T5.
```

## gate.flaky

Spec: north-star-v2 section 16.1 #2, 16.1 #8. Status: stub, built in phase 2.

```python file=kit/gates/flaky.py
# purpose: compares repeated test runs and lists flaky tests to quarantine.
# status: stub (phase 1). Spec: north-star-v2 section 16.1 #2, 16.1 #8.
```
