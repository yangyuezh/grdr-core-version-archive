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
    elements_root: Path | None = None,
    github_observation_max_gib: float | None = None,
    elements_full_mirror_max_gib: float | None = None,
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
    config["schema_version"] = "1.1.0"
    if elements_root is not None:
        config["elements_root"] = str(require_external(elements_root, "elements root"))
    if github_observation_max_gib is not None or elements_full_mirror_max_gib is not None:
        policy = config.setdefault("storage_capacity_policy", {})
        if not isinstance(policy, dict):
            raise ValueError("existing storage_capacity_policy must be an object")
        if github_observation_max_gib is not None:
            policy["github_release_observation_max_bytes"] = round(github_observation_max_gib * GIB)
        if elements_full_mirror_max_gib is not None:
            policy["elements_full_mirror_max_bytes"] = round(elements_full_mirror_max_gib * GIB)
        policy.setdefault("github_release_asset_max_bytes", GITHUB_RELEASE_ASSET_HARD_MAX_BYTES)
        github_limit = policy.get("github_release_observation_max_bytes", 5 * GIB)
        elements_limit = policy.get("elements_full_mirror_max_bytes", 10 * GIB)
        if not all(isinstance(value, int) and not isinstance(value, bool) and value > 0 for value in (github_limit, elements_limit)):
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
        "--elements-root",
        type=Path,
        help="Persist the expanded snapshot root under <GRDR_STATE_ROOT>/config.json",
    )
    parser.add_argument(
        "--github-observation-max-gib",
        type=float,
        help="Maximum total mirrored observation GiB assigned to one GitHub Release",
    )
    parser.add_argument(
        "--elements-full-mirror-max-gib",
        type=float,
        help="Maximum observation GiB treated as one complete Elements mirror",
    )
    args = parser.parse_args()
    pointer = args.pointer.expanduser().resolve()
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(str(CORE_ROOT.resolve()) + "\n", encoding="utf-8")
    print(f"Configured GRDR Core: {CORE_ROOT.resolve()}")
    print(f"Pointer: {pointer}")
    for name, value in (
        ("--github-observation-max-gib", args.github_observation_max_gib),
        ("--elements-full-mirror-max-gib", args.elements_full_mirror_max_gib),
    ):
        if value is not None and value <= 0:
            parser.error(f"{name} must be greater than zero")
    if any(value is not None for value in (
        args.elements_root,
        args.github_observation_max_gib,
        args.elements_full_mirror_max_gib,
    )):
        config_path = write_runtime_config(
            args.elements_root,
            args.github_observation_max_gib,
            args.elements_full_mirror_max_gib,
        )
        if args.elements_root is not None:
            print(f"Elements root: {require_external(args.elements_root, 'elements root')}")
        if args.github_observation_max_gib is not None:
            print(f"GitHub observation limit: {args.github_observation_max_gib:g} GiB")
        if args.elements_full_mirror_max_gib is not None:
            print(f"Elements full-mirror limit: {args.elements_full_mirror_max_gib:g} GiB")
        print(f"Runtime configuration: {config_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
