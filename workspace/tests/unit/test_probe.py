"""purpose: T1 fixtures for probe.py (ranked fallbacks, trap 10)."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import *  # noqa: E402,F403



def probe(results, needed=None, args=()):
    payload = {"results": results}
    if needed:
        payload["capabilities"] = needed
    return run_py(os.path.join(KIT, "scripts", "probe.py"), payload, ["-", *args])


class Probe(unittest.TestCase):
    def test_default_chosen_when_ok(self):
        rc, out, log = probe({"serena": {"ok": True}, "ctags": {"ok": True}}, ["codenav"])
        self.assertEqual(rc, 0, log)
        self.assertEqual(out["capabilities"]["codenav"]["chosen"], "serena")

    def test_fallback_when_no_language_server(self):
        rc, out, _ = probe({"serena": {"ok": False, "reason": "no language server for Delphi"},
                            "tree-sitter-analyzer": {"ok": False, "reason": "Delphi unsupported"},
                            "ctags": {"ok": True}}, ["codenav"])
        c = out["capabilities"]["codenav"]
        self.assertEqual(c["chosen"], "ctags")
        self.assertIn("no language server for Delphi", str(c["rejected"]))

    def test_nothing_works_asks(self):
        rc, out, _ = probe({"serena": {"ok": False}}, ["codenav"])
        self.assertEqual(rc, 1)
        self.assertIsNone(out["capabilities"]["codenav"]["chosen"])

    def test_writes_toolchain_md(self):
        d = tempfile.mkdtemp()
        out_md = os.path.join(d, "toolchain.md")
        rc, _, log = probe({"serena": {"ok": False, "reason": "crash"}, "ctags": {"ok": True}}, ["codenav"], ["--out", out_md])
        self.assertEqual(rc, 0, log)
        with open(out_md) as fh:
            text = fh.read()
        self.assertIn("purpose:", text)
        self.assertIn("ctags", text)
        self.assertIn("crash", text)

    def test_unknown_capability_usage_error(self):
        self.assertEqual(probe({}, ["teleport"])[0], 2)


if __name__ == "__main__":
    unittest.main()
