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
