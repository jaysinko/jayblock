"""Explain why a domain is blocked, allowlisted, or neither."""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

from jayblock.allowlist import is_allowlisted, load_allowlist
from jayblock.collapse import covering_entry
from jayblock.normalize import canonicalize
from jayblock.paths import ALLOWLIST_PATH, DIST, PSL_PATH
from jayblock.psl import PublicSuffixList


def load_blocked(list_path: Path) -> set[str]:
    blocked: set[str] = set()
    for line in list_path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        blocked.add(line.strip().lower())
    return blocked


def load_provenance(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def explain_domain(domain: str, *, profile: str = "aggressive", dist: Path = DIST) -> str:
    psl = PublicSuffixList(PSL_PATH)
    result = canonicalize(domain, psl)
    if result.domain is None:
        # Still try punycode-less lookup for debugging.
        query = domain.strip().lower().rstrip(".")
        note = f"({result.error})"
    else:
        query = result.domain
        note = ""

    allow, _ = load_allowlist(ALLOWLIST_PATH, psl)
    allow_hit = is_allowlisted(query, allow) if query else None
    list_path = dist / f"{profile}.txt"
    if not list_path.exists():
        return f"ERROR\nMissing artifact: {list_path}"
    blocked = load_blocked(list_path)
    cover = covering_entry(query, blocked) if query else None

    prov_path = dist / f"provenance-{profile}.json.gz"
    if not prov_path.exists():
        prov_path = dist / "provenance.json.gz"
    provenance = load_provenance(prov_path) if prov_path.exists() else None

    lines: list[str] = []
    if allow_hit:
        lines.append("ALLOWLISTED")
        if note:
            lines.append(note)
        lines.append(f"Query: {query}")
        lines.append(f"Allowlist entry: {allow_hit}")
        if cover:
            lines.append(
                f"Note: {cover} is present in {profile}, but the allowlist wins in JayBlock builds."
            )
        return "\n".join(lines) + "\n"

    if cover:
        lines.append("BLOCKED")
        if note:
            lines.append(note)
        lines.append(f"Query: {query}")
        if cover != query:
            lines.append(f"Matched via parent: {cover}")
        else:
            lines.append(f"Matched: {cover}")
        if provenance and cover in provenance.get("d", {}):
            src_meta = provenance.get("src", [])
            indexes = provenance["d"][cover]
            names = []
            categories: list[str] = []
            for idx in indexes:
                if 0 <= idx < len(src_meta):
                    item = src_meta[idx]
                    names.append(item.get("name") or item.get("id"))
                    categories.extend(item.get("categories") or [])
            lines.append("Sources:")
            for name in names:
                lines.append(f"- {name}")
            if categories:
                lines.append("Categories:")
                for cat in sorted(set(categories)):
                    lines.append(f"- {cat}")
        else:
            lines.append("Sources: (provenance unavailable)")
        return "\n".join(lines) + "\n"

    lines.append("NOT BLOCKED")
    if note:
        lines.append(note)
    lines.append(f"Query: {query or domain}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Explain a JayBlock domain decision")
    parser.add_argument("domain")
    parser.add_argument("--profile", default="aggressive")
    args = parser.parse_args(argv)
    sys.stdout.write(explain_domain(args.domain, profile=args.profile))
    return 0
