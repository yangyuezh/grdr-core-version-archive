#!/usr/bin/env python3
"""Audit one GRDR Step 2 database deep-map project through the canonical CLI."""

from __future__ import annotations

import argparse
import sys

from grdr import main as grdr_main


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    args = parser.parse_args()
    sys.argv = [sys.argv[0], "audit-database-deep-map-execution", args.project]
    grdr_main()


if __name__ == "__main__":
    main()
