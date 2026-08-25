# GRDR Storage Transaction Contract

## Fixed topology

One deeply read Source owns one private source repository. One dated or versioned snapshot owns one GitHub Release, one callable Elements directory, and one location-aware manifest. Immutable GRDR Core stores only shared schemas, Skills, programs, empty templates, and search infrastructure. External GRDR state stores the latest source-archive index card and canonical records.

The source repository declares its Core version. It must not fork or copy Core Skills.

## Three snapshot properties

Storage must persist three independent properties:

1. `knowledge_scope`: inherit the Plan scope mode, completion claim, boundary, snapshot time, and scope fingerprint without modification;
2. `observation_replication`: select `full_mirror`, `partitioned_mirror`, or `federated_on_demand` and state the exact completeness basis;
3. `observation_placement`: declare every actual or on-demand location: `github_release`, `elements`, `object_store`, `official_upstream`, or `research_project_cache`.
4. `capacity_assessment`: record the deployment-local thresholds, actual captured bytes, optional upstream-size estimate, policy-relative size class, selected mode and placements, and compliance result.

Knowledge completeness never implies observation replication completeness, and reduced observation custody never permits reduced knowledge depth.

## Required representations

The GitHub Release and Elements always contain:

- `knowledge/`: Plan, Execute ledgers, staged canonical records, evidence, canonical archive package and receipt, and human report;
- `agent/`: the source-scoped SQLite index, runtime descriptor, source-specific executable entrypoint, and sealed runtime audit.

`observations/` exists only at locations declared by the observation policy. The Release manifest binds the ordered logical file inventory, per-file locations, SHA-256 values, sizes, Release assets, external locations, canonical archive receipt, Core version, repository identity, and snapshot identity.

Raw observation files must never enter `knowledge/`. Exclude every observation input and every additional `raw_observation_exclusions` root during knowledge packaging, then reject any SHA-256 shared across the final knowledge and observation inventories. Release assets must have disjoint logical memberships.

## Mode obligations

- `full_mirror`: require nonzero observation inputs and exact agreement with the declared file denominator.
- `partitioned_mirror`: require nonzero inputs, a Schema-valid partition manifest, and exact agreement among partition boundaries, names, file paths, sizes, SHA-256 values, and declared file and partition denominators.
- `federated_on_demand`: require zero local observation inputs, an `official_upstream` location, and a runtime that resolves every indexed Variable.

GitHub observation archives are optional. Elements observation bytes are optional. A mounted object-store copy must be copied and hashed before completion. Research-project caches are derived use-plane artifacts and never mutate the canonical source snapshot.

## Transaction order

1. Audit the sealed Execute handoff.
2. Promote canonical records transactionally if necessary.
3. Inherit and verify the Plan knowledge scope.
4. Build the knowledge and Agent artifacts, exclude observation roots, and run the source runtime's offline full-variable self-test.
5. Apply the observation replication and placement policy, build each declared inventory, and prove no cross-component duplicate.
6. Generate Release assets and source-repository files.
7. Verify every claimed location and the non-receipt GitHub publication assets by read-back.
8. Build and upload the Storage receipt, then read back and verify its exact size and SHA-256 plus the Release tag and source-repository commit.
9. Transactionally seal publication evidence and receipts, then write the central source-archive card to external GRDR state and prove Core remained byte-identical.

Never write the central card before verified publication. Never reuse a snapshot ID for different bytes. Use a new snapshot for every changed upstream boundary, observation payload, completeness claim, or placement policy.

## Failure semantics

Local preparation may be retried idempotently only when the existing package passes audit and identifies the same snapshot. A path containing different content is a conflict, not a cache.

A failed GitHub publication leaves the package `ready_for_publish`; it does not undo verified external-state promotion or successfully materialized locations. A checksum, identity, completeness, duplication, or manifest mismatch requires a new snapshot build.
