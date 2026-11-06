"""purpose: T2 contract tests for the tracker capability (trap 9: read-only fallback)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contract  # noqa: E402


class TrackerContract(unittest.TestCase):
    def test_adapters_cover_the_interface(self):
        contract.check(self, "capability.tracker")

    def test_no_write_permission_falls_back_to_file(self):
        for a in contract.check(self, "capability.tracker"):
            text = contract.read(a["path"])
            if a["id"] == "adapter.tracker.file":
                self.assertIn("docs/ai/tracker-outbox.md", text)
            else:
                self.assertIn("adapter.tracker.file", text, a["id"])

    def test_ticket_text_is_data(self):
        for a in contract.check(self, "capability.tracker"):
            self.assertIn("gate.injection", contract.read(a["path"]), a["id"])


if __name__ == "__main__":
    unittest.main()
