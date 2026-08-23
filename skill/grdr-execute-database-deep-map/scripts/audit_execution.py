#!/usr/bin/env python3
"""Audit one GRDR Step 2 database deep-map project through the canonical CLI."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


INSTALLED_ROOT = Path("/Users/jasper/Documents/codex/grdr-core")


def resolve_root() -> Path:
    configured_root = os.environ.get("GRDR_ROOT")
    if configured_root:
        return Path(configured_root).expanduser().resolve()
    bundled_root = Path(__file__).resolve().parents[3]
    if (bundled_root / "scripts" / "grdr.py").is_file():
        return bundled_root
    return INSTALLED_ROOT


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    args = parser.parse_args()
    root = resolve_root()
    cli = root / "scripts" / "grdr.py"
    if not cli.is_file():
        print(json.dumps({
            "error": "grdr_project_not_found",
            "expected_root": str(root),
            "resolution": "Set GRDR_ROOT to the canonical GRDR project directory.",
        }, indent=2), file=sys.stderr)
        raise SystemExit(2)
    os.execv(sys.executable, [
        sys.executable, str(cli), "audit-database-deep-map-execution", args.project,
    ])


if __name__ == "__main__":
    main()
