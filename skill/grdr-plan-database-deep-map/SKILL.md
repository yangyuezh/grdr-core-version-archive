---
name: grdr-plan-database-deep-map
description: "Diagnose an authoritative database before GRDR ingestion, define an honest bounded work-unit universe, compose database-shape route contracts, resolve required human gates, and create a fingerprint-locked deep-map project. Use when Codex receives a database name, URL, catalog, GRDR Source ID, intake, or legacy deep-map project and must perform Step 1 of the GRDR Plan → Execute → Archive factory without beginning content extraction."
---

# GRDR Step 1 — Plan Database Deep Map

## Mission and exclusive boundary

Convert one database into an audited, executable plan. This Skill owns diagnosis, boundary design, work-unit inventory, route selection, human-gate definition, and creation or migration of the locked project. Its sole handoff is a `locked_deep_map_project`.

Do not deep-read unit content, stage candidate registry records, edit `registry/*.jsonl`, seal an archive package, or declare completion. Step 2 belongs to `$grdr-execute-database-deep-map`; Step 3 belongs to `$grdr-archive-database-deep-map`.

Use `$grdr` first when the database lacks a canonical Source identity. Step 1 requires a resolved `grdr:source:...` record so the plan can lock stable identity and provenance rather than a temporary URL label.

Locate GRDR at `${GRDR_ROOT}` or `/Users/jasper/Documents/codex/grdr`. Read `docs/DATABASE_DEEP_MAP_WORKFLOW.md`, then load only the relevant references:

- [diagnostic-matrix.md](references/diagnostic-matrix.md) for mandatory preflight dimensions;
- [database-archetypes.md](references/database-archetypes.md) for non-exclusive structural patterns;
- [route-contracts.md](references/route-contracts.md) for composable obligations;
- [lifecycle-boundaries.md](references/lifecycle-boundaries.md) for exhaustive, rolling, versioned, federated, and question-bounded scopes.

Strict planning requires `jsonschema`. From the repository root, use `.venv/bin/python`; create the environment and install `requirements-validation.txt` only when authorized.

## Diagnose the database, not its label

Collect official or otherwise authoritative evidence for:

1. identity, aliases, maintainer, producer, aggregator, mirror, and provenance roles;
2. disciplines and multi-parent disciplinary membership;
3. primary, secondary, or hybrid data origin and the data-generating process;
4. source-native structures, including catalogs, schemas, tables, cubes, surveys, graphs, corpora, arrays, streams, experiments, simulations, imaging, sequence data, files, and custom forms;
5. content modalities, lifecycle, version model, update and deletion behavior;
6. metadata access versus observation access, authentication, payment, license, privacy, ethics, sovereignty, and redistribution;
7. scale, partitionability, rate limits, compute requirements, metadata maturity, language, and schema stability;
8. the pass boundary, snapshot/version/window, denominator strategy, stable work-unit identity, ordering, authorized actions, and prohibited actions.

The classifications are multi-label. One database may belong to several disciplines and use several structural routes. Do not force it into a mutually exclusive tree. If no existing route explains the observed structure, select `open_world_custom` and preserve the unresolved facts.

## Fix the three mapping products before execution

The plan must state how Step 2 will recover:

- the source-native structural spine: Dataset → recursively nested DataStructure → 5A DataElement → 5B Variable;
- the multi-parent scientific-semantic spine: disciplines, fields, objects, systems, phenomena, processes, populations, observation units, analysis units, applications, and methods → Construct;
- the variable bridge: DataElement/DataStructure context → Variable → evidenced Construct.

Institution and Source are project-level provenance context. Dataset is the normal work-unit anchor. Resource is an access sidecar—API, file, query service, secure environment, authentication, license—not a content layer.

## Generate and audit the plan

```bash
GRDR_PYTHON="${GRDR_PYTHON:-$PWD/.venv/bin/python}"
"$GRDR_PYTHON" -c "import jsonschema"
"$GRDR_PYTHON" scripts/grdr.py list-database-route-modules
"$GRDR_PYTHON" scripts/grdr.py plan-database-deep-map <intake.json> --output <plan.json>
"$GRDR_PYTHON" scripts/grdr.py audit-database-deep-map-plan <plan.json>
```

Interpret `plan_status` literally:

- `ready`: Step 1 may create the locked project;
- `ready_with_gates`: the project may start, but protected operations remain unavailable until named humans decide the gates;
- `needs_evidence`: continue read-only diagnosis;
- `blocked`: the declared constraints prohibit the required work.

A finite count is required only when the declared boundary is enumerable. For dynamic, federated, virtual, or genuinely non-enumerable systems, define a reproducible rolling, partitioned, versioned, or question-bounded claim. Never convert “currently reachable” into “the whole database.”

## Create the locked handoff

The start specification must align with the audited plan and contain the ordered work-unit manifest. Include deprecated, empty, inaccessible, and restricted entries in an exhaustive denominator rather than silently omitting them.

```bash
"$GRDR_PYTHON" scripts/grdr.py start-database-deep-map <start-spec.json>
"$GRDR_PYTHON" scripts/grdr.py upgrade-database-deep-map <legacy-project>
"$GRDR_PYTHON" scripts/grdr.py database-deep-map-status <project>
```

A valid Step 1 handoff contains:

- `project.json` at schema `3.0.0`, including the three-step pipeline contract;
- audited plan, explicit boundary, selected route modules, typed risks, human gates, and SHA-256 plan/scope/unit locks;
- `units.jsonl` with deterministic order and stable upstream identities;
- `checks.jsonl` with every applicable route obligation;
- an open `staging_manifest.json`;
- generated `README.md`;
- zero audit errors.

Do not self-approve access, privacy, ethics, sovereignty, contested semantics, or publication gates. Record only an explicit named-human decision:

```bash
"$GRDR_PYTHON" scripts/grdr.py record-database-deep-map-human-gate <project> <gate-id> --decision <approved|rejected|not_applicable> --reviewer <name> --notes <basis>
```

## Handoff and report

End Step 1 when the plan is executable or truthfully blocked. Return the project and Source IDs, plan status, completion claim, boundary and timestamp/version/window, diagnostic dimensions, route modules, work-unit denominator and ordering, human gates, risk flags, lock fingerprints, audit result, and exact Step 2 command.

Never report that the database has been deeply read merely because its plan exists.
