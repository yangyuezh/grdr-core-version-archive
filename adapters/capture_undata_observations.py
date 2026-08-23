#!/usr/bin/env python3
"""Capture one reproducible public observation export per UNdata datamart route.

The capture is deliberately bounded. It does not claim to mirror every UNdata
observation. Dynamic datamarts use UNdata's official CSV export handler for the
first source-native variable in the locked metadata snapshot. Document-style
datamarts use the official table-presentation download. Alternative routes are
handled explicitly and failures remain in the manifest.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import signal
import urllib.error
import urllib.parse
import urllib.request
import zipfile


USER_AGENT = "GRDR/3.2 UNdata bounded observation capture"
DOWNLOAD_URL = "https://data.un.org/Handlers/DownloadHandler.ashx"
DOCUMENT_URL = "https://data.un.org/Handlers/DocumentDownloadHandler.ashx"
WORLDSTAT_URL = "https://data.un.org/en/iso/us.html"
MAX_BYTES = 100 * 1024 * 1024


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def safe_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "item"


def fetch(url: str, timeout: int) -> tuple[bytes, dict[str, str], int]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    def expire(_signum: int, _frame: object) -> None:
        raise TimeoutError(f"total request time exceeded {timeout} seconds")

    previous = signal.signal(signal.SIGALRM, expire)
    signal.setitimer(signal.ITIMER_REAL, timeout)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_BYTES:
                raise ValueError(f"response exceeds {MAX_BYTES} bytes")
            payload = response.read(MAX_BYTES + 1)
            if len(payload) > MAX_BYTES:
                raise ValueError(f"response exceeds {MAX_BYTES} bytes")
            headers = {key.casefold(): value for key, value in response.headers.items()}
            return payload, headers, response.status
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError(f"{type(exc).__name__}: {exc}") from exc
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def zip_summary(payload: bytes) -> dict[str, object]:
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        members = []
        for info in archive.infolist():
            row_count = None
            if info.filename.casefold().endswith(".csv"):
                with archive.open(info) as handle:
                    row_count = max(sum(1 for _ in handle) - 1, 0)
            members.append(
                {
                    "name": info.filename,
                    "size_bytes": info.file_size,
                    "crc32": f"{info.CRC:08x}",
                    "data_row_count": row_count,
                }
            )
        return {"members": members}


def write_capture(output: Path, filename: str, payload: bytes) -> dict[str, object]:
    target = output / filename
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing capture: {target}")
    target.write_bytes(payload)
    return {
        "path": filename,
        "size_bytes": len(payload),
        "sha256": sha256_bytes(payload),
    }


def dynamic_capture(mart: str, variable: dict[str, object], expected_rows: int | None, output: Path, timeout: int) -> dict[str, object]:
    data_filter = str(variable["filter"])
    query = urllib.parse.urlencode(
        {"DataFilter": urllib.parse.unquote(data_filter), "DataMartId": mart, "Format": "csv"}
    )
    url = f"{DOWNLOAD_URL}?{query}"
    filename = f"{safe_name(mart)}-{safe_name(str(variable['label']))}.zip"
    target = output / filename
    reused = target.is_file()
    if reused:
        payload = target.read_bytes()
        headers: dict[str, str] = {}
        status = 200
        stored = {"path": filename, "size_bytes": len(payload), "sha256": sha256_bytes(payload)}
    else:
        payload, headers, status = fetch(url, timeout)
        stored = write_capture(output, filename, payload)
    if not zipfile.is_zipfile(BytesIO(payload)):
        raise RuntimeError("official CSV export did not return a ZIP archive")
    summary = zip_summary(payload)
    downloaded_rows = sum(
        int(item["data_row_count"] or 0) for item in summary["members"]  # type: ignore[index]
    )
    return {
        "mart_id": mart,
        "label": variable["label"],
        "data_filter": data_filter,
        "route": "official_csv_export",
        "request_url": url,
        "http_status": status,
        "content_type": headers.get("content-type"),
        "source_record_count": expected_rows,
        "downloaded_data_row_count": downloaded_rows,
        "upstream_100000_row_cap_applies": bool(expected_rows and expected_rows > 100000),
        "status": "captured",
        "reused_existing_capture": reused,
        **stored,
        **summary,
    }


def document_capture(mart: str, variable: dict[str, object], output: Path, timeout: int) -> dict[str, object]:
    decoded = urllib.parse.unquote(str(variable["filter"]))
    document_id = decoded.split(":", 1)[1]
    query = urllib.parse.urlencode({"id": document_id, "t": "bin"})
    url = f"{DOCUMENT_URL}?{query}"
    filename = f"{safe_name(mart)}-{safe_name(str(variable['label']))}-document.bin"
    target = output / filename
    reused = target.is_file()
    if reused:
        payload = target.read_bytes()
        headers: dict[str, str] = {}
        status = 200
        stored = {"path": filename, "size_bytes": len(payload), "sha256": sha256_bytes(payload)}
    else:
        payload, headers, status = fetch(url, timeout)
        stored = write_capture(output, filename, payload)
    return {
        "mart_id": mart,
        "label": variable["label"],
        "data_filter": variable["filter"],
        "route": "official_document_download",
        "request_url": url,
        "http_status": status,
        "content_type": headers.get("content-type"),
        "content_disposition": headers.get("content-disposition"),
        "status": "captured",
        "reused_existing_capture": reused,
        **stored,
    }


def alternative_captures(snapshot: dict[str, object], output: Path, timeout: int) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    alternatives = snapshot.get("alternatives", {})
    if not isinstance(alternatives, dict):
        return results
    for mart in sorted(alternatives):
        item = alternatives[mart]
        if not isinstance(item, dict):
            continue
        if mart not in {"KI", "WorldStat"}:
            probe = item.get("observation_probe", {})
            results.append(
                {
                    "mart_id": mart,
                    "label": f"{mart} observation endpoint",
                    "route": item.get("route"),
                    "request_url": item.get("url"),
                    "status": "not_captured",
                    "reason": probe.get("message", "No successful observation route in the locked snapshot") if isinstance(probe, dict) else "No successful observation route in the locked snapshot",
                }
            )
            continue
        url = str(item["url"]) if mart == "KI" else WORLDSTAT_URL
        label = item.get("issue") if mart == "KI" else "World Statistics Pocketbook — United States profile"
        filename = "ki-statistical-yearbook-2025.pdf" if mart == "KI" else "worldstat-united-states-profile.html"
        route = "official_current_publication" if mart == "KI" else "official_country_profile"
        try:
            target = output / filename
            reused = target.is_file()
            if reused:
                payload = target.read_bytes()
                headers: dict[str, str] = {}
                status = 200
                stored = {"path": filename, "size_bytes": len(payload), "sha256": sha256_bytes(payload)}
            else:
                payload, headers, status = fetch(url, timeout)
                stored = write_capture(output, filename, payload)
            results.append(
                {
                    "mart_id": mart,
                    "label": label,
                    "route": route,
                    "request_url": url,
                    "http_status": status,
                    "content_type": headers.get("content-type"),
                    "status": "captured",
                    "reused_existing_capture": reused,
                    **stored,
                }
            )
        except (RuntimeError, FileExistsError) as exc:
            results.append(
                {
                    "mart_id": mart,
                    "label": label,
                    "route": route,
                    "request_url": url,
                    "status": "not_captured",
                    "reason": str(exc),
                }
            )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metadata_snapshot", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.timeout < 1:
        raise SystemExit("--timeout must be positive")
    if args.output_dir.exists() and not args.resume:
        raise SystemExit(f"output directory already exists: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=args.resume)

    with gzip.open(args.metadata_snapshot, "rt", encoding="utf-8") as handle:
        snapshot = json.load(handle)

    captures: list[dict[str, object]] = []
    explorer = snapshot.get("explorer", {})
    for mart in sorted(explorer):
        item = explorer[mart]
        variables = item.get("variables", [])
        if not variables:
            captures.append({"mart_id": mart, "status": "not_captured", "reason": "no source-native variable in locked snapshot"})
            continue
        variable = variables[0]
        probe = item.get("preview_probe", {})
        expected = (probe.get("headers") or {}).get("recordcount") if isinstance(probe, dict) else None
        expected_rows = int(expected) if expected and str(expected).isdigit() else None
        try:
            if urllib.parse.unquote(str(variable["filter"])).startswith("docID:"):
                result = document_capture(mart, variable, args.output_dir, args.timeout)
            else:
                result = dynamic_capture(mart, variable, expected_rows, args.output_dir, args.timeout)
        except (RuntimeError, FileExistsError) as exc:
            result = {
                "mart_id": mart,
                "label": variable.get("label"),
                "data_filter": variable.get("filter"),
                "status": "not_captured",
                "reason": str(exc),
            }
        captures.append(result)

    captures.extend(alternative_captures(snapshot, args.output_dir, args.timeout))
    captured = [item for item in captures if item["status"] == "captured"]
    manifest = {
        "schema_version": "1.0.0",
        "source_id": snapshot["source_id"],
        "project_id": snapshot["project_id"],
        "metadata_snapshot_boundary": snapshot["snapshot_boundary"],
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "capture_claim": "One bounded official observation export or table presentation per reachable UNdata datamart route; not a full-site observation mirror.",
        "selection_rule": "For each Explorer datamart, use the first variable in the locked source-native order. For alternative routes, capture only an official observation-bearing publication or profile.",
        "attempted_datamarts": len(captures),
        "captured_datamarts": len(captured),
        "not_captured_datamarts": len(captures) - len(captured),
        "total_captured_bytes": sum(int(item["size_bytes"]) for item in captured),
        "captures": captures,
    }
    manifest_path = args.output_dir / "observation-capture-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: manifest[key] for key in ("attempted_datamarts", "captured_datamarts", "not_captured_datamarts", "total_captured_bytes")}, indent=2))


if __name__ == "__main__":
    main()
