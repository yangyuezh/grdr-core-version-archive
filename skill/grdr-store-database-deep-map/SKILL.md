---
name: grdr-store-database-deep-map
description: "Store one sealed GRDR database deep-map as a versioned, callable AI-agent snapshot: transactionally promote its canonical records into external GRDR state while leaving Core immutable, build a source-specific private Git repository, package the complete knowledge graph, Agent SQLite index, source runtime, and captured observations, materialize the matching Elements snapshot, publish one GitHub Release per snapshot, verify runtime coverage and SHA-256 parity, update the external central index card, and issue the final Storage receipt. Use only for Step 3 after grdr-execute-database-deep-map reports Storage readiness."
---

# GRDR Step 3 — Store Database Deep Map

## Mission and exclusive boundary

Turn one sealed Step 2 execution into one durable `versioned_database_snapshot`. Own the complete Storage transaction:

1. promote the sealed candidates into the canonical registry under external `GRDR_STATE_ROOT` and keep its internal archive receipt without modifying Core;
2. create or update one private source repository that references, but never copies, GRDR Core;
3. build the complete knowledge artifact, Agent SQLite index, source-specific runtime, and observation-data artifacts;
4. store the compressed distribution in one GitHub Release for the snapshot;
5. store the same logical snapshot as an expanded Elements directory;
6. verify every logical file and Release asset with SHA-256 and prove the runtime resolves every indexed Variable;
7. write the external central GRDR source-archive card and final Storage receipt.

Do not discover new content, change the Plan boundary, repair Execute ledgers, manufacture missing observations, combine multiple databases into one source repository, write database records into Core, implement unified research search inside Storage, or mark a locally prepared package complete before GitHub publication is verified. Search, matching, snapshot mounting, access-plan resolution, and retrieval belong to the independent GRDR Agent Runtime; Storage only packages and validates its source-scoped runtime input.

Resolve the absolute directory containing this active `SKILL.md`, then set `GRDR_LAUNCHER` to its bundled `scripts/grdr.py`. The launcher finds immutable Core without depending on the caller's working directory and selects Core's `.venv/bin/python` when present. Read [storage-contract.md](references/storage-contract.md), [repository-layout.md](references/repository-layout.md), and [completion-contract.md](references/completion-contract.md).

## Require the sealed Execute handoff

Start only when:

```bash
python3 "$GRDR_LAUNCHER" audit-database-deep-map-execution <project>
```

reports `execution_ready_for_storage: true`. Step 3 may perform the external-state canonical promotion if it has not already occurred, but it may not weaken any Step 2 obligation or modify Core.

## Define the snapshot

Create a Schema-valid Storage specification with:

- stable Source and source slug;
- one snapshot ID and one Release tag;
- exact GRDR Core version and repository URL;
- one private `owner/grdr-source-<slug>` repository and local working path;
- the Elements root;
- at least one named observation-data input containing nonzero bytes;
- source-specific adapter files needed for reproducibility.
- one Schema-valid `grdr-source-runtime/1.0` descriptor and its source-specific executable files.

The source repository references the Core version. Never duplicate Core Skills into it.

## Materialize and audit locally

```bash
python3 "$GRDR_LAUNCHER" prepare-database-deep-map-storage <project>
python3 "$GRDR_LAUNCHER" prepare-database-storage <project> <storage-spec.json>
python3 "$GRDR_LAUNCHER" audit-database-storage <project>
python3 "$GRDR_LAUNCHER" database-storage-status <project>
```

Preparation must produce:

- ordinary source-repository files: configuration, adapters, locked Plan, snapshot manifest, canonical archive receipt, README, and tests;
- Release assets: complete knowledge archive, one Agent runtime archive containing the SQLite index, runtime descriptor, executable entrypoint and runtime audit, one or more observation archives, and `manifest.json`;
- Elements: the complete expanded `knowledge/`, `agent/`, and `observations/` tree;
- `storage_package.json` bound to the canonical archive receipt and every logical checksum.

Reject zero observation files, zero total observation bytes, any indexed Variable the runtime cannot resolve, checksum mismatch, missing repository files, path conflicts, altered manifests, or incomplete Release-to-Elements coverage.

## Publish and close Storage

For the normal end-to-end path:

```bash
python3 "$GRDR_LAUNCHER" publish-database-storage <project>
```

Or run preparation and publication together:

```bash
python3 "$GRDR_LAUNCHER" store-database-deep-map <project> <storage-spec.json>
```

Publication creates or updates the private source repository, pushes its reviewable files, creates one GitHub Release for the snapshot, uploads the prepared assets, reads back the Release URL, records the source-repository commit, seals `storage_receipt.json`, uploads that receipt, writes the matching Elements receipt, and updates `registry/source_archives.jsonl`.

If publication was performed by another trusted process, record its verified machine evidence with:

```bash
python3 "$GRDR_LAUNCHER" record-database-storage-publication <project> <publication.json>
```

Do not invent a publication record. Verify repository, Release, tag, commit, asset names, sizes, and hashes first.

## Report

Return Source, project, and snapshot IDs; Core version; source repository and Release URLs; Elements path; knowledge, Agent-index, and observation counts; logical size; Release asset count; canonical archive, logical-content, package, publication, and Storage-receipt fingerprints; central card ID; and final audit.

Only `storage_complete: true`, `completion_ready: true`, and a valid `storage_receipt.json` mean the three-step factory has completed. A canonical archive receipt alone means knowledge records entered GRDR; it does not mean the database snapshot has been stored.
