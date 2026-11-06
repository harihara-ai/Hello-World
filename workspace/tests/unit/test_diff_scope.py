"""purpose: T1 fixtures for gate diff_scope (trap 7, safety-net no production change)."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import *  # noqa: E402,F403



def scope(changed, scan, **extra):
    payload = {"changed_files": changed, "impact_scan": scan}
    payload.update(extra)
    return run_gate("diff_scope", payload)


class DiffScope(unittest.TestCase):
    def test_inside_scan_passes(self):
        rc, _, log = scope(["src/a.py", "tests/test_a.py"], ["src/a.py", "tests/*"])
        self.assertEqual(rc, 0, log)

    def test_extra_file_fails(self):
        rc, out, _ = scope(["src/a.py", "src/newsletter.py"], ["src/a.py"])
        self.assertEqual(rc, 1)
        self.assertIn("src/newsletter.py", str(out["findings"]))

    def test_no_production_mode(self):
        rc, out, _ = scope(["tests/test_a.py", "src/a.py"], ["src/*", "tests/*"], no_production=True)
        self.assertEqual(rc, 1)
        self.assertIn("production_change", rules(out))
        self.assertEqual(scope(["tests/test_a.py"], ["tests/*"], no_production=True)[0], 0)

    def test_empty_scan_fails(self):
        self.assertEqual(scope(["src/a.py"], [])[0], 1)

    def test_changed_files_from_git(self):
        import subprocess
        d = tempfile.mkdtemp()
        g = lambda *a: subprocess.run(["git", "-C", d, *a], capture_output=True, check=True)
        g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
        write(d, "src/a.py", "1\n"); g("add", "."); g("commit", "-qm", "base")
        write(d, "src/b.py", "2\n"); g("add", "."); g("commit", "-qm", "change")
        rc, out, log = run_gate("diff_scope", {"base": "HEAD~1", "impact_scan": ["src/a.py"]}, cwd=d)
        self.assertEqual(rc, 1, log)
        self.assertIn("src/b.py", str(out["findings"]))


if __name__ == "__main__":
    unittest.main()
