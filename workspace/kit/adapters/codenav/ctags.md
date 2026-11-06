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
