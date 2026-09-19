from __future__ import annotations

import unittest
from pathlib import Path

import bootstrap  # noqa: F401

from jayblock.explain import explain_domain
from jayblock.paths import DIST


class ExplainTests(unittest.TestCase):
    def test_blocked_tracker(self) -> None:
        if not (DIST / "aggressive.txt").exists():
            raise unittest.SkipTest("artifacts missing")
        out = explain_domain("doubleclick.net")
        self.assertTrue(out.startswith("BLOCKED"), out)
        self.assertIn("Sources:", out)

    def test_not_blocked_example(self) -> None:
        if not (DIST / "aggressive.txt").exists():
            raise unittest.SkipTest("artifacts missing")
        out = explain_domain("example.com")
        self.assertTrue(out.startswith("NOT BLOCKED"), out)

    def test_allowlisted_youtube(self) -> None:
        if not (DIST / "aggressive.txt").exists():
            raise unittest.SkipTest("artifacts missing")
        out = explain_domain("googlevideo.com")
        self.assertTrue(out.startswith("ALLOWLISTED"), out)


if __name__ == "__main__":
    unittest.main()
