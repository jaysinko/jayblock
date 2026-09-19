from __future__ import annotations

import json
import unittest
from pathlib import Path

import bootstrap  # noqa: F401

from jayblock.collapse import covering_entry
from jayblock.paths import DIST, MUST_BLOCK_PATH, PROTECTED_PATH, ROOT


def _read_names(path: Path) -> list[str]:
    names: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        names.append(text.split("#", 1)[0].strip().lower())
    return names


def _load_blocked(profile: str = "aggressive") -> set[str]:
    path = DIST / f"{profile}.txt"
    blocked: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        blocked.add(line.strip().lower())
    return blocked


class DistArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.list_path = DIST / "aggressive.txt"
        if not cls.list_path.exists():
            raise unittest.SkipTest("dist/aggressive.txt missing; run tools/build.py first")
        cls.blocked = _load_blocked("aggressive")
        cls.text = cls.list_path.read_text(encoding="utf-8")

    def test_not_empty(self) -> None:
        self.assertGreater(len(self.blocked), 10000)
        self.assertGreater(self.list_path.stat().st_size, 100_000)

    def test_header_is_domain_list_not_hosts_or_abp(self) -> None:
        self.assertIn("# JayBlock Aggressive", self.text)
        self.assertNotIn("0.0.0.0 ", self.text)
        self.assertNotIn("||", self.text)
        self.assertNotIn("denied-remote-domains", self.text)

    def test_sorted_unique(self) -> None:
        domains = [line for line in self.text.splitlines() if line and not line.startswith("#")]
        self.assertEqual(domains, sorted(domains))
        self.assertEqual(len(domains), len(set(domains)))

    def test_no_wildcard_or_hosts_syntax(self) -> None:
        for domain in list(self.blocked)[:5000]:
            self.assertFalse(domain.startswith("*."))
            self.assertFalse(domain.startswith("www.www."))

    def test_must_block(self) -> None:
        missing = []
        for name in _read_names(MUST_BLOCK_PATH):
            if covering_entry(name, self.blocked) is None:
                missing.append(name)
        self.assertEqual(missing, [], f"expected blocked, missing: {missing}")

    def test_protected_not_blocked(self) -> None:
        hits = []
        for name in _read_names(PROTECTED_PATH):
            cover = covering_entry(name, self.blocked)
            if cover is not None:
                hits.append(f"{name} matched by {cover}")
        self.assertEqual(hits, [], "critical infrastructure blocked:\n" + "\n".join(hits))

    def test_stats_json(self) -> None:
        stats = json.loads((DIST / "stats.json").read_text(encoding="utf-8"))
        self.assertEqual(stats["profile"], "aggressive")
        self.assertGreater(stats["final_domains"], 10000)
        self.assertEqual(stats["final_domains"], len(self.blocked))
        self.assertGreater(stats["file_size_bytes"], 100_000)
        self.assertIn("aggressive", stats["profiles"])
        self.assertIn("balanced", stats["profiles"])
        self.assertIn("nuclear", stats["profiles"])

    def test_provenance_exists(self) -> None:
        path = DIST / "provenance.json.gz"
        self.assertTrue(path.exists())
        self.assertGreater(path.stat().st_size, 1000)

    def test_profiles_exist(self) -> None:
        for name in ("balanced", "aggressive", "nuclear"):
            path = DIST / f"{name}.txt"
            self.assertTrue(path.exists(), path)
            self.assertGreater(path.stat().st_size, 50_000)

    def test_nuclear_is_superset_size(self) -> None:
        nuclear = len(_load_blocked("nuclear"))
        aggressive = len(self.blocked)
        balanced = len(_load_blocked("balanced"))
        self.assertGreaterEqual(aggressive, balanced)
        self.assertGreaterEqual(nuclear, aggressive)

    def test_no_repo_secrets(self) -> None:
        suspicious = ("BEGIN PRIVATE KEY", "AKIA", "ghp_", "gho_", "xoxb-")
        skip_parts = {"cache", ".git", "tests", "dist"}
        for path in ROOT.rglob("*"):
            if not path.is_file() or path.suffix not in {".txt", ".yml", ".yaml", ".py", ".md", ".json"}:
                continue
            if any(part in skip_parts for part in path.parts):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for token in suspicious:
                self.assertNotIn(token, text, f"{path} contains {token}")


if __name__ == "__main__":
    unittest.main()
