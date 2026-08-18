#!/usr/bin/env python3
"""Build the evidence-backed UNdata catalog snapshot and deep SDMX examples.

This curator is intentionally source-specific.  It parses the official UNdata
catalog, asserts the expected snapshot boundary, and merges deterministic GRDR
records.  Network access is only used when the operator explicitly runs this
script; normal registry validation and catalog generation remain offline.
"""

from __future__ import annotations

import argparse
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urljoin
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry"
CATALOG_URL = "https://data.un.org/DataMartInfo.aspx"
ABOUT_URL = "https://data.un.org/Host.aspx?Content=About"
API_URL = "https://data.un.org/Host.aspx?Content=API"
TERMS_URL = "https://data.un.org/Host.aspx?Content=UNdataUse"
DATAFLOW_URL = "https://data.un.org/ws/rest/dataflow/all/all/latest"
ENERGY_DSD_URL = "https://data.un.org/ws/rest/datastructure/UNSD/DSD_ENERGY/1.2"
GHG_DSD_URL = "https://data.un.org/ws/rest/datastructure/UNSD/DSD_GHG_UNDATA/1.0"
STAMP = "2026-08-18T00:00:00Z"
SNAPSHOT = "2026-08-18"

EXPECTED_DATASET_IDS = [
    "ComTrade", "POP", "EDATA", "ENV", "FAO", "GenderStat", "GHG", "33",
    "32", "16", "UNIDO", "ICS", "IFS", "30", "LABORSTA", "MDG",
    "SNAAMA", "SNA", "18", "SDGs", "SOWC", "UNESCO", "UNAIDS", "UNHCR",
    "KI", "WHO", "29", "WDI", "22", "25", "CLINO", "PopDiv", "WorldStat",
    "ITU", "31", "19",
]
EXPECTED_GLOSSARY_IDS = ["DemogG", "EnvironmentG", "SNAAMAG", "SDMX", "SNAG", "PopDivG"]


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if value:
            self.parts.append(value)


def text(fragment: str) -> str:
    parser = TextExtractor()
    parser.feed(fragment)
    return unescape(" ".join(parser.parts)).replace("\xa0", " ").strip()


def fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": "GRDR/0.5 source profiler"})
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", "replace")


def parse_catalog(html: str) -> tuple[list[dict], list[dict]]:
    blocks = re.findall(
        r'<div class="DataMart" id="([^"]+)"[^>]*>(.*?)(?=</div></div><div class="GoTop">)',
        html,
        re.S,
    )
    parsed: list[dict] = []
    for catalog_id, block in blocks:
        title_match = re.search(r"<h1>(.*?)</h1>", block, re.S)
        provider_match = re.search(
            r'<h2>.*?<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, re.S
        )
        description_match = re.search(r'<div class="MetaInfo">(.*?)</div>', block, re.S)
        update_match = re.search(r'<div class="Update">(.*?)</div>', block, re.S)
        if not all((title_match, provider_match, description_match, update_match)):
            raise RuntimeError(f"UNdata catalog block {catalog_id!r} changed shape")
        update_text = text(update_match.group(1))
        last_match = re.search(r"Last update in UNdata:\s*(.*?)\s+Next update", update_text)
        next_match = re.search(r"Next update in UNdata:\s*(.*)$", update_text)
        parsed.append(
            {
                "catalog_id": catalog_id,
                "name": text(title_match.group(1)),
                "provider_name": text(provider_match.group(2)),
                "provider_url": urljoin(CATALOG_URL, provider_match.group(1)),
                "description": text(description_match.group(1)),
                "last_update": last_match.group(1).strip() if last_match else None,
                "next_update": next_match.group(1).strip() if next_match else None,
            }
        )
    datasets = parsed[: len(EXPECTED_DATASET_IDS)]
    glossaries = parsed[len(EXPECTED_DATASET_IDS) :]
    if [item["catalog_id"] for item in datasets] != EXPECTED_DATASET_IDS:
        raise RuntimeError("UNdata dataset catalog boundary changed; inspect before updating GRDR")
    if [item["catalog_id"] for item in glossaries] != EXPECTED_GLOSSARY_IDS:
        raise RuntimeError("UNdata glossary catalog boundary changed; inspect before updating GRDR")
    return datasets, glossaries


def slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", normalized.casefold()).strip("-")


def iso_date(value: str | None) -> str | None:
    if not value or not re.fullmatch(r"\d{4}/\d{2}/\d{2}", value):
        return None
    return value.replace("/", "-")


def lifecycle(item: dict) -> str:
    content = item["description"].casefold()
    if "currently archived" in content:
        return "archived"
    if "no longer updated" in content or "no longer update" in content:
        return "deprecated"
    next_update = iso_date(item["next_update"])
    if next_update and next_update >= SNAPSHOT:
        return "active"
    return "unknown"


PROVIDER_IDS = {
    "United Nations Statistics Division": "grdr:institution:unsd",
    "Food and Agriculture Organization": "grdr:institution:fao",
    "United Nations Framework Convention on Climate Change": "grdr:institution:unfccc",
    "United Nations Office on Drugs and Crime": "grdr:institution:unodc",
    "United Nations Development Programme": "grdr:institution:undp",
    "United Nations Industrial Development Organization": "grdr:institution:unido",
    "International Monetary Fund": "grdr:institution:imf",
    "International Labour Organization": "grdr:institution:ilo",
    "Organisation for Economic Co-operation and Development": "grdr:institution:oecd",
    "United Nations Children's Fund": "grdr:institution:unicef",
    "UNESCO Institute for Statistics": "grdr:institution:unesco-uis",
    "Joint United Nations Programme on HIV/AIDS": "grdr:institution:unaids",
    "United Nations High Commissioner for Refugees": "grdr:institution:unhcr",
    "World Health Organization": "grdr:institution:who",
    "United Nations Population Division": "grdr:institution:un-population-division",
    "The World Bank": "grdr:institution:world-bank",
    "World Meteorological Organization": "grdr:institution:wmo",
    "International Telecommunications Union": "grdr:institution:itu",
    "World Tourism Organization": "grdr:institution:un-tourism",
}

