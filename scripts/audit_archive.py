#!/usr/bin/env python3
"""Build or verify the GRDR version-audit ledger from immutable Git objects."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audit"
SOURCE = AUDIT / "version-map.jsonl"
LEDGER = AUDIT / "version-ledger.jsonl"
CSV_PATH = AUDIT / "version-ledger.csv"
MANIFEST = AUDIT / "archive-manifest.json"
SUMS = AUDIT / "SHA256SUMS"
README = ROOT / "README.md"


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def render() -> dict[str, bytes]:
    source_rows = load_jsonl(SOURCE)
    readme = README.read_text()
    seen_ids: set[str] = set()
    seen_tags: set[str] = set()
    ledger_rows: list[dict] = []

    for item in source_rows:
        record_id = item["record_id"]
        tag = item["archive_tag"]
        if record_id in seen_ids:
            raise ValueError(f"duplicate record_id: {record_id}")
        if tag in seen_tags:
            raise ValueError(f"duplicate archive_tag: {tag}")
        if f"`{record_id}`" not in readme:
            raise ValueError(f"README is missing audit record: {record_id}")
        seen_ids.add(record_id)
        seen_tags.add(tag)

        commit = git("rev-parse", f"{tag}^{{commit}}")
        expected = item["expected_commit"]
        if commit != expected:
            raise ValueError(f"{tag} resolves to {commit}, expected {expected}")

        tree = git("rev-parse", f"{commit}^{{tree}}")
        version_path = item.get("version_path", "VERSION")
        version_text = git("show", f"{commit}:{version_path}").strip()
        if version_text != item["version"]:
            raise ValueError(
                f"{tag} contains VERSION={version_text!r}, expected {item['version']!r}"
            )

        source_commit = item.get("source_commit")
        source_tree = None
        if source_commit:
            git("cat-file", "-e", f"{source_commit}^{{commit}}")
            source_path = item["source_path"]
            source_tree = git("rev-parse", f"{source_commit}:{source_path}")
            if source_tree != item["expected_source_tree"]:
                raise ValueError(
                    f"{record_id} source tree {source_tree} != {item['expected_source_tree']}"
                )
            if source_tree != tree:
                raise ValueError(f"{record_id} extracted tree is not byte-identical to source")

        metadata = git("show", "-s", "--format=%cI%x00%s", commit).split("\x00", 1)
        row = dict(item)
        row.update(
            {
                "archive_commit": commit,
                "tree_sha": tree,
                "committed_at": metadata[0],
                "commit_subject": metadata[1],
            }
        )
        if source_tree:
            row["source_tree_sha"] = source_tree
        ledger_rows.append(row)

    jsonl = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for row in ledger_rows
    ).encode()

    fields = [
        "record_id",
        "version",
        "status",
        "canonical",
        "product_shape",
        "archive_tag",
        "archive_commit",
        "tree_sha",
        "committed_at",
        "source_repository",
        "source_ref",
        "source_path",
        "notes",
    ]
    from io import StringIO

    csv_buffer = StringIO()
    writer = csv.DictWriter(
        csv_buffer,
        fieldnames=fields,
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(ledger_rows)
    csv_bytes = csv_buffer.getvalue().encode()

    release_rows = [row for row in ledger_rows if row["canonical"] and row["status"] == "release"]
    manifest = {
        "schema_version": "1.1.0",
        "archive_role": "software_version_audit",
        "record_count": len(ledger_rows),
        "canonical_version_node_count": sum(row["canonical"] for row in ledger_rows),
        "canonical_release_count": len(release_rows),
        "expected_archival_release_count": len(ledger_rows),
        "pre_1_0_provenance_count": sum(
            row["status"] == "pre_1_0_provenance" for row in ledger_rows
        ),
        "historical_variant_count": sum(
            row["status"] in {"historical_variant", "equivalent_tree_variant"}
            for row in ledger_rows
        ),
        "post_release_docs_count": sum(
            row["status"] == "post_release_docs" for row in ledger_rows
        ),
        "coverage": {
            "requested_from": "1.0.0",
            "requested_through": "4.5.4",
            "earliest_preserved": "0.1.0",
            "latest_preserved": "4.5.4",
            "formal_4_0_0_release_found": False,
            "v4_0_0_candidate_preserved": True,
        },
        "version_map_sha256": sha256(SOURCE),
        "version_ledger_sha256": hashlib.sha256(jsonl).hexdigest(),
        "version_ledger_csv_sha256": hashlib.sha256(csv_bytes).hexdigest(),
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()

    payloads = {
        "version-ledger.jsonl": jsonl,
        "version-ledger.csv": csv_bytes,
        "archive-manifest.json": manifest_bytes,
    }
    sum_lines = [f"{sha256(SOURCE)}  version-map.jsonl"]
    for name, payload in payloads.items():
        sum_lines.append(f"{hashlib.sha256(payload).hexdigest()}  {name}")
    payloads["SHA256SUMS"] = ("\n".join(sum_lines) + "\n").encode()
    return payloads


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write deterministic audit outputs")
    args = parser.parse_args()
    payloads = render()

    mismatches: list[str] = []
    for name, expected in payloads.items():
        path = AUDIT / name
        if args.write:
            path.write_bytes(expected)
        elif not path.exists() or path.read_bytes() != expected:
            mismatches.append(name)

    if mismatches:
        print("audit outputs are stale: " + ", ".join(mismatches), file=sys.stderr)
        return 1

    manifest = json.loads(payloads["archive-manifest.json"])
    print(
        json.dumps(
            {
                "status": "passed",
                "record_count": manifest["record_count"],
                "canonical_release_count": manifest["canonical_release_count"],
                "earliest": manifest["coverage"]["earliest_preserved"],
                "latest": manifest["coverage"]["latest_preserved"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
