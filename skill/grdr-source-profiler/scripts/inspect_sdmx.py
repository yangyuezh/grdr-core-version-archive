#!/usr/bin/env python3
"""Inspect SDMX 2.1 dataflows, data structures, and codelists as JSON."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def label(element: ET.Element, kind: str = "Name") -> str | None:
    for child in element.iter():
        if local(child.tag) == kind and child.text and child.text.strip():
            return " ".join(child.text.split())
    return None


def fetch(url: str, timeout: int, accept: str = "application/vnd.sdmx.structure+xml;version=2.1") -> tuple[int, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "GRDR source profiler SDMX inspector/0.1",
            "Accept": accept,
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.read()


def enum_ref(component: ET.Element) -> dict | None:
    for child in component.iter():
        if local(child.tag) != "Enumeration":
            continue
        for ref in child.iter():
            if local(ref.tag) == "Ref":
                return {
                    "agency_id": ref.attrib.get("agencyID"),
                    "id": ref.attrib.get("id"),
                    "version": ref.attrib.get("version"),
                    "class": ref.attrib.get("class"),
                }
    return None


def dataflows(payload: bytes) -> list[dict]:
    root = ET.fromstring(payload)
    results = []
    for item in root.iter():
        if local(item.tag) != "Dataflow":
            continue
        structure = None
        for ref in item.iter():
            if local(ref.tag) == "Ref" and ref.attrib.get("class") == "DataStructure":
                structure = dict(ref.attrib)
                break
        results.append(
            {
                "agency_id": item.attrib.get("agencyID"),
                "id": item.attrib.get("id"),
                "version": item.attrib.get("version"),
                "name": label(item),
                "description": label(item, "Description"),
                "data_structure": structure,
            }
        )
    return results


def structure(payload: bytes) -> dict:
    root = ET.fromstring(payload)
    dsd = next((item for item in root.iter() if local(item.tag) == "DataStructure"), None)
    if dsd is None:
        raise ValueError("response contains no DataStructure")
    components = []
    for item in dsd.iter():
        kind = local(item.tag)
        if kind not in {"Dimension", "TimeDimension", "PrimaryMeasure", "Attribute"} or "id" not in item.attrib:
            continue
        components.append(
            {
                "id": item.attrib["id"],
                "component_type": kind,
                "position": int(item.attrib["position"]) if item.attrib.get("position", "").isdigit() else None,
                "assignment_status": item.attrib.get("assignmentStatus"),
                "enumeration": enum_ref(item),
            }
        )
    components.sort(key=lambda row: (row["position"] is None, row["position"] or 999, row["component_type"], row["id"]))
    return {
        "agency_id": dsd.attrib.get("agencyID"),
        "id": dsd.attrib.get("id"),
        "version": dsd.attrib.get("version"),
        "name": label(dsd),
        "components": components,
    }


def codelists(payload: bytes, requested_id: str | None = None) -> list[dict]:
    root = ET.fromstring(payload)
    results = []
    for item in root.iter():
        if local(item.tag) != "Codelist" or (requested_id and item.attrib.get("id") != requested_id):
            continue
        codes = [
            {"id": code.attrib.get("id"), "name": label(code), "description": label(code, "Description")}
            for code in item
            if local(code.tag) == "Code"
        ]
        results.append(
            {
                "agency_id": item.attrib.get("agencyID"),
                "id": item.attrib.get("id"),
                "version": item.attrib.get("version"),
                "name": label(item),
                "code_count": len(codes),
                "codes": codes,
            }
        )
    return results


def endpoint(base_url: str, *parts: str) -> str:
    return "/".join([base_url.rstrip("/"), *(urllib.parse.quote(part, safe="") for part in parts)])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=30)
    commands = parser.add_subparsers(dest="command", required=True)
    flows = commands.add_parser("list-dataflows")
    flows.add_argument("base_url")
    describe = commands.add_parser("describe-structure")
    describe.add_argument("base_url")
    describe.add_argument("agency_id")
    describe.add_argument("structure_id")
    describe.add_argument("version", nargs="?", default="latest")
    codes = commands.add_parser("list-codelist")
    codes.add_argument("base_url")
    codes.add_argument("agency_id")
    codes.add_argument("codelist_id")
    codes.add_argument("version", nargs="?", default="latest")
    probe = commands.add_parser("probe-data")
    probe.add_argument("base_url")
    probe.add_argument("dataflow_id")
    probe.add_argument("key", help="Ordered SDMX dimension key; use dots for wildcards")
    probe.add_argument("--start-period")
    probe.add_argument("--end-period")
    args = parser.parse_args()
    if args.timeout < 1:
        raise SystemExit("--timeout must be positive")
    if args.command == "probe-data":
        url = endpoint(args.base_url, "data", args.dataflow_id, args.key)
        query = urllib.parse.urlencode(
            {
                key: value
                for key, value in {"startPeriod": args.start_period, "endPeriod": args.end_period}.items()
                if value
            }
        )
        if query:
            url = f"{url}?{query}"
        try:
            status, payload = fetch(url, args.timeout, "application/vnd.sdmx.genericdata+xml;version=2.1")
            result = {
                "operation": "probe_data",
                "request_url": url,
                "status": "passing",
                "http_status": status,
                "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "byte_count": len(payload),
                "preview": payload[:500].decode("utf-8", "replace"),
            }
            exit_code = 0
        except Exception as exc:  # Preserve the concrete upstream failure in machine-readable output.
            result = {
                "operation": "probe_data",
                "request_url": url,
                "status": "failing",
                "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "error": type(exc).__name__,
                "message": str(exc),
            }
            exit_code = 1
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        raise SystemExit(exit_code)
    if args.command == "list-dataflows":
        url, parse = endpoint(args.base_url, "dataflow", "all", "all", "latest"), dataflows
    elif args.command == "describe-structure":
        url, parse = endpoint(args.base_url, "datastructure", args.agency_id, args.structure_id, args.version), structure
    else:
        url = endpoint(args.base_url, "codelist", args.agency_id, args.codelist_id, args.version)
        parse = lambda payload: codelists(payload, args.codelist_id)
    status, payload = fetch(url, args.timeout)
    print(
        json.dumps(
            {
                "operation": args.command.replace("-", "_"),
                "request_url": url,
                "http_status": status,
                "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "response": parse(payload),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
