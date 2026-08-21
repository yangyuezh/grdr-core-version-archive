---
name: grdr-execute-database-deep-map
description: "Execute a fingerprint-locked GRDR database deep-map project: resume its deterministic queue, deeply recover each work unit's native data structure and disciplinary semantics, build the DataElement-to-Variable-to-Construct bridge, stage evidence-backed canonical candidates, and close every route obligation without writing the canonical registry. Use for Step 2 when an existing schema-3 deep-map project must be started, resumed, repaired, or audited through a sealed archive handoff."
---

# GRDR Step 2 — Execute Database Deep Map

## Mission and exclusive boundary

Deep-read one database inside the exact Step 1 boundary and produce a sealed `staged_deep_map_records` handoff. This Skill owns evidence acquisition, deterministic enumeration, candidate record staging, content-stage closure, both graph spines, the variable bridge, route checks, typed blockers, recovery, and archive-package preparation.

Never edit `registry/*.jsonl` directly or call `archive-database-deep-map`. Only `$grdr-archive-database-deep-map` may promote staged records into the canonical registry. Do not silently change the plan, scope, denominator, work-unit order, or route assignment; start a new bounded pass or use an explicit migration.

Locate GRDR at `${GRDR_ROOT}` or `/Users/jasper/Documents/codex/grdr`. Read `docs/DATABASE_DEEP_MAP_WORKFLOW.md` and the task-relevant references:

- [engineering-contract.md](references/engineering-contract.md) for locks, deterministic recovery, staging, and drift rejection;
- [six-layer-standard.md](references/six-layer-standard.md) for entity meaning;
- [within-stage-enumeration.md](references/within-stage-enumeration.md) for counts, partitions, cursors, and checksums;
- [exception-recovery.md](references/exception-recovery.md) for access, scale, drift, ambiguity, and gates;
- [multidimensional-data.md](references/multidimensional-data.md) when cubes or meaning-bearing dimensions occur.

Use the JSON examples for phase, stage, spine, and check updates. Strict execution requires `jsonschema`; use the repository `.venv/bin/python`.

## Resume from machine state

At every fresh session, interruption, or handoff:

```bash
GRDR_PYTHON="${GRDR_PYTHON:-$PWD/.venv/bin/python}"
"$GRDR_PYTHON" scripts/grdr.py audit-database-deep-map-execution <project>
"$GRDR_PYTHON" scripts/grdr.py database-deep-map-status <project>
"$GRDR_PYTHON" scripts/grdr.py resume-database-deep-map <project>
```

Audit and status are read-only. Resume records history, so call it once when actually resuming. Work only on `next_target`. The queue is dependency-aware and deterministic; do not substitute an easier dataset, sample, stage, spine, or check.

If audit reports lock drift, stop execution. Do not overwrite the lock. Compare current machine state with the recorded plan, scope, and unit fingerprints.

## Deep-read the returned work unit

For each target, preserve source-native identities and authoritative evidence. The six execution stages are:

1. `dataset`: producer, method, population or universe, observation and analysis units, coverage, release, quality, uncertainty, limitations, and citation;
2. `data_structure`: the database's real recursive organization—catalog, collection, schema, table, view, dataflow, cube, questionnaire, instrument, wave, graph, corpus, array, stream, run, experiment, file hierarchy, or custom topology;
3. `data_element` (5A): native measures, fields, dimensions, identifiers, items, attributes, codes, weights, flags, coordinates, segments, annotations, and derived fields;
4. `variable` (5B): research-matchable operational quantities with units, population, resolution, dimension selections, comparable identity, joins, missingness, and derivation;
5. `construct`: evidenced scientific meaning, distinguishing direct, subjective, administrative, constructed, modelled, forecast, proxy, and latent measures;
6. `access`: metadata and observation routes tested separately, including API/file/query/secure environment, authentication, limits, formats, license, and reproducibility.

Access Resources attach to Dataset or DataStructure. They do not replace the database structure.

## Build two trunks and one bridge

Counts alone do not close a work unit.

- The structural spine must connect Dataset → recursive DataStructure → DataElement → Variable and preserve native nesting, grain, ordering, keys, cardinality, lineage, identifiers, roots, leaves, and edges.
- The scientific-semantic spine must connect multi-parent disciplinary and scientific-semantic nodes to Constructs. Preserve valid combinations instead of reducing them to one discipline or topic string.
- The variable bridge must prove how stored elements and structural selections form a Variable and what evidenced Construct that Variable measures.

