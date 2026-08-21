---
name: grdr-archive-database-deep-map
description: "Audit and archive a sealed GRDR database deep-map execution package: verify the Plan → Execute fingerprint chain, detect canonical conflicts, validate the prospective merged registry, promote staged records, rebuild the human catalog, and issue an immutable archive receipt. Use only for Step 3 after grdr-execute-database-deep-map reports archive readiness; this is the sole database deep-map Skill authorized to write the canonical GRDR registry."
---

# GRDR Step 3 — Archive Database Deep Map

## Mission and exclusive boundary

Promote one sealed, verified Step 2 package into the canonical GRDR registry and issue a fingerprinted receipt. This Skill is the only step allowed to write `registry/*.jsonl`.

Do not discover new database content, change the plan, change the boundary, edit work-unit ledgers, fill missing evidence, modify staged records, or relax a failed obligation. Return any such work to a new Step 1 or Step 2 pass.

Locate GRDR at `${GRDR_ROOT}` or `/Users/jasper/Documents/codex/grdr`. Read [archive-contract.md](references/archive-contract.md) and [completion-contract.md](references/completion-contract.md). Strict archival validation requires `jsonschema`; use the repository `.venv/bin/python`.

## Require the sealed handoff

A candidate project must contain:

- schema-3 `project.json` with unchanged plan, scope, and unit-manifest locks;
- fully closed execution ledgers and route checks;
- sealed `staging_manifest.json`;
- schema-valid staged collections under `staging/`;
- `archive_package.json` whose plan, scope, unit, execution-ledger, staging-manifest, and package fingerprints are current;
- no unresolved or rejected human gate;
- `execution_ready_for_archive: true`.

Inspect without writing canonical state:

```bash
GRDR_PYTHON="${GRDR_PYTHON:-$PWD/.venv/bin/python}"
"$GRDR_PYTHON" scripts/grdr.py database-deep-map-archive-status <project>
"$GRDR_PYTHON" scripts/grdr.py audit-database-deep-map-archive <project>
```

The audit validates the prospective canonical registry and compares every staged record with its captured base fingerprint. A create whose ID now exists, an update whose base changed, a missing record, a stale package, catalog inconsistency, or Schema/integrity failure blocks archival.

Do not resolve a conflict by directly editing the manifest, package, or canonical record. Reopen through a new bounded execution pass, restage against the current base, and obtain a new sealed package.

## Promote transactionally

Only when `ready_to_archive: true`:

```bash
"$GRDR_PYTHON" scripts/grdr.py archive-database-deep-map <project>
```

The command:

1. re-runs the archive audit;
2. builds the prospective merged registry;
3. writes only staged create/update collections;
4. runs strict registry validation;
5. rebuilds and checks the human catalog;
6. rolls back canonical files, catalog, project, manifest, and receipt if any post-write gate fails;
7. marks validation and completion phases verified;
8. issues `archive_receipt.json` tied to the exact package fingerprint.

The operation is idempotent after a valid receipt. Repeating it returns `already_archived` without another promotion.

## Verify completion

```bash
"$GRDR_PYTHON" scripts/grdr.py database-deep-map-archive-status <project>
"$GRDR_PYTHON" scripts/grdr.py audit-database-deep-map <project>
"$GRDR_PYTHON" scripts/validate_registry.py
"$GRDR_PYTHON" scripts/build_catalog.py --check
```

Completion requires `archive_complete: true` and `completion_ready: true`. A closed execution without a receipt is only ready for archival. A receipt with stale fingerprints is invalid.

The receipt records project and Source IDs, package fingerprint, registry version, create/update/unchanged counts, collection counts, validation results, archive time, and its own fingerprint. Git history and release metadata version the repository; the receipt identifies this project transaction.

## Report

Return the exact bounded completion claim—not an unqualified “100%”—plus project and Source IDs, package and receipt fingerprints, promoted and unchanged counts by collection, registry and catalog validation results, archive time, final audit status, repository commit/tag, GitHub release, and CI result.

If archival is blocked, report the precise conflict or stale fingerprint and the required Step 1 or Step 2 recovery. Never claim ingestion without a valid receipt.
