---
name: grdr
description: Operate and expand GRDR, an AI-agent-native, all-discipline global Data Source Registry, Dataset Knowledge Graph, and Agent Research Data Infrastructure. Use when Codex needs to discover, verify, register, classify, assess, connect, cite, or update authoritative and academically valuable databases; audit disciplinary coverage; trace provenance, methodology, access, or licensing; or map a scientific question to compatible data sources, variables, and unresolved data gaps.
---

# Global Research Data Registry

## Preserve the project definition

Treat GRDR as an immutable Core plus external mutable registry state:

- a versioned Data Source Registry whose database records live outside the Core code tree;
- a Dataset Knowledge Graph;
- Agent Research Data Infrastructure;
- a source-matching and data-gap reasoning system;
- a continuously expanding cross-disciplinary knowledge base.
- a distributed snapshot system in which every selected, fully deep-read database has its own versioned source repository, GitHub Release, callable Elements copy, location-aware observation policy, and source-specific runtime.
- an independent Agent Runtime that searches, mounts, resolves, and calls those stored snapshots.

Do not build one monolithic warehouse or copy every registered upstream source. Keep Core database-independent and immutable. Store global cards and canonical records under `GRDR_STATE_ROOT` (default `~/.grdr`), while databases selected for the three-step factory finish as complete, source-scoped knowledge and Agent snapshots. Store observation bytes as a full mirror, partitioned mirror, or federated-on-demand source according to the snapshot's explicit policy.

## Follow the current phase

Prioritize:

1. stabilizing schemas, evidence standards, evaluation dimensions, and Agent interfaces;
2. constructing the first approximately 100-source cross-disciplinary registry;
3. verifying source authority, scope, access, methodology, license, and provenance;
4. deepening representative sources to dataset and variable level;
5. preparing fast local indexes for Agent retrieval.

Treat 100 as a first-round workload target, never a collection limit. Continue later through institution, discipline, and scientific-question snowball expansion.

## Locate the project

Resolve the absolute directory containing this active `SKILL.md`, then set `GRDR_LAUNCHER` to its bundled `scripts/grdr.py`. It locates Core through `GRDR_ROOT`, the Codex pointer written by Core's `scripts/configure_core.py`, current ancestors, or a bundled checkout. Never assume the caller's working directory.

Configure an external expanded-snapshot root once instead of repeating `--elements-root`. This writes deployment-local configuration under external `GRDR_STATE_ROOT`, never into Core:

