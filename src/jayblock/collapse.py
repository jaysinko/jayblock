"""Remove descendant domains that Little Snitch domain matching already covers.

Little Snitch 6 domain blocklists match the listed domain and every hostname
under it. Official docs (accessed 2026-09-18):

https://help.obdev.at/littlesnitch6/concepts-blocklists

Therefore tracker.example.com already blocks metrics.tracker.example.com.
We never invent parent domains, and public-suffix rejection happens earlier.
"""

from __future__ import annotations


def collapse_descendants(
    domains: dict[str, set[str]],
) -> tuple[dict[str, set[str]], int]:
    """Keep the shortest blocked ancestor; merge provenance into it."""
    kept: dict[str, set[str]] = {}
    redundant = 0
    # Shorter (fewer labels) first so parents are inserted before children.
    ordered = sorted(domains, key=lambda d: (d.count("."), d))
    present = set()
    for domain in ordered:
        labels = domain.split(".")
        ancestor = None
        for i in range(1, len(labels)):
            parent = ".".join(labels[i:])
            if parent in present:
                ancestor = parent
                break
        sources = domains[domain]
        if ancestor is not None:
            kept[ancestor].update(sources)
            redundant += 1
            continue
        kept[domain] = set(sources)
        present.add(domain)
    return kept, redundant


def covering_entry(domain: str, blocked: set[str]) -> str | None:
    """Return the blocklist entry that would match this hostname, if any."""
    labels = domain.split(".")
    # Prefer the most specific match (longest suffix in the set).
    for i in range(len(labels)):
        candidate = ".".join(labels[i:])
        if candidate in blocked:
            return candidate
    return None
