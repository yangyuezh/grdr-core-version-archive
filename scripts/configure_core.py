#!/usr/bin/env python3
"""Register this immutable GRDR Core clone for installed Skill launchers."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile


CORE_ROOT = Path(__file__).resolve().parents[1]
GIB = 1024 ** 3
GITHUB_RELEASE_ASSET_HARD_MAX_BYTES = 2 * GIB - 1


def require_external(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if resolved == CORE_ROOT or CORE_ROOT in resolved.parents:
        raise ValueError(f"{label} must be outside the immutable GRDR Core repository")
    return resolved


def write_runtime_config(
    snapshot_cache_root: Path | None = None,
    github_observation_max_gib: float | None = None,
) -> Path:
    configured_state = os.environ.get("GRDR_STATE_ROOT")
    state = require_external(
        Path(configured_state) if configured_state else Path.home() / ".grdr",
        "GRDR_STATE_ROOT",
    )
    state.mkdir(parents=True, exist_ok=True)
    config_path = state / "config.json"
    if config_path.is_file():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid existing GRDR runtime configuration: {config_path}") from exc
        if not isinstance(config, dict):
            raise ValueError(f"invalid existing GRDR runtime configuration: {config_path}")
    else:
        config = {}
    config["schema_version"] = "1.2.0"
    if snapshot_cache_root is not None:
        config["snapshot_cache_root"] = str(
            require_external(snapshot_cache_root, "snapshot cache root")
        )
        config.pop("elements_root", None)
    if github_observation_max_gib is not None:
        policy = config.setdefault("storage_capacity_policy", {})
        if not isinstance(policy, dict):
            raise ValueError("existing storage_capacity_policy must be an object")
        policy["github_release_observation_max_bytes"] = round(github_observation_max_gib * GIB)
        policy.pop("elements_full_mirror_max_bytes", None)
        policy.setdefault("github_release_asset_max_bytes", GITHUB_RELEASE_ASSET_HARD_MAX_BYTES)
        github_limit = policy.get("github_release_observation_max_bytes", 5 * GIB)
        if not isinstance(github_limit, int) or isinstance(github_limit, bool) or github_limit <= 0:
            raise ValueError("storage capacity limits must be positive byte counts")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".config.", suffix=".tmp", dir=config_path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(config, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, config_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    return config_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_codex_root = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    parser.add_argument("--pointer", type=Path, default=default_codex_root / "grdr-core-root")
    parser.add_argument(
        "--snapshot-cache-root",
        type=Path,
        help="Optional disposable local cache for expanded GitHub snapshots",
    )
    parser.add_argument(
        "--github-observation-max-gib",
        type=float,
        help="Maximum total mirrored observation GiB assigned to one GitHub Release",
    )
    args = parser.parse_args()
    pointer = args.pointer.expanduser().resolve()
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(str(CORE_ROOT.resolve()) + "\n", encoding="utf-8")
    print(f"Configured GRDR Core: {CORE_ROOT.resolve()}")
    print(f"Pointer: {pointer}")
    for name, value in (
        ("--github-observation-max-gib", args.github_observation_max_gib),
    ):
        if value is not None and value <= 0:
            parser.error(f"{name} must be greater than zero")
    if any(value is not None for value in (
        args.snapshot_cache_root,
        args.github_observation_max_gib,
    )):
        config_path = write_runtime_config(
            args.snapshot_cache_root,
            args.github_observation_max_gib,
        )
        if args.snapshot_cache_root is not None:
            print(
                "Snapshot cache root: "
                f"{require_external(args.snapshot_cache_root, 'snapshot cache root')}"
            )
        if args.github_observation_max_gib is not None:
            print(f"GitHub observation limit: {args.github_observation_max_gib:g} GiB")
        print(f"Runtime configuration: {config_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
