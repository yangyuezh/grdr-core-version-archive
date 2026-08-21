# Changelog

All notable changes to GRDR are documented here. Versions follow Semantic Versioning.

## [3.1.0] - 2026-08-20

### Added

- The first complete production demonstration of the three-Skill database factory: UNdata was independently planned, executed, and archived as `grdr:deep-map-project:undata-2026-08-21`, with a fingerprint-locked 36-datamart boundary and immutable archive receipt.
- A reproducible UNdata metadata curator covering all 36 official datamarts and six glossary sidecars through source-specific Explorer, SDMX codelist, current Statistical Yearbook, and official technical-note routes.
- A high-cardinality atomic execution-batch operation that validates and records phase, stage, dual-spine, bridge, and route-check updates in one rollback-safe project transaction.
- Dated UNdata evidence and execution artifacts: 8,719 Explorer hierarchy nodes, 9,334 source-exposed variables, 194 data elements, 41 semantic nodes, and 43,000 knowledge-graph relationships.
- Regression tests for atomic high-cardinality execution, rollback on an invalid target, UNdata snapshot denominators, canonical archive counts, receipt integrity, and the human-readable result boundary.

### Changed

- UNdata's new production project closed 216/216 content stages, 108/108 graph products, and 638/638 route obligations, then archived 62,013 validated candidate records (61,975 creates and 38 updates) into the canonical registry.
- High-cardinality human catalogs now keep the database overview readable and deterministically paginate Variable and Construct layers at 100 records per page, while retaining complete canonical JSONL records for agents.
- Catalog relationship traversal now precomputes each source's relevant entity set once, reducing a full 207-page consistency check from minutes to seconds at UNdata scale.
- The Execute Skill and engineering contract now specify the atomic batch path for large bounded databases; single-item update commands remain available for diagnosis and repair.
- The UNdata curator deletes rebuildable candidate and execution-batch intermediates after successful staging and execution, while preserving the sealed staging package, evidence snapshot, ledgers, and archive receipt.

### Boundary clarification

- “Complete” means complete for the fingerprint-locked, dated source-exposed metadata boundary: all 36 official UNdata datamarts were routed and enumerated without sampling. GRDR mirrored zero observation rows, records failed/degraded observation endpoints explicitly, and does not claim that UNdata supersedes each contributing provider's primary methodology or releases.
- The earlier `deep_map_projects/undata` project remains as an auditable historical partial run; it is not the completed production project and was not rewritten to manufacture progress.

## [3.0.0] - 2026-08-20

### Added

- Three independent database factory Skills: `$grdr-plan-database-deep-map`, `$grdr-execute-database-deep-map`, and `$grdr-archive-database-deep-map`, each with a single responsibility and explicit handoff artifact.
- A schema-3 pipeline contract that binds the Plan → Execute → Archive sequence, step isolation, staging-before-archive, canonical-write ownership, and fingerprinted handoffs.
- Project-local execution staging with schema-validated JSON/JSONL batches, per-record create/update/unchanged decisions, canonical base fingerprints, prospective merged-registry validation, atomic rejection rollback, and `stage-database-deep-map-records`.
- A sealed archive package and immutable archive receipt, with schemas for both artifacts and a staging-manifest schema.
- `audit-database-deep-map-execution`, `prepare-database-deep-map-archive`, `audit-database-deep-map-archive`, `database-deep-map-archive-status`, and `archive-database-deep-map` operations.
- Optimistic canonical conflict detection and a transactional archival path that rolls back affected registry collections, catalog output, project state, manifest, and receipt if any post-write validation fails.
- Regression coverage proving that Step 2 leaves canonical registry bytes unchanged, Step 3 requires the fingerprint chain, a valid receipt is required for completion, and repeated archival is idempotent.

### Changed

- The former monolithic `$grdr-deep-map-database` Skill is replaced by the three-step factory in both the repository and installed Codex Skills. Git history retains the old Skill and all earlier releases.
- `$grdr` now acts as the factory controller: it resolves Source identity, dispatches the three database Skills, and preserves research matching as a downstream function.
- Execution no longer writes canonical records before completion. Candidate Institution, Source, Dataset, recursive DataStructure, 5A DataElement, 5B Variable, Construct, Resource, SemanticNode, and Relationship records remain staged until Archive promotes them.
- Database completion now requires both `execution_ready_for_archive` and a currently valid archive receipt; a fully closed Step 2 project is only ready for archival.
- UNdata was migrated without losing or exaggerating progress: 36 datamarts, 216 required stages, 19.44% mapped, 0.93% strictly closed, 108 graph products, and 727 route obligations remain intact in an open Step 2 project.

### Boundary clarification

- Step isolation is a hard GRDR engineering rule. External paid, restricted, changing, deleted, undocumented, or genuinely non-enumerable content still limits the truthful upstream claim, but cannot justify silent drift, skipped obligations, direct canonical writes, or false completion.

## [2.0.0] - 2026-08-20

### Added

