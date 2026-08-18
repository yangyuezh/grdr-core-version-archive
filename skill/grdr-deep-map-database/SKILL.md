---
name: grdr-deep-map-database
description: "Deep-read one authoritative database into GRDR and establish its evidence-backed mapping topology across institution, database, dataset, database-internal structure, source-native data elements, research-matchable variables, and theoretical constructs. Use when Codex receives a database name, URL, catalog, or GRDR source ID and must verify authority, enumerate a declared scope, recover native schemas or hierarchies, map elements into variables and constructs, attach access routes, audit completeness, or write canonical GRDR records and human catalog pages."
---

# GRDR Deep-Map Database

## Purpose and boundary

Use this Skill to turn one database from a shallow source entry into a verified, traversable GRDR map. Use `$grdr` for registry-wide discovery, gap expansion, project orchestration, and question-to-data matching. Use `$grdr-indicator-builder` for question- or literature-derived indicator systems.

Never treat a missing GRDR record as proof that the upstream database lacks that content. Never present one completed chain as a complete upstream inventory unless the enumeration evidence supports that claim.

## Locate GRDR and load the contract

Use `${GRDR_ROOT}` when set. Otherwise use `/Users/jasper/Documents/codex/grdr`.

Before writing, read:

- `docs/SOURCE_PROFILING_PROTOCOL.md`
- `docs/ONTOLOGY.md`
- the Institution, Source, Dataset, DataStructure, DataElement, Variable, Construct, Resource, Relationship, and SourceProfile schemas
- [references/six-layer-standard.md](references/six-layer-standard.md)
- [references/multidimensional-data.md](references/multidimensional-data.md) when the source is a cube, schema, table system, questionnaire, array, graph, or other structured collection

Audit an existing source first:

```bash
python3 scripts/grdr.py audit-source-depth grdr:source:undata
```

The standalone Skill wrapper is:

```bash
python3 skill/grdr-deep-map-database/scripts/audit_database_map.py grdr:source:undata
```

## Declare the bounded pass

Select exactly one scope mode: `identity_only`, `representative_chain`, `question_driven`, `priority_catalog`, `catalog_level`, or `exhaustive_snapshot`.

Create or update the source's single current `SourceProfile`. Record the scope statement, inventory claim, seven entity claims for the six-layer model, separate access claim, enumeration method and boundary, blockers, and review time. Large databases should be mapped in successive versioned passes.

## Build the six-layer topology

### 1. Institution

Identify and evidence the producer, publisher, maintainer, funder, and governor. These roles may belong to different organizations.

### 2. Database / Source

Resolve canonical identity, aliases, provenance position, scope, authority, lifecycle, access policy, license, and update policy.

### 3. Dataset

Enumerate datasets inside the declared pass. Record population, observation unit, coverage, release, methodology, limitations, citation, and official evidence. A catalog page is evidence for a Dataset; it is not the Dataset itself.

### 4. DataStructure

Recover how the database actually organizes data before extracting variables. Register the upstream catalog hierarchy, dataflow, multidimensional schema, table/view, API schema, file layout, questionnaire, instrument, scientific array, or graph schema. Preserve native system, agency, object class, ID, version, parent structure, datasets, and the resources that expose or document it.

This layer is the bridge between a named Dataset and its fields, dimensions, questions, observations, or variables. Do not replace it with an API or download link.

### 5A. DataElement

Mirror source-native components defined by the DataStructure: measures, dimensions, identifiers, time dimensions, attributes, weights, flags, units, code lists, field order, and attachment levels. Each element must point to at least one `DataStructure` record.

### 5B. Variable

Create a research-matchable operational variable only when its meaning can be reconstructed from official metadata. In a cube this normally requires a measure plus meaning-bearing dimension selections. In a table, questionnaire, or schema it may be a documented field, item, derived field, or comparable series. Each variable must point to its DataStructure, datasets, constructs, measurement class, unit, population, resolutions, comparability, join keys, and evidence.

If the native structure or operational meaning is unresolved, stop at 5A. Never infer a variable from source-level topic tags.

### 6. Construct

Link variables to research concepts. Distinguish direct observations, administrative and subjective measures, constructed indices, modeled estimates, forecasts, proxies, and latent estimates. Preserve scope limits, uncertainty, and incompatible definitions.

## Attach access information without changing the hierarchy

Register APIs, CSV or bulk downloads, query tools, documentation, secure environments, applications, authentication, rate limits, formats, and licenses as `Resource` sidecars. Link them to the Dataset or DataStructure with `accessed_via`; Resource is not layer 4 and never advances profiling depth.

Test structure metadata and observation retrieval independently. A working schema endpoint does not prove that observation data are retrievable.

For SDMX sources, the bundled inspector can enumerate dataflows, inspect a DSD, and probe observations:

```bash
python3 skill/grdr-deep-map-database/scripts/inspect_sdmx.py list-dataflows https://data.un.org/ws/rest
python3 skill/grdr-deep-map-database/scripts/inspect_sdmx.py describe-structure https://data.un.org/ws/rest UNSD DSD_ENERGY 1.2
python3 skill/grdr-deep-map-database/scripts/inspect_sdmx.py probe-data https://data.un.org/ws/rest DF_UNData_UNFCC A.EN_ATM_PFCE.DNK.Gg_CO2 --start-period 2000 --end-period 2000
```

## Validate and publish the map

After canonical records and relationships are written, run:

```bash
python3 scripts/validate_registry.py
python3 scripts/build_catalog.py
python3 scripts/build_catalog.py --check
python3 scripts/grdr.py audit-source-depth <source-id>
python3 -m unittest discover -s tests
```

Promote verification only when evidence supports the exact claim. Respect authentication, payment, consent, ethics review, data-use agreements, licenses, and rate limits.

Report the source ID, pass scope, before/after counts for all layers, added or updated IDs, native structure-to-element-to-variable mappings, construct links, access sidecars, verification changes, inventory boundary, blockers, next bounded pass, GRDR version, and GitHub release status.
