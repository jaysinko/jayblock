"""Build JayBlock domain lists from untrusted upstream sources."""

from __future__ import annotations

import gzip
import hashlib
import json
import shutil
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jayblock.allowlist import apply_allowlist, load_allowlist
from jayblock.collapse import collapse_descendants
from jayblock.configload import load_yaml
from jayblock.fetch import FetchError, fetch_source
from jayblock.normalize import canonicalize
from jayblock.parse import parse_list
from jayblock.paths import (
    ALLOWLIST_PATH,
    DIST,
    POLICY_PATH,
    PSL_PATH,
    ROOT,
    SOURCES_PATH,
)
from jayblock.psl import PublicSuffixList

HEADER_PREFIX = "JayBlock"


@dataclass
class ProfileBuild:
    profile: str
    domains: dict[str, set[str]]
    stats: dict[str, Any]
    text: str
    fingerprint: str


@dataclass
class BuildResult:
    profiles: dict[str, ProfileBuild] = field(default_factory=dict)
    generated_at: str = ""
    default_profile: str = "aggressive"
    errors: list[str] = field(default_factory=list)


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    return load_yaml(path)


def load_sources(path: Path = SOURCES_PATH) -> dict[str, dict[str, Any]]:
    data = load_yaml(path)
    sources = {}
    for item in data["sources"]:
        sources[item["id"]] = item
    return sources


def _source_ids_for_profile(policy: dict[str, Any], profile: str) -> list[str]:
    try:
        return list(policy["profiles"][profile]["sources"])
    except KeyError as exc:
        raise SystemExit(f"unknown profile {profile!r}") from exc


def _write_list(profile: str, domains: list[str], generated_at: str, fingerprint: str) -> str:
    lines = [
        f"# {HEADER_PREFIX} {profile.capitalize()}",
        "# Machine-wide privacy, advertising, tracking, and malware blocklist",
        "# for Little Snitch 6. Domain format: each name blocks itself and all",
        "# hostnames under it. Do not convert this file to /etc/hosts syntax.",
        "# https://github.com/jaysinko/jayblock",
        "# License: GPL-3.0",
        f"# Profile: {profile}",
        f"# Generated: {generated_at}",
        f"# Domains: {len(domains)}",
        f"# Fingerprint: sha256:{fingerprint}",
        "#",
    ]
    lines.extend(domains)
    lines.append("")
    return "\n".join(lines)


