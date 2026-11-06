# Glossary

purpose: shared terms used by every component; new terms are added here, not redefined elsewhere.

| Term | Meaning |
| --- | --- |
| Change | One spec, one branch, one PR. Folder `openspec/changes/<name>/` |
| Slice | One requirement or a few scenarios, vertically complete, independently testable |
| Task | One scenario, one red-green cycle |
| Floor | Minimum bar in the kit's `policy.yml`. Repos may raise it, never lower it silently |
| REQ ID | `REQ-<AREA>-<NNN>`, for example `REQ-BILL-004` |
| Impact scan | List of files and symbols a change may touch (`impact.md`) |
| Characterization test | Test that pins current behaviour of untested code before it changes |
| Gate | Deterministic check, JSON in and JSON out. G1 ready, G2 slice ready, G3 slice done, G4 PR done |
| observed / inferred / confirmed | Confidence of a fact. Only `confirmed` may become a spec |
| Playbook | Steps for one work item type |
| Capability / adapter | Interface for a tool kind / one tool that implements it |
