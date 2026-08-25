# Changelog

## [4.2.0] - 2026-08-25

### Added

- Add deployment-local, adjustable GitHub-observation and Elements-full-mirror capacity thresholds, with 5 GiB and 10 GiB defaults, pre-copy enforcement, optional upstream-size estimates, and a sealed policy-relative size assessment in every new snapshot.
- Add a strict observation partition-manifest schema that binds Source, snapshot, partition boundaries, input names, every relative member path, byte size, SHA-256 value, and both denominators.
- Pass a location-aware `elements_mirror`, `mounted_object_store`, or `official_upstream` context to every invoked source runtime.

### Fixed

- Require full manifest and SHA-256 verification before ordinary distributed search, resolution, traversal, or invocation treats a local snapshot as callable; invalidate the process-local verification cache on any file metadata change.
- Treat a missing declared Elements observation placement as a hard error and remove a failed online materialization instead of returning a partially callable snapshot.
- Upload and read back the final Storage receipt before writing local completion state or the external central card; bind the verification evidence to repository, tag, exact commit, all Release assets, receipt size, and receipt SHA-256.
- Require partitioned mirrors to match the complete partition manifest instead of merely hashing an unchecked file.
- Align the README architecture and decision tables with actual local-mirror, mounted-mirror, federated, capacity, and post-Storage research-cache behavior.

### Validation

- Add regression coverage for capacity thresholds, strict partition members, failed remote receipt verification, complete-state transaction ordering, full Runtime verification, verification-cache invalidation, and route selection.
- Retain compatibility with existing two-argument publication recording by downloading and verifying the already-uploaded Release receipt.

## [4.1.1] - 2026-08-25

### Fixed

- Detect research mappings whose persisted semantic paths point to a superseded or missing source snapshot, report `needs_rerun`, and block misleading data invocation until recall, alignment, traversal, and matching are rebuilt.
- Make ordinary variable search default to latest callable source snapshots while retaining explicit `--snapshot-policy history` access to canonical historical records.
- Persist the deployment-local Elements root in external GRDR state so Agent commands can discover an existing external-disk snapshot without repeated command-line flags.
- Align the database factory documentation and Execute Skill with the schema-4.1 immutable-Core and external-card contract.

### Validation

- Add regression coverage for persisted Elements discovery, environment precedence, current-only variable search, stale research-project status, resumable rematching, and stale-fetch rejection.
- Revalidate all six installed Skill launchers, all three observation modes, Core isolation, Release metadata, and the complete synthetic R→B→A runtime path.

## [4.1.0] - 2026-08-24

### Added

- Add three independent snapshot properties: Plan-inherited knowledge scope, Storage-selected observation replication, and multi-location observation placement.
- Add executable `full_mirror`, `partitioned_mirror`, and `federated_on_demand` observation modes with explicit file or partition denominators and completeness claims.
- Decouple GitHub Release assets from large observation storage while keeping complete knowledge and Agent artifacts available in both Release and Elements.
- Add location-aware per-file manifests for GitHub, Elements, mounted object storage, official upstream access, and on-demand research-project caching.
- Add `fetch-variable --research-project-dir` and `fetch-indicator-data --seal-data-snapshot` to preserve query-scoped data, arguments, Runtime results, provenance, and SHA-256 manifests under a research project.

### Fixed

- Exclude declared raw-observation roots from the knowledge archive, reject knowledge/observation content-hash overlap, and reject duplicated logical membership across Release assets.
- Replace the obsolete all-content Release-to-Elements parity assumption with mandatory knowledge/Agent parity and location-specific observation verification.
- Preserve runtime callability when a large database's observations remain on Elements, mounted large storage, or the official upstream.

### Validation

- Add end-to-end Storage coverage for a full mirror on GitHub and Elements, an Elements-only partitioned mirror, and a zero-local-observation federated snapshot.
- Add regression coverage proving project-local raw observations are absent from knowledge and that on-demand research calls seal fingerprinted project snapshots.
- Retain schema compatibility for existing Storage 2.0 packages, receipts, publications, and source-archive cards.

## [4.0.2] - 2026-08-24

### Fixed

- Keep the Plan-time work-unit manifest immutable when Execute stages a newly created Dataset whose `dataset_id` was necessarily unknown before canonical promotion.
- Record the Dataset ID in the verified Dataset stage and graph topology without silently mutating the fingerprint-locked work unit.

### Validation

- Add a regression test covering a new source whose Dataset is created in Execute and confirm that stage closure preserves all Plan, scope, and unit-manifest fingerprints.
- Forward-test the fix against the exhaustive UNESCO UIS 12-package deep-map, including 51,228 staged knowledge-graph records, 72 stages, 36 spines, and 295 route checks.

## [4.0.1] - 2026-08-23

### Fixed

