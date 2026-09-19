from __future__ import annotations

import unittest

import bootstrap  # noqa: F401

from jayblock.normalize import canonicalize, is_valid_hostname, looks_like_ip, punycode
from jayblock.paths import PSL_PATH
from jayblock.psl import PublicSuffixList


class NormalizeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.psl = PublicSuffixList(PSL_PATH)

    def test_punycode(self) -> None:
        self.assertEqual(punycode("münchen.de"), "xn--mnchen-3ya.de")

    def test_ip_rejected(self) -> None:
        self.assertTrue(looks_like_ip("127.0.0.1"))
        self.assertTrue(looks_like_ip("::1"))
        self.assertEqual(canonicalize("127.0.0.1", self.psl).error, "ip-address")

    def test_localhost_rejected(self) -> None:
        self.assertEqual(canonicalize("localhost", self.psl).error, "localhost")

    def test_public_suffix_rejected(self) -> None:
        self.assertEqual(canonicalize("com", self.psl).error, "public-suffix")
        self.assertEqual(canonicalize("github.io", self.psl).error, "public-suffix")
        self.assertEqual(canonicalize("co.uk", self.psl).error, "public-suffix")

    def test_github_pages_project_ok(self) -> None:
        result = canonicalize("evil.github.io", self.psl)
        self.assertEqual(result.domain, "evil.github.io")

    def test_valid_domain(self) -> None:
        result = canonicalize("  Ads.Example.COM. ", self.psl)
        self.assertEqual(result.domain, "ads.example.com")
        self.assertTrue(is_valid_hostname(result.domain or ""))

    def test_malformed(self) -> None:
        self.assertIsNotNone(canonicalize("not_a_host.com", self.psl).error)
        self.assertIsNotNone(canonicalize("example", self.psl).error)


if __name__ == "__main__":
    unittest.main()
