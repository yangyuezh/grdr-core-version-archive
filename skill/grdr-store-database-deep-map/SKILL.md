---
name: grdr-store-database-deep-map
description: "Store one sealed GRDR database deep-map as a versioned, callable AI-agent snapshot: preserve its locked knowledge scope, require tested online routes for every registered Variable, independently choose full, partitioned, or no observation replication, exclude raw observations from knowledge, package the complete knowledge graph and source Runtime, verify every declared route and physical location, publish the source repository and GitHub Release, update the external central card, and issue the final Storage receipt. Use only for Step 3 after grdr-execute-database-deep-map reports Storage readiness."
---

# GRDR Step 3 — Store Database Deep Map

## Mission and exclusive boundary

Turn one sealed Step 2 execution into one durable `versioned_database_snapshot`. Own the complete Storage transaction:

1. promote the sealed candidates into the canonical registry under external `GRDR_STATE_ROOT` and keep its internal archive receipt without modifying Core;
2. create or update one private source repository that references, but never copies, GRDR Core;
3. inherit the exact Plan knowledge scope and independently declare online access, observation replication, and observation placement;
4. require source Runtime 2.0 to test every declared online route, map every registered Variable to at least one executable route, and pass Core-driven parameterized fetch acceptance with a real Variable;
5. load the deployment-local capacity policy, measure actual observation bytes before copying, record any upstream-size estimate, and validate the selected replication and placement;
6. build the complete knowledge artifact, Agent SQLite index, source Runtime, online manifests/audits, and only the observation artifacts required by the selected replication mode;
7. publish knowledge and Agent artifacts in the GitHub Release and place observation bytes only where declared; any local expanded copy is a disposable cache;
8. verify every declared route and location, prove zero knowledge/observation duplication, and prove the Runtime resolves every indexed Variable both offline and online;
9. upload the final receipt, read it back from GitHub, and only then write the external central card and complete state.

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
- one replication mode: `full_mirror`, `partitioned_mirror`, or `no_mirror`;
- an optional upstream observation-size estimate and evidence basis when the full upstream byte size is known;
- an explicit completeness claim and the actual observation placements;
- named nonzero observation inputs for full/partitioned modes, or zero inputs and zero replication placements for no-mirror mode;
- an `online_access` contract whose completion requirement is `all_registered_variables_online_callable`, with official status, one or more executable routes, and explicit authority and verification method;
- every additional project path containing raw observations that must be excluded from knowledge;
- an on-demand research-project cache policy;
- source-specific adapter files needed for reproducibility.
- one Schema-valid `grdr-source-runtime/2.0` descriptor and its source-specific executable files, including `self-test-online` and the route-context protocol.
- `runtime.acceptance_probes`: at least one real registered Variable queried under `latest` with a Core-standard selector appropriate to the source: an entity `identifier`, a `country`, and/or a period boundary; when the snapshot has an offline route, add an `offline` probe too. Every probe must require nonzero rows and explicitly name the acceptable selected route.

Configure the GitHub observation threshold outside Core. The default is 5 GiB of observations per database Release and is adjustable without changing the Skill. Every GitHub Release file must remain strictly below 2 GiB. These are the only two default capacity boundaries. Treat the resulting size label as a policy-relative recommendation, never as a database identity or a reason to reduce knowledge scope.

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
- Release assets: complete knowledge archive, one Agent runtime archive containing the SQLite index, Runtime 2.0 descriptor, executable entrypoint, offline runtime audit, online access manifest, online runtime audit, and Core-to-Runtime invocation acceptance audit; optional observation archives only when GitHub is an observation placement; and `manifest.json`;
- optional local runtime cache: a lightweight verified Agent shard by default, with complete Release expansion only on explicit request; neither scope is canonical or required for completion;
- optional mounted large-data copies plus verified official or GRDR Release online routes;
- `storage_package.json` bound to the locked knowledge scope, completeness claim, location-aware file inventory, canonical archive receipt, and every checksum.

Always exclude declared observation roots from `knowledge/`. Reject any content hash shared by knowledge and observations. Reject zero or denominator-mismatched observations in mirror modes, any observation input or placement in no-mirror mode, any indexed Variable the Runtime cannot resolve, any online route whose test failed, any registered Variable with no tested online route, any Core-standard parameterized fetch that fails or returns zero rows/files, checksum mismatch, missing repository files, path conflicts, altered manifests, or mismatch at any location that claims a copy.

For `partitioned_mirror`, require `observation_partition_manifest.schema.json`. Every partition must state a boundary and must enumerate exactly the copied files, relative paths, sizes, and SHA-256 values. Partition names must equal `observation_inputs[].name`; file and partition counts must match both the manifest and the Storage completeness declaration.

## Publish and close Storage

For the normal end-to-end path:

```bash
python3 "$GRDR_LAUNCHER" publish-database-storage <project>
```

Or run preparation and publication together:

```bash
python3 "$GRDR_LAUNCHER" store-database-deep-map <project> <storage-spec.json>
```

Publication creates or updates the private source repository, pushes its reviewable files, creates one GitHub Release for the snapshot, and uploads the prepared knowledge/Agent and any GitHub-placed observation assets. It then constructs and uploads `storage_receipt.json`, reads back the repository, Release tag, exact commit, every asset, and the receipt hash. Only after that verification succeeds may it transactionally write local project evidence, complete project state, and the external `registry/source_archives.jsonl` card. A failed receipt upload leaves the snapshot `ready_for_publish`, never `complete`.

If publication was performed by another trusted process, record its verified machine evidence with:

```bash
python3 "$GRDR_LAUNCHER" record-database-storage-publication <project> <publication.json> [storage-receipt.json]
```

Do not invent a publication record. The command performs its own GitHub read-back verification; when the receipt path is omitted it downloads the Release receipt before sealing.

## Report

Return Source, project, and snapshot IDs; Core version; knowledge scope and completion claim; online completion state, official status, route methods, online Variable coverage and route policies; observation replication mode, completeness claim, placements, file and partition counts; source repository and Release URLs; optional local-cache state and external locations; knowledge, observation, logical-content, package, publication, and Storage-receipt fingerprints; central card ID; and final audit.

Only `storage_complete: true`, `completion_ready: true`, and a valid `storage_receipt.json` mean the three-step factory has completed. A canonical archive receipt alone means knowledge records entered GRDR; it does not mean the database snapshot has been stored.