INSTITUTION_ALIASES = {
    "grdr:institution:unfccc": ["UNFCCC"],
    "grdr:institution:unodc": ["UNODC"],
    "grdr:institution:undp": ["UNDP"],
    "grdr:institution:unido": ["UNIDO"],
    "grdr:institution:unicef": ["UNICEF"],
    "grdr:institution:unaids": ["UNAIDS"],
    "grdr:institution:unhcr": ["UNHCR"],
    "grdr:institution:un-population-division": ["UN DESA Population Division"],
    "grdr:institution:wmo": ["WMO"],
    "grdr:institution:itu": ["ITU"],
    "grdr:institution:un-tourism": ["UN Tourism", "UNWTO"],
}


DEEP_DATASET_IDS = {
    "EDATA": "grdr:dataset:undata-energy-statistics",
    "GHG": "grdr:dataset:undata-greenhouse-gas-inventory",
}


def dataset_id(item: dict) -> str:
    return DEEP_DATASET_IDS.get(item["catalog_id"], f"grdr:dataset:undata-{slug(item['name'])}")


def catalog_evidence() -> dict:
    return {
        "url": CATALOG_URL,
        "title": "UNdata datamarts and update calendar",
        "publisher": "United Nations Statistics Division",
        "evidence_type": "official_catalog",
        "supports": ["identity", "description", "provider", "catalog_membership", "update_metadata"],
        "retrieved_at": STAMP,
        "archived_url": None,
    }


def dataset_record(item: dict) -> dict:
    did = dataset_id(item)
    resources = ["grdr:resource:undata-datamart-catalog", "grdr:resource:undata-terms-of-use"]
    scope = {
        "disciplines": ["multidisciplinary"],
        "topics": [],
        "population": None,
        "observation_units": ["country-period or other dataset-specific unit"],
        "geographic_coverage": None,
        "spatial_resolution": None,
        "temporal_coverage": None,
        "temporal_resolution": None,
        "modalities": ["tabular"],
    }
    methodology = {
        "data_generating_processes": [],
        "harmonization": "unknown",
        "modeled_estimates": "unknown",
        "methodology_url": None,
        "limitations": [
            "This catalog-level record verifies identity, provider, description, and update metadata only.",
            "Variables, coverage, methodology, comparability, and current access must be profiled from the responsible source before research use.",
        ],
    }
    if item["catalog_id"] == "EDATA":
        scope.update(
            {
                "disciplines": ["energy statistics", "environmental science", "economics"],
                "topics": ["energy production", "energy trade", "energy conversion", "final energy consumption"],
                "population": "Countries and areas represented in the UNdata Energy Statistics SDMX structure.",
                "observation_units": ["country-commodity-transaction-year"],
                "geographic_coverage": "251 reference-area codes in the checked SDMX codelist; actual series availability varies.",
                "spatial_resolution": "Country or area",
                "temporal_coverage": "1990 onward according to the UNdata catalog; series-specific availability varies.",
                "temporal_resolution": "Annual in the profiled dataflow",
            }
        )
        methodology.update(
            {
                "data_generating_processes": ["official statistics", "national reporting", "international compilation"],
                "harmonization": "within_source",
                "modeled_estimates": "unknown",
                "methodology_url": "https://unstats.un.org/unsd/energystats/questionnaire/documents/Energy-Questionnaire-Guidelines.pdf",
                "limitations": [
                    "Coverage varies by country, commodity, transaction, and year.",
                    "Observation units vary by commodity and must be read from UNIT_MEASURE and UNIT_MULT.",
                    "The checked SDMX structure endpoint worked, but documented observation queries timed out or returned HTTP 500 across live probes on 2026-08-18.",
                ],
            }
        )
        resources += [
            "grdr:resource:undata-energy-browser",
            "grdr:resource:undata-energy-dsd",
            "grdr:resource:undata-api-manual",
            "grdr:resource:undata-dataflow-catalog",
        ]
    elif item["catalog_id"] == "GHG":
        scope.update(
            {
                "disciplines": ["climate science", "environmental science", "public policy"],
                "topics": ["greenhouse gas emissions", "carbon dioxide", "methane", "nitrous oxide", "fluorinated gases"],
                "population": "Parties and areas represented in the UNdata UNFCCC SDMX structure.",
                "observation_units": ["party-gas-year"],
                "geographic_coverage": "43 reference-area codes in the checked SDMX codelist; actual series availability varies.",
                "spatial_resolution": "Party or area",
                "temporal_coverage": "1990 to the latest submitted year, subject to reporting availability.",
                "temporal_resolution": "Annual in the profiled dataflow",
            }
        )
        methodology.update(
            {
                "data_generating_processes": ["national greenhouse gas inventories", "international compilation", "modelled estimates"],
                "harmonization": "within_source",
                "modeled_estimates": "some",
                "methodology_url": "https://www.ipcc-nggip.iges.or.jp/public/2006gl/",
                "limitations": [
                    "The UNdata catalog republishes the most recently submitted inventory information; reporting years and completeness vary by Party.",
                    "The profiled indicators exclude land use, land-use change and forestry (LULUCF).",
                    "The checked SDMX structure endpoint worked, but documented observation queries timed out or returned HTTP 500 across live probes on 2026-08-18.",
                ],
            }
        )
        resources += [
            "grdr:resource:undata-ghg-browser",
            "grdr:resource:undata-ghg-dsd",
            "grdr:resource:undata-api-manual",
            "grdr:resource:undata-dataflow-catalog",
        ]
    return {
        "schema_version": "0.1.0",
        "id": did,
        "name": item["name"],
        "aliases": [],
        "source_native": {
            "catalog_id": item["catalog_id"],
            "catalog_url": f"{CATALOG_URL}#{item['catalog_id']}",
            "provider_name": item["provider_name"],
            "provider_url": item["provider_url"],
            "lifecycle_status": lifecycle(item),
            "last_upstream_update": item["last_update"],
            "next_upstream_update": item["next_update"],
        },
        "source_ids": ["grdr:source:undata"],
        "description": item["description"],
        "scope": scope,
        "release": {
            "current_version": None,
            "release_date": iso_date(item["last_update"]),
            "update_frequency": f"UNdata catalog lists next update as {item['next_update']}." if item["next_update"] else None,
            "revision_policy_known": None,
            "historical_vintages_available": None,
        },
        "methodology": methodology,
        "resource_ids": resources,
        "citation": {"preferred_citation": None, "doi": None, "citation_url": f"{CATALOG_URL}#{item['catalog_id']}"},
        "verification": {
            "status": "partially_verified",
            "last_verified_at": STAMP,
            "notes": "Official UNdata catalog metadata checked. Deep resource, structure, variable, and construct profiling is complete only for Energy Statistics and Greenhouse Gas Inventory Data in this snapshot.",
        },
        "evidence": [catalog_evidence()],
    }


