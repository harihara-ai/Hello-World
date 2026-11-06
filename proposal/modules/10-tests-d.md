purpose: working source for the kit's own tests (T1 unit, T2 contract, T3 mutation); run by forge selftest.

# Tests

Not kit components, so not in the manifest. `tests/run.sh` runs all three levels.

## tests/unit/test_probe.py

````python file=tests/unit/test_probe.py
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
````

## tests/unit/test_spec_lint.py

````python file=tests/unit/test_spec_lint.py
"""purpose: T1 fixtures for gate spec_lint (G1 spec checks, trap 2)."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import *  # noqa: E402,F403


def lint(text, **policy):
    d = tempfile.mkdtemp()
    p = write(d, "spec.md", text)
    return run_gate("spec_lint", {"spec": p, "policy": policy})


class SpecLint(unittest.TestCase):
    def test_clean_spec_passes(self):
        rc, out, log = lint(CLEAN_SPEC)
        self.assertEqual(rc, 0, log)
        self.assertTrue(out["pass"])
        self.assertEqual(out["gate"], "spec_lint")

    def test_vague_words_fail(self):
        rc, out, _ = lint(CLEAN_SPEC.replace("Coupons.", "Coupons.").replace(
            "Loyal customers pay full price.", "The checkout must be fast and user-friendly."))
        self.assertEqual(rc, 1)
        self.assertIn("vague_word", rules(out))

    def test_vague_word_with_number_allowed(self):
        rc, _, log = lint(CLEAN_SPEC.replace("pay full price.", "pay full price; pricing is fast (under 50 ms)."))
        self.assertEqual(rc, 0, log)

    def test_requirement_without_id_fails(self):
        rc, out, _ = lint(CLEAN_SPEC.replace("### REQ-DISC-002: No", "### No"))
        self.assertEqual(rc, 1)
        self.assertIn("req_id", rules(out))

    def test_missing_error_case_fails(self):
        rc, out, _ = lint(CLEAN_SPEC.replace("Errors: none\n", ""))
        self.assertIn("error_case", rules(out))
        self.assertEqual(rc, 1)

    def test_scenario_needs_given_when_then_and_level(self):
        rc, out, _ = lint(CLEAN_SPEC.replace("  Then the price is 99.99\n  Level: unit\n", ""))
        self.assertEqual(rc, 1)
        self.assertTrue({"gwt", "test_level"} <= rules(out))

    def test_open_questions_fail(self):
        rc, out, _ = lint(CLEAN_SPEC.replace("## Open questions\nnone", "## Open questions\nWhich currency?"))
        self.assertIn("open_questions", rules(out))

    def test_missing_ticket_and_section_fail(self):
        rc, out, _ = lint(CLEAN_SPEC.replace("Ticket: SHOP-12\n", "").replace("## Out of scope\n", "## Notes\n"))
        self.assertTrue({"ticket", "section"} <= rules(out))

    def test_nfr_needs_number(self):
        rc, out, _ = lint(CLEAN_SPEC.replace("## Non-functional\nnone", "## Non-functional\nPricing is quick."))
        self.assertIn("nfr_threshold", rules(out))

    def test_too_long_fails(self):
        rc, out, _ = lint(CLEAN_SPEC, max_spec_lines=10)
        self.assertIn("size", rules(out))

    def test_duplicate_id_fails(self):
        rc, out, _ = lint(CLEAN_SPEC.replace("REQ-DISC-002", "REQ-DISC-001"))
        self.assertIn("duplicate_id", rules(out))

    def test_missing_file_is_usage_error(self):
        rc, _, _ = run_gate("spec_lint", {"spec": "/nonexistent/spec.md"})
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
````

## tests/unit/test_state.py

````python file=tests/unit/test_state.py
"""purpose: T1 fixtures for state.sh (the Genie's state JSON)."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import *  # noqa: E402,F403

import json
import subprocess


def git(d, *a):
    subprocess.run(["git", "-C", d, *a], capture_output=True, check=True)


class State(unittest.TestCase):
    def state(self, d):
        p = subprocess.run(["bash", os.path.join(KIT, "scripts", "state.sh")], cwd=d, capture_output=True, text=True)
        return p.returncode, json.loads(p.stdout)

    def setUp(self):
        self.d = tempfile.mkdtemp()
        git(self.d, "init", "-q", "-b", "main")
        git(self.d, "config", "user.email", "t@t")
        git(self.d, "config", "user.name", "t")
        write(self.d, "README", "x\n")
        git(self.d, "add", ".")
        git(self.d, "commit", "-qm", "init")

    def test_no_change(self):
        rc, s = self.state(self.d)
        self.assertEqual(rc, 0)
        self.assertEqual(s["branch"], "main")
        self.assertIsNone(s["ticket"])
        self.assertFalse(s["change_exists"])

    def test_change_with_status_and_gate(self):
        git(self.d, "checkout", "-q", "-b", "feature/SHOP-12-add-discount")
        ch = "openspec/changes/SHOP-12-add-discount/"
        write(self.d, ch + "status.md", 'slice: S1\nnext: run /gate done "now"\n')
        write(self.d, ch + "gates-ready.json", {"stage": "ready", "pass": True})
        rc, s = self.state(self.d)
        self.assertEqual(s["ticket"], "SHOP-12")
        self.assertEqual(s["change"], "SHOP-12-add-discount")
        self.assertTrue(s["change_exists"])
        self.assertEqual(s["next"], 'run /gate done "now"')
        self.assertEqual(s["last_gate"], {"stage": "ready", "pass": True})

    def test_not_a_repo(self):
        rc, s = self.state(tempfile.mkdtemp())
        self.assertIsNone(s["branch"])


if __name__ == "__main__":
    unittest.main()
````

## tests/unit/test_trace_check.py

````python file=tests/unit/test_trace_check.py
"""purpose: T1 fixtures for gate trace_check (requirement to test, trap 6)."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import *  # noqa: E402,F403



class Trace(unittest.TestCase):
    def setUp(self):
        self.root, self.ch = make_repo()

    def check(self, **extra):
        payload = {"spec_dirs": [self.ch], "test_dirs": ["tests"]}
        payload.update(extra)
        return run_gate("trace_check", payload, cwd=self.root)

    def test_every_requirement_tested_passes(self):
        rc, out, log = self.check()
        self.assertEqual(rc, 0, log)

    def test_requirement_without_test_fails(self):
        write(self.root, "tests/test_discount.py", "# REQ-DISC-001\n")
        rc, out, _ = self.check()
        self.assertEqual(rc, 1)
        self.assertIn("REQ-DISC-002", str(out["findings"]))

    def test_no_ids_in_spec_fails(self):
        write(self.root, self.ch + "/spec.md", "nothing here\n")
        self.assertEqual(self.check()[0], 1)

    def test_missing_test_dirs_fails(self):
        self.assertEqual(self.check(test_dirs=["nope"])[0], 1)

    def test_orphan_test_id_warns_only(self):
        write(self.root, "tests/test_x.py", "# REQ-OTHER-009\n")
        rc, out, _ = self.check()
        self.assertEqual(rc, 0)
        self.assertIn("orphan_id", rules(out))


if __name__ == "__main__":
    unittest.main()
````
