purpose: working source for the kit's own tests (T1 unit, T2 contract, T3 mutation); run by forge selftest.

# Tests

Not kit components, so not in the manifest. `tests/run.sh` runs all three levels.

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
        self.assertFalse(s["bootstrapped"])

    def test_bootstrapped_when_index_and_policy_exist(self):
        write(self.d, "docs/ai/index.json", "[]")
        write(self.d, "docs/ai/policy.yml", "version: 1\n")
        self.assertTrue(self.state(self.d)[1]["bootstrapped"])

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
"""purpose: T1 fixtures for gate trace_check (requirement to test, trap 6; F01, F02)."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import *  # noqa: E402,F403



class Trace(unittest.TestCase):
    def setUp(self):
        self.root, self.ch = make_repo()

    def check(self, **extra):
        payload = {"spec_dirs": [self.ch]}
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

    def test_id_in_production_code_does_not_count(self):
        write(self.root, "tests/test_discount.py", "# REQ-DISC-001\n")
        write(self.root, "src/discount.py", "# REQ-DISC-002\n")
        self.assertEqual(self.check()[0], 1)

    def test_test_dirs_input_is_ignored(self):
        write(self.root, "tests/test_discount.py", "# REQ-DISC-001\n")
        self.assertEqual(self.check(test_dirs=["src", "openspec"])[0], 1)

    def test_underscore_ids_in_java_and_csharp_names(self):
        os.remove(os.path.join(self.root, "tests/test_discount.py"))
        write(self.root, "src/test/java/shop/DiscountTest.java", "void REQ_DISC_001_tenPercent() {}\n")
        write(self.root, "Shop.Tests/DiscountTests.cs", "public void Req_Disc_002_NoDiscount() {}\n")
        rc, _, log = self.check()
        self.assertEqual(rc, 0, log)

    def test_feature_tags_count(self):
        os.remove(os.path.join(self.root, "tests/test_discount.py"))
        write(self.root, "features/discount.feature", "@REQ-DISC-001 @REQ-DISC-002\nFeature: x\n")
        self.assertEqual(self.check()[0], 0)

    def test_no_ids_in_spec_fails(self):
        write(self.root, self.ch + "/spec.md", "nothing here\n")
        self.assertEqual(self.check()[0], 1)

    def test_no_test_files_fails(self):
        os.remove(os.path.join(self.root, "tests/test_discount.py"))
        self.assertEqual(self.check()[0], 1)

    def test_orphan_test_id_warns_only(self):
        write(self.root, "tests/test_x.py", "# REQ-OTHER-009\n")
        rc, out, _ = self.check()
        self.assertEqual(rc, 0)
        self.assertIn("orphan_id", rules(out))


if __name__ == "__main__":
    unittest.main()
````
