#!/usr/bin/env python3
"""Register this immutable GRDR Core clone for installed Skill launchers."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile


CORE_ROOT = Path(__file__).resolve().parents[1]


def require_external(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if resolved == CORE_ROOT or CORE_ROOT in resolved.parents:
        raise ValueError(f"{label} must be outside the immutable GRDR Core repository")
    return resolved


def write_runtime_config(elements_root: Path) -> Path:
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
    config.update({
        "schema_version": "1.0.0",
        "elements_root": str(require_external(elements_root, "elements root")),
    })
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
    args = parser.parse_args()
    pointer = args.pointer.expanduser().resolve()
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(str(CORE_ROOT.resolve()) + "\n", encoding="utf-8")
    print(f"Configured GRDR Core: {CORE_ROOT.resolve()}")
    print(f"Pointer: {pointer}")
    if args.elements_root is not None:
        config_path = write_runtime_config(args.elements_root)
        print(f"Elements root: {require_external(args.elements_root, 'elements root')}")
        print(f"Runtime configuration: {config_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
