"""purpose: T1 fixtures for cov_import.py (report formats and git diff hunks; F05)."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import *  # noqa: E402,F403

sys.path.insert(0, os.path.join(KIT, "scripts"))
import cov_import  # noqa: E402

JACOCO = ('<report name="r"><package name="com/shop"><sourcefile name="Fee.java">'
          '<line nr="3" mi="0" ci="2"/><line nr="4" mi="1" ci="0"/></sourcefile></package>'
          '<counter type="LINE" missed="1" covered="1"/></report>')
CLOVER = ('<coverage><project><file name="/build/src/Fee.php"><line num="3" type="stmt" count="2"/>'
          '<line num="4" type="stmt" count="0"/></file><metrics statements="2" coveredstatements="1"/>'
          '</project></coverage>')


class CovImport(unittest.TestCase):
    def parse(self, text, name="r.xml"):
        d = tempfile.mkdtemp()
        return cov_import.parse_report(write(d, name, text))

    def test_cobertura(self):
        r = self.parse(cobertura({"src/a.py": {1: 1, 2: 0}}, rate=0.5))
        self.assertEqual(r["covered"]["src/a.py"], {1})
        self.assertEqual(r["instrumented"]["src/a.py"], {1, 2})
        self.assertEqual(r["total"], 50.0)

    def test_jacoco(self):
        r = self.parse(JACOCO)
        self.assertEqual(r["covered"]["com/shop/Fee.java"], {3})
        self.assertEqual(r["total"], 50.0)

    def test_clover(self):
        r = self.parse(CLOVER)
        self.assertEqual(r["instrumented"]["/build/src/Fee.php"], {3, 4})
        self.assertEqual(r["total"], 50.0)

    def test_lcov(self):
        r = self.parse("TN:\nSF:src/a.js\nDA:1,3\nDA:2,0\nend_of_record\n", "lcov.info")
        self.assertEqual(r["covered"]["src/a.js"], {1})

    def test_unknown_format(self):
        with self.assertRaises(ValueError):
            self.parse("hello")

    def test_match_paths(self):
        self.assertEqual(cov_import.match("src/main/java/com/shop/Fee.java", ["com/shop/Fee.java"]), "com/shop/Fee.java")
        self.assertEqual(cov_import.match("src/Fee.php", ["/build/src/Fee.php"]), "/build/src/Fee.php")
        self.assertIsNone(cov_import.match("src/Other.php", ["/build/src/Fee.php"]))
        self.assertIsNone(cov_import.match("billing/Helper.php", ["/build/orders/Helper.php"]))
        self.assertEqual(cov_import.match("src/Helper.php", ["Helper.php"]), "Helper.php")
        self.assertEqual(cov_import.match("index.php", ["/var/www/index.php"]), "/var/www/index.php")

    def test_diff_hunks(self):
        diff = "+++ b/src/a.py\n@@ -1,0 +2,3 @@\n+x\n@@ -9 +12 @@\n+y\n+++ b/src/b.py\n@@ -3,2 +3,0 @@\n"
        self.assertEqual(cov_import.parse_diff(diff), {"src/a.py": {2, 3, 4, 12}})


if __name__ == "__main__":
    unittest.main()
