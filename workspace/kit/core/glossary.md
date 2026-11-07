# Glossary

purpose: shared terms used by every component; new terms are added here, not redefined elsewhere.

| Term | Meaning |
| --- | --- |
| Change | One spec, two PRs: the plan, then the code. Folder `openspec/changes/<name>/` |
| Slice | One requirement or a few scenarios, vertically complete, independently testable |
| Task | One scenario, one red-green cycle |
| Floor | Minimum bar in the kit's `policy.yml`. Repos may raise it, never lower it silently |
| REQ ID | `REQ-<AREA>-<NNN>`, for example `REQ-BILL-004` |
| Impact scan | Globs of files a change may touch (`inputs/diff_scope.json`, merged with the plan) |
| Characterization test | Test that pins current behaviour of untested code before it changes |
| Gate | Deterministic check, JSON in and JSON out. G1 ready, G2 slice ready, G3 slice done, G4 PR done |
| observed / inferred / confirmed | Confidence of a fact. Only `confirmed` may become a spec |
| Playbook | Steps for one work item type |
| Capability / adapter | Interface for a tool kind / one tool that implements it |
| green / amber / red | Granularity score of a slice: fine / review / must split. Two ambers also mean split |
| L0 to L3 | Knowledge load levels: always loaded, module card, symbols, raw source |