- Make semantic candidate recall default to the latest verified callable snapshot instead of mixing historical canonical versions into ordinary current-data research.
- Add explicit `--snapshot-policy history` for longitudinal snapshot discovery without deleting or rewriting historical registry records.
- Prefer snapshot-bound candidates over their central duplicates and report the applied snapshot policy and callable-source count.

### Validation

- Add a regression fixture proving historical canonical constructs are suppressed for a Source with a callable latest snapshot while remaining available in history mode.
- Re-run the complete Core release, isolation, portability, Storage, semantic traversal, and runtime test suite.

## [4.0.0] - 2026-08-23

### Breaking architecture boundary

- Make GRDR Core immutable and database-independent: all canonical records, source snapshot cards, deep-map projects, research projects, and generated state now live under an external `GRDR_STATE_ROOT`.
- Refuse any mutable-state root located inside the Core repository and require Storage to leave every Core registry template byte-identical.
- Upgrade the deep-map project contract to schema 4.0 with explicit immutable-Core and external-state requirements.

### Portability

- Add location-independent launchers to all six Skills and a portable Core pointer configured by `scripts/configure_core.py`.
- Remove machine-specific paths and source-specific examples from the reusable Core bundle.
- Support execution from an arbitrary database repository, working directory, cloned Core location, or machine.

### Validation

- Add mandatory tests for arbitrary-directory Skill invocation, pointer configuration, Core-state rejection, and post-Storage Core cleanliness.
- Strengthen release checks so every Core registry file must be empty and no machine-specific or real-database trace can enter the release.
- Validate the complete research-indicator → B semantic spine → A variable → official runtime workflow against an external, callable source snapshot without copying it into Core.

## [3.4.0] - 2026-08-23

### Added

- Add the sixth formal Skill, `grdr-resolve-research-semantics`, for the research use-plane R→B→A workflow.
- Add full-text semantic candidate recall across central and distributed Construct, SemanticNode, and Variable records.
- Persist evidence-constrained `ResearchIndicator → SemanticNode/Construct` decisions in project-scoped `semantic_alignments.jsonl` without mutating canonical B.
- Traverse stored B→A relationships into fingerprinted Variable, DataElement, DataStructure, Dataset, source, and snapshot paths.
- Add explainable semantic-graph matching, fit classification, alignment/path references in final mappings, and indicator-scoped official runtime invocation.
- Add schemas for semantic candidates, Agent decisions, persisted alignments, and graph paths.
- Extend research-project status, resume, rematching, and contested-mapping approval across the new semantic artifacts.

### Validation

- Add a synthetic five-layer integration test from candidate recall through source-runtime invocation.
- Forward-test the complete workflow against the callable distributed source snapshot indexed by Core, including a dry-run official access plan.

## [3.3.0] - 2026-08-23

### Added

- Add an independent distributed Agent Runtime for snapshot discovery, unified variable search, online Release materialization, variable resolution, and source-runtime invocation.
- Make research-project indicator matching and mapping audits consume the same distributed construct and variable records as direct Runtime search.
- Define the `grdr-source-runtime/1.0` protocol and package a source-specific executable runtime beside every Agent SQLite index.
- Require Storage artifact format 2.0 to prove that every indexed variable resolves through the source runtime before publication.
- Package the complete `agent/` directory as a deterministic Release archive so GitHub Release and Elements remain the same logical callable snapshot.
- Add runtime identity and asset information to the central source-archive card and final Storage receipt.

### Architecture

- Keep Plan → Execute → Storage as the database production plane.
- Keep search, matching, mounting, access-plan resolution, and official-source retrieval in the separate GRDR Agent Runtime use plane.

## [3.2.2] - 2026-08-22

### Fixed

- Validate a completed distributed `source_archives.jsonl` card without requiring the database's canonical Source record to be copied into GRDR Core.
- Add an integration regression test for a non-empty central archive index with an otherwise isolated Core registry.

## [3.2.1] - 2026-08-22

### Fixed

- Ignore macOS AppleDouble (`._*`) and `.DS_Store` metadata during Storage input selection, knowledge copying, logical inventory, and deterministic archive creation.
- Add a regression test proving external-disk sidecars cannot enter a database snapshot or break Release-to-Elements parity.
- Permit the central `source_archives.jsonl` index to contain completed source-snapshot cards while continuing to reject canonical database content from Core.

## [3.2.0] - 2026-08-22

### Added

- Isolated GRDR Core in a fresh repository without inherited database history.
- Fixed three independent Skills: Plan, Execute, and Storage.
- Added the generic route-contract planner, deterministic execution engine, transactional storage engine, research indicator builder, schemas, CLI, and Agent protocols.
- Added empty canonical registry templates and synthetic isolation tests.

### Storage contract

- One private source repository per database.
- One complete GitHub Release per database snapshot.
- One logically identical expanded Elements snapshot.
- Complete knowledge, Agent SQLite index, captured observations, SHA-256 parity, central source card, and final Storage receipt.

### Repository boundary

- No real database records, deep-map projects, adapters, generated source catalogs, or observation data are stored in GRDR Core.
