# Changelog

## [4.5.8] - 2026-08-30

### Fixed

- Materialize and SHA-256-verify the complete GitHub Release snapshot on the first `reproducible` fetch when only the lightweight Agent cache is present.
- Bind `github_release_snapshot` routes to the materialized observation directory, so source Runtimes receive the frozen observation files instead of an empty route root.
- Preserve the lightweight default: `latest` still invokes a healthy official route without downloading knowledge or observation assets, and upgrades to the Release only when that fallback is actually selected.

### Validation

- Add regression coverage for policy ordering, official-to-Release fallback, and automatic Agent-to-full cache upgrade.
- Isolate semantic-resolution and Indicator Builder fixtures from the workstation's live registry and snapshot cache, preventing database growth from leaking into Core unit tests.
- Reproduce the defect and verify the repair with the private Epoch AI `2026-08-30-r1` Release: the Core public entry point returns the same 45 filtered model-training-compute rows through both `latest` official access and the frozen `reproducible` Release route; the upgraded cache passes complete knowledge, observation, and logical-parity verification.

## [4.5.7] - 2026-08-29

### Fixed

- Treat the ignored local Release-asset build directory as disposable after a GitHub publication has been verified, matching the existing optional local snapshot-cache contract.
- Keep pre-publication preparation strict: missing local Release assets still block publication, while a completed snapshot may be audited from its fingerprinted publication evidence, Storage receipt, source repository, and central card after local build bytes are removed.

### Validation

- Add regression coverage that rejects a missing Release build cache before publication and accepts its absence only after publication evidence exists.
- Preserve full checksum and archive-member verification whenever the local build cache remains present.

## [4.5.6] - 2026-08-29

### Changed

- Make high-cardinality deep-map staging, audit, sealing, and canonical promotion scale with the incoming database instead of the complete historical registry.
- Validate staged records through their transitive canonical-reference closure and retain exact cross-entity referential checks without materializing unrelated database records.
- Stream affected canonical JSONL collections through an atomic, rollback-safe promotion transaction; unchanged historical collections are neither loaded nor rewritten.
- Reuse compiled JSON Schema validators across large execution batches.

### Validation

- Proved the upgrade against the locked ILOSTAT deep map: 91,610 candidate records, 1,958 work units, 11,748 stage closures, 5,874 topology closures, and 46,999 route checks passed with zero audit errors.
- Reduced the historical-registry audit path observed during ILOSTAT planning from roughly five minutes and 20 GB peak memory to about five seconds and 338 MB; the complete 91,610-record staging transaction completed in about 82 seconds at 2.36 GB peak memory.
- Add regression coverage that fails if staging or Storage calls the legacy whole-registry materializer, plus a streamed update-and-append merge test.

## [4.5.5] - 2026-08-29

### Changed

- Split derived local materialization into a default lightweight `agent` scope and an explicit `full` scope. Agent scope downloads only the source SQLite, Runtime files, online-route audits, manifest, receipt, and a cache profile; it never downloads knowledge or observation payloads.
- Make global-index refresh automatically restore a missing lightweight Agent shard from the verified GitHub Release, keeping a Source searchable, routable, and officially callable without retaining its full local database mirror.
- Add `materialize-source-snapshot --scope agent|full`; preserve legacy complete caches as `full` and allow an Agent cache to be explicitly upgraded to a complete expansion.

### Integrity and validation

- Bind every Schema-valid derived cache profile to Source, snapshot, and logical-content fingerprint; verify exact Agent inventory for lightweight caches and exact complete GitHub inventory for full caches.
- Keep full knowledge and observation requirements unchanged in canonical GitHub Releases and Storage receipts. The new cache scopes affect only disposable use-plane bytes.
- Add regression coverage for Agent-only verification, payload omission, tamper rejection, and selective Release-asset download.

## [4.5.4] - 2026-08-28

### Fixed

- Bind execution-spine checkpoints to graph topology only: node identities, edge identities and endpoints, roots, and leaves.
- Stop serializing complete Variable, Construct, DataElement, definition, evidence, and Codelist payloads when computing a topology fingerprint; those contents remain independently protected by the staging manifest.
- Record the new `topology-v2` fingerprint contract on newly created and batch-recorded spines while retaining Schema compatibility with existing sealed projects.

### Validation

- Add regression coverage proving that large non-topological record payloads do not affect the spine fingerprint while a changed graph endpoint does.
- Preserve endpoint membership, connectivity, staged-content fingerprints, execution locks, and Storage receipt verification as independent completion gates.

## [4.5.3] - 2026-08-28

### Fixed

- Resolve the Storage contract contradiction exposed by OECD Data Explorer: a current-only large database may use `no_mirror` without falsely labeling its mutable official API as a frozen or version-pinned observation route.
- Keep complete `latest` online coverage and Core-driven parameterized invocation mandatory for every registered Variable.
- Permit an empty source-level `reproducible` policy only when `no_mirror` is paired with an enabled on-demand research-project snapshot cache; record the limitation as `research_snapshot_required`.

### Semantics and validation

- Persist an explicit reproducibility status and evidence basis in online-access manifests, Storage snapshot profiles, generated source documentation, and package validation.
- Preserve existing source-level reproducible and offline routes whenever a frozen, versioned, local, mounted, or GRDR Release observation path actually exists.
- Add regression coverage for a current-only, no-mirror source and document that its first bounded `latest` result must be sealed before reproducible research use.

## [4.5.2] - 2026-08-28

### Fixed

