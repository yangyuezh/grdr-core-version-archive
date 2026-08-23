#!/usr/bin/env python3
"""Run the canonical GRDR indicator-project audit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from grdr import main as grdr_main


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir")
    args = parser.parse_args()

    sys.argv = [
        sys.argv[0],
        "audit-indicator-project",
        str(Path(args.project_dir).expanduser().resolve()),
    ]
    grdr_main()


if __name__ == "__main__":
    main()
