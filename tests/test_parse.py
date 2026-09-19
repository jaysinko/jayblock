from __future__ import annotations

import unittest

import bootstrap  # noqa: F401

from jayblock.parse import parse_line, parse_list


class ParseTests(unittest.TestCase):
    def test_comments(self) -> None:
        self.assertEqual(parse_line("# hello").skipped, "comment")
        self.assertEqual(parse_line("! Title: x").skipped, "comment")

    def test_wildcard_domain(self) -> None:
        self.assertEqual(parse_line("*.ads.example.com").domain, "ads.example.com")

    def test_hosts(self) -> None:
        self.assertEqual(parse_line("0.0.0.0 tracker.example.com").domain, "tracker.example.com")
        self.assertEqual(parse_line("127.0.0.1 ads.example.net # note").domain, "ads.example.net")

    def test_abp_domain_rule(self) -> None:
        self.assertEqual(parse_line("||doubleclick.net^").domain, "doubleclick.net")
        self.assertTrue(parse_line("@@||example.com^").allow)
        self.assertEqual(parse_line("||example.com^$script").skipped, "abp-unsupported")

    def test_cosmetic_and_regex_ignored(self) -> None:
        self.assertEqual(parse_line("example.com##.ad").skipped, "cosmetic")
        self.assertEqual(parse_line("/ads[0-9]+/").skipped, "regex")

    def test_parse_list(self) -> None:
        text = """
# comment
*.tracker.example.com
0.0.0.0 ads.example.net
||doubleclick.net^
@@||keep.example.com^
"""
        blocked, allowed, stats = parse_list(text)
        self.assertIn("tracker.example.com", blocked)
        self.assertIn("ads.example.net", blocked)
        self.assertIn("doubleclick.net", blocked)
        self.assertEqual(allowed, ["keep.example.com"])
        self.assertGreaterEqual(stats.extracted, 3)


if __name__ == "__main__":
    unittest.main()
