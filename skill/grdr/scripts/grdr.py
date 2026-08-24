#!/usr/bin/env python3
"""Locate immutable GRDR Core and forward one command to its canonical CLI."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys


def valid_core(path: Path) -> bool:
    return (
        (path / "VERSION").is_file()
        and (path / "scripts" / "grdr.py").is_file()
        and (path / "skill" / "grdr" / "SKILL.md").is_file()
    )


def ancestors(path: Path) -> list[Path]:
    return [path, *path.parents]


def resolve_core() -> Path:
    candidates: list[Path] = []
    configured = os.environ.get("GRDR_ROOT")
    if configured:
        candidates.append(Path(configured).expanduser())

    codex_root = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    pointer = codex_root / "grdr-core-root"
    if pointer.is_file():
        value = pointer.read_text(encoding="utf-8").strip()
        if value:
            candidates.append(Path(value).expanduser())
    candidates.append(codex_root / "grdr-core")
    candidates.extend(ancestors(Path.cwd()))
    candidates.extend(ancestors(Path(__file__).resolve()))

    checked: list[str] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if str(resolved) in checked:
            continue
        checked.append(str(resolved))
        if valid_core(resolved):
            return resolved
    raise FileNotFoundError(
        "GRDR Core was not found. Set GRDR_ROOT or run Core's "
        "scripts/configure_core.py once. Checked: " + ", ".join(checked)
    )


def main() -> None:
    try:
        root = resolve_core()
    except (OSError, ValueError) as exc:
        print(
            json.dumps({"error": "grdr_core_not_found", "message": str(exc)}, indent=2),
            file=sys.stderr,
        )
        raise SystemExit(2)
    preferred_python = root / ".venv" / "bin" / "python"
    python = str(preferred_python) if preferred_python.is_file() else sys.executable
    cli = root / "scripts" / "grdr.py"
    os.execv(python, [python, str(cli), *sys.argv[1:]])


if __name__ == "__main__":
    main()
