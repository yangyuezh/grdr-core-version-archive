#!/usr/bin/env python3
"""Check that the local GRDR release metadata is internally consistent."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$")


def main() -> int:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    errors: list[str] = []

    if not SEMVER.fullmatch(version):
        errors.append(f"VERSION is not valid Semantic Versioning: {version!r}")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"## [{version}]" not in changelog:
        errors.append(f"CHANGELOG.md has no entry for {version}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if f"Version `{version}`" not in readme:
        errors.append(f"README.md does not identify Version `{version}`")

    skill = ROOT / "skill" / "grdr" / "SKILL.md"
    if not skill.is_file():
        errors.append("version-controlled Skill bundle is missing")
    elif not skill.read_text(encoding="utf-8").startswith("---\nname: grdr\n"):
        errors.append("version-controlled Skill identity is not 'grdr'")

    legacy_skill = ROOT / "skill" / "global-research-data-warehouse"
    if legacy_skill.exists():
        errors.append("legacy global-research-data-warehouse Skill bundle still exists")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"GRDR release metadata is consistent for v{version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
