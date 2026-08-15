#!/usr/bin/env python3
"""Run the canonical GRDR six-layer source-depth audit."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


DEFAULT_ROOT = Path("/Users/jasper/Documents/codex/grdr")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("source_id", nargs="?")
    group.add_argument("--all", action="store_true", help="Audit every registered source")
    args = parser.parse_args()

    root = Path(os.environ.get("GRDR_ROOT", str(DEFAULT_ROOT))).expanduser().resolve()
    cli = root / "scripts" / "grdr.py"
    if not cli.is_file():
        print(
            json.dumps(
                {
                    "error": "grdr_project_not_found",
                    "expected_root": str(root),
                    "resolution": "Set GRDR_ROOT to the canonical GRDR project directory.",
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        raise SystemExit(2)

    command = "audit-all-source-depth" if args.all else "audit-source-depth"
    arguments = [sys.executable, str(cli), command]
    if args.source_id:
        arguments.append(args.source_id)
    os.execv(sys.executable, arguments)


if __name__ == "__main__":
    main()
