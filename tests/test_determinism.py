from __future__ import annotations

import hashlib
import unittest

import bootstrap  # noqa: F401

from jayblock.generate import _fingerprint, _write_list


class DeterminismTests(unittest.TestCase):
    def test_same_domains_same_fingerprint(self) -> None:
        domains = ["ads.example.com", "tracker.example.net"]
        self.assertEqual(_fingerprint(domains), _fingerprint(list(domains)))
        self.assertNotEqual(_fingerprint(domains), _fingerprint(list(reversed(domains))))

    def test_header_does_not_change_fingerprint(self) -> None:
        domains = ["ads.example.com"]
        fp = _fingerprint(domains)
        text_a = _write_list("aggressive", domains, "2026-01-01T00:00:00Z", fp)
        text_b = _write_list("aggressive", domains, "2026-12-31T00:00:00Z", fp)
        body_a = "\n".join(line for line in text_a.splitlines() if not line.startswith("#") and line)
        body_b = "\n".join(line for line in text_b.splitlines() if not line.startswith("#") and line)
        self.assertEqual(body_a, body_b)
        self.assertEqual(hashlib.sha256(body_a.encode()).hexdigest(), fp)


if __name__ == "__main__":
    unittest.main()
