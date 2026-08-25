---
name: grdr-store-database-deep-map
description: "Store one sealed GRDR database deep-map as a versioned, callable AI-agent snapshot: preserve its locked knowledge scope, choose full-mirror, partitioned-mirror, or federated observation handling, exclude raw observations from knowledge, package the complete knowledge graph and source runtime, verify every declared physical location, publish the source repository and GitHub Release, update the external central card, and issue the final Storage receipt. Use only for Step 3 after grdr-execute-database-deep-map reports Storage readiness."
---

# GRDR Step 3 — Store Database Deep Map

## Mission and exclusive boundary

Turn one sealed Step 2 execution into one durable `versioned_database_snapshot`. Own the complete Storage transaction:

1. promote the sealed candidates into the canonical registry under external `GRDR_STATE_ROOT` and keep its internal archive receipt without modifying Core;
2. create or update one private source repository that references, but never copies, GRDR Core;
3. inherit the exact Plan knowledge scope and independently declare observation replication and placement;
4. build the complete knowledge artifact, Agent SQLite index, source-specific runtime, and only the observation artifacts required by the selected mode;
5. publish knowledge and Agent artifacts in the GitHub Release, materialize them in Elements, and place observation bytes only where declared;
6. verify every declared location with SHA-256, prove zero knowledge/observation duplication, and prove the runtime resolves every indexed Variable;
7. write the external central GRDR source-archive card and final Storage receipt.

Do not discover new content, change the Plan boundary, repair Execute ledgers, manufacture missing observations, combine multiple databases into one source repository, write database records into Core, implement unified research search inside Storage, or mark a locally prepared package complete before GitHub publication is verified. Search, matching, snapshot mounting, access-plan resolution, and retrieval belong to the independent GRDR Agent Runtime; Storage only packages and validates its source-scoped runtime input.

Resolve the absolute directory containing this active `SKILL.md`, then set `GRDR_LAUNCHER` to its bundled `scripts/grdr.py`. The launcher finds immutable Core without depending on the caller's working directory and selects Core's `.venv/bin/python` when present. Read [storage-contract.md](references/storage-contract.md), [repository-layout.md](references/repository-layout.md), and [completion-contract.md](references/completion-contract.md). When composing the Storage specification, also read [observation-modes.md](references/observation-modes.md).

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
- one observation mode: `full_mirror`, `partitioned_mirror`, or `federated_on_demand`;
- an explicit completeness claim and the actual observation placements;
- named nonzero observation inputs for full/partitioned modes, or zero local inputs plus an official-upstream record for federated mode;
- every additional project path containing raw observations that must be excluded from knowledge;
- an on-demand research-project cache policy;
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
- Release assets: complete knowledge archive, one Agent runtime archive containing the SQLite index, runtime descriptor, executable entrypoint and runtime audit, optional observation archives only when GitHub is an observation placement, and `manifest.json`;
- Elements: complete expanded `knowledge/` and `agent/`, plus `observations/` only when Elements is an observation placement;
- optional mounted large-data copies or verified official-upstream pointers;
- `storage_package.json` bound to the locked knowledge scope, completeness claim, location-aware file inventory, canonical archive receipt, and every checksum.

Always exclude declared observation roots from `knowledge/`. Reject any content hash shared by knowledge and observations. Reject zero or denominator-mismatched observations in mirror modes, local observations in federated mode, any indexed Variable the runtime cannot resolve, checksum mismatch, missing repository files, path conflicts, altered manifests, or mismatch at any location that claims a copy.

## Publish and close Storage

For the normal end-to-end path:

```bash
python3 "$GRDR_LAUNCHER" publish-database-storage <project>
```

Or run preparation and publication together:

```bash
python3 "$GRDR_LAUNCHER" store-database-deep-map <project> <storage-spec.json>
```

Publication creates or updates the private source repository, pushes its reviewable files, creates one GitHub Release for the snapshot, uploads the prepared knowledge/Agent and any GitHub-placed observation assets, reads back the Release URL, records the source-repository commit, seals `storage_receipt.json`, writes the matching Elements receipt, and updates `registry/source_archives.jsonl`.

If publication was performed by another trusted process, record its verified machine evidence with:

```bash
python3 "$GRDR_LAUNCHER" record-database-storage-publication <project> <publication.json>
```

Do not invent a publication record. Verify repository, Release, tag, commit, asset names, sizes, and hashes first.

## Report

Return Source, project, and snapshot IDs; Core version; knowledge scope and completion claim; observation replication mode, completeness claim, placements, file and partition counts; source repository and Release URLs; Elements and external locations; knowledge, observation, logical-content, package, publication, and Storage-receipt fingerprints; central card ID; and final audit.

Only `storage_complete: true`, `completion_ready: true`, and a valid `storage_receipt.json` mean the three-step factory has completed. A canonical archive receipt alone means knowledge records entered GRDR; it does not mean the database snapshot has been stored.
