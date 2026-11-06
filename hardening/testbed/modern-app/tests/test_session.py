import os
import tempfile
import unittest

# Flaky by design (trap 5): the test shares a state file with the previous run, so it alternates.
STATE = os.path.join(tempfile.gettempdir(), "testbed-modern-app-session.state")


class Session(unittest.TestCase):
    def test_session_counter(self):
        n = 0
        if os.path.exists(STATE):
            with open(STATE) as fh:
                n = int(fh.read() or 0)
        with open(STATE, "w") as fh:
            fh.write(str(n + 1))
        self.assertEqual(n % 2, 0)