def institution_records(items: list[dict]) -> list[dict]:
    records = []
    seen: set[str] = set()
    current = {item["id"]: item for item in load_records("institutions.jsonl")}
    for item in items:
        iid = PROVIDER_IDS[item["provider_name"]]
        if iid in seen or iid == "grdr:institution:unsd":
            continue
        seen.add(iid)
        provider_evidence = {
            "url": CATALOG_URL,
            "title": "UNdata datamarts and update calendar",
            "publisher": "United Nations Statistics Division",
            "evidence_type": "official_catalog",
            "supports": ["institution_identity", "dataset_provider_role"],
            "retrieved_at": STAMP,
            "archived_url": None,
        }
        if iid in current:
            record = current[iid]
            record["verification"] = {
                "status": "partially_verified",
                "last_verified_at": STAMP,
                "notes": "Institution identity and its upstream provider role in UNdata are verified from the official catalog; the full institutional mandate remains outside this profiling pass.",
            }
            evidence = record.get("evidence", [])
            evidence = [entry for entry in evidence if entry.get("url") != CATALOG_URL]
            record["evidence"] = [*evidence, provider_evidence]
            records.append(record)
            continue
        records.append(
            {
                "schema_version": "0.1.0",
                "id": iid,
                "name": item["provider_name"],
                "aliases": INSTITUTION_ALIASES.get(iid, []),
                "institution_type": "intergovernmental_organization",
                "jurisdiction": "International / United Nations system",
                "primary_url": item["provider_url"],
                "verification": {
                    "status": "partially_verified",
                    "last_verified_at": STAMP,
                    "notes": "Institution identity and upstream provider role are verified from the official UNdata catalog; its full mandate requires separate institutional profiling.",
                },
                "evidence": [provider_evidence],
            }
        )
    return records


def resource_records(dataset_ids: list[str]) -> list[dict]:
    energy = DEEP_DATASET_IDS["EDATA"]
    ghg = DEEP_DATASET_IDS["GHG"]
    common_evidence = {
        "publisher": "United Nations Statistics Division",
        "retrieved_at": STAMP,
        "archived_url": None,
    }

    def record(rid: str, name: str, datasets: list[str], kind: str, url: str, formats: list[str],
               machine: str, evidence_type: str, supports: list[str], status: str = "verified",
               note: str | None = None) -> dict:
        return {
            "schema_version": "0.1.0", "id": rid, "name": name,
            "source_id": "grdr:source:undata", "dataset_ids": datasets,
            "resource_type": kind, "url": url, "formats": formats,
            "access": {
                "availability": "open", "authentication": "none", "machine_access": machine,
                "rate_limit_known": None, "license_status": "documented_open",
                "notes": note,
            },
            "verification": {"status": status, "last_verified_at": STAMP, "notes": note},
            "evidence": [
                {"url": url, "title": name, "evidence_type": evidence_type, "supports": supports, **common_evidence}
            ],
        }

    return [
        record("grdr:resource:undata-datamart-catalog", "UNdata datamart catalog and update calendar", dataset_ids, "catalog", CATALOG_URL, ["HTML"], "partial", "official_catalog", ["catalog", "provider", "description", "update_metadata"]),
        record("grdr:resource:undata-terms-of-use", "UNdata terms of use", dataset_ids, "documentation", TERMS_URL, ["HTML"], "none", "license", ["license", "attribution", "republishing_policy"]),
        record("grdr:resource:undata-api-manual", "UNdata SDMX API manual", [energy, ghg], "documentation", API_URL, ["HTML"], "none", "api_documentation", ["sdmx_api", "formats", "query_documentation"]),
        record("grdr:resource:undata-dataflow-catalog", "UNdata SDMX dataflow catalog", [energy, ghg], "api", DATAFLOW_URL, ["SDMX-XML"], "documented", "api_documentation", ["dataflow_inventory", "structure_discovery"]),
        record("grdr:resource:undata-energy-browser", "UNdata Energy Statistics browser", [energy], "browser_query", "https://data.un.org/Browse.aspx?d=EDATA", ["HTML", "CSV"], "partial", "official_documentation", ["interactive_access", "csv_download"]),
        record("grdr:resource:undata-energy-dsd", "UNdata Energy Statistics SDMX data structure", [energy], "api", ENERGY_DSD_URL, ["SDMX-XML"], "documented", "api_documentation", ["dimensions", "attributes", "measure", "codelists"]),
        record("grdr:resource:undata-ghg-browser", "UNdata Greenhouse Gas Inventory browser", [ghg], "browser_query", "https://data.un.org/Browse.aspx?d=GHG", ["HTML", "CSV"], "partial", "official_documentation", ["interactive_access", "csv_download"]),
        record("grdr:resource:undata-ghg-dsd", "UNdata Greenhouse Gas Inventory SDMX data structure", [ghg], "api", GHG_DSD_URL, ["SDMX-XML"], "documented", "api_documentation", ["dimensions", "measure", "codelists"]),
        record("grdr:resource:undata-glossary-catalog", "UNdata glossary catalog", [], "catalog", CATALOG_URL, ["HTML"], "partial", "official_catalog", ["six_glossary_entries", "definitions_catalog"]),
    ]


