---
name: grdr-source-profiler
description: "Decompose and deeply profile a database for GRDR across six linked layers: institution, source, dataset, resource, data element and variable, and construct. Use when Codex receives a database name, URL, catalog, or GRDR source ID and needs to verify its publisher and authority, inventory datasets and access routes, recover source-native structures, extract variable metadata, map measurements to research constructs, assess profiling depth, or write evidence-backed records and human catalog pages into GRDR."
---

# GRDR Source Profiler

## Preserve the distinction

Treat this Skill as the deep-curation workflow for one database. Use `$grdr` for the broader registry, coverage expansion, and research-question matching.

Do not construct question-specific indicator hierarchies from a research topic or literature corpus. That is the responsibility of `$grdr-indicator-builder`. This Skill supplies source-native datasets, variables, definitions, and constructs to the downstream matcher.

Never interpret a missing GRDR record as proof that the upstream database lacks a dataset, resource, variable, or construct. Never interpret one six-layer example as a complete upstream inventory.

## Locate GRDR

Use `${GRDR_ROOT}` when set. Otherwise use:

```text
/Users/jasper/Documents/codex/grdr
```

Read `docs/SOURCE_PROFILING_PROTOCOL.md`; the Institution, Source, Dataset, Resource, DataElement, Variable, Construct, Relationship, and SourceProfile schemas; [references/six-layer-standard.md](references/six-layer-standard.md); and [references/multidimensional-data.md](references/multidimensional-data.md) before writing records. The seven content entity types occupy six layers because DataElement and Variable are both inside layer 5; Relationship and SourceProfile are supporting records.

## Resolve the input

When given a GRDR source ID, audit it first:

```bash
python3 scripts/grdr.py audit-source-depth grdr:source:undata
```

When given a name or URL:

1. search `registry/sources.jsonl` and canonical aliases first;
2. resolve redirects, mirrors, predecessor systems, and official ownership;
3. reuse the existing ID when identity matches;
4. nominate new Institution and Source records only when no matching source exists.

## Declare the profiling scope

Choose and report one scope before expanding:

- `identity_only`
- `representative_chain`
- `question_driven`
- `priority_catalog`
- `catalog_level`
- `exhaustive_snapshot`

For large portals, work in versioned batches. Do not claim `catalog_level` or `exhaustive_snapshot` without a reproducible enumeration method, upstream counts or pagination, and a dated boundary.

Create or update the source's single current scope record in `registry/source_profiles.jsonl` using `schemas/source_profile.schema.json`; Git preserves prior versions. The record must state the scope, inventory claim, per-layer claims, enumeration method and boundary, blockers, and review time. Do this even for `identity_only`; absence of a profile record is not a completeness claim.

## Decompose in six layers

### 1. Institution

Separate producer, publisher, maintainer, funder, and governor. Verify identity, mandate, jurisdiction, and official role.

### 2. Source

Resolve canonical identity, scope, authority role, provenance position, access modes, license, update policy, and official evidence.

### 3. Dataset

Enumerate the declared scope from official catalogs or documentation. Record methodology, population, unit, spatial and temporal coverage, release, revision, limitations, citation, and evidence.

### 4. Resource

Register concrete APIs, files, downloads, query tools, documentation, cloud collections, secure environments, application routes, and physical access. Record format, authentication, machine access, rate limits, and license.

### 5. Data element and variable

First restore the source-native structure as `DataElement` records: dimensions, measures, identifiers, time dimensions, attributes, weights, flags, units, code lists, ordering, and attachment levels. Then construct research-matchable `Variable` records by linking a measure to the required dimension selections.

For SDMX sources, enumerate dataflows and inspect the referenced DSD before registering variables. Use the bundled inspector when helpful:

```bash
python3 skill/grdr-source-profiler/scripts/inspect_sdmx.py list-dataflows https://data.un.org/ws/rest
python3 skill/grdr-source-profiler/scripts/inspect_sdmx.py describe-structure https://data.un.org/ws/rest UNSD DSD_ENERGY 1.2
python3 skill/grdr-source-profiler/scripts/inspect_sdmx.py probe-data https://data.un.org/ws/rest DF_UNData_UNFCC A.EN_ATM_PFCE.DNK.Gg_CO2 --start-period 2000 --end-period 2000
```

For DCAT, JSON Schema, relational catalogs, codebooks, or questionnaires, preserve their equivalent native hierarchy and identifiers. Record definition, unit, denominator, population, observation unit, resolutions, measurement class, comparability, and join keys.

If the measure element is unresolved or no dimension selection gives the candidate its research meaning, stop at 5A and do not create a 5B Variable. For multidimensional profiles, populate `source_profile.layer_5_details` with separate 5A/5B counts, claims, and boundaries.

Test metadata/structure and observation data independently. Store successful structure evidence on DataElements and Resource/Adapter records; store data-query failures or degradation on the Resource/Adapter/Monitor and in source-profile blockers. Never let a working DSD imply that observations are retrievable.

Do not infer variables from source- or dataset-level topic tags.

### 6. Construct

Map variables to concepts and distinguish direct observations, subjective measures, administrative measures, constructed indices, modeled estimates, forecasts, proxies, and latent estimates. Preserve uncertainty and definition boundaries.

## Write and validate

Write facts only to canonical `registry/*.jsonl` files and relationships. Then run:

```bash
python3 scripts/validate_registry.py
python3 scripts/build_catalog.py
python3 scripts/build_catalog.py --check
python3 scripts/grdr.py audit-source-depth <source-id>
python3 -m unittest discover -s tests
```

Promote a verification state only when suitable evidence supports the changed claims. Respect authentication, payment, consent, ethics review, data-use agreements, licenses, and rate limits.

## Report the result

Return:

- source ID and declared profiling scope;
- before-and-after state for all six layers;
- added and updated record IDs;
- evidence and verification changes;
- dataset and variable inventory boundaries;
- data-structure coverage and the exact transformation from native elements to research-matchable variables;
- access, license, or technical blockers;
- unresolved unknowns and the next bounded profiling pass;
- GRDR version and GitHub release status.