- Replace quadratic duplicate detection in large staged-record batches with a linear-time set scan while retaining exact duplicate rejection.
- Replace repeated list membership scans in execution-spine endpoint and connectivity validation with set membership, so full topology audits scale linearly with graph size.
- Bound successful staging command output for batches above 1,000 records to a deterministic sample and complete ID fingerprint instead of emitting every canonical ID.

### Validation

- Add large synthetic regression cases for duplicate detection and spine membership.
- Validate the repaired execution path against an OECD deep map containing 331,002 canonical candidates and 250,912 relationships; the six content stages, three spines, and 31 shape-specific checks completed with zero audit errors or warnings. OECD-specific records remain external to database-independent Core.

## [4.5.1] - 2026-08-26

### Fixed

- Close the Storage acceptance gap that allowed a source Runtime to pass its own offline/online declarations while rejecting Core's public `fetch-variable` parameter names.
- Add Core-driven parameterized invocation probes using a real registered Variable, nonempty observation results, output artifacts, and an explicit selected-route expectation.
- Require a `latest` probe for every nonempty Variable index and an additional `offline` probe whenever the snapshot declares an offline route.

### Audit and artifacts

- Persist `invocation_acceptance_audit.json` inside the Agent artifact and bind it into the Storage package, local materialization audit, source README, and generated source-repository tests.
- Add regression coverage that rejects the exact `--start-period` versus source-specific `--start-year` protocol drift discovered during source validation.
- Revalidate the repaired gate against a completed real source snapshot: its online and offline population probes for one country and two years each returned two rows through their required routes. Source-specific evidence remains in the external version archive, not in database-independent Core.

## [4.5.0] - 2026-08-25

### Added

- Add an external, rebuildable Global Index & Routing Layer inside Core Agent Runtime, without creating a seventh Skill or a fourth database-production step.
- Add cross-source SQLite/FTS discovery records, exact entity locators, Variable-to-Construct links, tested Variable-to-route mappings, source-card fingerprints, and a machine-readable global-index manifest.
- Add `global-index-status`, `update-global-index`, `rebuild-global-index`, `audit-global-index`, and `route-variable` commands.

### Performance and routing

- Replace ordinary all-source variable and semantic discovery with two-stage retrieval: global candidate recall followed by opening only selected source Agent indexes.
- Route known Variables to candidate Sources before source Runtime 2.0 verification and invocation; preserve the legacy central/distributed scan as an explicit failure fallback.
- Incrementally refresh only changed central records or source snapshots. An unchanged index performs no SQLite or manifest write; explicit audit can still force complete source verification.

### Architecture and validation

- Keep the populated global index under external `GRDR_STATE_ROOT/indexes/`; Core contains only generic code, Schema, documentation, and synthetic tests.
- Add deterministic rebuild, incremental no-op, search, route, integrity-audit, and source-isolation tests; align the North Star, Agent protocol, access architecture, workflow, diagrams, and relevant Skills with the executable Runtime boundary.

## [4.4.0] - 2026-08-25

### Changed

- Make the GitHub source repository and Release the canonical published snapshot; remove external Elements storage from new Storage specifications, capacity decisions, completion gates, receipts, and diagrams.
- Treat any expanded local snapshot as a disposable, rebuildable runtime cache. Retain read compatibility for legacy Elements paths and Core 4.0–4.3 source cards.
- Reduce the default capacity contract to two GitHub boundaries: 5 GiB total observation bytes per database Release and strictly under 2 GiB per Release asset.

### Performance and reliability

- Persist manifest-bound full-SHA verification receipts outside immutable Core, so unchanged snapshots avoid rehashing all content on every fresh CLI process while explicit audit, first materialization, and file mutation still force full verification.
- Prefilter official route candidates through the exact Variable-to-route map before invoking a source Runtime.
- Add bounded exponential-backoff retry for transient official-route timeouts, HTTP 429/5xx responses, and connection interruptions; preserve an attempt-by-attempt trace and never retry semantic or request errors.

### Validation

- Add Schema 4.1 Storage artifacts and Plan pipeline contract 4.2 with mandatory GitHub knowledge/Agent publication and optional local cache semantics.
- Update Storage, Runtime, Skills, human/Agent documentation, architecture diagrams, capacity tables, and compatibility tests to the same executable contract.

## [4.3.0] - 2026-08-25

### Breaking storage and runtime contract

- Separate every snapshot into three independent axes: Plan-locked knowledge scope, mandatory online access, and capacity-dependent observation replication.
- Replace `federated_on_demand` as a replication choice with `no_mirror`; official online access is now universal rather than one mutually exclusive storage mode.
- Upgrade new source artifacts to `grdr-source-runtime/2.0` and route context `grdr-route-context/1.0`.

### Added

- Add Schema-validated `online_access.json` and `online_runtime_audit.json` artifacts with explicit official availability, API/bulk-download/browser-automation/GRDR-Release methods, exact Variable-to-route coverage, and zero-unresolved completion.
- Add `latest`, `reproducible`, and `offline` Runtime policies with ordered route attempts, automatic declared-route fallback, and selected-route evidence.
- Add independent full-mirror, partitioned-mirror, and no-mirror replication while keeping capacity thresholds limited to copied observation bytes.
- Persist requested route policy and actual observation route in research-project data snapshots.

### Validation

- Add Storage regression coverage for all three replication modes and for rejection of any indexed Variable without an online route.
- Add Runtime regression coverage for latest/reproducible/offline ordering and official-to-GRDR-Release fallback.
- Align the architecture diagrams, decision tables, workflow documentation, and relevant Skills with the executable v4.3 contract.

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
