# GRDR Storage Transaction Contract

## Fixed topology

One deeply read Source owns one private source repository. One dated or versioned snapshot owns one GitHub Release and one expanded Elements directory. Immutable GRDR Core stores only shared schemas, Skills, programs, empty templates, and search infrastructure. External GRDR state stores the latest source-archive index card and canonical records.

The source repository declares its Core version. It must not fork or copy Core Skills.

## Required representations

The GitHub Release is the compressed distribution representation. Elements is the expanded working representation. Physical layouts differ, but both must expand to the same logical file set:

- `knowledge/`: Plan, Execute ledgers, staged canonical records, evidence, canonical archive package and receipt, and human report;
- `agent/`: the source-scoped SQLite index, runtime descriptor, source-specific executable entrypoint, and sealed runtime audit;
- `observations/`: every observation file captured for the snapshot.

`storage_package.json` and Release `manifest.json` bind the ordered logical file inventory, SHA-256 values, sizes, Release assets, canonical archive receipt, Core version, repository identity, and snapshot identity.

## Transaction order

1. Audit the sealed Execute handoff.
2. Promote canonical records transactionally if necessary.
3. Build the complete local snapshot in a temporary directory and run the source runtime's offline full-variable self-test.
4. Generate Release assets and source-repository files.
5. Verify archive membership and SHA-256 parity against Elements.
6. Publish and read back GitHub repository and Release state.
7. Seal the Storage receipt.
8. Write the central source-archive card to external GRDR state and prove Core remained byte-identical.

Never write the central card before verified publication. Never reuse a snapshot ID for different bytes. Use a new snapshot for every changed upstream boundary or observation payload.

## Failure semantics

Local preparation may be retried idempotently only when the existing package passes audit and identifies the same snapshot. A path containing different content is a conflict, not a cache.

A failed GitHub publication leaves the package `ready_for_publish`; it does not undo the verified Elements copy or canonical promotion. Resume publication from the persisted package. A checksum, identity, or manifest mismatch requires a new snapshot build.