def data_element_records() -> list[dict]:
    specs = [
        # dataset, prefix, dataflow, dsd, version, resource, native, label, type, position, role, codelist
        ("energy", "DF_UNDATA_ENERGY", "DSD_ENERGY", "1.2", "energy-dsd", "FREQ", "Frequency", "dimension", 1, ["filter"], ("CL_FREQ", "SDMX", "2.0", None)),
        ("energy", "DF_UNDATA_ENERGY", "DSD_ENERGY", "1.2", "energy-dsd", "REF_AREA", "Reference area", "identifier", 2, ["filter", "join_key", "geographic_key"], ("CL_AREA_NRG", "UNSD", "1.2", 251)),
        ("energy", "DF_UNDATA_ENERGY", "DSD_ENERGY", "1.2", "energy-dsd", "COMMODITY", "Energy commodity", "dimension", 3, ["filter"], ("CL_COMMODITY_NRG", "UNSD", "1.0", 75)),
        ("energy", "DF_UNDATA_ENERGY", "DSD_ENERGY", "1.2", "energy-dsd", "TRANSACTION", "Energy transaction", "dimension", 4, ["filter"], ("CL_TRANSACTION_NRG", "UNSD", "1.1", 216)),
        ("energy", "DF_UNDATA_ENERGY", "DSD_ENERGY", "1.2", "energy-dsd", "TIME_PERIOD", "Time period", "time_dimension", 5, ["time_key", "join_key"], None),
        ("energy", "DF_UNDATA_ENERGY", "DSD_ENERGY", "1.2", "energy-dsd", "OBS_VALUE", "Observation value", "measure", None, ["measure"], None),
        ("energy", "DF_UNDATA_ENERGY", "DSD_ENERGY", "1.2", "energy-dsd", "UNIT_MULT", "Unit multiplier", "attribute", None, ["multiplier"], ("CL_UNIT_MULT", "SDMX", "1.1", None)),
        ("energy", "DF_UNDATA_ENERGY", "DSD_ENERGY", "1.2", "energy-dsd", "UNIT_MEASURE", "Unit of measure", "attribute", None, ["unit"], ("CL_UNIT_MEASURE_NRG", "UNSD", "1.0", 5)),
        ("energy", "DF_UNDATA_ENERGY", "DSD_ENERGY", "1.2", "energy-dsd", "OBS_STATUS", "Observation status", "flag", None, ["status"], ("CL_OBS_STATUS", "SDMX", "2.1", None)),
        ("energy", "DF_UNDATA_ENERGY", "DSD_ENERGY", "1.2", "energy-dsd", "CONVERSION_FACTOR", "Conversion factor", "attribute", None, ["conversion"], None),
        ("ghg", "DF_UNData_UNFCC", "DSD_GHG_UNDATA", "1.0", "ghg-dsd", "FREQ", "Frequency", "dimension", 1, ["filter"], ("CL_FREQ", "UNSD", "1.0", None)),
        ("ghg", "DF_UNData_UNFCC", "DSD_GHG_UNDATA", "1.0", "ghg-dsd", "INDICATOR", "Greenhouse gas indicator", "dimension", 2, ["filter"], ("CL_INDICATOR", "UNSD", "1.0", 7)),
        ("ghg", "DF_UNData_UNFCC", "DSD_GHG_UNDATA", "1.0", "ghg-dsd", "REF_AREA", "Reference area", "identifier", 3, ["filter", "join_key", "geographic_key"], ("CL_REF_AREA", "UNSD", "1.0", 43)),
        ("ghg", "DF_UNData_UNFCC", "DSD_GHG_UNDATA", "1.0", "ghg-dsd", "UNIT", "Unit", "attribute", 4, ["unit", "filter"], ("CL_UNIT", "UNSD", "1.0", 1)),
        ("ghg", "DF_UNData_UNFCC", "DSD_GHG_UNDATA", "1.0", "ghg-dsd", "TIME_PERIOD", "Time period", "time_dimension", 5, ["time_key", "join_key"], None),
        ("ghg", "DF_UNData_UNFCC", "DSD_GHG_UNDATA", "1.0", "ghg-dsd", "OBS_VALUE", "Observation value", "measure", None, ["measure"], None),
    ]
    records = []
    for dataset_key, dataflow, dsd, version, resource_key, native, label, element_type, position, roles, codelist in specs:
        did = DEEP_DATASET_IDS["EDATA" if dataset_key == "energy" else "GHG"]
        dsd_url = ENERGY_DSD_URL if dataset_key == "energy" else GHG_DSD_URL
        codelist_value = None
        if codelist:
            cid, agency, cversion, count = codelist
            codelist_url = f"https://data.un.org/ws/rest/codelist/{agency}/{cid}/{cversion}"
            codelist_value = {"id": cid, "agency_id": agency, "version": cversion, "url": codelist_url, "code_count": count}
        evidence = [{"url": dsd_url, "title": f"UNdata {dataset_key.title()} SDMX data structure", "publisher": "United Nations Statistics Division", "evidence_type": "data_structure", "supports": ["element_identity", "element_type", "position", "representation"], "retrieved_at": STAMP, "archived_url": None}]
        if codelist_value:
            evidence.append({"url": codelist_value["url"], "title": f"UNdata SDMX codelist {codelist_value['id']}", "publisher": "United Nations Statistics Division", "evidence_type": "codelist", "supports": ["codelist_identity", "codes", "code_count"], "retrieved_at": STAMP, "archived_url": None})
        records.append(
            {
                "schema_version": "0.1.0",
                "id": f"grdr:data-element:undata-{dataset_key}-{slug(native)}",
                "name": native,
                "label": label,
                "dataset_ids": [did],
                "resource_ids": [f"grdr:resource:undata-{resource_key}"],
                "element_type": element_type,
                "source_native": {
                    "system": "SDMX 2.1", "agency_id": "UNSD", "dataflow_id": dataflow,
                    "data_structure_id": dsd, "structure_version": version,
                    "native_id": native, "position": position,
                    "attachment_level": "observation" if native in {"OBS_VALUE", "OBS_STATUS", "CONVERSION_FACTOR"} else "series_or_dataset",
                },
                "definition": label,
                "unit": "See the unit attribute for each observation or series." if native == "OBS_VALUE" else None,
                "representation": {"data_type": "decimal" if native in {"OBS_VALUE", "CONVERSION_FACTOR"} else "coded or time value", "allowed_values_note": "See the referenced official codelist." if codelist else None},
                "codelist": codelist_value,
                "roles": roles,
                "verification": {"status": "partially_verified", "last_verified_at": STAMP, "notes": "Element identity, type, position, representation reference, and codelist linkage checked in the official SDMX data structure. Semantic definitions remain limited to the official concept/code labels available in this pass."},
                "evidence": evidence,
            }
        )
    return records


