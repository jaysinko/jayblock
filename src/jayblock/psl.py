"""Mozilla Public Suffix List matching.

Implements the algorithm from https://publicsuffix.org/list/ so parent-domain
collapsing never crosses a public-suffix boundary (for example github.io).
"""

from __future__ import annotations

from pathlib import Path


class PublicSuffixList:
    def __init__(self, path: Path) -> None:
        self._normal: set[tuple[str, ...]] = set()
        self._wildcard: set[tuple[str, ...]] = set()
        self._exception: set[tuple[str, ...]] = set()
        self._load(path)

    def _load(self, path: Path) -> None:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("//"):
                continue
            rule = line.lower()
            if rule.startswith("!"):
                self._exception.add(tuple(reversed(rule[1:].split("."))))
            elif rule.startswith("*."):
                self._wildcard.add(tuple(reversed(rule[2:].split("."))))
            else:
                self._normal.add(tuple(reversed(rule.split("."))))

    def public_suffix(self, domain: str) -> str:
        labels = domain.lower().rstrip(".").split(".")
        n = len(labels)
        if n == 0 or labels == [""]:
            return domain
        rev = labels[::-1]
        exception_len: int | None = None
        longest_normal = 0
        longest_wild = 0
        for length in range(1, n + 1):
            key = tuple(rev[:length])
            if key in self._exception:
                exception_len = length
            if key in self._normal:
                longest_normal = length
            if length >= 2 and tuple(rev[: length - 1]) in self._wildcard:
                longest_wild = max(longest_wild, length)
        if exception_len is not None:
            ps_len = max(exception_len - 1, 1)
        else:
            ps_len = max(longest_normal, longest_wild, 1)
        ps_len = min(ps_len, n)
        return ".".join(labels[n - ps_len :])

    def is_public_suffix(self, domain: str) -> bool:
        cleaned = domain.lower().rstrip(".")
        return bool(cleaned) and self.public_suffix(cleaned) == cleaned

    def registrable(self, domain: str) -> str | None:
        """Return eTLD+1, or None if the domain is a public suffix."""
        cleaned = domain.lower().rstrip(".")
        labels = cleaned.split(".")
        suffix = self.public_suffix(cleaned)
        suffix_len = len(suffix.split("."))
        if len(labels) <= suffix_len:
            return None
        return ".".join(labels[len(labels) - suffix_len - 1 :])
