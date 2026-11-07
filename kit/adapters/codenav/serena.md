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
