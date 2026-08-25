#!/usr/bin/env python3
"""Resolve immutable GRDR Core paths and mutable GRDR state paths."""

from __future__ import annotations

import json
import os
from pathlib import Path


CORE_ROOT = Path(__file__).resolve().parents[1]
CORE_REGISTRY_ROOT = CORE_ROOT / "registry"
REGISTRY_FILENAMES = tuple(sorted(path.name for path in CORE_REGISTRY_ROOT.glob("*.jsonl")))


def _require_external(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if resolved == CORE_ROOT or CORE_ROOT in resolved.parents:
        raise ValueError(f"{label} must be outside the immutable GRDR Core repository")
    return resolved


def state_root() -> Path:
    """Return the external mutable-state root, never the Core repository."""

    configured = os.environ.get("GRDR_STATE_ROOT")
    root = Path(configured).expanduser() if configured else Path.home() / ".grdr"
    return _require_external(root, "GRDR_STATE_ROOT")


def runtime_config_file() -> Path:
    """Return the deployment-local GRDR configuration file."""

    return state_root() / "config.json"


def elements_root() -> Path:
    """Return the persisted Elements root, with environment override support."""

    configured = os.environ.get("GRDR_ELEMENTS_ROOT")
    if configured:
        return _require_external(Path(configured), "GRDR_ELEMENTS_ROOT")
    config_path = runtime_config_file()
    if config_path.is_file():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid GRDR runtime configuration: {config_path}") from exc
        if not isinstance(config, dict):
            raise ValueError(f"invalid GRDR runtime configuration: {config_path}")
        value = config.get("elements_root")
        if value is not None:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"invalid elements_root in GRDR runtime configuration: {config_path}")
            return _require_external(Path(value), "configured elements_root")
    return _require_external(state_root() / "elements", "default elements root")


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
