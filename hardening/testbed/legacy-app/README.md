purpose: synthetic legacy repo (PHP with a Delphi unit) for the trap test bed. Not real code; fixtures only.

`src/Invoice.php` has no tests and hidden behaviour (drops negative lines, rounds half down).
`src/Legacy/Tax.pas` is Delphi, a language with no language server in the probe.
The clean change `INV-7-late-fee` adds a late fee with tests. Trap overlays live in `../cases/legacy-app/`.
