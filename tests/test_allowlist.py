from __future__ import annotations

import unittest

import bootstrap  # noqa: F401

from jayblock.allowlist import apply_allowlist, is_allowlisted


class AllowlistTests(unittest.TestCase):
    def test_suffix_match(self) -> None:
        allow = {"example.com"}
        self.assertEqual(is_allowlisted("example.com", allow), "example.com")
        self.assertEqual(is_allowlisted("ads.example.com", allow), "example.com")
        self.assertIsNone(is_allowlisted("example.net", allow))

    def test_public_suffix_namespace(self) -> None:
        allow = {"githubusercontent.com"}
        self.assertEqual(
            is_allowlisted("raw.githubusercontent.com", allow),
            "githubusercontent.com",
        )
        allow = {"ads.google.com"}
        self.assertEqual(is_allowlisted("pagead.ads.google.com", allow), "ads.google.com")
        self.assertIsNone(is_allowlisted("google.com", allow))
        self.assertIsNone(is_allowlisted("mail.google.com", allow))

    def test_apply(self) -> None:
        domains = {
            "ads.example.com": {"src"},
            "tracker.net": {"src"},
        }
        kept, removed, hits = apply_allowlist(domains, {"example.com"})
        self.assertEqual(removed, 1)
        self.assertIn("tracker.net", kept)
        self.assertNotIn("ads.example.com", kept)
        self.assertEqual(hits["example.com"], 1)


if __name__ == "__main__":
    unittest.main()
