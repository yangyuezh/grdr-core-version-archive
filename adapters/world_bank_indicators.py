#!/usr/bin/env python3
"""Access World Bank Indicators API v2 with provenance-bearing JSON output."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


BASE_URL = "https://api.worldbank.org/v2"
ADAPTER_ID = "grdr:adapter:world-bank-indicators-api-v2"
USER_AGENT = "GRDR/0.1 agent research data infrastructure"


def fetch(path: str, parameters: dict[str, Any], timeout: int) -> None:
    query = urllib.parse.urlencode(
        {key: value for key, value in parameters.items() if value is not None}
    )
    url = f"{BASE_URL}/{path}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
            status = response.status
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "adapter_id": ADAPTER_ID,
                    "request_url": url,
                    "error": type(exc).__name__,
                    "message": str(exc),
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    output = {
        "adapter_id": ADAPTER_ID,
        "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "request_url": url,
        "http_status": status,
        "upstream": "World Bank Indicators API v2",
        "response": payload,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=30)
    commands = parser.add_subparsers(dest="command", required=True)

    metadata = commands.add_parser("indicator-metadata")
    metadata.add_argument("indicator_code")

    data = commands.add_parser("indicator-data")
    data.add_argument("indicator_code")
    data.add_argument("--economies", default="all")
    data.add_argument("--start")
    data.add_argument("--end")
    data.add_argument("--page", type=int, default=1)
    data.add_argument("--per-page", type=int, default=1000)

    commands.add_parser("sources")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.timeout < 1:
        raise SystemExit("--timeout must be positive")
    if args.command == "indicator-metadata":
        code = urllib.parse.quote(args.indicator_code, safe="")
        fetch(f"indicator/{code}", {"format": "json"}, args.timeout)
        return
    if args.command == "indicator-data":
        code = urllib.parse.quote(args.indicator_code, safe="")
        economies = urllib.parse.quote(args.economies, safe=";")
        date_range = None
        if args.start or args.end:
            date_range = f"{args.start or ''}:{args.end or ''}".strip(":")
        fetch(
            f"country/{economies}/indicator/{code}",
            {
                "format": "json",
                "date": date_range,
                "page": args.page,
                "per_page": args.per_page,
            },
            args.timeout,
        )
        return
    fetch("source", {"format": "json", "per_page": 1000}, args.timeout)


if __name__ == "__main__":
    main()