CONSTRUCT_SPECS = {
    "energy-production": ("Energy production", "The quantity of energy commodities produced within the reporting reference area and period.", "physical_quantity"),
    "energy-imports": ("Energy imports", "The quantity of energy commodities entering the reporting reference area during the period.", "physical_quantity"),
    "energy-exports": ("Energy exports", "The quantity of energy commodities leaving the reporting reference area during the period.", "physical_quantity"),
    "total-energy-supply": ("Total energy supply", "The energy supply available to the reporting economy under the UNdata energy transaction classification.", "computed_or_formal"),
    "final-energy-consumption": ("Final energy consumption", "Energy delivered to final consumers under the UNdata energy transaction classification.", "physical_quantity"),
    "industrial-energy-consumption": ("Industrial energy consumption", "Final energy consumption by manufacturing, construction, and non-fuel industry under the UNdata classification.", "physical_quantity"),
    "co2-emissions-excluding-lulucf": ("Carbon dioxide emissions excluding LULUCF", "Reported anthropogenic carbon dioxide emissions excluding land use, land-use change and forestry, expressed as CO2 equivalent.", "environmental"),
    "ghg-emissions-excluding-lulucf": ("Greenhouse gas emissions excluding LULUCF", "Reported anthropogenic greenhouse gas emissions excluding land use, land-use change and forestry, expressed as CO2 equivalent.", "environmental"),
    "methane-emissions-excluding-lulucf": ("Methane emissions excluding LULUCF", "Reported anthropogenic methane emissions excluding land use, land-use change and forestry, expressed as CO2 equivalent.", "environmental"),
    "nitrous-oxide-emissions-excluding-lulucf": ("Nitrous oxide emissions excluding LULUCF", "Reported anthropogenic nitrous oxide emissions excluding land use, land-use change and forestry, expressed as CO2 equivalent.", "environmental"),
    "hfc-emissions": ("Hydrofluorocarbon emissions", "Reported anthropogenic hydrofluorocarbon emissions expressed as CO2 equivalent.", "environmental"),
    "pfc-emissions": ("Perfluorocarbon emissions", "Reported anthropogenic perfluorocarbon emissions expressed as CO2 equivalent.", "environmental"),
    "sf6-emissions": ("Sulphur hexafluoride emissions", "Reported anthropogenic sulphur hexafluoride emissions expressed as CO2 equivalent.", "environmental"),
}


def construct_records() -> list[dict]:
    records = []
    for key, (name, definition, construct_type) in CONSTRUCT_SPECS.items():
        is_energy = key.startswith("energy-") or key in {"total-energy-supply", "final-energy-consumption", "industrial-energy-consumption"}
        url = "https://data.un.org/ws/rest/codelist/UNSD/CL_TRANSACTION_NRG/1.1" if is_energy else "https://data.un.org/ws/rest/codelist/UNSD/CL_INDICATOR/1.0"
        records.append(
            {
                "schema_version": "0.1.0", "id": f"grdr:construct:{key}", "name": name,
                "aliases": [], "definition": definition,
                "domains": ["energy statistics"] if is_energy else ["climate science", "environmental accounting"],
                "construct_type": construct_type, "broader_construct_ids": [],
                "scope_notes": "This construct is bounded by the official UNdata transaction or indicator code used in the linked variable; it is not automatically interchangeable with differently bounded measures.",
                "verification": {"status": "partially_verified", "last_verified_at": STAMP, "notes": "Construct semantics are grounded in the official catalog and SDMX code label; a separate disciplinary standard review remains required for full verification."},
                "evidence": [{"url": url, "title": "UNdata official SDMX structure and codelist", "publisher": "United Nations Statistics Division", "evidence_type": "controlled_vocabulary", "supports": ["construct_boundary", "operationalization"], "retrieved_at": STAMP, "archived_url": None}],
            }
        )
    return records


