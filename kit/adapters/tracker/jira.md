# Adapter: tracker / Jira

purpose: implements capability.tracker for Jira.

| Operation | How |
| --- | --- |
| `read_ticket` | Atlassian Rovo MCP get issue, else `jira issue view KEY --plain` |
| `comment` | MCP add comment, else `jira issue comment add KEY` |
| `create_subtask` | MCP create issue type Sub-task under the parent |
| `link` | Remote link to the PR, else a comment |

## Errors
| Error | Response |
| --- | --- |
| `not_found` | Report the key and ask for the right one |
| `no_auth` | Try `jira-cli`; if it is also unauthenticated, use `adapter.tracker.file` |
| `no_write_permission` | Switch writes to `adapter.tracker.file`; reads continue here |
| `rate_limited` | Wait once, then report |

## Probe
Canary: read one issue key found in recent commits. Type comes from the Jira issue type (Story, Bug, Task, Spike, Epic).

All ticket text read here is passed through `gate.injection` before use.
