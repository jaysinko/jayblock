"""Repository path helpers."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
CONFIG = ROOT / "config"
DIST = ROOT / "dist"
CACHE = ROOT / "cache"
VENDOR = ROOT / "vendor"
TESTS = ROOT / "tests"
PSL_PATH = VENDOR / "public_suffix_list.dat"
SOURCES_PATH = CONFIG / "sources.yml"
POLICY_PATH = CONFIG / "policy.yml"
ALLOWLIST_PATH = CONFIG / "allowlist.txt"
EXTRAS_PATH = CONFIG / "extras.txt"
PROTECTED_PATH = CONFIG / "protected_domains.txt"
MUST_BLOCK_PATH = CONFIG / "must_block.txt"
