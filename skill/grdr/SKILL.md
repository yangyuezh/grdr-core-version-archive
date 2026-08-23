---
name: grdr
description: Operate and expand GRDR, an AI-agent-native, all-discipline global Data Source Registry, Dataset Knowledge Graph, and Agent Research Data Infrastructure. Use when Codex needs to discover, verify, register, classify, assess, connect, cite, or update authoritative and academically valuable databases; audit disciplinary coverage; trace provenance, methodology, access, or licensing; or map a scientific question to compatible data sources, variables, and unresolved data gaps.
---

# Global Research Data Registry

## Preserve the project definition

Treat GRDR as:

- a versioned Data Source Registry;
- a Dataset Knowledge Graph;
- Agent Research Data Infrastructure;
- a source-matching and data-gap reasoning system;
- a continuously expanding cross-disciplinary knowledge base.
- a distributed snapshot system in which every selected, fully deep-read database has its own versioned source repository, GitHub Release, matching Elements copy, and source-specific callable runtime.
- an independent Agent Runtime that searches, mounts, resolves, and calls those stored snapshots.

Do not build one monolithic warehouse or copy every registered upstream source. The global registry remains broad; databases selected for the three-step deep-map factory must finish as complete, source-scoped snapshots with knowledge, Agent index, and captured observations.

## Follow the current phase

Prioritize:

1. stabilizing schemas, evidence standards, evaluation dimensions, and Agent interfaces;
2. constructing the first approximately 100-source cross-disciplinary registry;
3. verifying source authority, scope, access, methodology, license, and provenance;
4. deepening representative sources to dataset and variable level;
5. preparing fast local indexes for Agent retrieval.

Treat 100 as a first-round workload target, never a collection limit. Continue later through institution, discipline, and scientific-question snowball expansion.

## Locate the project

Use `${GRDR_ROOT}` when set. Otherwise use:

```text
/Users/jasper/Documents/codex/grdr-core
```

Before modifying records, read `docs/NORTH_STAR.md`, the relevant schema, and [references/curation-standard.md](references/curation-standard.md).

