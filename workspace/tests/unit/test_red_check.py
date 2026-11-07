"""purpose: T1 fixtures for gate red_check (changed tests must fail on base code; spec 10.4 #1; H05, J03, J08, C01, C02)."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import *  # noqa: E402,F403

TEST = ("import os, sys, unittest\nsys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))\n"
        "import m\n\n\nclass T(unittest.TestCase):\n    def test_f(self):\n        self.assertEqual(m.f(), %s)\n")


class RedCheck(unittest.TestCase):
    def setUp(self):
        self.d = git_init(write_tree({"src/m.py": "def f():\n    return 1\n", "tests/test_m.py": TEST % 1}))
        self.base = git(self.d, "rev-parse", "HEAD").strip()

    def red(self, wtype="story", cmd=None):
        return run_gate("red_check", {"base": self.base, "type": wtype, "test_cmd": cmd or TEST_CMD}, cwd=self.d)

    def change(self):
        write(self.d, "src/m.py", "def f():\n    return 2\n")
        write(self.d, "tests/test_m.py", TEST % 2)

    def test_behaviour_change_with_new_test_is_red(self):
        self.change()
        rc, out, log = self.red()
        self.assertEqual(rc, 0, log)

    def test_working_tree_is_restored(self):
        self.change()
        write(self.d, "src/new.py", "x = 1\n")
        self.red()
        with open(os.path.join(self.d, "src/m.py")) as fh:
            self.assertIn("return 2", fh.read())
        self.assertTrue(os.path.exists(os.path.join(self.d, "src/new.py")))

    def test_test_that_passes_on_base_fails(self):
        write(self.d, "src/m.py", "def f():\n    return 2\n")
        write(self.d, "tests/test_n.py", "import unittest\n\n\nclass T(unittest.TestCase):\n    def test_x(self):\n        pass\n")
        rc, out, _ = self.red()
        self.assertEqual(rc, 1)
        self.assertIn("tests_pass_on_base", rules(out))

    def test_story_without_changed_tests_fails(self):
        write(self.d, "src/m.py", "def f():\n    return 2\n")
        rc, out, _ = self.red()
        self.assertIn("no_new_tests", rules(out))

    def test_runner_that_cannot_start_is_an_error_not_red(self):
        self.change()
        rc, out, _ = self.red(cmd="no-such-test-runner-xyz")
        self.assertEqual(rc, 1)
        self.assertIn("runner_error", rules(out))

    def test_tests_placeholder_runs_only_changed_tests(self):
        write(self.d, "tests/test_broken.py", "import unittest\n\n\nclass B(unittest.TestCase):\n    def test_b(self):\n        self.fail()\n")
        git(self.d, "add", "-A"); git(self.d, "commit", "-qm", "broken unrelated test on base")
        self.base = git(self.d, "rev-parse", "HEAD").strip()
        write(self.d, "tests/test_n.py", "import unittest\n\n\nclass T(unittest.TestCase):\n    def test_x(self):\n        pass\n")
        rc, out, _ = self.red(cmd=sys.executable + " -B -m unittest {tests}")  # no -I: unittest imports by path from cwd
        self.assertIn("tests_pass_on_base", rules(out))

    def test_refactor_and_spike_have_nothing_to_check(self):
        self.change()
        self.assertEqual(self.red("refactor")[0], 0)
        self.assertEqual(self.red("spike")[0], 0)

    def test_missing_test_command_fails(self):
        self.change()
        rc, out, _ = run_gate("red_check", {"base": self.base, "type": "story"}, cwd=self.d)
        self.assertIn("no_test_cmd", rules(out))


if __name__ == "__main__":
    unittest.main()