ENERGY_VARIABLES = [
    ("01", "Production", "energy-production"),
    ("03", "Imports", "energy-imports"),
    ("04", "Exports", "energy-exports"),
    ("GA", "Total energy supply", "total-energy-supply"),
    ("NA", "Final consumption", "final-energy-consumption"),
    ("121", "Consumption by manufacturing, construction and non-fuel industry", "industrial-energy-consumption"),
]
GHG_VARIABLES = [
    ("EN_ATM_METH_XLULUCF", "Methane emissions excluding LULUCF", "methane-emissions-excluding-lulucf"),
    ("EN_ATM_CO2E_XLULUCF", "Carbon dioxide emissions excluding LULUCF", "co2-emissions-excluding-lulucf"),
    ("EN_CLC_GHGE_XLULUCF", "Greenhouse gas emissions excluding LULUCF", "ghg-emissions-excluding-lulucf"),
    ("EN_ATM_HFCE", "Hydrofluorocarbon emissions", "hfc-emissions"),
    ("EN_ATM_NO2E_XLULUCF", "Nitrous oxide emissions excluding LULUCF", "nitrous-oxide-emissions-excluding-lulucf"),
    ("EN_ATM_PFCE", "Perfluorocarbon emissions", "pfc-emissions"),
    ("EN_ATM_SF6E", "Sulphur hexafluoride emissions", "sf6-emissions"),
]


def variable_records() -> list[dict]:
    records = []
    for dataset_key, specs in (("energy", ENERGY_VARIABLES), ("ghg", GHG_VARIABLES)):
        is_energy = dataset_key == "energy"
        did = DEEP_DATASET_IDS["EDATA" if is_energy else "GHG"]
        dataflow = "DF_UNDATA_ENERGY" if is_energy else "DF_UNData_UNFCC"
        dsd = "DSD_ENERGY" if is_energy else "DSD_GHG_UNDATA"
        dimension = "TRANSACTION" if is_energy else "INDICATOR"
        dimension_element = f"grdr:data-element:undata-{dataset_key}-{slug(dimension)}"
        measure_element = f"grdr:data-element:undata-{dataset_key}-obs-value"
        url = "https://data.un.org/ws/rest/codelist/UNSD/CL_TRANSACTION_NRG/1.1" if is_energy else "https://data.un.org/ws/rest/codelist/UNSD/CL_INDICATOR/1.0"
        for code, label, construct_key in specs:
            unit = "Commodity-specific unit with UNIT_MULT multiplier" if is_energy else "Gigagrams (Gg) CO2 equivalent"
            records.append(
                {
                    "schema_version": "0.1.0",
                    "id": f"grdr:variable:undata-{dataset_key}-{slug(code)}",
                    "name": code, "label": label, "aliases": [], "dataset_ids": [did],
                    "construct_ids": [f"grdr:construct:{construct_key}"],
                    "source_native": {
                        "system": "SDMX 2.1", "dataflow_id": dataflow, "data_structure_id": dsd,
                        "measure_element_id": measure_element,
                        "dimension_selections": [{"element_id": dimension_element, "code": code, "label": label}],
                    },
                    "role_candidates": ["outcome", "exposure", "control", "confounder", "context"],
                    "unit": unit, "denominator": None,
                    "population": "Countries/areas and series present in the selected UNdata dataflow.",
                    "observation_unit": "country-commodity-year" if is_energy else "party-gas-year",
                    "spatial_resolution": "Country or area" if is_energy else "Party or area",
                    "temporal_resolution": "Annual",
                    "measurement": {
                        "type": "administrative_measure" if is_energy else "modelled_estimate",
                        "objective_subjective": "objective", "directness": "constructed",
                        "definition": label,
                        "construction_notes": "Research-matchable variable formed by selecting the official SDMX dimension code and reading OBS_VALUE; units and flags must be retained.",
                    },
                    "comparability": {"status": "partially_comparable", "notes": "The dataflow uses a common international code structure, but availability, national methods, revisions, units, and inventory methods may differ."},
                    "join_keys": ["REF_AREA", "TIME_PERIOD"],
                    "verification": {"status": "partially_verified", "last_verified_at": STAMP, "notes": "Code, label, structure membership, unit framing, and construct link checked. Observation retrieval remains degraded and series-level coverage was not enumerated."},
                    "evidence": [{"url": url, "title": f"UNdata {dataset_key.title()} SDMX data structure and codelists", "publisher": "United Nations Statistics Division", "evidence_type": "data_dictionary", "supports": ["code", "label", "data_structure", "unit", "operationalization"], "retrieved_at": STAMP, "archived_url": None}],
                }
            )
    return records


def relationship_record(rid: str, subject: str, predicate: str, obj: str, url: str, supports: list[str]) -> dict:
    return {
        "schema_version": "0.1.0", "id": f"grdr:relationship:{rid}",
        "subject_id": subject, "predicate": predicate, "object_id": obj, "qualifiers": {},
        "verification": {"status": "verified", "last_verified_at": STAMP, "notes": "Relationship checked against the cited official catalog or SDMX structure."},
        "evidence": [{"url": url, "title": "UNdata official catalog or SDMX metadata", "evidence_type": "official_metadata", "supports": supports, "retrieved_at": STAMP}],
    }


