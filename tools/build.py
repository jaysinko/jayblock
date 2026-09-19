#!/usr/bin/env python3
"""Build JayBlock artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jayblock.generate import build  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build JayBlock Little Snitch lists")
    parser.add_argument(
        "--profile",
        default="all",
        help="balanced, aggressive, nuclear, or all (default)",
    )
    parser.add_argument("--offline", action="store_true", help="use cached upstream files only")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    profiles = None if args.profile == "all" else [args.profile]
    result = build(profiles=profiles, fetch=not args.offline, write=not args.no_write)
    for name, built in result.profiles.items():
        stats = built.stats
        print(
            f"{name}: {stats['final_domains']} domains "
            f"({stats['file_size_bytes']} bytes, {stats['build_time_seconds']}s)"
        )
    if result.errors:
        print("non-fatal source errors:", file=sys.stderr)
        for err in result.errors:
            print(f"  {err}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
