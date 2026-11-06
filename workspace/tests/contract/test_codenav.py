"""purpose: T2 contract tests for the codenav capability (trap 10: fallback without a language server)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contract  # noqa: E402


class CodenavContract(unittest.TestCase):
    def test_adapters_cover_the_interface(self):
        contract.check(self, "capability.codenav")

    def test_fallback_results_are_inferred(self):
        text = contract.read("kit/adapters/codenav/ctags.md")
        self.assertIn("inferred", text)


if __name__ == "__main__":
    unittest.main()