```bash
python3 "$GRDR_ROOT/scripts/configure_core.py" --elements-root /absolute/path/to/GRDR
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
python3 "$GRDR_LAUNCHER" stats
python3 "$GRDR_LAUNCHER" list-source-archives
python3 "$GRDR_LAUNCHER" search-sources --query climate
python3 "$GRDR_LAUNCHER" search-datasets --topic population
python3 "$GRDR_LAUNCHER" search-variables --construct population
python3 "$GRDR_LAUNCHER" search-variables --construct population --snapshot-policy history
python3 "$GRDR_LAUNCHER" source-snapshot-status --source-id grdr:source:example --verify
python3 "$GRDR_LAUNCHER" resolve-variable-access grdr:variable:example-measure
python3 "$GRDR_LAUNCHER" fetch-variable grdr:variable:example-measure --dry-run
python3 "$GRDR_LAUNCHER" trace-provenance grdr:variable:example-measure
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
3. `$grdr-store-database-deep-map` alone promotes the sealed records, inherits the locked knowledge scope, selects observation replication and placement, excludes raw observations from knowledge, builds the callable snapshot artifacts, verifies every declared location and the source runtime, writes the central card, and issues the Storage receipt.

Keep this production factory separate from the Agent Runtime use plane. Storage delivers and verifies the source runtime; unified search, online snapshot materialization, variable access resolution, and official retrieval are Core runtime operations.

The map preserves Institution and Source as provenance context; Dataset; recursive DataStructure; 5A DataElement and 5B Variable; and Construct. Resource is an access sidecar. It must also close a source-native structural spine, a multi-parent scientific-semantic spine, and the Variable-to-Construct bridge. Audit current depth first:

```bash
python3 "$GRDR_LAUNCHER" audit-source-depth <source-id>
python3 "$GRDR_LAUNCHER" audit-all-source-depth
```

Treat `six_layer_chain_present` as evidence that at least one chain exists, never as proof that the full upstream catalog has been inventoried.

For every nontrivial pass, use the persistent workflow rather than an ad hoc browsing session:

```bash
python3 "$GRDR_LAUNCHER" list-database-route-modules
python3 "$GRDR_LAUNCHER" plan-database-deep-map <intake-or-spec.json> --output <plan.json>
python3 "$GRDR_LAUNCHER" audit-database-deep-map-plan <plan.json>
python3 "$GRDR_LAUNCHER" start-database-deep-map <spec.json>
python3 "$GRDR_LAUNCHER" database-deep-map-status <project>
python3 "$GRDR_LAUNCHER" resume-database-deep-map <project>
python3 "$GRDR_LAUNCHER" record-database-deep-map-stage <project> <update.json>
python3 "$GRDR_LAUNCHER" record-database-deep-map-spine <project> <spine-update.json>
python3 "$GRDR_LAUNCHER" record-database-deep-map-check <project> <check-update.json>
python3 "$GRDR_LAUNCHER" stage-database-deep-map-records <project> <records.jsonl>
python3 "$GRDR_LAUNCHER" audit-database-deep-map-execution <project>
python3 "$GRDR_LAUNCHER" prepare-database-deep-map-storage <project>
python3 "$GRDR_LAUNCHER" prepare-database-storage <project> <storage-spec.json>
python3 "$GRDR_LAUNCHER" audit-database-storage <project>
python3 "$GRDR_LAUNCHER" publish-database-storage <project>
python3 "$GRDR_LAUNCHER" database-storage-status <project>
```

Diagnose origin, structure, modality, lifecycle, versioning, access, sensitivity, scale, metadata maturity, boundary, denominator, and constraints before starting. Compose machine route contracts; use `open_world_custom` for unexplained shapes instead of forcing a closed taxonomy. Keep projects under external GRDR state or an explicit absolute project path. Enforce the plan, scope, and unit-manifest locks and follow the deterministic dependency-valid next target. Step 2 may write only project staging; Step 3 may write the external registry state and source-archive cards but must never write database content into the immutable Core tree. Only a valid Storage receipt declares bounded factory completion.

## Keep the human catalog synchronized

Treat human readability as required, even though AI agents are the primary users. Every deeply stored source must have an independent source-repository `README.md` covering Institution, Source, Dataset, DataStructure, DataElement & Variable, Construct, and access-sidecar Resources. Never regenerate the immutable Core README from mutable source records.

Generate source pages only from the source snapshot's canonical records. Display missing depth as unknown or not yet registered; never invent fields to make a page look complete.

## Match scientific questions

When the user provides a scientific question:

1. use `$grdr-indicator-builder` when the constructs or indicators must be derived from a topic or literature corpus;
2. use `$grdr-resolve-research-semantics` to recall persisted B candidates, align every leaf ResearchIndicator to the existing B spine, traverse B→A, assess fit, explain paths, and invoke mapped source runtimes;
3. identify constructs, outcomes, exposures, mechanisms, confounders, moderators, population, unit, time, and geography;
4. create a data-requirement matrix from approved leaf indicators;
5. retrieve candidate sources, datasets, and variables;
6. assess construct, population, time, space, granularity, access, and joinability fit;
7. distinguish direct measures, constructed measures, modeled estimates, forecasts, and proxies;
8. diagnose missing objective, subjective, administrative, experimental, observational, or multimodal data;
9. recommend additional sources without claiming unfound data already exists.

Use:

```bash
python3 "$GRDR_LAUNCHER" diagnose-coverage /absolute/path/to/request.json
```

Matching is a core value of GRDR, but it depends on continued registry breadth and depth.
Keep question-specific literature, indicators, and mappings under `research_projects/<project-id>/`; do not mix them into the canonical global source registry.

For a persisted topic-scaffold project, use the executable lifecycle:

```bash
python3 "$GRDR_LAUNCHER" start-research-project <spec.json>
python3 "$GRDR_LAUNCHER" research-project-status <project-id>
python3 "$GRDR_LAUNCHER" resume-research-project <project-id>
python3 "$GRDR_LAUNCHER" prepare-semantic-candidates <project-id>
python3 "$GRDR_LAUNCHER" align-research-indicators <project-id> <decisions.jsonl>
python3 "$GRDR_LAUNCHER" traverse-semantic-paths <project-id>
python3 "$GRDR_LAUNCHER" match-indicators <project-id>
python3 "$GRDR_LAUNCHER" explain-indicator-match <project-id> <indicator-id>
python3 "$GRDR_LAUNCHER" fetch-indicator-data <project-id> <indicator-id> --dry-run
python3 "$GRDR_LAUNCHER" fetch-indicator-data <project-id> <indicator-id> --seal-data-snapshot
python3 "$GRDR_LAUNCHER" expand-from-data-gaps <project-id>
# After candidate sources have been deepened or new sources registered:
python3 "$GRDR_LAUNCHER" resume-research-project <project-id>
python3 "$GRDR_LAUNCHER" rerun-matching <project-id>
```

The Agent may run every command above automatically. `approve-human-gate` is different: call it only after the human explicitly provides the reviewer identity and approval notes. Never use it to convert an Agent-generated topic scaffold into a formal, literature-grounded result. Preserve `workflow.json`, `data_gaps.jsonl`, `semantic_candidates.jsonl`, `semantic_alignments.jsonl`, and `semantic_paths.jsonl` with the five research-content files. Project-scoped R→B decisions must never be copied into canonical registry collections.

Treat `mapping_snapshot_health.status: stale` or `workflow_status: needs_rerun` as a hard invocation stop. Rebuild candidates with `--replace`, persist a current R→B decision, rebuild B→A paths, and run `rerun-matching`; never invoke an identifier carried forward from a superseded source snapshot.

## Use access extensions carefully

Read [references/access-architecture.md](references/access-architecture.md) only when adding an API adapter, federated query, or lawful snapshot. Keep source discovery and metadata separate from data retrieval.

Never bypass authentication, payment, consent, ethics review, data-use agreements, rate limits, or access controls.

## Release every functional batch

Read `docs/RELEASE_PROCESS.md`. For each completed functional or contract-changing batch:

1. bump `VERSION`;
2. update `CHANGELOG.md`;
3. validate the registry and tests;
4. commit only GRDR files;
5. tag the version;
6. push the branch and tag to GitHub;
7. report the version and GitHub URL.

Commit documentation-only corrections without changing `VERSION` when they alter no behavior, schema, Skill contract, or artifact. Never move an existing tag.

## Validate changes

```bash
"$GRDR_ROOT/.venv/bin/python" "$GRDR_ROOT/scripts/validate_registry.py"
"$GRDR_ROOT/.venv/bin/python" "$GRDR_ROOT/scripts/build_catalog.py" --check
"$GRDR_ROOT/.venv/bin/python" -m unittest discover -s "$GRDR_ROOT/tests"
```

Report added coverage, verification levels, unresolved evidence, matching limitations, version, and release status.
