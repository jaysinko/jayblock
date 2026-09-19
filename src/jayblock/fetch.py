"""Untrusted upstream retrieval with sanity checks."""

from __future__ import annotations

import hashlib
import json
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jayblock.paths import CACHE

USER_AGENT = "JayBlock/1.0 (+https://github.com/jaysinko/jayblock; privacy blocklist builder)"


class FetchError(RuntimeError):
    pass


@dataclass
class FetchResult:
    source_id: str
    url: str
    text: str
    sha256: str
    bytes_len: int
    from_cache: bool
    status: int


def _opener() -> urllib.request.OpenerDirector:
    context = ssl.create_default_context()
    https = urllib.request.HTTPSHandler(context=context)
    return urllib.request.build_opener(https)


def _looks_like_html(payload: bytes) -> bool:
    head = payload.lstrip().lower()[:200]
    return head.startswith(b"<!doctype") or head.startswith(b"<html") or head.startswith(b"<head")


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_manifest(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fetch_bytes(url: str, timeout: int) -> tuple[int, bytes, str]:
    if not url.startswith("https://"):
        raise FetchError(f"refusing non-HTTPS URL: {url}")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/plain,*/*;q=0.1"},
        method="GET",
    )
    opener = _opener()
    try:
        with opener.open(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            final = response.geturl()
            if not final.startswith("https://"):
                raise FetchError(f"redirect left HTTPS: {final}")
            payload = response.read()
            return status, payload, final
    except urllib.error.HTTPError as exc:
        raise FetchError(f"HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise FetchError(f"network error for {url}: {exc.reason}") from exc


def fetch_source(source: dict[str, Any], *, timeout: int = 90, force: bool = False) -> FetchResult:
    source_id = source["id"]
    if source.get("path"):
        path = Path(source["path"])
        if not path.is_absolute():
            from jayblock.paths import ROOT

            path = ROOT / path
        payload = path.read_bytes()
        text = payload.decode("utf-8-sig")
        digest = hashlib.sha256(payload).hexdigest()
        return FetchResult(source_id, str(path), text, digest, len(payload), False, 200)

    cache_dir = CACHE / "upstream"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{source_id}.txt"
    manifest_path = CACHE / "manifest.json"
    manifest = _load_manifest(manifest_path)

    urls = [source["url"], *source.get("fallbacks", [])]
    last_error: Exception | None = None
    payload = b""
    used_url = urls[0]
    status = 0
    for url in urls:
        try:
            status, payload, used_url = fetch_bytes(url, timeout=timeout)
            last_error = None
            break
        except FetchError as exc:
            last_error = exc
            continue
    if last_error is not None and not payload:
        if cache_file.exists() and not force:
            # Do not silently succeed a required source from stale cache during
            # a production publish; callers decide. We still expose the error.
            raise last_error
        raise last_error

    if _looks_like_html(payload):
        raise FetchError(f"{source_id} returned HTML, not a blocklist ({used_url})")
    if not payload.strip():
        raise FetchError(f"{source_id} returned an empty body")

    sanity = source.get("sanity", {})
    size = len(payload)
    min_bytes = int(sanity.get("min_bytes", 0))
    max_bytes = int(sanity.get("max_bytes", 80_000_000))
    if size < min_bytes:
        raise FetchError(f"{source_id} too small: {size} < {min_bytes} bytes")
    if size > max_bytes:
        raise FetchError(f"{source_id} too large: {size} > {max_bytes} bytes")

    previous = manifest.get(source_id, {})
    prev_size = int(previous.get("bytes", 0))
    if prev_size and not source.get("path"):
        shrink = float(sanity.get("max_shrink_ratio", 0.5))
        growth = float(sanity.get("max_growth_ratio", 3.0))
        if size < prev_size * shrink:
            raise FetchError(
                f"{source_id} shrank unexpectedly: {prev_size} -> {size} bytes"
            )
        if size > prev_size * growth:
            raise FetchError(
                f"{source_id} grew unexpectedly: {prev_size} -> {size} bytes"
            )

    text = payload.decode("utf-8-sig")
    digest = hashlib.sha256(payload).hexdigest()
    cache_file.write_bytes(payload)
    manifest[source_id] = {
        "url": used_url,
        "bytes": size,
        "sha256": digest,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": status,
    }
    _save_manifest(manifest_path, manifest)
    return FetchResult(source_id, used_url, text, digest, size, False, status)
