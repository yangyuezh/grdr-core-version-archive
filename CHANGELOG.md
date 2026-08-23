# Changelog

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
