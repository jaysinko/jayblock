"""Hostname canonicalization and validation."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass

from jayblock.psl import PublicSuffixList

# RFC 1123 / LDH labels, plus punycode A-labels.
_LABEL_RE = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")
_LOCAL_NAMES = {
    "localhost",
    "local",
    "broadcasthost",
    "ip6-localhost",
    "ip6-loopback",
    "localhost.localdomain",
}


@dataclass(frozen=True)
class NormalizeResult:
    domain: str | None
    error: str | None


def punycode(domain: str) -> str:
    cleaned = domain.strip().rstrip(".").lower()
    return cleaned.encode("idna").decode("ascii")


def looks_like_ip(value: str) -> bool:
    text = value.strip().strip("[]")
    try:
        ipaddress.ip_address(text)
        return True
    except ValueError:
        return False


def is_valid_hostname(domain: str) -> bool:
    if not domain or len(domain) > 253:
        return False
    if domain.endswith("."):
        domain = domain[:-1]
    if looks_like_ip(domain):
        return False
    labels = domain.split(".")
    if len(labels) < 2:
        return False
    return all(_LABEL_RE.match(label) for label in labels)


def canonicalize(raw: str, psl: PublicSuffixList) -> NormalizeResult:
    text = raw.strip().strip(".").lower()
    if not text:
        return NormalizeResult(None, "empty")
    if text in _LOCAL_NAMES:
        return NormalizeResult(None, "localhost")
    if looks_like_ip(text):
        return NormalizeResult(None, "ip-address")
    if "_" in text or " " in text or "/" in text or ":" in text:
        return NormalizeResult(None, "malformed")
    try:
        ascii_domain = punycode(text)
    except (UnicodeError, ValueError):
        return NormalizeResult(None, "idna")
    if psl.is_public_suffix(ascii_domain):
        return NormalizeResult(None, "public-suffix")
    if not is_valid_hostname(ascii_domain):
        return NormalizeResult(None, "invalid-hostname")
    if psl.registrable(ascii_domain) is None:
        return NormalizeResult(None, "not-registrable")
    return NormalizeResult(ascii_domain, None)


def parent_candidates(domain: str) -> list[str]:
    """Return the domain followed by each ancestor, longest first."""
    labels = domain.split(".")
    return [".".join(labels[i:]) for i in range(len(labels))]
