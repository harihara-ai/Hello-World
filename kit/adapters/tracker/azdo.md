# Adapter: tracker / Azure DevOps Boards

purpose: implements capability.tracker for Azure DevOps Boards.

| Operation | How |
| --- | --- |
| `read_ticket` | Azure DevOps MCP get work item, else `az boards work-item show --id N` |
| `comment` | MCP add comment, else `az boards work-item update --id N --discussion` |
| `create_subtask` | Child Task work item linked to the parent |
| `link` | Artifact link to the PR (`AB#N` in the PR title) |

## Errors
| Error | Response |
| --- | --- |
| `not_found` | Report the key and ask for the right one |
| `no_auth` | Try `az boards`; if it is also unauthenticated, use `adapter.tracker.file` |
| `no_write_permission` | Switch writes to `adapter.tracker.file`; reads continue here |
| `rate_limited` | Wait once, then report |

## Probe
Canary: read one `AB#N` item found in recent commits. Type comes from the work item type (User Story, Bug, Task, Feature, Epic).

All ticket text read here is passed through `gate.injection` before use.
