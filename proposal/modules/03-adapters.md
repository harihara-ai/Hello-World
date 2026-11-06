purpose: working source for the adapters components of the kit (tangled into workspace/).

# Adapters

Each adapter implements one capability and must name every operation and error of it (T2).

## adapter.tracker.github

Section 4 tracker row.

````md file=kit/adapters/tracker/github.md
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
````

## adapter.tracker.jira

Section 4 tracker row.

````md file=kit/adapters/tracker/jira.md
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
````

## adapter.tracker.azdo

Section 4 tracker row.

````md file=kit/adapters/tracker/azdo.md
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
````

## adapter.tracker.file

Sections 13, 17.4. Trap 9.

````md file=kit/adapters/tracker/file.md
# Adapter: tracker / file (read-only fallback)

purpose: implements capability.tracker with files when no tracker API or write permission exists.

| Operation | How |
| --- | --- |
| `read_ticket` | Read `docs/ai/tickets/<KEY>.md` (pasted by the user or exported). Type from its `Type:` line |
| `comment` | Append `## <KEY> comment` and the text to `docs/ai/tracker-outbox.md` |
| `create_subtask` | Append a `## <KEY> sub-task: <title>` entry to `docs/ai/tracker-outbox.md` |
| `link` | Append the link entry to `docs/ai/tracker-outbox.md` |

## Errors
| Error | Response |
| --- | --- |
| `not_found` | No ticket file: ask the user to paste the ticket into `docs/ai/tickets/<KEY>.md` |
| `no_auth` | Not applicable; files need no auth |
| `no_write_permission` | Not applicable; all writes go to the outbox |
| `rate_limited` | Not applicable |

## Probe
Always works. The Genie tells the user once: "Tracker is read-only; updates are in docs/ai/tracker-outbox.md for you to copy."

Ticket files are user input: run `gate.injection` on them like any other ticket text.
````

## adapter.codenav.serena

Section 4.

````md file=kit/adapters/codenav/serena.md
# Adapter: codenav / Serena (default)

purpose: implements capability.codenav with Serena's language-server tools.

| Operation | How |
| --- | --- |
| `find_symbol` | Serena `find_symbol` |
| `references` | Serena `find_referencing_symbols` |
| `impact` | References of each symbol, grouped by module; untested = no test file references it |
| `outline` | Serena `get_symbols_overview` |

## Errors
| Error | Response |
| --- | --- |
| `no_language_server` | Report `{ok: false, reason}` to `kit/scripts/probe.py`; it picks the next tool |
| `index_timeout` | Same as a failed probe |
| `not_found` | Say nothing matched; do not guess |

## Probe
Start Serena at project scope, find one known symbol and its references. Fails for languages without a
language server (Delphi is the likely gap) or when the server crashes on a large repo. Results are `observed`.
````

## adapter.codenav.ctags

Sections 4, 13. Trap 10.

````md file=kit/adapters/codenav/ctags.md
# Adapter: codenav / ctags plus ripgrep (last fallback)

purpose: implements capability.codenav with universal-ctags and ripgrep for languages no other tool supports.

| Operation | How |
| --- | --- |
| `find_symbol` | `ctags -R --fields=+n -f .ctags-index` once, then look the name up in the index |
| `references` | `rg -n -w <name>`; text matches, so results are `inferred`, not `observed` |
| `impact` | References grouped by top folder; module boundaries from `docs/ai/repo-map.md` |
| `outline` | `ctags -x <file>` |

## Errors
| Error | Response |
| --- | --- |
| `no_language_server` | Not applicable; ctags parses most languages including Pascal/Delphi |
| `index_timeout` | Index one module at a time |
| `not_found` | Say nothing matched; do not guess |

## Probe
Run ctags on one module and find one known symbol. Record in `toolchain.md` that edits are text-based
here: re-read the file before each edit and keep slices smaller.
````
