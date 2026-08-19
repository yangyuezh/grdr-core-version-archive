---
name: grdr-deep-map-database
description: "Deep-read one authoritative database into GRDR through a persistent, resumable, evidence-backed workflow with database-shape classification, primary/secondary provenance tracing, bounded work-unit inventory, route-specific extraction, counted six-layer mapping, progress reporting, blockers, and strict completion gates. Use when Codex receives a database name, URL, catalog, or GRDR source ID and must start, resume, audit, or complete exhaustive or bounded database mapping; recover native schemas; enumerate data elements and variables; map constructs; attach access routes; or write canonical GRDR records and human catalog pages."
---

# GRDR Deep-Map Database

## Use the persistent workflow

Turn one database into a verified, traversable GRDR map. Use `$grdr` for registry-wide discovery and question-to-data matching. Use `$grdr-indicator-builder` for question- or literature-derived indicators.

Do not perform a nontrivial database pass as an untracked sequence of browsing and edits. Create or resume a persistent project under `deep_map_projects/<source-slug>/`. The project must contain:

- `project.json`: database classification, bounded scope, phase state, history, and next actions;
- `units.jsonl`: one work unit per bounded upstream dataset or equivalent collection, with counted stage states;
- `README.md`: generated human-readable progress.

Locate GRDR at `${GRDR_ROOT}` or `/Users/jasper/Documents/codex/grdr`. Before writing, read `docs/DATABASE_DEEP_MAP_WORKFLOW.md`, the relevant canonical schemas, and these references:

- [references/six-layer-standard.md](references/six-layer-standard.md) for entity meaning;
- [references/database-archetypes.md](references/database-archetypes.md) to select routes by storage form and discipline;
- [references/completion-contract.md](references/completion-contract.md) before changing a stage to complete;
- [references/within-stage-enumeration.md](references/within-stage-enumeration.md) to select the next native item and preserve a batch cursor;
- [references/multidimensional-data.md](references/multidimensional-data.md) for cubes and other multidimensional systems.

The machine contracts are `schemas/database_deep_map_project.schema.json`, `schemas/database_deep_map_unit.schema.json`, `schemas/database_deep_map_phase_update.schema.json`, and `schemas/database_deep_map_stage_update.schema.json`. Copy [references/phase-update.example.json](references/phase-update.example.json) or [references/stage-update.example.json](references/stage-update.example.json) before constructing an update; do not invent field names from memory.

## Start or resume; never improvise progress

Search and audit the source first:

```bash
python3 scripts/grdr.py audit-source-depth <source-id>
python3 scripts/grdr.py start-database-deep-map <spec.json>
python3 scripts/grdr.py database-deep-map-status <project>
python3 scripts/grdr.py resume-database-deep-map <project>
```

`database-deep-map-status` and `audit-database-deep-map` are read-only and return `next_target` plus `queue_preview`. Use them for inspection. `resume-database-deep-map` records a history event and refreshes the human report, so use it only when actually resuming work.

Generate the start specification from official source evidence. Classify:

- disciplines;
- `primary`, `secondary`, or `hybrid` origin;
- original producer, official harmonizer, curated repository, mirror, or derivative aggregator role;
- production modes;
- structural archetypes;
- access regime;
- required route modules.

Classify each work unit independently when a portal mixes different producers or storage forms. Preserve original producers and transformations for secondary data.

## Fix the bounded universe

Declare the scope, snapshot time, enumeration method, expected work-unit count, and evidence. Use one work unit per Dataset or equivalent upstream collection. Do not report a percentage while the expected work-unit count is unknown.

For an exhaustive claim, enumerate every item inside the dated boundary, including deprecated, restricted, empty, and inaccessible entries. These may later be evidenced as not applicable or blocked; they may not silently disappear.

## Execute each unit in order

For every work unit, execute all required stages:

