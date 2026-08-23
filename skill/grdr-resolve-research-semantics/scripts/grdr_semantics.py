#!/usr/bin/env python3
"""Run the canonical GRDR research semantic resolver commands."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys


INSTALLED_ROOT = Path("/Users/jasper/Documents/codex/grdr-core")
ALLOWED_COMMANDS = {
    "prepare-semantic-candidates",
    "align-research-indicators",
    "traverse-semantic-paths",
    "match-indicators",
    "rerun-matching",
    "explain-indicator-match",
    "fetch-indicator-data",
    "research-project-status",
}


def resolve_root() -> Path:
    configured = os.environ.get("GRDR_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    bundled = Path(__file__).resolve().parents[3]
    if (bundled / "scripts" / "grdr.py").is_file():
        return bundled
    return INSTALLED_ROOT


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ALLOWED_COMMANDS:
        print(
            json.dumps(
                {
                    "error": "semantic_resolver_command_required",
                    "allowed_commands": sorted(ALLOWED_COMMANDS),
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        raise SystemExit(2)
    root = resolve_root()
    cli = root / "scripts" / "grdr.py"
    if not cli.is_file():
        print(
            json.dumps(
                {
                    "error": "grdr_project_not_found",
                    "expected_root": str(root),
                    "resolution": "Set GRDR_ROOT to the canonical GRDR Core directory.",
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        raise SystemExit(2)
    os.execv(sys.executable, [sys.executable, str(cli), *sys.argv[1:]])


if __name__ == "__main__":
    main()
