purpose: synthetic modern repo (Python, unittest) for the trap test bed. Not real code; fixtures only.

`tests/test_session.py` is flaky: it shares a state file between runs, so it alternates pass and fail.
The clean change `CART-3-bulk-discount` adds a bulk discount with tests. Trap overlays live in `../cases/modern-app/`.
Run tests: `python3 -m unittest discover -s tests -v` from this folder.
