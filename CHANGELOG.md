# Changelog

All notable changes to GRDR are documented here. Versions follow Semantic Versioning.

## [1.1.0] - 2026-08-19

### Added

- Persistent database deep-mapping projects under `deep_map_projects/<source>/`, with a bounded project definition, ordered work-unit ledger, generated human report, history, blockers, and deterministic next action.
- Seven executable database lifecycle operations: `start-database-deep-map`, `database-deep-map-status`, `resume-database-deep-map`, `record-database-deep-map-phase`, `record-database-deep-map-stage`, `audit-database-deep-map`, and `complete-database-deep-map`.
- Database and work-unit classification for discipline, primary/secondary origin, provenance role, production mode, structural archetype, access regime, and composable extraction routes.
- Strict schemas and completion contract for counted Dataset, DataStructure, DataElement, Variable, Construct, and Access stages.
- Route guidance for catalogs, statistical cubes, tables, APIs, surveys, administrative systems, geospatial data, scientific arrays, biomedical data, knowledge graphs, multimodal corpora, restricted environments, and derived data.
- Read-only exact `next_target` and queue previews, deterministic within-stage native ordering and cursor rules, legal update examples, and a bundled SDMX inspection entry point.

### Changed

- `$grdr-deep-map-database` is now an executable, resumable state machine rather than a guidance-only profiling procedure.
- Mapping progress and strict completion are reported separately; only fully counted and evidenced `verified_complete` or `not_applicable` stages count toward strict completion.
- The generated catalog now exposes persistent deep-map progress for every registered source and links to the corresponding project report where one exists.
- UNdata has been migrated into the first real 36-work-unit deep-map project. Its prior records remain useful evidence, but are no longer mistaken for complete database coverage.

### Results

- The dated UNdata boundary contains all 36 official datamarts and 216 required work-unit stages.
- At migration, 42 stages are mapped and 2 are strictly closed: 19.44% mapping progress and 0.93% strict completion, with two documented access blockers.
- The next deterministic target is the Energy Statistics variable stage using the SDMX-cube route; GRDR cannot declare UNdata complete until every bounded stage closes and all blockers are resolved.

## [1.0.0] - 2026-08-18

### Added

- First-class `DataStructure` schema, registry collection, CLI query, validation rules, catalog rendering, and typed knowledge-graph relationships.
- Explicit deep-map topology for UNdata Energy Statistics, UNdata Greenhouse Gas Inventory, and the representative World Development Indicators chain.
- `$grdr-deep-map-database`, a dedicated Skill for deep-reading a database and mapping its native structure through data elements, research variables, and theoretical constructs.

### Changed

- Stabilized the six-layer content chain as Institution → Source → Dataset → DataStructure → 5A DataElement / 5B Variable → Construct.
- Moved Resource out of the content hierarchy: APIs, files, queries, authentication, limits, and licenses are now access sidecars and do not advance profiling depth.
- Replaced `$grdr-source-profiler` with `$grdr-deep-map-database` across the repository, installed Skills, documentation, tests, and release checks.
- Upgraded SourceProfile to schema `1.0.0` with separate DataStructure, DataElement, Variable, Construct, and access claims.

### Migration note

- This is a major version because the layer-4 meaning and SourceProfile contract are incompatible with the 0.x model. Version 1.0 stabilizes the mapping architecture; it does not claim complete deep coverage of all registered databases.

## [0.6.0] - 2026-08-18

### Added

- Seven persisted research-project operations: `start-research-project`, `research-project-status`, `approve-human-gate`, `resume-research-project`, `match-indicators`, `expand-from-data-gaps`, and `rerun-matching`.
- Workflow-state and data-gap schemas, deterministic orchestration logic, lifecycle history, exact-construct matching, independent fit dimensions, and bounded candidate-source expansion.
- First real exploratory closed-loop project covering population, final energy consumption, income per capita, industrial structure, and carbon dioxide emissions excluding LULUCF.
- Human-readable project report and regression tests covering the full exploratory cycle and explicit named-human approval recording.

### Changed

