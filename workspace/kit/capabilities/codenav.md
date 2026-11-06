# Capability: codenav

purpose: interface for code navigation; impact scans and edits call these operations, never a tool directly.

## Operations
- `find_symbol`: in `{name}`; out `[{symbol, file, line}]`.
- `references`: in `{symbol}`; out `[{file, line}]`.
- `impact`: in `{symbols}`; out `{files, symbols, contracts, untested}` for `impact.md`.
- `outline`: in `{file}`; out top-level symbols of one file.

## Errors
- `no_language_server`: the language is not supported. `kit/scripts/probe.py` picks the next tool.
- `index_timeout`: indexing took too long. Treat as a failed probe.
- `not_found`: nothing matched. Say so; do not guess.

## Probe contract
Every adapter defines a canary: find one known symbol and list its references in under 60 seconds.
The result `{ok, reason}` feeds `kit/scripts/probe.py`, which records the choice in `docs/ai/toolchain.md`.
