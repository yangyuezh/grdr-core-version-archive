---
name: grdr-source-profiler
description: "Decompose and deeply profile a database for GRDR across six linked layers: institution, source, dataset, resource, variable, and construct. Use when Codex receives a database name, URL, catalog, or GRDR source ID and needs to verify its publisher and authority, inventory datasets and access routes, extract variable metadata, map measurements to research constructs, assess profiling depth, or write evidence-backed records and human catalog pages into GRDR."
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

Read `docs/SOURCE_PROFILING_PROTOCOL.md`, the relevant six entity schemas, and [references/six-layer-standard.md](references/six-layer-standard.md) before writing records.

## Resolve the input

When given a GRDR source ID, audit it first:

```bash
python3 scripts/profile_source.py grdr:source:undata
```

When given a name or URL:

1. search `sources.jsonl` and canonical aliases first;
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

### 5. Variable

Use official dictionaries, codebooks, schemas, questionnaires, or reproducible API metadata. Record definition, unit, denominator, population, observation unit, resolutions, measurement class, comparability, and join keys.

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
- access, license, or technical blockers;
- unresolved unknowns and the next bounded profiling pass;
- GRDR version and GitHub release status.