- Research projects now preserve two coordinator artifacts—`workflow.json` and `data_gaps.jsonl`—alongside the five evidence and indicator artifacts.
- A current-snapshot miss now becomes an auditable expansion record and can be rechecked after registry deepening without being misreported as external nonexistence.
- The main GRDR and indicator-builder Skills now document the executable closed loop and the boundary between automated Agent work and human decisions.

### Results

- The first test matched 3 of 5 leaf requirements directly: CO2 emissions excluding LULUCF, population size, and final energy consumption.
- Income per capita and industrial structure remained explicit current-snapshot gaps; UNdata National Accounts Main Aggregates was identified as a profiling lead, not asserted as a verified variable match.
- The actual project remains an exploratory topic scaffold with the indicator-framework gate pending; no human approval was inferred or self-issued.

## [0.5.0] - 2026-08-18

### Added

- First catalog-level database profile: all 36 UNdata datamarts plus a separate record of the six official glossaries at the 2026-08-18 snapshot boundary.
- Deep Energy Statistics and Greenhouse Gas Inventory chains with 16 SDMX data elements, 13 research-matchable variables, and 13 evidence-linked constructs.
- `DataElement` schema and `get-data-element` command for dimensions, measures, identifiers, time dimensions, attributes, units, code lists, flags, and conversion metadata inside layer 5.
- UNdata SDMX adapter, health record, deterministic catalog curator, and reusable generic SDMX inspector bundled with `$grdr-source-profiler`.
- Upstream-provider institution relationships and human-readable profiling-scope, enumeration, completeness, and blocker details on every database page.

### Changed

- Layer 5 is now explicitly divided into 5A source-native data-structure elements and 5B research-matchable variables without adding a seventh GRDR layer.
- `$grdr-source-profiler` now requires multidimensional structure recovery before variable construction and tests metadata access separately from observation access.
- UNdata access is recorded as degraded rather than unavailable: official dataflow and data-structure endpoints work, while documented observation queries timed out or returned HTTP 500 across dated live probes.
- UNdata catalog completeness is bounded to the official datamart identity catalog; resource, variable, and construct depth remains explicitly representative.

## [0.4.0] - 2026-08-16

### Added

- Dedicated `$grdr-indicator-builder` Skill connecting research questions and substantial literature corpora to evidence-linked, multi-level indicator systems.
- Separate schemas for indicator projects, literature documents, atomic evidence units, research-indicator hierarchies, and indicator-to-GRDR-variable mappings.
- Deterministic `audit-indicator-project` command checking evidence traceability, hierarchy integrity, leaf operationalization, variable references, mapping semantics, and human approval gates.
- Topic-only exploratory scaffolding and formal corpus-grounded workflows without imposing an arbitrary universal paper-count threshold.
- Explicit human responsibility for corpus-boundary approval, final indicator-framework approval, and contested proxy or definition-conflict mappings.

### Changed

- The main `$grdr` Skill now coordinates a dual chain: source-native six-layer database profiling and question-specific literature-grounded indicator construction, joined at leaf-level variable matching.
- Question-specific literature, indicators, and mappings are isolated from the canonical global registry under `research_projects/<project-id>/`.

## [0.3.1] - 2026-08-15

### Fixed

- Made the `$grdr-source-profiler` wrapper discover a repository-bundled GRDR root before falling back to the local installed path, so the Skill works in GitHub Actions and other checkouts.

## [0.3.0] - 2026-08-15

### Added

- Dedicated `$grdr-source-profiler` Skill for evidence-backed six-layer decomposition of individual databases.
- Six-layer source profiling protocol with explicit scope modes, integrity rules, completion conditions, and large-catalog safeguards.
- Persistent source-profile records and schema for inventory scope, per-layer claims, enumeration boundaries, blockers, and review dates.
- `audit-source-depth` and `audit-all-source-depth` commands to distinguish source-only registrations, dataset-depth work, variable-depth work, and six-layer chains.
- Human catalog visibility for each database's current profiling stage and the explicit distinction between a populated chain and complete upstream inventory.

### Changed

- The main `$grdr` Skill now routes deep database decomposition to the dedicated profiler workflow.
- Release checks now require both version-controlled GRDR Skills.

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
