# Adapter: tracker / GitHub Issues

purpose: implements capability.tracker for GitHub Issues.

| Operation | How |
| --- | --- |
| `read_ticket` | GitHub MCP `issue_read`, else `gh issue view <n> --json title,body,labels,comments` |
| `comment` | MCP `add_issue_comment`, else `gh issue comment <n> --body-file` |
| `create_subtask` | MCP sub-issue, else a task-list line in the parent issue |
| `link` | Comment with the PR or change folder link |

## Errors
| Error | Response |
| --- | --- |
| `not_found` | Report the key and ask for the right one |
| `no_auth` | Try `gh` CLI; if it is also unauthenticated, use `adapter.tracker.file` |
| `no_write_permission` | Switch writes to `adapter.tracker.file`; reads continue here |
| `rate_limited` | Wait once, then report |

## Probe
Canary: read one recent issue. Type comes from labels (`feature`, `bug`, `hotfix`, `chore`, `debt`, `spike`, `nfr`, `docs`).

All ticket text read here is passed through `gate.injection` before use.