1. `dataset`: identity, producer, methodology, population, observation unit, coverage, version, limitations, citation;
2. `data_structure`: source-native hierarchy, schema, table, dataflow, instrument, array, graph, file layout, or corpus organization;
3. `data_element`: every required field, dimension, measure, identifier, item, attribute, weight, flag, code list, coordinate, or annotation class;
4. `variable`: the complete declared operational-variable universe, with definition, unit, population, resolutions, comparability, and joins;
5. `construct`: research meaning, measurement class, directness, proxy/model boundary, and disciplinary semantics;
6. `access`: API, query, file, bulk download, secure environment, authentication, limits, license, and separate metadata/observation tests.

Select route modules from the unit's actual shape. The six stages stay fixed; the extraction route changes. For example, use `sdmx_cube` for a statistical cube, `survey_instrument` for questionnaires and microdata, `scientific_array` for NetCDF/HDF/Zarr, `biomedical` for sample/assay/sequence structures, and `corpus_multimodal` for document or media collections.

Write facts and relationships to canonical `registry/*.jsonl`. Then record the stage through an update file:

```bash
python3 scripts/grdr.py record-database-deep-map-stage <project> <stage-update.json>
python3 scripts/grdr.py record-database-deep-map-phase <project> <phase-update.json>
```

The command rejects unknown GRDR IDs, wrong entity types, missing counts, count mismatches, unsupported completion claims, and blocked states without blockers.

After each update, run read-only `database-deep-map-status` and work on its returned next target. Run `resume-database-deep-map` once when a new work session actually resumes and its history event is desired. Do not choose a convenient example while earlier required work remains invisible.

Inside the selected stage, follow [the deterministic enumeration rule](references/within-stage-enumeration.md). Preserve official order where available; otherwise use complete source-native ID order. Record the current native cursor in `notes`, and update it after every batch. A stage-level count without a reproducible native universe and cursor is not enough for completion.

For SDMX 2.1 systems, use the bundled inspector instead of writing a new parser:

```bash
python3 skill/grdr-deep-map-database/scripts/inspect_sdmx.py list-dataflows <base-url>
python3 skill/grdr-deep-map-database/scripts/inspect_sdmx.py describe-structure <base-url> <agency> <dsd-id> <version>
python3 skill/grdr-deep-map-database/scripts/inspect_sdmx.py list-codelist <base-url> <agency> <codelist-id> <version>
python3 skill/grdr-deep-map-database/scripts/inspect_sdmx.py probe-data <base-url> <dataflow-id> <ordered-key>
```

## Use states literally

- `not_started`, `enumerating`, `in_progress`: open work;
- `mapped_complete`: the bounded expected count is fully registered, but verification remains incomplete;
- `verified_complete`: expected count, registered count, verified count, completion basis, and evidence all agree;
- `not_applicable`: expected count is zero and evidence proves why;
- `blocked`: work is unresolved and blockers are recorded.

Never use `mapped_complete` merely because several examples exist. Never use `verified_complete` while the expected count is unknown. A restricted database can have complete metadata and access documentation, but an unresolved required stage remains blocked.

## Enforce strict completion

Two percentages are reported:

- mapping progress includes `mapped_complete`;
- strict completion counts only `verified_complete` and evidenced `not_applicable`.

Only `complete-database-deep-map` may declare completion:

```bash
python3 scripts/grdr.py audit-database-deep-map <project>
python3 scripts/grdr.py complete-database-deep-map <project>
```

Completion requires a fixed work-unit universe, verified identity/classification/boundary/inventory phases, every required unit stage closed, no blockers, valid canonical references, registry Schema validation, and a current human catalog. “Six-layer chain present” and “variable matching ready” are never completion claims.

## Report

Return project and source IDs, boundary and snapshot, classification and routes, work-unit counts, mapping and strict-completion percentages, per-stage state counts, next target, blockers, changed canonical IDs, validation results, version, and GitHub release status.
