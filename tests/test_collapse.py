from __future__ import annotations

import unittest

import bootstrap  # noqa: F401

from jayblock.collapse import collapse_descendants, covering_entry


class CollapseTests(unittest.TestCase):
    def test_descendant_removed(self) -> None:
        domains = {
            "tracker.example.com": {"a"},
            "metrics.tracker.example.com": {"b"},
            "other.example.org": {"a"},
        }
        kept, redundant = collapse_descendants(domains)
        self.assertEqual(redundant, 1)
        self.assertIn("tracker.example.com", kept)
        self.assertNotIn("metrics.tracker.example.com", kept)
        self.assertEqual(kept["tracker.example.com"], {"a", "b"})
        self.assertIn("other.example.org", kept)

    def test_does_not_invent_parent(self) -> None:
        domains = {"ads.example.com": {"a"}, "tracker.example.com": {"a"}}
        kept, redundant = collapse_descendants(domains)
        self.assertEqual(redundant, 0)
        self.assertEqual(set(kept), {"ads.example.com", "tracker.example.com"})

    def test_covering_entry(self) -> None:
        blocked = {"tracker.example.com", "ads.net"}
        self.assertEqual(
            covering_entry("metrics.tracker.example.com", blocked),
            "tracker.example.com",
        )
        self.assertIsNone(covering_entry("example.com", blocked))


if __name__ == "__main__":
    unittest.main()
