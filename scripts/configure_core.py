#!/usr/bin/env python3
"""Register this immutable GRDR Core clone for installed Skill launchers."""

from __future__ import annotations

import argparse
import os
from pathlib import Path


CORE_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_codex_root = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    parser.add_argument("--pointer", type=Path, default=default_codex_root / "grdr-core-root")
    args = parser.parse_args()
    pointer = args.pointer.expanduser().resolve()
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(str(CORE_ROOT.resolve()) + "\n", encoding="utf-8")
    print(f"Configured GRDR Core: {CORE_ROOT.resolve()}")
    print(f"Pointer: {pointer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
