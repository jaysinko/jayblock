from __future__ import annotations

import unittest

import bootstrap  # noqa: F401

from jayblock.paths import PSL_PATH
from jayblock.psl import PublicSuffixList


class PublicSuffixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.psl = PublicSuffixList(PSL_PATH)

    def test_com(self) -> None:
        self.assertEqual(self.psl.public_suffix("example.com"), "com")
        self.assertEqual(self.psl.registrable("www.example.com"), "example.com")
        self.assertTrue(self.psl.is_public_suffix("com"))
        self.assertFalse(self.psl.is_public_suffix("example.com"))

    def test_co_uk(self) -> None:
        self.assertEqual(self.psl.public_suffix("bbc.co.uk"), "co.uk")
        self.assertEqual(self.psl.registrable("www.bbc.co.uk"), "bbc.co.uk")
        self.assertTrue(self.psl.is_public_suffix("co.uk"))

    def test_github_io(self) -> None:
        self.assertTrue(self.psl.is_public_suffix("github.io"))
        self.assertEqual(self.psl.registrable("foo.github.io"), "foo.github.io")
        self.assertIsNone(self.psl.registrable("github.io"))


if __name__ == "__main__":
    unittest.main()
