#!/usr/bin/env python3
"""Verify that every GRDR audit tag has a correctly classified GitHub Release."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_MAP = ROOT / "audit" / "version-map.jsonl"
DEFAULT_REPOSITORY = "yangyuezh/grdr-core-version-archive"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def github_releases(repository: str) -> list[dict]:
    command = [
        "gh",
        "release",
        "list",
        "--repo",
        repository,
        "--limit",
        "1000",
        "--json",
        "tagName,isDraft,isPrerelease,name",
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPOSITORY),
    )
    args = parser.parse_args()

    expected = load_jsonl(VERSION_MAP)
    actual = {item["tagName"]: item for item in github_releases(args.repository)}
    errors: list[str] = []

    for item in expected:
        tag = item["archive_tag"]
        release = actual.get(tag)
        if release is None:
            errors.append(f"missing GitHub Release: {tag}")
            continue
        if release["isDraft"]:
            errors.append(f"draft GitHub Release: {tag}")
        expected_prerelease = item["status"] != "release"
        if release["isPrerelease"] != expected_prerelease:
            errors.append(
                f"wrong prerelease classification: {tag}; "
                f"expected {expected_prerelease}, got {release['isPrerelease']}"
            )

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "status": "passed",
                "repository": args.repository,
                "expected_audit_releases": len(expected),
                "verified_audit_releases": len(expected),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
