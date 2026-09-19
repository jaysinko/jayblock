"""Minimal YAML loader with a PyYAML fast path."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_yaml(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            f"JayBlock requires PyYAML to read {path.name}. "
            "Install with: python3 -m pip install -r requirements.txt"
        ) from exc
    data = yaml.safe_load(text)
    if data is None:
        raise ValueError(f"{path} is empty")
    return data