def _fingerprint(domains: list[str]) -> str:
    payload = "\n".join(domains).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _provenance_payload(
    profile: str,
    domains: dict[str, set[str]],
    source_meta: dict[str, dict[str, Any]],
    generated_at: str,
) -> bytes:
    source_ids = sorted({sid for srcs in domains.values() for sid in srcs})
    index = {sid: i for i, sid in enumerate(source_ids)}
    sources = []
    for sid in source_ids:
        meta = source_meta.get(sid, {})
        sources.append(
            {
                "id": sid,
                "name": meta.get("name", sid),
                "categories": meta.get("categories", []),
                "homepage": meta.get("homepage"),
            }
        )
    blocked = {domain: sorted(index[s] for s in srcs) for domain, srcs in sorted(domains.items())}
    body = {
        "v": 1,
        "profile": profile,
        "generated_at": generated_at,
        "src": sources,
        "d": blocked,
    }
    raw = json.dumps(body, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return gzip.compress(raw, compresslevel=9, mtime=0)


def build_profile(
    profile: str,
    *,
    policy: dict[str, Any],
    sources: dict[str, dict[str, Any]],
    fetched: dict[str, str],
    psl: PublicSuffixList,
    allow: set[str],
    generated_at: str,
) -> ProfileBuild:
    started = time.perf_counter()
    source_ids = _source_ids_for_profile(policy, profile)
    extracted_total = 0
    valid_raw = 0
    invalid = Counter()
    combined: dict[str, set[str]] = {}
    source_stats: list[dict[str, Any]] = []
    extra_allows: set[str] = set()

    for source_id in source_ids:
        source = sources[source_id]
        text = fetched[source_id]
        blocked, allowed, parse_stats = parse_list(text, fmt=source.get("format", "domains"))
        extracted_total += parse_stats.extracted
        accepted = 0
        for raw in blocked:
            result = canonicalize(raw, psl)
            if result.domain is None:
                invalid[result.error or "invalid"] += 1
                continue
            accepted += 1
            valid_raw += 1
            combined.setdefault(result.domain, set()).add(source_id)
        for raw in allowed:
            result = canonicalize(raw, psl)
            if result.domain:
                extra_allows.add(result.domain)
        min_entries = int(source.get("sanity", {}).get("min_entries", 0))
        if min_entries and accepted < min_entries:
            raise SystemExit(
                f"{source_id}: only {accepted} accepted domains, expected >= {min_entries}"
            )
        source_stats.append(
            {
                "id": source_id,
                "name": source.get("name", source_id),
                "extracted": parse_stats.extracted,
                "accepted": accepted,
                "parse_skipped": parse_stats.skipped,
                "allow_rules": parse_stats.allow_rules,
            }
        )

    unique_valid = len(combined)
    duplicates_removed = valid_raw - unique_valid
    effective_allow = set(allow) | extra_allows
    after_allow, allowlisted, allow_hits = apply_allowlist(combined, effective_allow)
    collapse = bool(policy.get("collapse_redundant_subdomains", True))
    if collapse:
        after_collapse, redundant = collapse_descendants(after_allow)
    else:
        after_collapse, redundant = after_allow, 0

    ordered = sorted(after_collapse)
    fingerprint = _fingerprint(ordered)
    text = _write_list(profile, ordered, generated_at, fingerprint)
    elapsed = round(time.perf_counter() - started, 3)
    stats = {
        "profile": profile,
        "upstream_entries": extracted_total,
        "valid_domains": unique_valid,
        "duplicates_removed": duplicates_removed,
        "invalid_rejected": dict(invalid),
        "allowlisted": allowlisted,
        "allowlist_hits": allow_hits,
        "redundant_domains_removed": redundant,
        "final_domains": len(ordered),
        "file_size_bytes": len(text.encode("utf-8")),
        "build_time_seconds": elapsed,
        "fingerprint": fingerprint,
        "sources": source_stats,
        "collapse_redundant_subdomains": collapse,
    }
    return ProfileBuild(profile, after_collapse, stats, text, fingerprint)


def build(
    *,
    profiles: list[str] | None = None,
    fetch: bool = True,
    write: bool = True,
) -> BuildResult:
    policy = load_policy()
    source_defs = load_sources()
    default_profile = policy.get("default_profile", "aggressive")
    wanted = profiles or list(policy["profiles"])
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    psl = PublicSuffixList(PSL_PATH)
    allow, allow_errors = load_allowlist(ALLOWLIST_PATH, psl)
    if allow_errors:
        raise SystemExit("allowlist errors:\n" + "\n".join(allow_errors))

    needed_ids: list[str] = []
    for profile in wanted:
        for source_id in _source_ids_for_profile(policy, profile):
            if source_id not in needed_ids:
                needed_ids.append(source_id)

    fetched: dict[str, str] = {}
    errors: list[str] = []
    for source_id in needed_ids:
        source = source_defs[source_id]
        try:
            if fetch:
                result = fetch_source(source, timeout=int(source.get("timeout_seconds", 90)))
                fetched[source_id] = result.text
            else:
                from jayblock.paths import CACHE

                cached = CACHE / "upstream" / f"{source_id}.txt"
                if source.get("path"):
                    path = ROOT / source["path"] if not Path(source["path"]).is_absolute() else Path(source["path"])
                    fetched[source_id] = path.read_text(encoding="utf-8-sig")
                elif cached.exists():
                    fetched[source_id] = cached.read_text(encoding="utf-8-sig")
                else:
                    raise FetchError(f"no cache for {source_id}")
        except (FetchError, OSError) as exc:
            message = f"{source_id}: {exc}"
            if source.get("required", True):
                raise SystemExit(f"required source failed: {message}") from exc
            errors.append(message)

    result = BuildResult(generated_at=generated_at, default_profile=default_profile, errors=errors)
    previous_stats = {}
    stats_path = DIST / "stats.json"
    if stats_path.exists():
        try:
            previous_stats = json.loads(stats_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous_stats = {}

    for profile in wanted:
        built = build_profile(
            profile,
            policy=policy,
            sources=source_defs,
            fetched=fetched,
            psl=psl,
            allow=allow,
            generated_at=generated_at,
        )
        _guard_against_broken_output(profile, built, previous_stats)
        result.profiles[profile] = built

    if write:
        _write_artifacts(result, source_defs)
    return result


def _guard_against_broken_output(
    profile: str, built: ProfileBuild, previous_stats: dict[str, Any]
) -> None:
    if built.stats["final_domains"] < 1000:
        raise SystemExit(f"{profile}: refusing to publish an almost-empty list")
    prev_profiles = previous_stats.get("profiles", {})
    prev = prev_profiles.get(profile) or (
        previous_stats if previous_stats.get("profile") == profile else None
    )
    if not prev:
        return
    prev_count = int(prev.get("final_domains", 0))
    if not prev_count:
        return
    new_count = built.stats["final_domains"]
    if new_count < prev_count * 0.5:
        raise SystemExit(
            f"{profile}: domain count dropped {prev_count} -> {new_count}; refusing to replace last known-good list"
        )
    if new_count > prev_count * 3:
        raise SystemExit(
            f"{profile}: domain count jumped {prev_count} -> {new_count}; refusing unexplained explosion"
        )


def _write_artifacts(result: BuildResult, source_defs: dict[str, dict[str, Any]]) -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    (DIST / "optional").mkdir(parents=True, exist_ok=True)
    default = result.profiles[result.default_profile]
    stats = {
        "generated_at": result.generated_at,
        "profile": default.profile,
        "upstream_entries": default.stats["upstream_entries"],
        "valid_domains": default.stats["valid_domains"],
        "duplicates_removed": default.stats["duplicates_removed"],
        "redundant_domains_removed": default.stats["redundant_domains_removed"],
        "allowlisted": default.stats["allowlisted"],
        "final_domains": default.stats["final_domains"],
        "file_size_bytes": default.stats["file_size_bytes"],
        "build_time_seconds": default.stats["build_time_seconds"],
        "fingerprint": default.fingerprint,
        "profiles": {name: built.stats for name, built in result.profiles.items()},
        "errors": result.errors,
    }
    (DIST / "stats.json").write_text(json.dumps(stats, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for name, built in result.profiles.items():
        (DIST / f"{name}.txt").write_text(built.text, encoding="utf-8")
        payload = _provenance_payload(name, built.domains, source_defs, result.generated_at)
        (DIST / f"provenance-{name}.json.gz").write_bytes(payload)
    # Compact alias for the default profile, as specified in the project layout.
    default_prov = DIST / f"provenance-{result.default_profile}.json.gz"
    (DIST / "provenance.json.gz").write_bytes(default_prov.read_bytes())
    optional_src = ROOT / "config" / "optional-local-apps.lsrules"
    if optional_src.exists():
        shutil.copyfile(optional_src, DIST / "optional" / "local-apps.lsrules")
    _write_index(result)


def _write_index(result: BuildResult) -> None:
    default = result.profiles[result.default_profile]
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>JayBlock</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font: 16px/1.45 -apple-system, BlinkMacSystemFont, sans-serif; margin: 2rem; max-width: 42rem; }}
    code {{ background: #f4f4f4; padding: 0.1em 0.3em; }}
  </style>
</head>
<body>
  <h1>JayBlock</h1>
  <p>Machine-wide privacy and advertising blocklists for Little Snitch 6.</p>
  <p>Default profile: <strong>{result.default_profile}</strong> ({default.stats["final_domains"]} domains).</p>
  <ul>
    <li><a href="aggressive.txt">aggressive.txt</a> (subscribe to this)</li>
    <li><a href="balanced.txt">balanced.txt</a></li>
    <li><a href="nuclear.txt">nuclear.txt</a> (experimental)</li>
    <li><a href="stats.json">stats.json</a></li>
  </ul>
  <p>Source: <a href="https://github.com/jaysinko/jayblock">github.com/jaysinko/jayblock</a></p>
</body>
</html>
"""
    (DIST / "index.html").write_text(html, encoding="utf-8")
