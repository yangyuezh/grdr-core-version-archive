---
name: grdr-deep-map-database
description: "Deep-read an authoritative database into GRDR and build its source-native structure spine, scientific-semantic spine, and variable-to-construct bridge through a locked, resumable, evidence-backed execution contract. Use when Codex receives a database name, URL, catalog, GRDR source ID, or existing deep-map project and must diagnose, plan, start, resume, repair, audit, or complete bounded database ingestion without silent scope drift."
---

# GRDR Deep-Map Database

## Mission and boundaries

Turn one database into a verified, traversable GRDR map. The database may contain many datasets and may combine multiple structures, producers, modalities, versions, access regimes, or disciplines.

Use `$grdr` for registry-wide discovery and research-question matching. Use `$grdr-indicator-builder` for question- or literature-derived indicator systems. This Skill owns the source-side process: fully understand a database inside a declared boundary, convert it into canonical GRDR records, and preserve enough evidence for another Agent or human to audit every claim.

Never treat a finite archetype list as complete. Diagnose first, compose known route contracts, and use the open-world route when the source does not fit. Unknown means unresolved, not absent.

The engineering guarantee is about GRDR's own execution: an executable project has immutable plan, scope, and work-unit locks; a deterministic dependency-aware queue; persisted checkpoints; audit-rejected drift; dual-spine completion gates; and evidence-only closure. It is not a promise that an upstream owner will expose inaccessible, paid, changing, deleted, undocumented, or genuinely non-enumerable content. Such conditions must remain explicit blockers or bounded claims and can never be converted into invented completeness.

Locate GRDR at `${GRDR_ROOT}` or `/Users/jasper/Documents/codex/grdr`. Before a write, read `docs/DATABASE_DEEP_MAP_WORKFLOW.md` and only the task-relevant references:

- [diagnostic-matrix.md](references/diagnostic-matrix.md): mandatory preflight dimensions;
- [engineering-contract.md](references/engineering-contract.md): non-negotiable execution locks, queue, checkpoints, drift rejection, and completion behavior;
- [route-contracts.md](references/route-contracts.md): route composition and check execution;
- [six-layer-standard.md](references/six-layer-standard.md): canonical content meaning;
- [lifecycle-boundaries.md](references/lifecycle-boundaries.md): exhaustive, rolling, versioned, federated, and question-bounded scopes;
- [within-stage-enumeration.md](references/within-stage-enumeration.md): deterministic counts, partitions, and cursors;
- [exception-recovery.md](references/exception-recovery.md): access, scale, drift, format, ambiguity, and human-gate recovery;
- [completion-contract.md](references/completion-contract.md): strict completion.

