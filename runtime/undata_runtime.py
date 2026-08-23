#!/usr/bin/env python3
"""Callable Agent runtime for the GRDR UNdata semantic federated mirror."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
from io import BytesIO, StringIO, TextIOWrapper
import json
from pathlib import Path
import re
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from typing import Any


SOURCE_ID = "grdr:source:undata"
USER_AGENT = "GRDR UNdata source runtime/1.0"
DOWNLOAD_URL = "https://data.un.org/Handlers/DownloadHandler.ashx"
DOCUMENT_URL = "https://data.un.org/Handlers/DocumentDownloadHandler.ashx"
SDMX_DATA_URL = "https://data.un.org/ws/rest/data"
MAX_BYTES = 100 * 1024 * 1024
OFFICIAL_DOMAINS = {"data.un.org", "unstats.un.org"}


def emit(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def safe_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "undata-result"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def connect(index: Path) -> sqlite3.Connection:
    if not index.is_file():
        raise ValueError(f"Agent index does not exist: {index}")
    connection = sqlite3.connect(index)
    source = connection.execute("SELECT value FROM metadata WHERE key = 'source_id'").fetchone()
    if source is None or source[0] != SOURCE_ID:
        connection.close()
        raise ValueError("Agent index is not the GRDR UNdata snapshot")
    return connection


def record(connection: sqlite3.Connection, record_id: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT payload_json FROM records WHERE id = ?", (record_id,)).fetchone()
    return json.loads(row[0]) if row else None


def records(connection: sqlite3.Connection, entity_type: str) -> list[dict[str, Any]]:
    rows = connection.execute("SELECT payload_json FROM records WHERE entity_type = ?", (entity_type,))
    return [json.loads(row[0]) for row in rows]


def related_resources(connection: sqlite3.Connection, dataset_ids: list[str]) -> list[dict[str, Any]]:
    return [item for item in records(connection, "resources") if set(item.get("dataset_ids", [])) & set(dataset_ids)]


def require_variable(connection: sqlite3.Connection, variable_id: str) -> dict[str, Any]:
    variable = record(connection, variable_id)
    if variable is None or not variable_id.startswith("grdr:variable:undata-"):
        raise ValueError(f"UNdata variable not found: {variable_id}")
    return variable


def official_url(url: str) -> str:
    host = (urllib.parse.urlparse(url).hostname or "").casefold()
    if host not in OFFICIAL_DOMAINS:
        raise ValueError(f"runtime refused a non-official endpoint: {url}")
    return url


def resolve_explorer(variable: dict[str, Any], dataset: dict[str, Any]) -> dict[str, Any]:
    data_filter = urllib.parse.unquote(str(variable["name"]))
    mart = str(dataset.get("source_native", {}).get("catalog_id") or "")
    if not mart:
        raise ValueError("Explorer variable has no parent datamart ID")
    if data_filter.startswith("docID:"):
        document_id = data_filter.split(":", 1)[1]
        url = f"{DOCUMENT_URL}?{urllib.parse.urlencode({'id': document_id, 't': 'bin'})}"
        return {
            "access_mode": "official_document_download",
            "request_url": official_url(url),
            "request_method": "GET",
            "response_format": "source-native document",
            "native_query": {"DataMartId": mart, "document_id": document_id},
            "row_level_filtering": "not_applicable",
        }
    query = urllib.parse.urlencode({"DataFilter": data_filter, "DataMartId": mart, "Format": "csv"})
    return {
        "access_mode": "official_explorer_csv_export",
        "request_url": official_url(f"{DOWNLOAD_URL}?{query}"),
        "request_method": "GET",
        "response_format": "ZIP containing CSV",
        "native_query": {"DataMartId": mart, "DataFilter": data_filter, "Format": "csv"},
        "upstream_row_cap": 100000,
        "row_level_filtering": "local_after_download",
    }


def resolve_sdmx(connection: sqlite3.Connection, variable: dict[str, Any]) -> dict[str, Any]:
    native = variable["source_native"]
    dataflow = native.get("dataflow_id")
    if not dataflow:
        raise ValueError("SDMX variable has no dataflow_id")
    structures = [record(connection, item) for item in variable.get("data_structure_ids", [])]
    structure_ids = {item["id"] for item in structures if item}
    dimensions = [
        item for item in records(connection, "data_elements")
        if set(item.get("data_structure_ids", [])) & structure_ids
        and item.get("element_type") == "dimension"
        and isinstance(item.get("source_native", {}).get("position"), int)
    ]
    dimensions.sort(key=lambda item: item["source_native"]["position"])
    if not dimensions:
        raise ValueError("SDMX variable has no ordered dimension metadata")
    series_element_id = native.get("dimension_selections", [{}])[0].get("element_id")
    key_parts = [str(variable["name"]) if item["id"] == series_element_id else "" for item in dimensions]
    if str(variable["name"]) not in key_parts:
        raise ValueError("SDMX variable cannot be placed in the ordered dimension key")
    key = ".".join(key_parts)
    url = f"{SDMX_DATA_URL}/{urllib.parse.quote(str(dataflow), safe='')}/{urllib.parse.quote(key, safe='.+')}"
    return {
        "access_mode": "official_sdmx_rest",
        "request_url": official_url(url),
        "request_method": "GET",
        "request_headers": {"Accept": "text/csv"},
        "response_format": "CSV",
        "native_query": {
            "dataflow_id": dataflow,
            "dimension_order": [item["source_native"]["native_id"] for item in dimensions],
            "key": key,
            "series_code": variable["name"],
        },
        "row_level_filtering": "upstream_time_and_local_geography",
    }


def resolve_publication(variable: dict[str, Any], resources: list[dict[str, Any]]) -> dict[str, Any]:
    resource = next((item for item in resources if item.get("url")), None)
    if resource is None:
        raise ValueError("publication variable has no official document resource")
    return {
        "access_mode": "official_publication_locator",
        "request_url": official_url(resource["url"]),
        "request_method": "GET",
        "response_format": ", ".join(resource.get("formats", [])) or "official document",
        "native_query": {"table_or_series_id": variable["name"], "label": variable["label"]},
        "row_level_filtering": "document_extraction_required",
        "limitation": "The registered source exposes this variable through an official publication rather than a row-addressable UNdata API route.",
    }


def resolve(connection: sqlite3.Connection, variable_id: str) -> dict[str, Any]:
    variable = require_variable(connection, variable_id)
    datasets = [record(connection, item) for item in variable.get("dataset_ids", [])]
    datasets = [item for item in datasets if item]
    if not datasets:
        raise ValueError("variable has no registered parent dataset")
    system = variable.get("source_native", {}).get("system")
    if system == "UNdata Explorer":
        access = resolve_explorer(variable, datasets[0])
    elif system == "UNdata SDMX":
        access = resolve_sdmx(connection, variable)
    elif system == "UNSD official publication":
        access = resolve_publication(variable, related_resources(connection, variable["dataset_ids"]))
    else:
        raise ValueError(f"unsupported UNdata source-native system: {system!r}")
    return {
        "operation": "resolve_variable",
        "source_id": SOURCE_ID,
        "variable_id": variable_id,
        "variable_label": variable["label"],
        "dataset_ids": variable["dataset_ids"],
        "construct_ids": variable["construct_ids"],
        "measurement": variable["measurement"],
        "join_keys": variable["join_keys"],
        "source_native": variable["source_native"],
        "access_plan": access,
    }


def fetch_bytes(url: str, headers: dict[str, str], timeout: int) -> tuple[bytes, dict[str, str], int]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **headers})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            length = response.headers.get("Content-Length")
            if length and int(length) > MAX_BYTES:
                raise ValueError(f"response exceeds {MAX_BYTES} bytes")
            payload = response.read(MAX_BYTES + 1)
            if len(payload) > MAX_BYTES:
                raise ValueError(f"response exceeds {MAX_BYTES} bytes")
            return payload, {key.casefold(): value for key, value in response.headers.items()}, response.status
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError(f"{type(exc).__name__}: {exc}") from exc


def row_matches(row: dict[str, str], country: str | None, start: str | None, end: str | None) -> bool:
    normalized = {key.casefold().replace(" ", "_"): (value or "") for key, value in row.items()}
    if country:
        candidates = [value for key, value in normalized.items() if key in {"country", "country_or_area", "location", "ref_area", "area"}]
        if candidates and not any(country.casefold() in value.casefold() for value in candidates):
            return False
    if start or end:
        values = [value for key, value in normalized.items() if key in {"year", "time_period", "time", "period"}]
        if values:
            value = values[0]
            if start and value < start:
                return False
            if end and value > end:
                return False
    return True


def filter_csv_text(text: str, country: str | None, start: str | None, end: str | None) -> tuple[str, int, int]:
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        return text, 0, 0
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=reader.fieldnames, dialect=dialect)
    writer.writeheader()
    total = selected = 0
    for row in reader:
        total += 1
        if row_matches(row, country, start, end):
            writer.writerow(row)
            selected += 1
    return output.getvalue(), total, selected


def filtered_outputs(payload: bytes, content_type: str, output: Path, stem: str, country: str | None, start: str | None, end: str | None) -> list[dict[str, Any]]:
    if not any((country, start, end)):
        return []
    results = []
    candidates: list[tuple[str, str]] = []
    if zipfile.is_zipfile(BytesIO(payload)):
        with zipfile.ZipFile(BytesIO(payload)) as archive:
            for member in archive.infolist():
                if member.filename.casefold().endswith(".csv"):
                    with archive.open(member) as handle:
                        candidates.append((Path(member.filename).stem, TextIOWrapper(handle, encoding="utf-8-sig", errors="replace").read()))
    elif "csv" in content_type.casefold():
        candidates.append((stem, payload.decode("utf-8-sig", "replace")))
    for name, text in candidates:
        filtered, total, selected = filter_csv_text(text, country, start, end)
        target = output / f"{safe_name(name)}-filtered.csv"
        target.write_text(filtered, encoding="utf-8")
        results.append({"path": str(target), "source_rows": total, "selected_rows": selected, "sha256": hashlib.sha256(filtered.encode()).hexdigest()})
    return results


def fetch_variable(connection: sqlite3.Connection, args: argparse.Namespace) -> dict[str, Any]:
    plan = resolve(connection, args.variable_id)
    access = plan["access_plan"]
    if args.start_period or args.end_period:
        if access["access_mode"] == "official_sdmx_rest":
            query = urllib.parse.urlencode({
                key: value for key, value in {"startPeriod": args.start_period, "endPeriod": args.end_period}.items() if value
            })
            access = {**access, "request_url": access["request_url"] + ("?" + query if query else "")}
            plan["access_plan"] = access
    if args.dry_run:
        return {"operation": "fetch_variable", "status": "dry_run", "plan": plan}
    if not args.output_dir:
        raise ValueError("--output-dir is required unless --dry-run is used")
    output = Path(args.output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    payload, headers, status = fetch_bytes(access["request_url"], access.get("request_headers", {}), args.timeout)
    content_type = headers.get("content-type", "application/octet-stream")
    suffix = ".zip" if zipfile.is_zipfile(BytesIO(payload)) else Path(urllib.parse.urlparse(access["request_url"]).path).suffix
    if not suffix:
        suffix = ".csv" if "csv" in content_type.casefold() else ".bin"
    stem = safe_name(plan["variable_label"])
    raw_path = output / f"{stem}-raw{suffix}"
    if raw_path.exists():
        raise FileExistsError(f"refusing to overwrite existing result: {raw_path}")
    raw_path.write_bytes(payload)
    filtered = filtered_outputs(payload, content_type, output, stem, args.country, args.start_period, args.end_period)
    result = {
        "operation": "fetch_variable",
        "status": "fetched",
        "source_id": SOURCE_ID,
        "variable_id": args.variable_id,
        "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "request_url": access["request_url"],
        "http_status": status,
        "content_type": content_type,
        "raw_path": str(raw_path),
        "size_bytes": len(payload),
        "sha256": sha256_bytes(payload),
        "filters": {"country": args.country, "start_period": args.start_period, "end_period": args.end_period},
        "filtered_outputs": filtered,
        "plan": plan,
    }
    provenance_path = output / f"{stem}-provenance.json"
    provenance_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result["provenance_path"] = str(provenance_path)
    return result


def self_test(connection: sqlite3.Connection) -> dict[str, Any]:
    variables = records(connection, "variables")
    route_counts: dict[str, int] = {}
    unresolved = []
    unresolved_count = 0
    for variable in variables:
        try:
            result = resolve(connection, variable["id"])
            route = result["access_plan"]["access_mode"]
            route_counts[route] = route_counts.get(route, 0) + 1
        except (KeyError, TypeError, ValueError) as exc:
            unresolved_count += 1
            if len(unresolved) < 20:
                unresolved.append({"variable_id": variable.get("id"), "message": str(exc)})
    resolved_count = len(variables) - unresolved_count
    return {
        "operation": "self_test",
        "source_id": SOURCE_ID,
        "status": "ready" if unresolved_count == 0 else "failing",
        "variable_count": len(variables),
        "resolvable_variable_count": resolved_count,
        "unresolved_variable_count": unresolved_count,
        "route_counts": dict(sorted(route_counts.items())),
        "unresolved_examples": unresolved,
        "network_used": False,
    }


def search(connection: sqlite3.Connection, query: str, limit: int) -> dict[str, Any]:
    needle = query.casefold()
    matches = [item for item in records(connection, "variables") if needle in json.dumps(item, ensure_ascii=False).casefold()]
    matches.sort(key=lambda item: item["label"].casefold())
    return {
        "operation": "search",
        "source_id": SOURCE_ID,
        "query": query,
        "total_matches": len(matches),
        "results": [{"id": item["id"], "label": item["label"], "dataset_ids": item["dataset_ids"]} for item in matches[:limit]],
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    self_test_command = commands.add_parser("self-test")
    self_test_command.add_argument("--index", type=Path, required=True)
    search_command = commands.add_parser("search")
    search_command.add_argument("--index", type=Path, required=True)
    search_command.add_argument("--query", required=True)
    search_command.add_argument("--limit", type=int, default=20)
    resolve_command = commands.add_parser("resolve-variable")
    resolve_command.add_argument("--index", type=Path, required=True)
    resolve_command.add_argument("--variable-id", required=True)
    fetch_command = commands.add_parser("fetch-variable")
    fetch_command.add_argument("--index", type=Path, required=True)
    fetch_command.add_argument("--variable-id", required=True)
    fetch_command.add_argument("--dry-run", action="store_true")
    fetch_command.add_argument("--output-dir")
    fetch_command.add_argument("--country")
    fetch_command.add_argument("--start-period")
    fetch_command.add_argument("--end-period")
    fetch_command.add_argument("--timeout", type=int, default=180)
    return root


def main() -> None:
    args = parser().parse_args()
    if hasattr(args, "timeout") and args.timeout < 1:
        raise SystemExit("--timeout must be positive")
    connection = connect(args.index.expanduser().resolve())
    try:
        if args.command == "self-test":
            result = self_test(connection)
        elif args.command == "search":
            if args.limit < 1:
                raise ValueError("--limit must be positive")
            result = search(connection, args.query, args.limit)
        elif args.command == "resolve-variable":
            result = resolve(connection, args.variable_id)
        else:
            result = fetch_variable(connection, args)
    except (FileExistsError, RuntimeError, ValueError) as exc:
        emit({"operation": args.command, "status": "error", "error": type(exc).__name__, "message": str(exc)})
        raise SystemExit(1) from exc
    finally:
        connection.close()
    emit(result)


if __name__ == "__main__":
    main()
