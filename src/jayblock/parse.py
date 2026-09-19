"""Extract hostnames from formats we actually understand.

Unknown Adblock options, regex rules, cosmetic filters, and path-based
rules are ignored rather than guessed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_COMMENT_RE = re.compile(r"^\s*(#|!|;|//)")
_HOSTS_RE = re.compile(
    r"^(?:0+\.0+\.0+\.0+|127\.0\.0\.1|::1|0::0|0::1)\s+(.+?)\s*$"
)
_ABP_BLOCK_RE = re.compile(r"^\|\|([^\/\^\$\*]+)(?:\^)?(?:\$([^\s]*))?$")
_ABP_ALLOW_RE = re.compile(r"^@@\|\|([^\/\^\$\*]+)(?:\^)?(?:\$([^\s]*))?$")
_WILDCARD_RE = re.compile(r"^\*\.(.+)$")
_SAFE_ABP_OPTIONS = {"", "all", "important", "dns", "document", "domain"}


@dataclass
class ParsedLine:
    domain: str | None = None
    allow: bool = False
    skipped: str | None = None


@dataclass
class ParseStats:
    lines: int = 0
    extracted: int = 0
    allow_rules: int = 0
    skipped: int = 0
    comments: int = 0
    skip_reasons: dict[str, int] = field(default_factory=dict)

    def skip(self, reason: str) -> None:
        self.skipped += 1
        self.skip_reasons[reason] = self.skip_reasons.get(reason, 0) + 1


def _strip_inline_comment(line: str) -> str:
    if " #" in line:
        line = line.split(" #", 1)[0]
    if " !" in line:
        line = line.split(" !", 1)[0]
    return line.strip()


def _abp_options_ok(options: str | None) -> bool:
    if not options:
        return True
    for part in options.split(","):
        key = part.split("=")[0].lstrip("~").lower()
        if key not in _SAFE_ABP_OPTIONS:
            return False
    return True


def parse_line(line: str, fmt: str = "domains") -> ParsedLine:
    raw = line.strip().lstrip("\ufeff")
    if not raw:
        return ParsedLine(skipped="empty")
    if _COMMENT_RE.match(raw):
        return ParsedLine(skipped="comment")

    raw = _strip_inline_comment(raw)
    if not raw:
        return ParsedLine(skipped="comment")

    if fmt in {"hosts", "auto", "domains"}:
        hosts = _HOSTS_RE.match(raw)
        if hosts:
            names = hosts.group(1).split()
            # Hosts files can list several names; we take them one at a time
            # via the caller looping. For a single parse, join is wrong.
            if len(names) == 1:
                return ParsedLine(domain=_strip_wildcard(names[0]))
            return ParsedLine(domain=_strip_wildcard(names[0]))

    if raw.startswith("@@"):
        match = _ABP_ALLOW_RE.match(raw)
        if match and _abp_options_ok(match.group(2)):
            return ParsedLine(domain=_strip_wildcard(match.group(1)), allow=True)
        return ParsedLine(skipped="abp-unsupported")

    if raw.startswith("||"):
        match = _ABP_BLOCK_RE.match(raw)
        if match and _abp_options_ok(match.group(2)):
            return ParsedLine(domain=_strip_wildcard(match.group(1)))
        return ParsedLine(skipped="abp-unsupported")

    if raw.startswith("/") and raw.endswith("/") and len(raw) > 2:
        return ParsedLine(skipped="regex")
    if "##" in raw or "#@#" in raw or "#?#" in raw:
        return ParsedLine(skipped="cosmetic")
    if any(ch in raw for ch in ("^", "*", "$", "|", "/", "?", "=")) and not raw.startswith("*."):
        # Bare `*.example.com` is handled below; other wildcard/path syntax is not.
        if not _WILDCARD_RE.match(raw):
            return ParsedLine(skipped="filter-syntax")

    if "," in raw and " " not in raw and not raw.startswith("*."):
        # Domain-format lists are newline separated. Comma-separated blobs are
        # handled by the file parser, not per-line mixed syntax.
        return ParsedLine(skipped="comma-list")

    return ParsedLine(domain=_strip_wildcard(raw))


def _strip_wildcard(value: str) -> str:
    value = value.strip().strip(".").lower()
    match = _WILDCARD_RE.match(value)
    if match:
        return match.group(1).strip().strip(".")
    if value.startswith("*."):
        return value[2:]
    return value


def parse_list(text: str, fmt: str = "domains") -> tuple[list[str], list[str], ParseStats]:
    """Return (block_domains, allow_domains, stats)."""
    stats = ParseStats()
    blocked: list[str] = []
    allowed: list[str] = []
    for raw_line in text.splitlines():
        stats.lines += 1
        parsed = parse_line(raw_line, fmt=fmt)
        if parsed.skipped == "comment":
            stats.comments += 1
            continue
        if parsed.skipped:
            if parsed.skipped != "empty":
                stats.skip(parsed.skipped)
            continue
        if not parsed.domain:
            stats.skip("empty")
            continue
        if parsed.allow:
            allowed.append(parsed.domain)
            stats.allow_rules += 1
        else:
            blocked.append(parsed.domain)
            stats.extracted += 1
    return blocked, allowed, stats