- A hard execution contract for database deep maps: mandatory unknown-database diagnosis, immutable plan/scope/work-unit locks, deterministic dependency-aware queues, persisted checkpoint recovery, silent-drift rejection, evidence-only completion, and explicit external-blocker transparency.
- Two machine-audited graph trunks and one bridge for every work unit: the source-native structural spine, multi-parent scientific-semantic spine, and Variable-to-Construct bridge.
- `SemanticNode` as a first-class canonical registry entity for disciplines, fields, research objects, systems, phenomena, processes, states, populations, observation/analysis units, applications, and methods, including multi-parent and external-classification mappings.
- `record-database-deep-map-spine`, a strict update operation that verifies prerequisite stages, canonical ownership, allowed node types, relationship endpoints, roots, leaves, connectedness, denominators, canonical verification counts, checkpoints, checksums, and topology fingerprints.
- Structure-native `DataStructure` fields for family, native type/path, hierarchy level, grain, ordering, key elements, child structures, semantic links, and lineage.
- A dedicated engineering contract, dual-spine completion rules, spine-update example, human-readable catalog output, semantic-node search/get commands, and regression tests for lock drift, deterministic recovery, dependency-valid scheduling, and premature spine rejection.

### Changed

- Database deep mapping is no longer considered complete when six entity inventories and route checks alone close; all three graph products must also be verified or evidenced not applicable.
- Route modules now declare independent `module_kinds`, separating structural templates, generation-process templates, disciplinary semantic extensions, access/lifecycle/governance/provenance sidecars, technical recovery, and open-world fallback instead of presenting a flat mixed taxonomy.
- The core route contract now has 75 facets, including execution-lock, resume-integrity, structural-spine, disciplinary-spine, and variable-bridge obligations. The migrated UNdata project therefore exposes 727 required checks and 108 required graph products while preserving its honest 42/216 mapped-stage and 2/216 strictly closed-stage progress.
- State-file replacement is atomic, rejected stage/check/spine updates roll back, and graph tasks are withheld from the queue until their content-stage prerequisites are mapped.

### Boundary clarification

- The engineering guarantee concerns GRDR-controlled execution and validation. It does not promise that an upstream owner will expose paid, restricted, deleted, changing, undocumented, or genuinely non-enumerable content; those conditions remain explicit blockers or bounded completion claims and can never be converted into false completeness.

## [1.2.0] - 2026-08-19

### Added

- An open-world preflight planner that diagnoses database identity, provenance, production process, structure, modality, lifecycle, versioning, access, sensitivity, scale, metadata maturity, language, boundary, denominator, authorization, and constraints before execution.
- A machine-readable registry of 29 composable database-route modules with 70 mandatory facets, universal obligations, route fallbacks, official-standard links where applicable, and an explicit unknown/custom extension route.
- Specialized contracts for catalogs, files, tables, APIs, SDMX cubes, surveys, administrative records, geospatial data, arrays, streams, biomedical and clinical systems, graphs, corpora, experiments, simulations, physical collections, qualitative archives, scholarly communication, digital platforms, ML assets, software workflows, restricted access, secondary provenance, federations, and legacy/proprietary systems.
- Five Agent commands for route discovery, plan generation and audit, legacy-project upgrade, route-check recording, and named-human database gate decisions.
- `checks.jsonl` route-obligation ledgers, typed blocker recovery semantics, current-route contract auditing, and completion gates that require both canonical object stages and database-shape-specific checks.
- Regression intakes and tests spanning a restricted federated clinical system, rolling sensor/geospatial/array data, a multilingual scholarly graph/corpus/model system, and an unresolved legacy archive.
- Skill references for the diagnostic matrix, route contracts, lifecycle boundaries, exception recovery, and check updates.

### Changed

- `$grdr-deep-map-database` now diagnoses and plans before execution instead of assuming a finite database taxonomy or relying on a manually chosen route list.
- Project and work-unit schemas now persist diagnostic plans, content modalities, lifecycle and versioning semantics, sensitivity, open route identifiers, rolling/bounded scopes, and `needs_human_review` state.
- Completion now rejects unresolved critical dimensions, stale or incomplete route plans, missing or altered route facets, Agent-unresolved human gates, and passed unit checks whose content stage is not mapped.
- UNdata was migrated without changing its honest content-stage progress: 36 work units, 216 stages, 19.44% mapped, and 0.93% strictly complete. The migration additionally exposes 617 required route checks, with one pre-existing boundary/denominator check closed and six route checks inheriting the two documented blocked Access stages.

### Safety and recovery

- Sensitive, controlled, or question-bounded operations generate explicit human gates; Agents may prepare evidence but cannot self-approve them.
- Dynamic, rolling, federated, non-enumerable, large-scale, inaccessible, schema-drifting, multilingual, proprietary, and semantically ambiguous sources now have explicit continuation and recovery rules rather than being silently skipped or forced into a familiar type.
- Strict planners and validators now fail with an actionable dependency error when `jsonschema` is unavailable; `requirements-validation.txt` and local virtual-environment instructions make the validation path reproducible.

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