Strict Schema validation and deep-map planning require `jsonschema`. Use a project-local environment; a skipped validator is a failure, not a warning:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-validation.txt
```

Use `.venv/bin/python` instead of `python3` for planning, deep-map audits, completion, registry validation, and tests.

## Search before expanding

Run the bundled wrapper:

```bash
python3 scripts/grdr.py stats
python3 scripts/grdr.py list-source-archives
python3 scripts/grdr.py search-sources --query climate
python3 scripts/grdr.py search-datasets --topic population
python3 scripts/grdr.py search-variables --construct population
python3 scripts/grdr.py source-snapshot-status --source-id grdr:source:example --verify
python3 scripts/grdr.py resolve-variable-access grdr:variable:example-measure
python3 scripts/grdr.py fetch-variable grdr:variable:example-measure --dry-run
python3 scripts/grdr.py trace-provenance grdr:variable:example-measure
```

Treat unverified records as candidates. Treat an empty result as `not_found_in_registry_snapshot`, not proof that no external source exists.

## Discover and curate sources

Read [references/domain-coverage.md](references/domain-coverage.md). Search official catalogs, primary producers, disciplinary repositories, standards, data papers, upstream provenance, citations, and non-English systems.

For each candidate:

1. Resolve canonical identity and maintainer.
2. Classify the authority and provenance role.
3. Collect evidence for scope, methods, coverage, access, license, versioning, and citation.
4. Register only defensible facts; leave unresolved fields unknown.
5. Add explicit provenance, containment, derivation, mirror, and replacement relationships.
6. Validate before promoting verification status.

Separate institutional authority from task-specific fitness. Do not rank every field by one universal prestige score.

## Route the three-step database factory

When one database must be understood beyond Source registration, dispatch three separate installed Skills in order:

1. `$grdr-plan-database-deep-map` diagnoses the database, fixes the boundary and work-unit universe, composes route obligations, and creates the locked project;
2. `$grdr-execute-database-deep-map` follows the deterministic queue, deeply maps every work unit, stages candidate records, and seals a fingerprinted handoff without canonical writes;
3. `$grdr-store-database-deep-map` alone promotes the sealed records, builds the source repository and full callable snapshot artifacts, publishes one private GitHub Release, materializes the matching Elements directory, verifies the source runtime, writes the central card, and issues the Storage receipt.

Keep this production factory separate from the Agent Runtime use plane. Storage delivers and verifies the source runtime; unified search, online snapshot materialization, variable access resolution, and official retrieval are Core runtime operations.

The map preserves Institution and Source as provenance context; Dataset; recursive DataStructure; 5A DataElement and 5B Variable; and Construct. Resource is an access sidecar. It must also close a source-native structural spine, a multi-parent scientific-semantic spine, and the Variable-to-Construct bridge. Audit current depth first:

```bash
python3 scripts/grdr.py audit-source-depth <source-id>
python3 scripts/grdr.py audit-all-source-depth
```

Treat `six_layer_chain_present` as evidence that at least one chain exists, never as proof that the full upstream catalog has been inventoried.

For every nontrivial pass, use the persistent workflow rather than an ad hoc browsing session:

```bash
python3 scripts/grdr.py list-database-route-modules
python3 scripts/grdr.py plan-database-deep-map <intake-or-spec.json> --output <plan.json>
python3 scripts/grdr.py audit-database-deep-map-plan <plan.json>
python3 scripts/grdr.py start-database-deep-map <spec.json>
python3 scripts/grdr.py database-deep-map-status <project>
python3 scripts/grdr.py resume-database-deep-map <project>
python3 scripts/grdr.py record-database-deep-map-stage <project> <update.json>
python3 scripts/grdr.py record-database-deep-map-spine <project> <spine-update.json>
python3 scripts/grdr.py record-database-deep-map-check <project> <check-update.json>
python3 scripts/grdr.py stage-database-deep-map-records <project> <records.jsonl>
python3 scripts/grdr.py audit-database-deep-map-execution <project>
python3 scripts/grdr.py prepare-database-deep-map-storage <project>
python3 scripts/grdr.py prepare-database-storage <project> <storage-spec.json>
python3 scripts/grdr.py audit-database-storage <project>
python3 scripts/grdr.py publish-database-storage <project>
python3 scripts/grdr.py database-storage-status <project>
```

Diagnose origin, structure, modality, lifecycle, versioning, access, sensitivity, scale, metadata maturity, boundary, denominator, and constraints before starting. Compose machine route contracts; use `open_world_custom` for unexplained shapes instead of forcing a closed taxonomy. Keep projects under `deep_map_projects/<source-or-pass>/`. Enforce the plan, scope, and unit-manifest locks and follow the deterministic dependency-valid next target. Step 2 may write only project staging; only Step 3 may write canonical registry files and source-archive cards. Only a valid Storage receipt declares bounded factory completion; a canonical archive receipt alone proves registry promotion, not database storage.

## Keep the human catalog synchronized

Treat human readability as required, even though AI agents are the primary users. Every registered source must appear in the root `README.md` and have an independent `catalog/sources/<source-slug>/README.md` page covering Institution, Source, Dataset, DataStructure, DataElement & Variable, and Construct, plus access-sidecar Resources.

After changing any of those registry layers, run:

```bash
.venv/bin/python scripts/build_catalog.py
.venv/bin/python scripts/build_catalog.py --check
```

Generate pages only from canonical registry records. Display missing depth as unknown or not yet registered; never invent fields to make a page look complete.

## Match scientific questions

When the user provides a scientific question:

1. use `$grdr-indicator-builder` when the constructs or indicators must be derived from a topic or literature corpus;
2. identify constructs, outcomes, exposures, mechanisms, confounders, moderators, population, unit, time, and geography;
3. create a data-requirement matrix from approved leaf indicators;
4. retrieve candidate sources, datasets, and variables;
5. assess construct, population, time, space, granularity, access, and joinability fit;
6. distinguish direct measures, constructed measures, modeled estimates, forecasts, and proxies;
7. diagnose missing objective, subjective, administrative, experimental, observational, or multimodal data;
8. recommend additional sources without claiming unfound data already exists.

Use:

```bash
python3 scripts/grdr.py diagnose-coverage /absolute/path/to/request.json
```

Matching is a core value of GRDR, but it depends on continued registry breadth and depth.
Keep question-specific literature, indicators, and mappings under `research_projects/<project-id>/`; do not mix them into the canonical global source registry.

For a persisted topic-scaffold project, use the executable lifecycle:

```bash
python3 scripts/grdr.py start-research-project <spec.json>
python3 scripts/grdr.py research-project-status <project-id>
python3 scripts/grdr.py resume-research-project <project-id>
python3 scripts/grdr.py match-indicators <project-id>
python3 scripts/grdr.py expand-from-data-gaps <project-id>
# After candidate sources have been deepened or new sources registered:
python3 scripts/grdr.py resume-research-project <project-id>
python3 scripts/grdr.py rerun-matching <project-id>
```

The Agent may run every command above automatically. `approve-human-gate` is different: call it only after the human explicitly provides the reviewer identity and approval notes. Never use it to convert an Agent-generated topic scaffold into a formal, literature-grounded result. Preserve `workflow.json` and `data_gaps.jsonl` with the five research-content files.

## Use access extensions carefully

Read [references/access-architecture.md](references/access-architecture.md) only when adding an API adapter, federated query, or lawful snapshot. Keep source discovery and metadata separate from data retrieval.

Never bypass authentication, payment, consent, ethics review, data-use agreements, rate limits, or access controls.

## Release every completed batch

Read `docs/RELEASE_PROCESS.md`. For each completed development batch:

1. bump `VERSION`;
2. update `CHANGELOG.md`;
3. validate the registry and tests;
4. commit only GRDR files;
5. tag the version;
6. push the branch and tag to GitHub;
7. report the version and GitHub URL.

## Validate changes

```bash
cd "${GRDR_ROOT:-/Users/jasper/Documents/codex/grdr-core}"
.venv/bin/python scripts/validate_registry.py
.venv/bin/python scripts/build_catalog.py --check
.venv/bin/python -m unittest discover -s tests
```

Report added coverage, verification levels, unresolved evidence, matching limitations, version, and release status.
