#!/usr/bin/env python3
"""Inspect and query UNdata's SDMX REST service with provenance-bearing JSON."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any


BASE_URL = "https://data.un.org/ws/rest"
ADAPTER_ID = "grdr:adapter:undata-sdmx"
USER_AGENT = "GRDR/0.5 agent research data infrastructure"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(element: ET.Element, name: str) -> str | None:
    for child in element.iter():
        if local_name(child.tag) == name and child.text:
            value = " ".join(child.text.split())
            if value:
                return value
    return None


def fetch(url: str, timeout: int, accept: str = "application/vnd.sdmx.structure+xml;version=2.1") -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read(4096).decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"{type(exc).__name__}: {exc}") from exc


def provenance(url: str, status: int) -> dict[str, Any]:
    return {
        "adapter_id": ADAPTER_ID,
        "upstream": "UNdata SDMX REST service",
        "request_url": url,
        "http_status": status,
        "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }


def parse_dataflows(payload: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(payload)
    results = []
    for element in root.iter():
        if local_name(element.tag) != "Dataflow":
            continue
        structure_ref = None
        for descendant in element.iter():
            if local_name(descendant.tag) == "Ref" and descendant.attrib.get("class") == "DataStructure":
                structure_ref = dict(descendant.attrib)
                break
        results.append(
            {
                "agency_id": element.attrib.get("agencyID"),
                "id": element.attrib.get("id"),
                "version": element.attrib.get("version"),
                "name": child_text(element, "Name"),
                "description": child_text(element, "Description"),
                "data_structure": structure_ref,
            }
        )
    return results


def enumeration_ref(component: ET.Element) -> dict[str, Any] | None:
    for element in component.iter():
        if local_name(element.tag) != "Enumeration":
            continue
        for descendant in element.iter():
            if local_name(descendant.tag) == "Ref":
                return {
                    "agency_id": descendant.attrib.get("agencyID"),
                    "id": descendant.attrib.get("id"),
                    "version": descendant.attrib.get("version"),
                    "class": descendant.attrib.get("class"),
                }
    return None


def parse_datastructure(payload: bytes) -> dict[str, Any]:
    root = ET.fromstring(payload)
    structure = next((item for item in root.iter() if local_name(item.tag) == "DataStructure"), None)
    if structure is None:
        raise ValueError("response contains no DataStructure")
    components = []
    supported = {"Dimension", "TimeDimension", "PrimaryMeasure", "Attribute"}
    for element in structure.iter():
        kind = local_name(element.tag)
        if kind not in supported or "id" not in element.attrib:
            continue
        components.append(
            {
                "id": element.attrib["id"],
                "component_type": kind,
                "position": int(element.attrib["position"]) if element.attrib.get("position", "").isdigit() else None,
                "assignment_status": element.attrib.get("assignmentStatus"),
                "concept_identity": next(
                    (
                        dict(ref.attrib)
                        for child in element
                        if local_name(child.tag) == "ConceptIdentity"
                        for ref in child.iter()
                        if local_name(ref.tag) == "Ref"
                    ),
                    None,
                ),
                "enumeration": enumeration_ref(element),
            }
        )
    components.sort(key=lambda item: (item["position"] is None, item["position"] or 999, item["component_type"], item["id"]))
    return {
        "agency_id": structure.attrib.get("agencyID"),
        "id": structure.attrib.get("id"),
        "version": structure.attrib.get("version"),
        "name": child_text(structure, "Name"),
        "components": components,
    }


def parse_codelist(payload: bytes, requested_id: str | None = None) -> list[dict[str, Any]]:
    root = ET.fromstring(payload)
    output = []
    for codelist in root.iter():
        if local_name(codelist.tag) != "Codelist":
            continue
        if requested_id and codelist.attrib.get("id") != requested_id:
            continue
        codes = []
        for code in codelist:
            if local_name(code.tag) != "Code":
                continue
            codes.append({"id": code.attrib.get("id"), "name": child_text(code, "Name"), "description": child_text(code, "Description")})
        output.append(
            {
                "agency_id": codelist.attrib.get("agencyID"),
                "id": codelist.attrib.get("id"),
                "version": codelist.attrib.get("version"),
                "name": child_text(codelist, "Name"),
                "code_count": len(codes),
                "codes": codes,
            }
        )
    return output


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def safe_run(url: str, timeout: int, parser: Any, operation: str, accept: str = "application/vnd.sdmx.structure+xml;version=2.1") -> None:
    try:
        status, payload = fetch(url, timeout, accept)
        emit({**provenance(url, status), "operation": operation, "response": parser(payload)})
    except (RuntimeError, ValueError, ET.ParseError) as exc:
        emit({"adapter_id": ADAPTER_ID, "operation": operation, "request_url": url, "error": type(exc).__name__, "message": str(exc)})
        raise SystemExit(1) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=30)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list-dataflows")

    structure = commands.add_parser("describe-structure")
    structure.add_argument("agency_id")
    structure.add_argument("structure_id")
    structure.add_argument("version", nargs="?", default="latest")

    codelist = commands.add_parser("list-codelist")
    codelist.add_argument("agency_id")
    codelist.add_argument("codelist_id")
    codelist.add_argument("version", nargs="?", default="latest")

    data = commands.add_parser("get-data")
    data.add_argument("dataflow_id")
    data.add_argument("key", help="Ordered SDMX dimension key; use dots for wildcards")
    data.add_argument("--start-period")
    data.add_argument("--end-period")

    probe = commands.add_parser("probe")
    probe.add_argument("--dataflow", default="DF_UNData_UNFCC")
    probe.add_argument("--key", default="A.EN_ATM_PFCE.DNK.Gg_CO2")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.timeout < 1:
        raise SystemExit("--timeout must be positive")
    if args.command == "list-dataflows":
        url = f"{BASE_URL}/dataflow/all/all/latest"
        safe_run(url, args.timeout, parse_dataflows, "list_dataflows")
        return
    if args.command == "describe-structure":
        url = f"{BASE_URL}/datastructure/{urllib.parse.quote(args.agency_id, safe='')}/{urllib.parse.quote(args.structure_id, safe='')}/{urllib.parse.quote(args.version, safe='')}"
        safe_run(url, args.timeout, parse_datastructure, "describe_datastructure")
        return
    if args.command == "list-codelist":
        url = f"{BASE_URL}/codelist/{urllib.parse.quote(args.agency_id, safe='')}/{urllib.parse.quote(args.codelist_id, safe='')}/{urllib.parse.quote(args.version, safe='')}"
        safe_run(url, args.timeout, lambda body: parse_codelist(body, args.codelist_id), "list_codelist_codes")
        return
    if args.command == "get-data":
        base = f"{BASE_URL}/data/{urllib.parse.quote(args.dataflow_id, safe='')}/{urllib.parse.quote(args.key, safe='.+')}"
        query = urllib.parse.urlencode({key: value for key, value in {"startPeriod": args.start_period, "endPeriod": args.end_period}.items() if value})
        url = f"{base}?{query}" if query else base
        safe_run(url, args.timeout, lambda body: {"byte_count": len(body), "preview": body[:1000].decode("utf-8", "replace")}, "get_data", "application/vnd.sdmx.genericdata+xml;version=2.1")
        return

    # Probe is deliberately compact: it verifies metadata discovery and reports
    # the known data path independently, so a data failure does not erase usable
    # structural metadata.
    metadata_checks = [
        ("dataflows", f"{BASE_URL}/dataflow/all/all/latest", parse_dataflows),
        ("energy_structure", f"{BASE_URL}/datastructure/UNSD/DSD_ENERGY/1.2", parse_datastructure),
    ]

    def run_metadata_check(spec: tuple[str, str, Any]) -> dict[str, Any]:
        name, url, parser_fn = spec
        try:
            status, body = fetch(url, args.timeout)
            parsed = parser_fn(body)
            return {"name": name, "status": "passing", "http_status": status, "result_count": len(parsed) if isinstance(parsed, list) else len(parsed["components"])}
        except (RuntimeError, ValueError, ET.ParseError) as exc:
            return {"name": name, "status": "failing", "message": str(exc)}

    def run_data_check() -> dict[str, Any]:
        data_url = f"{BASE_URL}/data/{urllib.parse.quote(args.dataflow, safe='')}/{urllib.parse.quote(args.key, safe='.+')}?startPeriod=2000&endPeriod=2000"
        try:
            status, body = fetch(data_url, args.timeout, "application/vnd.sdmx.genericdata+xml;version=2.1")
            return {"name": "data", "status": "passing", "http_status": status, "byte_count": len(body), "request_url": data_url}
        except RuntimeError as exc:
            return {"name": "data", "status": "failing", "message": str(exc), "request_url": data_url}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(run_metadata_check, spec) for spec in metadata_checks]
        futures.append(executor.submit(run_data_check))
        checks = [future.result() for future in futures]
    emit({"adapter_id": ADAPTER_ID, "operation": "probe", "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(), "status": "passing" if all(item["status"] == "passing" for item in checks) else "degraded", "checks": checks})


if __name__ == "__main__":
    main()
