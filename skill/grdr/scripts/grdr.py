#!/usr/bin/env python3
"""Forward commands to the canonical GRDR registry CLI."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


DEFAULT_ROOT = Path("/Users/jasper/Documents/codex/grdr-core")


def main() -> None:
    root = Path(os.environ.get("GRDR_ROOT", str(DEFAULT_ROOT))).expanduser().resolve()
    cli = root / "scripts" / "grdr.py"
    if not cli.is_file():
        print(
            json.dumps(
                {
                    "error": "grdr_registry_not_found",
                    "expected_root": str(root),
                    "resolution": "Set GRDR_ROOT to the canonical GRDR project directory.",
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        raise SystemExit(2)
    os.execv(sys.executable, [sys.executable, str(cli), *sys.argv[1:]])


if __name__ == "__main__":
    main()