A statistical cube Variable is not merely its measure label: it includes every meaning-bearing dimension selection. A survey Variable must preserve instrument, question, response coding, wave, weight, and population context. Apply the selected route contracts to the actual work-unit shape, including mixed-shape databases.

## Stage first, then close ledgers

Construct schema-valid candidate records and relationships in a JSON object, JSON array, or JSONL batch. Stage them transactionally:

```bash
"$GRDR_PYTHON" scripts/grdr.py stage-database-deep-map-records <project> <records.jsonl>
```

This command validates record schemas and the prospective merged registry, captures base and staged fingerprints, writes only `<project>/staging/*.jsonl`, and rolls back a rejected batch. Verify that canonical `registry/*.jsonl` files remain unchanged.

Only after referenced candidates are staged, record the matching ledger update:

```bash
"$GRDR_PYTHON" scripts/grdr.py record-database-deep-map-stage <project> <stage-update.json>
"$GRDR_PYTHON" scripts/grdr.py record-database-deep-map-spine <project> <spine-update.json>
"$GRDR_PYTHON" scripts/grdr.py record-database-deep-map-phase <project> <phase-update.json>
"$GRDR_PYTHON" scripts/grdr.py record-database-deep-map-check <project> <check-update.json>
```

A stage closes counts and canonical candidate IDs. A spine closes connected topology. A check discharges database-shape-specific obligations. All three are independently mandatory.

For a high-cardinality source, after every candidate in the bounded batch is staged, a single transaction may apply arrays named `phases`, `stages`, `spines`, and `checks`:

```bash
"$GRDR_PYTHON" scripts/grdr.py record-database-deep-map-execution-batch <project> <execution-batch.json>
```

Use this only to avoid repeatedly rescanning the same large staged registry. The operation validates every ordinary update schema, rejects duplicate or unknown targets, recomputes verification counts, checkpoint checksums, and topology fingerprints, writes all ledgers atomically, runs the full execution audit once, and rolls the entire batch back on error. It does not stage candidates, alter locks, relax queue obligations, seal the handoff, or write canonical records.

For SDMX, use the bundled inspector:

```bash
"$GRDR_PYTHON" skill/grdr-execute-database-deep-map/scripts/inspect_sdmx.py list-dataflows <base-url>
"$GRDR_PYTHON" skill/grdr-execute-database-deep-map/scripts/inspect_sdmx.py describe-structure <base-url> <agency> <dsd-id> <version>
"$GRDR_PYTHON" skill/grdr-execute-database-deep-map/scripts/inspect_sdmx.py list-codelist <base-url> <agency> <codelist-id> <version>
"$GRDR_PYTHON" skill/grdr-execute-database-deep-map/scripts/inspect_sdmx.py probe-data <base-url> <dataflow-id> <ordered-key>
```

## Keep the process moving truthfully

At every bounded batch, persist expected count, enumeration rule, completed count, last native ID, next native ID, snapshot/version, cursor checksum, evidence, and exact blocker. Continue every lawful independent branch.

Do not bypass controls, infer inaccessible observations, confuse access failure with absence, or mark convenience as `not_applicable`. Paid, restricted, changing, deleted, undocumented, or genuinely non-enumerable content limits the external claim; it does not weaken GRDR's requirement to record the boundary and blocker precisely.

Agents may prepare evidence but may not self-approve named human gates. Use the human-gate command only after the reviewer explicitly decides.

## Seal the Step 2 handoff

Repeat status, resume, stage, and update operations until the audit reports `execution_ready_for_archive: true`. Then:

```bash
"$GRDR_PYTHON" scripts/grdr.py prepare-database-deep-map-archive <project>
"$GRDR_PYTHON" scripts/grdr.py audit-database-deep-map-archive <project>
```

Preparation seals the staging manifest and writes a fingerprinted `archive_package.json`. After sealing, do not alter staged records or execution ledgers. If correction is necessary, create a new bounded execution pass rather than mutating the handoff.

## Handoff and report

Return project and Source IDs, locked boundary, work-unit denominator, selected routes, stage/spine/check progress, staged record IDs and action counts, human gates, blockers, next native cursor, execution audit, staging fingerprint, archive-package fingerprint, and exact Step 3 command.

Never report canonical ingestion until Step 3 issues a valid archive receipt.
