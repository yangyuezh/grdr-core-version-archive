# Changelog

All notable changes to GRDR are documented here. Versions follow Semantic Versioning.

## [0.2.0] - 2026-08-15

### Added

- Human- and Agent-readable database catalog generated from the canonical registry.
- Root README inventory containing every registered database, its publishing or maintaining institution, domain, verification status, and six-layer detail link.
- One independent directory and detailed page for every database, organized as Institution → Source → Dataset → Resource → Variable → Construct.
- Deterministic catalog generation and drift checks so new source records cannot omit their human-readable documentation.

### Changed

- GRDR curation rules now require the root README and six-layer catalog to remain synchronized with every source change.

## [0.1.1] - 2026-08-14

### Changed

- Renamed the Codex Skill from the legacy `global-research-data-warehouse` identifier to `grdr`.
- Standardized the installed folder, version-controlled Skill bundle, UI prompt, release checks, and documentation on `GRDR` and `$grdr`.
- Reframed legacy warehouse terminology as optional later-phase access and storage architecture rather than the project or Skill identity.

## [0.1.0] - 2026-08-14

### Added

- Project charter, North Star, ontology, assessment framework, Agent protocol, and rolling expansion plan.
- Machine-readable schemas for institutions, sources, datasets, resources, variables, constructs, relationships, adapters, storage records, and monitors.
- Initial cross-disciplinary registry with 18 institutions and 19 data sources.
- Evidence-backed partial verification for UNdata and eight core international data portals.
- First end-to-end source–dataset–resource–variable–construct example using World Development Indicators.
- Dependency-free JSON CLI for source, dataset, variable, provenance, access-layer, and registry-coverage queries.
- Registry validation and Agent workflow tests.
- Installed personal Codex Skill for operating and extending GRDR.

### Clarified

- GRDR is initially a Data Source Registry, Dataset Knowledge Graph, and Agent Research Data Infrastructure—not a project to copy every upstream dataset into one physical warehouse.
- The first approximately 100 sources are a bootstrap target, followed by institution, discipline, and scientific-question snowball expansion.