def relationship_records(items: list[dict], resources: list[dict], elements: list[dict], variables: list[dict]) -> list[dict]:
    records = []
    for item in items:
        did = dataset_id(item)
        provider_id = PROVIDER_IDS[item["provider_name"]]
        records.append(relationship_record(f"undata-contains-{slug(item['catalog_id'])}", "grdr:source:undata", "contains", did, CATALOG_URL, ["catalog_membership"]))
        records.append(relationship_record(f"{slug(did)}-produced-by-{provider_id.rsplit(':', 1)[-1]}", did, "produced_by", provider_id, CATALOG_URL, ["provider_role"]))
    for resource in resources:
        for did in resource["dataset_ids"]:
            records.append(relationship_record(f"{slug(did)}-accessed-via-{resource['id'].rsplit(':', 1)[-1]}", did, "accessed_via", resource["id"], resource["url"], ["resource_linkage"]))
    for element in elements:
        did = element["dataset_ids"][0]
        records.append(relationship_record(f"{slug(did)}-contains-{element['id'].rsplit(':', 1)[-1]}", did, "contains", element["id"], element["evidence"][0]["url"], ["data_structure_membership"]))
    for variable in variables:
        did = variable["dataset_ids"][0]
        records.append(relationship_record(f"{slug(did)}-contains-{variable['id'].rsplit(':', 1)[-1]}", did, "contains", variable["id"], variable["evidence"][0]["url"], ["variable_operationalization"]))
        records.append(relationship_record(f"{variable['id'].rsplit(':', 1)[-1]}-measures-{variable['construct_ids'][0].rsplit(':', 1)[-1]}", variable["id"], "measures", variable["construct_ids"][0], variable["evidence"][0]["url"], ["construct_mapping"]))
    records.append(
        relationship_record(
            "undata-wdi-mirrors-world-bank-wdi",
            "grdr:dataset:undata-world-development-indicators",
            "mirrors",
            "grdr:dataset:world-development-indicators",
            CATALOG_URL,
            ["upstream_world_bank_provider", "catalog_mirror_identity"],
        )
    )
    return records


def update_source_and_unsd() -> tuple[dict, dict]:
    source = next(json.loads(line) for line in (REGISTRY / "sources.jsonl").read_text().splitlines() if '"id":"grdr:source:undata"' in line)
    source["scope"]["topics"] = ["population", "economy", "education", "health", "labour", "trade", "environment", "energy", "climate", "industry", "tourism", "ICT", "crime"]
    source["access"]["license_status"] = "documented_open"
    source["access"]["access_notes"] = "UNdata permits copying and distribution with attribution. Browser, CSV, and SDMX access vary by datamart; not every datamart is API-enabled."
    source["verification"] = {"status": "partially_verified", "last_verified_at": STAMP, "notes": "Identity, maintainer, catalog boundary, access documentation, license terms, and selected SDMX structures checked. Underlying quality and methods remain the responsibility of each named provider."}
    source["evidence"] = [
        {"url": ABOUT_URL, "title": "About UNdata", "publisher": "United Nations Statistics Division", "evidence_type": "official_homepage", "supports": ["identity", "maintainer", "scope", "provenance_position"], "retrieved_at": STAMP, "archived_url": None},
        {"url": CATALOG_URL, "title": "UNdata datamarts and update calendar", "publisher": "United Nations Statistics Division", "evidence_type": "official_catalog", "supports": ["36_datamarts", "6_glossaries", "providers", "update_metadata"], "retrieved_at": STAMP, "archived_url": None},
        {"url": API_URL, "title": "UNdata API Manual", "publisher": "United Nations Statistics Division", "evidence_type": "api_documentation", "supports": ["machine_access", "formats", "api_scope"], "retrieved_at": STAMP, "archived_url": None},
        {"url": TERMS_URL, "title": "UNdata Terms of Use", "publisher": "United Nations Statistics Division", "evidence_type": "license", "supports": ["free_access", "copying", "distribution", "attribution", "provider_responsibility"], "retrieved_at": STAMP, "archived_url": None},
    ]
    institution = next(json.loads(line) for line in (REGISTRY / "institutions.jsonl").read_text().splitlines() if '"id":"grdr:institution:unsd"' in line)
    institution["verification"] = {"status": "verified", "last_verified_at": STAMP, "notes": "Identity, UNdata maintenance role, and official statistical mandate checked on UNSD official pages."}
    institution["evidence"] = [
        {"url": ABOUT_URL, "title": "About UNdata", "publisher": "United Nations Statistics Division", "evidence_type": "official_homepage", "supports": ["institution_identity", "maintenance_role"], "retrieved_at": STAMP, "archived_url": None},
        {"url": "https://unstats.un.org/home/about/", "title": "About the United Nations Statistics Division", "publisher": "United Nations Statistics Division", "evidence_type": "official_mandate", "supports": ["global_statistical_information", "standards", "coordination", "dissemination"], "retrieved_at": STAMP, "archived_url": None},
    ]
    return source, institution


