# Playbook: safety net (regression foundation)

purpose: build regression tests for a named scope in risk order, without touching production code.

1. **Scope.** Write `safety-net/<scope>/scope.md`: module, feature, journey or the area of a change.
2. **Inventory.** Run existing tests 3 times. Save the runs as `inputs/flaky.json`. Run `gate.flaky`; quarantine flaky tests with a ticket.
3. **Gap.** Score each unit for risk: churn, past defects, complexity, contract exposure, `docs/ai/critical-journeys.md`. Tier 1 to 4.
4. **Plan.** Cheapest test level per risk. Untested legacy code gets characterization tests first.
5. **Gherkin.** Draft from code, the running app and tickets, tagged `inferred`. A human confirms; then add REQ IDs and tags.
6. **Automate.** One framework per repo; feature, step, keyword, page-object and driver layers. No fixed sleeps.
7. **Stabilise.** Run each new test 5 times. `gate.flaky` must pass.
8. **Done.** `gate_check.py done --also flaky` with `"no_production": true` in `inputs/diff_scope.json`, so any production file fails `gate.diff_scope`.
