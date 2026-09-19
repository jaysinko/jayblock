"""Allowlist matching. Allowlisted names override every upstream source."""

from __future__ import annotations

from pathlib import Path

from jayblock.normalize import canonicalize, punycode
from jayblock.psl import PublicSuffixList


def _allow_entry(raw: str, psl: PublicSuffixList) -> tuple[str | None, str | None]:
    text = raw.strip().strip(".").lower()
    if not text:
        return None, "empty"
    try:
        ascii_domain = punycode(text)
    except (UnicodeError, ValueError):
        return None, "idna"
    if psl.is_public_suffix(ascii_domain):
        # Allowlisting a public suffix (github.io, githubusercontent.com)
        # exempts every name under that namespace.
        return ascii_domain, None
    result = canonicalize(ascii_domain, psl)
    return result.domain, result.error


def load_allowlist(path: Path, psl: PublicSuffixList) -> tuple[set[str], list[str]]:
    """Return (canonical domains, parse errors)."""
    domains: set[str] = set()
    errors: list[str] = []
    if not path.exists():
        return domains, [f"missing allowlist: {path}"]
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        domain, error = _allow_entry(line.split("#", 1)[0].strip(), psl)
        if domain is None:
            errors.append(f"{path.name}:{lineno}: {line!r} ({error})")
            continue
        domains.add(domain)
    return domains, errors


def is_allowlisted(domain: str, allow: set[str]) -> str | None:
    """Return the matching allowlist entry, if any."""
    labels = domain.split(".")
    for i in range(len(labels)):
        candidate = ".".join(labels[i:])
        if candidate in allow:
            return candidate
    return None


def apply_allowlist(
    domains: dict[str, set[str]], allow: set[str]
) -> tuple[dict[str, set[str]], int, dict[str, int]]:
    """Remove allowlisted domains and their descendants.

    Returns (kept, removed_count, removals_by_allow_entry).
    """
    kept: dict[str, set[str]] = {}
    removed = 0
    by_entry: dict[str, int] = {}
    for domain, sources in domains.items():
        hit = is_allowlisted(domain, allow)
        if hit:
            removed += 1
            by_entry[hit] = by_entry.get(hit, 0) + 1
            continue
        kept[domain] = sources
    return kept, removed, by_entry
