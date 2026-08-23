#!/usr/bin/env python3
"""Discover, materialize, search, and invoke distributed GRDR source snapshots."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
from typing import Any, Iterable


DEFAULT_ELEMENTS_ROOT = Path("/Volumes/Elements/GRDR")
LOGICAL_COMPONENTS = {"knowledge", "agent", "observations"}


class DistributedRuntimeError(ValueError):
    """Raised when a distributed snapshot cannot be trusted or invoked."""


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DistributedRuntimeError(f"expected a JSON object: {path}")
    return value


def load_cards(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def elements_root(value: str | Path | None = None) -> Path:
    if value is not None:
        return Path(value).expanduser().resolve()
    configured = os.environ.get("GRDR_ELEMENTS_ROOT")
    return Path(configured).expanduser().resolve() if configured else DEFAULT_ELEMENTS_ROOT


def source_slug(card: dict[str, Any]) -> str:
    prefix = "grdr:source-archive:"
    card_id = str(card.get("id", ""))
    if not card_id.startswith(prefix):
        raise DistributedRuntimeError(f"invalid source archive id: {card_id}")
    return card_id.removeprefix(prefix)


def snapshot_path(card: dict[str, Any], root: str | Path | None = None) -> Path:
    return elements_root(root) / "sources" / source_slug(card) / "snapshots" / card["latest_snapshot"]


def runtime_paths(card: dict[str, Any], root: str | Path | None = None) -> tuple[Path, Path, Path]:
    snapshot = snapshot_path(card, root)
    runtime = card.get("runtime")
    if not isinstance(runtime, dict):
        raise DistributedRuntimeError(f"{card['source_id']} latest snapshot has no callable Agent runtime")
    return snapshot, snapshot / runtime["agent_index"], snapshot / runtime["entrypoint"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def local_snapshot_status(card: dict[str, Any], root: str | Path | None = None, verify: bool = False) -> dict[str, Any]:
    snapshot = snapshot_path(card, root)
    status: dict[str, Any] = {
        "source_id": card["source_id"],
        "snapshot_id": card["latest_snapshot"],
        "snapshot_path": str(snapshot),
        "online_release": card["release"],
        "available_local": snapshot.is_dir(),
        "runtime_ready": False,
        "logical_parity_verified": False,
        "errors": [],
    }
    if not snapshot.is_dir():
        status["errors"].append("local Elements snapshot is not materialized")
        return status
    try:
        _, index, entrypoint = runtime_paths(card, root)
    except DistributedRuntimeError as exc:
        status["errors"].append(str(exc))
        return status
    descriptor_path = snapshot / "agent" / "runtime.json"
    receipt_path = snapshot / "receipts" / "storage_receipt.json"
    audit_path = snapshot / "agent" / "runtime_audit.json"
    required = [index, entrypoint, descriptor_path, receipt_path, audit_path]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        status["errors"].extend(f"missing {path}" for path in missing)
        return status
    receipt = read_json(receipt_path)
    descriptor = read_json(descriptor_path)
    audit = read_json(audit_path)
    if receipt.get("logical_content_fingerprint") != card.get("archive_fingerprint"):
        status["errors"].append("Elements receipt fingerprint differs from the central source card")
    if descriptor.get("source_id") != card["source_id"]:
        status["errors"].append("runtime descriptor source_id differs from the central source card")
    if audit.get("status") != "ready" or audit.get("unresolved_variable_count") != 0:
        status["errors"].append("runtime audit does not prove complete variable resolution")
    status["runtime_ready"] = not status["errors"]
    status["runtime_audit"] = audit
    if verify:
        records = []
        for component in sorted(LOGICAL_COMPONENTS):
            base = snapshot / component
            for path in sorted(base.rglob("*")):
                relative = path.relative_to(snapshot)
                if not path.is_file() or any(part.startswith("._") or part == ".DS_Store" for part in relative.parts):
                    continue
                records.append({
                    "path": relative.as_posix(),
                    "component": component,
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                })
        actual = fingerprint(records)
        status["computed_logical_fingerprint"] = actual
        status["logical_parity_verified"] = actual == card.get("archive_fingerprint")
        if not status["logical_parity_verified"]:
            status["errors"].append("computed Elements logical fingerprint differs from the central source card")
        status["runtime_ready"] = not status["errors"]
    return status


def available_runtimes(cards: Iterable[dict[str, Any]], root: str | Path | None = None) -> list[tuple[dict[str, Any], Path]]:
    result = []
    for card in cards:
        if not isinstance(card.get("runtime"), dict):
            continue
        status = local_snapshot_status(card, root)
        if status["runtime_ready"]:
            result.append((card, Path(status["snapshot_path"])))
    return result


def records_by_type(connection: sqlite3.Connection, entity_type: str) -> list[dict[str, Any]]:
    rows = connection.execute("SELECT payload_json FROM records WHERE entity_type = ?", (entity_type,))
    return [json.loads(row[0]) for row in rows]


def distributed_entity_records(
    cards: Iterable[dict[str, Any]], entity_type: str, root: str | Path | None = None
) -> list[dict[str, Any]]:
    """Return one deduplicated entity collection across callable local snapshots."""
    by_id: dict[str, dict[str, Any]] = {}
    for card, snapshot in available_runtimes(cards, root):
        index = snapshot / card["runtime"]["agent_index"]
        connection = sqlite3.connect(index)
        try:
            for item in records_by_type(connection, entity_type):
                item["_grdr_snapshot"] = {
                    "source_id": card["source_id"],
                    "snapshot_id": card["latest_snapshot"],
                    "release": card["release"],
                }
                by_id[item["id"]] = item
        finally:
            connection.close()
    return [by_id[key] for key in sorted(by_id)]


def record_by_id(connection: sqlite3.Connection, record_id: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT payload_json FROM records WHERE id = ?", (record_id,)).fetchone()
    return json.loads(row[0]) if row else None


def normalized(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(normalized(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(normalized(item) for item in value)
    return str(value).casefold()


def contains(value: Any, query: str | None) -> bool:
    return query is None or query.casefold() in normalized(value)


def distributed_variable_matches(
    cards: Iterable[dict[str, Any]],
    root: str | Path | None = None,
    *,
    query: str | None = None,
    construct: str | None = None,
    dataset_id: str | None = None,
    role: str | None = None,
    measurement_type: str | None = None,
    verification: str | None = None,
) -> list[dict[str, Any]]:
    matches = []
    for card, snapshot in available_runtimes(cards, root):
        index = snapshot / card["runtime"]["agent_index"]
        connection = sqlite3.connect(index)
        try:
            constructs = {item["id"]: item for item in records_by_type(connection, "constructs")}
            for variable in records_by_type(connection, "variables"):
                linked_constructs = [constructs[item] for item in variable.get("construct_ids", []) if item in constructs]
                if not contains(variable, query) or not contains(linked_constructs, construct):
                    continue
                if dataset_id and dataset_id not in variable.get("dataset_ids", []):
                    continue
                if role and role not in variable.get("role_candidates", []):
                    continue
                if measurement_type and measurement_type != variable.get("measurement", {}).get("type"):
                    continue
                if verification and verification != variable.get("verification", {}).get("status"):
                    continue
                matches.append({**variable, "_grdr_snapshot": {
                    "source_id": card["source_id"],
                    "snapshot_id": card["latest_snapshot"],
                    "location": str(snapshot),
                    "release": card["release"],
                }})
        finally:
            connection.close()
    matches.sort(key=lambda item: (item.get("verification", {}).get("status") != "verified", item.get("label", "").casefold()))
    return matches


def resolve_distributed_variable(cards: Iterable[dict[str, Any]], variable_id: str, root: str | Path | None = None) -> dict[str, Any] | None:
    for card, snapshot in available_runtimes(cards, root):
        index = snapshot / card["runtime"]["agent_index"]
        connection = sqlite3.connect(index)
        try:
            variable = record_by_id(connection, variable_id)
            if variable is None or not variable_id.startswith("grdr:variable:"):
                continue
            datasets = [record_by_id(connection, item) for item in variable.get("dataset_ids", [])]
            constructs = [record_by_id(connection, item) for item in variable.get("construct_ids", [])]
            structures = [record_by_id(connection, item) for item in variable.get("data_structure_ids", [])]
            return {
                "variable": variable,
                "datasets": [item for item in datasets if item],
                "constructs": [item for item in constructs if item],
                "data_structures": [item for item in structures if item],
                "snapshot": {
                    "source_id": card["source_id"],
                    "snapshot_id": card["latest_snapshot"],
                    "location": str(snapshot),
                    "release": card["release"],
                },
            }
        finally:
            connection.close()
    return None


def invoke_source_runtime(
    cards: Iterable[dict[str, Any]],
    variable_id: str,
    operation: str,
    root: str | Path | None = None,
    extra_args: Iterable[str] = (),
) -> dict[str, Any]:
    for card, snapshot in available_runtimes(cards, root):
        index = snapshot / card["runtime"]["agent_index"]
        connection = sqlite3.connect(index)
        try:
            if record_by_id(connection, variable_id) is None:
                continue
        finally:
            connection.close()
        entrypoint = snapshot / card["runtime"]["entrypoint"]
        arguments = list(extra_args)
        invocation_timeout = 90.0
        if "--timeout" in arguments:
            try:
                invocation_timeout = max(30.0, float(arguments[arguments.index("--timeout") + 1]) + 30.0)
            except (IndexError, ValueError):
                pass
        command = [sys.executable, str(entrypoint), operation, "--index", str(index), "--variable-id", variable_id, *arguments]
        try:
            completed = subprocess.run(
                command,
                cwd=entrypoint.parent,
                capture_output=True,
                text=True,
                timeout=invocation_timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise DistributedRuntimeError(
                f"source runtime exceeded {invocation_timeout:g} seconds"
            ) from exc
        if completed.returncode:
            raise DistributedRuntimeError((completed.stderr or completed.stdout).strip() or "source runtime invocation failed")
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise DistributedRuntimeError("source runtime did not emit one JSON object") from exc
        return {
            "source_id": card["source_id"],
            "snapshot_id": card["latest_snapshot"],
            "runtime_protocol": card["runtime"]["protocol_version"],
            "result": result,
        }
    raise DistributedRuntimeError(f"variable is absent from every locally available source runtime: {variable_id}")


def safe_extract(archive_path: Path, destination: Path) -> None:
    with tarfile.open(archive_path, "r:gz") as archive:
        root = destination.resolve()
        for member in archive.getmembers():
            target = (destination / member.name).resolve()
            if root not in target.parents and target != root:
                raise DistributedRuntimeError(f"unsafe archive member: {member.name}")
            if member.issym() or member.islnk():
                raise DistributedRuntimeError(f"archive links are not permitted: {member.name}")
        archive.extractall(destination)


def materialize_source_snapshot(card: dict[str, Any], root: str | Path | None = None) -> dict[str, Any]:
    if not isinstance(card.get("runtime"), dict):
        raise DistributedRuntimeError("the indexed snapshot predates the callable runtime artifact format")
    destination = snapshot_path(card, root)
    if destination.exists():
        status = local_snapshot_status(card, root, verify=True)
        if not status["runtime_ready"] or not status["logical_parity_verified"]:
            raise DistributedRuntimeError("existing Elements snapshot is incomplete or differs from the central card")
        return {"status": "already_materialized", **status}
    repository = card["repository"].removeprefix("https://github.com/").rstrip("/")
    release_tag = card["release"].rsplit("/tag/", 1)[-1]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{card['latest_snapshot']}.", dir=destination.parent) as temporary:
        workspace = Path(temporary)
        downloads = workspace / "downloads"
        downloads.mkdir()
        completed = subprocess.run(
            ["gh", "release", "download", release_tag, "--repo", repository, "--dir", str(downloads)],
            capture_output=True,
            text=True,
        )
        if completed.returncode:
            raise DistributedRuntimeError((completed.stderr or completed.stdout).strip() or "GitHub Release download failed")
        manifest_path = downloads / "manifest.json"
        if not manifest_path.is_file():
            raise DistributedRuntimeError("GitHub Release has no manifest.json")
        manifest = read_json(manifest_path)
        if manifest.get("source_id") != card["source_id"] or manifest.get("snapshot_id") != card["latest_snapshot"]:
            raise DistributedRuntimeError("GitHub Release manifest identity differs from the central card")
        if manifest.get("logical_content_fingerprint") != card["archive_fingerprint"]:
            raise DistributedRuntimeError("GitHub Release manifest fingerprint differs from the central card")
        logical = workspace / "logical"
        logical.mkdir()
        for asset in manifest["release_assets"]:
            path = downloads / asset["name"]
            if not path.is_file() or sha256_file(path) != asset["sha256"] or path.stat().st_size != asset["size_bytes"]:
                raise DistributedRuntimeError(f"GitHub Release asset failed SHA-256 verification: {asset['name']}")
            if path.name.endswith(".tar.gz"):
                safe_extract(path, logical)
            elif asset["component"] == "agent" and len(asset["logical_paths"]) == 1:
                target = logical / asset["logical_paths"][0]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
            else:
                raise DistributedRuntimeError(f"unsupported Release asset representation: {asset['name']}")
        actual = []
        for path in sorted(logical.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(logical).as_posix()
            actual.append({
                "path": relative,
                "component": relative.split("/", 1)[0],
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            })
        if actual != manifest["logical_files"]:
            raise DistributedRuntimeError("expanded GitHub Release differs from the manifest logical inventory")
        receipt = downloads / "storage_receipt.json"
        if not receipt.is_file():
            raise DistributedRuntimeError("GitHub Release has no final Storage receipt")
        receipts = logical / "receipts"
        receipts.mkdir()
        shutil.copy2(receipt, receipts / receipt.name)
        shutil.move(str(logical), str(destination))
    status = local_snapshot_status(card, root, verify=True)
    if not status["runtime_ready"] or not status["logical_parity_verified"]:
        raise DistributedRuntimeError("materialized Elements snapshot failed final verification")
    return {"status": "materialized", **status}
