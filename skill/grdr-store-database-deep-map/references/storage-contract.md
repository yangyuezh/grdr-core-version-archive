# GRDR Storage Transaction Contract

## Fixed topology

One deeply read Source owns one private source repository. One dated or versioned snapshot owns one GitHub Release and one location-aware manifest. An expanded local snapshot may be materialized as a disposable runtime cache, but it is not canonical storage and is never required for completion. Immutable GRDR Core stores only shared schemas, Skills, programs, empty templates, and search infrastructure. External GRDR state stores the latest source-archive index card and canonical records.

The source repository declares its Core version. It must not fork or copy Core Skills.

## Three independent snapshot axes

Storage must persist three independent properties:

1. `knowledge_scope`: inherit the Plan scope mode, completion claim, boundary, snapshot time, and scope fingerprint without modification;
2. `online_access`: require `all_registered_variables_online_callable`, declare official availability and executable routes, and persist exact route policies and test coverage;
3. `observation_replication`: select `full_mirror`, `partitioned_mirror`, or `no_mirror`, state the exact completeness basis, and declare any `github_release` or mounted `object_store` placements;
4. `cache`: separately declare whether research-project query snapshots may be created on demand;
5. `capacity_assessment`: record the deployment-local thresholds, actual captured bytes, optional upstream-size estimate, policy-relative size class, selected replication and placements, and compliance result.

Knowledge completeness, online callability, and observation replication are not interchangeable. Reduced observation custody never permits reduced knowledge depth or reduced online Variable coverage.

## Required representations

The GitHub Release always contains:

- `knowledge/`: Plan, Execute ledgers, staged canonical records, evidence, canonical archive package and receipt, and human report;
- `agent/`: the source-scoped SQLite index, Runtime 2.0 descriptor, source-specific executable entrypoint, sealed offline runtime audit, `online_access.json`, `online_runtime_audit.json`, and `invocation_acceptance_audit.json`.

`observations/` exists only at locations declared by the observation policy. The Release manifest binds the ordered logical file inventory, per-file locations, SHA-256 values, sizes, Release assets, external locations, canonical archive receipt, Core version, repository identity, and snapshot identity.

Raw observation files must never enter `knowledge/`. Exclude every observation input and every additional `raw_observation_exclusions` root during knowledge packaging, then reject any SHA-256 shared across the final knowledge and observation inventories. Release assets must have disjoint logical memberships.

## Online-access obligations

- The official state must be explicitly `callable` or `unavailable`, with an evidence basis.
- Routes may use `official_api`, `official_bulk_download`, `official_browser_automation`, or `grdr_release_snapshot`.
- Every declared route must pass the Runtime's `self-test-online` operation.
- The online audit must enumerate exactly the indexed Variables and give every Variable one or more tested route IDs.
- `unresolved_online_variable_count` must be zero. If neither an official route nor a GRDR Release route provides complete coverage, Storage cannot complete.
- Route policies must define `latest`, `reproducible`, and `offline`; Runtime records each attempted route and selected fallback. `latest` must be nonempty. `reproducible` may be empty only for a current-only `no_mirror` source with enabled on-demand research-project snapshots and an explicit `research_snapshot_required` status.
- Core must independently execute at least one real registered Variable through the public country/period `fetch-variable` arguments under `latest`; if an offline route exists, it must also execute an `offline` probe. Each probe must return the declared minimum nonzero row count and at least one output artifact, and its route and output fingerprint are sealed in `invocation_acceptance_audit.json`.
- A no-mirror source with only an unversioned current official route must not manufacture a source-wide reproducible route. It may complete with `research_snapshot_required`; the first bounded `latest` result must be sealed by the research project before reproducible analysis.

## Replication obligations

- `full_mirror`: require nonzero observation inputs and exact agreement with the declared file denominator.
- `partitioned_mirror`: require nonzero inputs, a Schema-valid partition manifest, and exact agreement among partition boundaries, names, file paths, sizes, SHA-256 values, and declared file and partition denominators.
- `no_mirror`: require zero observation inputs and zero replication placements. It does not relax online-access obligations.

GitHub observation archives are optional. A mounted object-store copy must be copied and hashed before completion. Local snapshot caches and research-project captures are derived use-plane artifacts and never mutate the canonical source snapshot.

## Transaction order

1. Audit the sealed Execute handoff.
2. Promote canonical records transactionally if necessary.
3. Inherit and verify the Plan knowledge scope.
4. Build the knowledge and Agent artifacts, exclude observation roots, and run the source Runtime's offline full-variable self-test.
5. Build the online-access manifest, run every online route test, prove exact all-Variable route coverage, then run Core-driven parameterized fetch probes and seal their invocation acceptance audit.
6. Apply the independent observation replication and placement policy, build each declared inventory, and prove no cross-component duplicate.
7. Generate Release assets and source-repository files.
8. Verify every claimed canonical location and the non-receipt GitHub publication assets by read-back; never require an optional local cache.
9. Build and upload the Storage receipt, then read back and verify its exact size and SHA-256 plus the Release tag and source-repository commit.
10. Transactionally seal publication evidence and receipts, then write the central source-archive card to external GRDR state and prove Core remained byte-identical.

Never write the central card before verified publication. Never reuse a snapshot ID for different bytes. Use a new snapshot for every changed upstream boundary, observation payload, completeness claim, or placement policy.

## Failure semantics

Local preparation may be retried idempotently only when the existing package passes audit and identifies the same snapshot. A path containing different content is a conflict, not a cache.

A failed GitHub publication leaves the package `ready_for_publish`; it does not undo verified external-state promotion or successfully materialized locations. A checksum, identity, completeness, duplication, or manifest mismatch requires a new snapshot build.