Strict planning and auditing require `jsonschema`; never accept a skipped validator as success. From the repository root, prepare and select a project-local interpreter when needed:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-validation.txt
GRDR_PYTHON="${GRDR_PYTHON:-$PWD/.venv/bin/python}"
"$GRDR_PYTHON" -c "import jsonschema"
```

If dependency installation is outside the authorized task, stop and report the dependency blocker. Use `$GRDR_PYTHON` for every GRDR command below.

## 1. Diagnose before starting

Build a standalone diagnostic intake or embed `diagnostic_intake` in a start specification. Do not infer the plan from a source label alone.

```bash
"$GRDR_PYTHON" scripts/grdr.py list-database-route-modules
"$GRDR_PYTHON" scripts/grdr.py plan-database-deep-map <intake-or-start-spec.json> --output <plan.json>
"$GRDR_PYTHON" scripts/grdr.py audit-database-deep-map-plan <plan.json>
```

The intake must describe evidence-backed identity, research goal and completion claim, origin and provenance roles, production modes, internal structures, modalities, lifecycle, versioning, access, sensitivity, scale, metadata maturity, languages, scope boundary, work-unit identity and denominator, authorized actions, prohibited actions, and known evidence.

Interpret `plan_status` literally:

- `ready`: executable;
- `ready_with_gates`: executable only outside protected operations until named humans decide the listed gates;
- `needs_evidence`: continue read-only diagnosis; do not start execution;
- `blocked`: the declared constraints prohibit the required work.

The planner selects `core_metadata` plus applicable route modules and produces mandatory facets. It may select several routes for one database. A portal-wide plan is not permission to apply every route to every work unit; classify mixed work units independently.

## 2. Fix the completion boundary and inventory

Register or resolve the canonical Source, then define what this pass can honestly complete. Use a Dataset or stable equivalent—collection, study, site extract, graph, corpus, instrument, model experiment, catalog partition, or rolling-window partition—as the work unit.

For enumerable scopes, preserve a dated/versioned manifest, stable identities, official or deterministic ordering, and expected count. Include deprecated, empty, inaccessible, and restricted entries in an exhaustive denominator. For rolling, federated, virtual, or non-enumerable systems, use the boundary rules in [lifecycle-boundaries.md](references/lifecycle-boundaries.md); never convert “currently reachable” into “the whole database.”

Start only with an audited executable plan:

```bash
"$GRDR_PYTHON" scripts/grdr.py start-database-deep-map <start-spec.json>
"$GRDR_PYTHON" scripts/grdr.py upgrade-database-deep-map <legacy-project>
```

Every project under `deep_map_projects/<source-or-pass>/` contains:

- `project.json`: plan, scope, phases, gates, history, and current state;
- `units.jsonl`: ordered work-unit ledger, six stage states, and three graph-closure states;
- `checks.jsonl`: route-contract obligations and typed blockers;
- `README.md`: generated human-readable progress and next target.

## 3. Follow the deterministic queue

```bash
"$GRDR_PYTHON" scripts/grdr.py database-deep-map-status <project>
"$GRDR_PYTHON" scripts/grdr.py resume-database-deep-map <project>
```

`status` and `audit` are read-only. `resume` writes a history event, so call it once when genuinely resuming. Work on the returned `next_target`; do not substitute a convenient example.

For each work unit, preserve the fixed content stages:

1. `dataset`: identity, producer, method, population/universe, observation unit, coverage, release, quality, limitations, and citation;
2. `data_structure`: source-native catalog/schema/table/dataflow/instrument/array/graph/corpus/run/file topology;
3. `data_element`: source-native fields, measures, dimensions, identifiers, items, attributes, codes, weights, flags, coordinates, segments, or annotations;
4. `variable`: research-matchable operational quantities with units, population, resolution, dimension selections, comparability, identity, and joins;
5. `construct`: evidenced research meaning and direct, subjective, administrative, constructed, modelled, forecast, proxy, or latent status;
6. `access`: metadata and observations tested separately, with API/file/query/environment, authentication, limits, license, and reproducibility.

Resource access remains a sidecar to Dataset or DataStructure; it is not a content layer. Write canonical `registry/*.jsonl` records and relationships before claiming a stage has mapped them.

The six stages populate two trunks and one bridge:

- **Source-native structure spine:** Dataset → DataStructure → DataElement → Variable. Institution and Source remain the project-level provenance context above every work unit. Preserve the database's real nesting, grain, ordering, keys, lineage, and native identifiers; do not flatten a cube, survey, graph, corpus, array, experiment, or file hierarchy into a generic table.
- **Scientific-semantic spine:** multi-parent SemanticNode graph → Construct. Classify by discipline, research field, object, system, phenomenon, process, population, observation unit, analysis unit, application area, and method wherever evidenced. Do not force a mutually exclusive discipline tree.
- **Variable bridge:** Variable → Construct, with any required DataElement/DataStructure context. This is the controlled connection between what the database stores and what research can claim it measures.

The content stages are inventory ledgers; the spines prove that the registered objects form connected, auditable mappings. Neither substitutes for the other.

## 4. Close stages, graph products, and route contracts

Copy `references/stage-update.example.json`, `references/spine-update.example.json`, `references/phase-update.example.json`, or `references/check-update.example.json` rather than inventing fields:

```bash
"$GRDR_PYTHON" scripts/grdr.py record-database-deep-map-stage <project> <stage-update.json>
"$GRDR_PYTHON" scripts/grdr.py record-database-deep-map-spine <project> <spine-update.json>
"$GRDR_PYTHON" scripts/grdr.py record-database-deep-map-phase <project> <phase-update.json>
"$GRDR_PYTHON" scripts/grdr.py record-database-deep-map-check <project> <check-update.json>
```

A stage answers “which canonical objects are mapped and counted.” A spine answers “do those objects form the required connected structural or semantic topology.” A route check answers “were the obligations specific to this database shape actually discharged.” All three must close. For example, a statistical cube must resolve ordered dimensions/codelists and prove observation access; a simulation archive must recover run/configuration lineage; a qualitative archive must preserve case/document/code provenance.

Use [within-stage-enumeration.md](references/within-stage-enumeration.md) inside every open stage. For SDMX, prefer the bundled inspector:

```bash
"$GRDR_PYTHON" skill/grdr-deep-map-database/scripts/inspect_sdmx.py list-dataflows <base-url>
"$GRDR_PYTHON" skill/grdr-deep-map-database/scripts/inspect_sdmx.py describe-structure <base-url> <agency> <dsd-id> <version>
"$GRDR_PYTHON" skill/grdr-deep-map-database/scripts/inspect_sdmx.py list-codelist <base-url> <agency> <codelist-id> <version>
"$GRDR_PYTHON" skill/grdr-deep-map-database/scripts/inspect_sdmx.py probe-data <base-url> <dataflow-id> <ordered-key>
```

## 5. Handle gates and failures without guessing

Agents may diagnose and prepare evidence, but may not approve privacy, ethics, sovereignty, access authorization, contested semantics, or question-bounded publication gates. A named human records the decision:

```bash
"$GRDR_PYTHON" scripts/grdr.py record-database-deep-map-human-gate <project> <gate-id> --decision <approved|rejected|not_applicable> --reviewer <name> --notes <decision-basis>
```

Record failures as typed check blockers: retryable, alternative route, authorization required, human decision required, upstream-only, or unknown. Continue all lawful independent work. Never bypass access controls, infer inaccessible observations, expose secrets or personal data, or treat failure as non-applicability. Follow [exception-recovery.md](references/exception-recovery.md).

If a new source shape is not explained by existing contracts, select `open_world_custom`, record observed structure and unresolved obligations, and propose a reusable route only after evidence and regression tests. Do not silently force the source into the nearest familiar type.

## 6. Complete only through the gate

```bash
"$GRDR_PYTHON" scripts/grdr.py audit-database-deep-map <project>
"$GRDR_PYTHON" scripts/grdr.py complete-database-deep-map <project>
```

Completion requires an executable resolved plan; unchanged plan, scope, and work-unit fingerprints; all human gates resolved without rejection; every required project phase closed; every required unit stage verified or evidenced not applicable; every structural spine, disciplinary spine, and variable bridge verified or evidenced not applicable; every route check passed or evidenced not applicable; no blockers or failed checks; valid canonical references; strict Schema validation; and synchronized human catalog output.

Report the exact completion claim and boundary, not a universal “100%.” A representative chain, catalog-only pass, question-bounded pass, rolling-current window, and exhaustive snapshot are different achievements.

## Report

Return project/source IDs, plan status, completion claim, boundary and snapshot/version/window, diagnostic dimensions and selected routes, work-unit denominator, stage and route-check progress, human gates, typed blockers, next target and cursor, changed canonical IDs, validation results, installed Skill version, Git commit/tag, GitHub release, and CI result.
