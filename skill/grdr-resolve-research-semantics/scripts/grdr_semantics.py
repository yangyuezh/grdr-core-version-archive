#!/usr/bin/env python3
"""Run the canonical GRDR research semantic resolver commands."""

from __future__ import annotations

import json
import sys

from grdr import main as grdr_main
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
    grdr_main()


if __name__ == "__main__":
    main()
