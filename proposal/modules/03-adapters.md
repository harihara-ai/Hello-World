purpose: working source for the adapters components of the kit (tangled into workspace/).

# Adapters

Each adapter implements one capability and passes that capability's shared contract suite.

## adapter.tracker.github

Spec: north-star-v2 section 4, 8. Status: stub, built in phase 2.

```md file=kit/adapters/tracker/github.md
purpose: tracker capability over GitHub MCP or gh CLI.
status: stub (phase 1). Spec: north-star-v2 section 4, 8.
```

## adapter.tracker.jira

Spec: north-star-v2 section 4, 8. Status: stub, built in phase 2.

```md file=kit/adapters/tracker/jira.md
purpose: tracker capability over Atlassian MCP or jira-cli.
status: stub (phase 1). Spec: north-star-v2 section 4, 8.
```

## adapter.tracker.azdo

Spec: north-star-v2 section 4, 8. Status: stub, built in phase 2.

```md file=kit/adapters/tracker/azdo.md
purpose: tracker capability over Azure DevOps MCP or az boards.
status: stub (phase 1). Spec: north-star-v2 section 4, 8.
```

## adapter.tracker.file

Spec: north-star-v2 section 13, 17.4. Status: stub, built in phase 2.

```md file=kit/adapters/tracker/file.md
purpose: read-only fallback: reads ticket files and writes intended updates to a file.
status: stub (phase 1). Spec: north-star-v2 section 13, 17.4.
```

## adapter.codenav.serena

Spec: north-star-v2 section 4. Status: stub, built in phase 2.

```md file=kit/adapters/codenav/serena.md
purpose: codenav capability over Serena language servers (default).
status: stub (phase 1). Spec: north-star-v2 section 4.
```

## adapter.codenav.ctags

Spec: north-star-v2 section 4, 13. Status: stub, built in phase 2.

```md file=kit/adapters/codenav/ctags.md
purpose: codenav fallback over universal-ctags plus ripgrep for languages with no language server.
status: stub (phase 1). Spec: north-star-v2 section 4, 13.
```
