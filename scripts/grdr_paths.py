#!/usr/bin/env python3
"""Resolve immutable GRDR Core paths and mutable GRDR state paths."""

from __future__ import annotations

import os
from pathlib import Path


CORE_ROOT = Path(__file__).resolve().parents[1]
CORE_REGISTRY_ROOT = CORE_ROOT / "registry"
REGISTRY_FILENAMES = tuple(sorted(path.name for path in CORE_REGISTRY_ROOT.glob("*.jsonl")))


def state_root() -> Path:
    """Return the external mutable-state root, never the Core repository."""

    configured = os.environ.get("GRDR_STATE_ROOT")
    root = Path(configured).expanduser() if configured else Path.home() / ".grdr"
    resolved = root.resolve()
    if resolved == CORE_ROOT or CORE_ROOT in resolved.parents:
        raise ValueError(
            "GRDR_STATE_ROOT must be outside the immutable GRDR Core repository"
        )
    return resolved


def ensure_registry_root() -> Path:
    """Create an external registry from Core's empty filename templates."""

    target = state_root() / "registry"
    target.mkdir(parents=True, exist_ok=True)
    for filename in REGISTRY_FILENAMES:
        path = target / filename
        if not path.exists():
            path.write_text("", encoding="utf-8")
    return target


def registry_root() -> Path:
    return ensure_registry_root()


def source_archive_file() -> Path:
    return registry_root() / "source_archives.jsonl"


def deep_map_projects_root() -> Path:
    target = state_root() / "deep_map_projects"
    target.mkdir(parents=True, exist_ok=True)
    return target


def research_projects_root() -> Path:
    target = state_root() / "research_projects"
    target.mkdir(parents=True, exist_ok=True)
    return target