def adapter_and_monitor() -> tuple[dict, dict]:
    adapter = {
        "schema_version": "0.1.0", "id": "grdr:adapter:undata-sdmx", "name": "UNdata SDMX metadata and data adapter",
        "source_id": "grdr:source:undata",
        "resource_ids": ["grdr:resource:undata-api-manual", "grdr:resource:undata-dataflow-catalog", "grdr:resource:undata-energy-dsd", "grdr:resource:undata-ghg-dsd"],
        "adapter_type": "api", "implementation": "adapters/undata_sdmx.py",
        "operations": ["list_dataflows", "describe_datastructure", "list_codelist_codes", "get_data"],
        "supported_storage_modes": ["federated_access", "local_snapshot"], "authentication": "none",
        "state": {"status": "degraded", "last_tested_at": STAMP, "last_error": "Official metadata and data-structure endpoints returned HTTP 200, but documented observation data queries timed out or returned HTTP 500 across live probes on 2026-08-18."},
        "verification": {"status": "partially_verified", "last_verified_at": STAMP, "notes": "Metadata operations were live-tested successfully; data retrieval is currently degraded."},
        "evidence": [
            {"url": API_URL, "title": "UNdata API Manual", "publisher": "United Nations Statistics Division", "evidence_type": "api_documentation", "supports": ["endpoint", "sdmx", "formats", "authentication"], "retrieved_at": STAMP},
            {"url": DATAFLOW_URL, "title": "UNdata SDMX live metadata test", "publisher": "United Nations Statistics Division", "evidence_type": "live_test", "supports": ["metadata_reachability", "15_dataflows", "response_shape"], "retrieved_at": STAMP},
        ],
    }
    monitor = {
        "schema_version": "0.1.0", "id": "grdr:monitor:undata-sdmx-health", "name": "UNdata SDMX metadata and data health monitor",
        "target_id": adapter["id"], "check_types": ["reachability", "response_shape", "metadata", "deprecation"],
        "interval_days": 30, "enabled": True,
        "implementation": "adapters/undata_sdmx.py probe --dataflow DF_UNData_UNFCC --key A.EN_ATM_PFCE.DNK.Gg_CO2",
        "state": {"status": "degraded", "last_checked_at": STAMP, "next_due_at": "2026-09-17T00:00:00Z", "last_message": "Metadata and structures reachable; observation query path timed out or returned HTTP 500 across live probes."},
        "verification": {"status": "partially_verified", "last_verified_at": STAMP, "notes": "Initial live probe completed; no recurring scheduler is included yet."},
        "evidence": [{"url": DATAFLOW_URL, "title": "UNdata SDMX live probe", "publisher": "United Nations Statistics Division", "evidence_type": "live_test", "supports": ["metadata_reachability", "degraded_data_path"], "retrieved_at": STAMP}],
    }
    return adapter, monitor


def source_profile() -> dict:
    return {
        "schema_version": "0.1.0", "id": "grdr:source-profile:undata", "source_id": "grdr:source:undata",
        "scope_mode": "catalog_level",
        "scope_statement": "Catalog-level enumeration covers all 36 datamarts and separately records the six glossaries listed on the official UNdata catalog on 2026-08-18. Energy Statistics and Greenhouse Gas Inventory Data are additionally profiled through resources, SDMX data structures, data elements, research-matchable variables, and constructs. Other datamarts remain catalog-identity records.",
        "inventory_claim": "catalog_scope_complete",
        "layer_claims": {"institution": "scope_complete", "source": "scope_complete", "dataset": "scope_complete", "resource": "representative_only", "variable": "representative_only", "construct": "representative_only"},
        "layer_5_details": {"data_element_claim": "representative_only", "variable_claim": "representative_only", "registered_data_element_count": 16, "registered_variable_count": 13, "notes": "5A and 5B cover the Energy Statistics and Greenhouse Gas Inventory SDMX structures only; they do not enumerate the other 34 datamarts."},
        "enumeration": {"method": "Parsed all ordered DataMart blocks on the official UNdata Sources page and verified the dataset/glossary boundary.", "upstream_item_count": 36, "snapshot_boundary": SNAPSHOT, "notes": "36 datamarts are represented as Dataset records; six glossaries are recorded as a separate catalog resource. The live SDMX dataflow endpoint exposed 15 dataflows, so API coverage must not be equated with catalog coverage."},
        "blockers": [
            {"type": "technical", "layer": "resource", "notes": "Documented observation data queries timed out or returned HTTP 500 across live probes on 2026-08-18, while metadata and structure endpoints remained operational."},
            {"type": "scale", "layer": "variable", "notes": "Thirty-four datamarts still require structure/codebook and variable-level profiling; catalog identity is not variable completeness."},
        ],
        "last_reviewed_at": STAMP,
    }


def load_records(filename: str) -> list[dict]:
    return [json.loads(line) for line in (REGISTRY / filename).read_text(encoding="utf-8").splitlines() if line.strip()]


def merge(filename: str, additions: list[dict]) -> None:
    current = {item["id"]: item for item in load_records(filename)}
    for item in additions:
        current[item["id"]] = item
    ordered = sorted(current.values(), key=lambda item: item["id"])
    (REGISTRY / filename).write_text("".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in ordered), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-registry", action="store_true", help="Merge the verified snapshot into registry JSONL files")
    args = parser.parse_args()
    items, glossaries = parse_catalog(fetch(CATALOG_URL))
    print(f"Verified UNdata catalog boundary: {len(items)} datamarts, {len(glossaries)} glossaries")
    if not args.write_registry:
        for item in items:
            print(f"{item['catalog_id']}\t{item['name']}\t{item['provider_name']}")
        return 0

    datasets = [dataset_record(item) for item in items]
    dataset_ids = [item["id"] for item in datasets]
    resources = resource_records(dataset_ids)
    elements = data_element_records()
    variables = variable_records()
    constructs = construct_records()
    relationships = relationship_records(items, resources, elements, variables)
    source, unsd = update_source_and_unsd()
    adapter, monitor = adapter_and_monitor()
    merge("institutions.jsonl", [unsd, *institution_records(items)])
    merge("sources.jsonl", [source])
    merge("datasets.jsonl", datasets)
    merge("resources.jsonl", resources)
    merge("data_elements.jsonl", elements)
    merge("variables.jsonl", variables)
    merge("constructs.jsonl", constructs)
    merge("relationships.jsonl", relationships)
    merge("adapters.jsonl", [adapter])
    merge("monitors.jsonl", [monitor])
    merge("source_profiles.jsonl", [source_profile()])
    print(f"Merged {len(datasets)} datasets, {len(elements)} data elements, {len(variables)} variables, and {len(constructs)} constructs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
