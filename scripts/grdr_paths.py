#!/usr/bin/env python3
"""Resolve immutable GRDR Core paths and mutable GRDR state paths."""

from __future__ import annotations

import json
import os
from pathlib import Path


CORE_ROOT = Path(__file__).resolve().parents[1]
CORE_REGISTRY_ROOT = CORE_ROOT / "registry"
REGISTRY_FILENAMES = tuple(sorted(path.name for path in CORE_REGISTRY_ROOT.glob("*.jsonl")))
GIB = 1024 ** 3
GITHUB_RELEASE_ASSET_HARD_MAX_BYTES = 2 * GIB - 1
DEFAULT_STORAGE_CAPACITY_POLICY = {
    "github_release_observation_max_bytes": 5 * GIB,
    "elements_full_mirror_max_bytes": 10 * GIB,
    "github_release_asset_max_bytes": GITHUB_RELEASE_ASSET_HARD_MAX_BYTES,
}


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


def _runtime_config() -> dict:
    config_path = runtime_config_file()
    if not config_path.is_file():
        return {}
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid GRDR runtime configuration: {config_path}") from exc
    if not isinstance(config, dict):
        raise ValueError(f"invalid GRDR runtime configuration: {config_path}")
    return config


def elements_root() -> Path:
    """Return the persisted Elements root, with environment override support."""

    configured = os.environ.get("GRDR_ELEMENTS_ROOT")
    if configured:
        return _require_external(Path(configured), "GRDR_ELEMENTS_ROOT")
    config_path = runtime_config_file()
    config = _runtime_config()
    value = config.get("elements_root")
    if value is not None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"invalid elements_root in GRDR runtime configuration: {config_path}")
        return _require_external(Path(value), "configured elements_root")
    return _require_external(state_root() / "elements", "default elements root")


def storage_capacity_policy() -> dict[str, int | str]:
    """Return deployment-local observation storage thresholds.

    These thresholds classify and constrain observation replication only. They
    never reduce the Plan-locked knowledge scope.
    """

    values = dict(DEFAULT_STORAGE_CAPACITY_POLICY)
    configured = _runtime_config().get("storage_capacity_policy", {})
    if not isinstance(configured, dict):
        raise ValueError("storage_capacity_policy in GRDR runtime configuration must be an object")
    for key in (
        "github_release_observation_max_bytes",
        "elements_full_mirror_max_bytes",
        "github_release_asset_max_bytes",
    ):
        if key in configured:
            value = configured[key]
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"storage capacity setting {key} must be a positive integer")
            values[key] = value
    environment_overrides = {
        "github_release_observation_max_bytes": "GRDR_GITHUB_OBSERVATION_MAX_BYTES",
        "elements_full_mirror_max_bytes": "GRDR_ELEMENTS_FULL_MIRROR_MAX_BYTES",
        "github_release_asset_max_bytes": "GRDR_GITHUB_RELEASE_ASSET_MAX_BYTES",
    }
    used_environment_override = False
    for key, environment_name in environment_overrides.items():
        raw = os.environ.get(environment_name)
        if raw is None:
            continue
        try:
            value = int(raw)
        except ValueError as exc:
            raise ValueError(f"{environment_name} must be a positive integer byte count") from exc
        if value < 1:
            raise ValueError(f"{environment_name} must be a positive integer byte count")
        values[key] = value
        used_environment_override = True
    if values["github_release_asset_max_bytes"] > GITHUB_RELEASE_ASSET_HARD_MAX_BYTES:
        raise ValueError(
            "github_release_asset_max_bytes cannot exceed GitHub's under-2-GiB per-file limit"
        )
    values["source"] = (
        "environment_override"
        if used_environment_override
        else "external_config"
        if "storage_capacity_policy" in _runtime_config()
        else "core_default"
    )
    return values


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
