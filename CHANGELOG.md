# Changelog

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
