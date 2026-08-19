# Database Archetypes and Route Selection

Keep the six GRDR stages fixed. Select one or more route modules according to the actual storage structure and data-generating process.

| Archetype | Common domains | Structure to recover | Elements and variables that matter | Route |
|---|---|---|---|---|
| Hierarchical catalog | all disciplines, repositories | catalog → collection → dataset → version | catalog identifiers, producer, coverage, version | `catalog` |
| Statistical cube | official statistics, economics, demography | dataflow/DSD or cube dimensions | measure, dimensions, codelists, flags, unit, multiplier | `sdmx_cube` |
| Relational/table collection | administration, business, public data | database/schema/table/view/keys | columns, types, PK/FK, derived fields, row grain | `table_schema` |
| JSON/XML API | cross-domain services | endpoints, object schemas, pagination | properties, enums, IDs, nested arrays, query semantics | `api_schema` |
| Survey/questionnaire/microdata | social science, health, education | study → wave → instrument → section → item | questions, response codes, weights, strata, PSU, derived scales | `survey_instrument` |
| Administrative/event system | government, clinical, firms | source system → event/table → linkage | event time, entity IDs, codes, eligibility, revisions | `administrative_provenance` |
| Geospatial vector/raster | geography, earth/environment | collection → layer/tile → CRS/grid | geometry, band, CRS, resolution, mask, quality | `geospatial` |
| Scientific array/time series | climate, ocean, physics, engineering | collection → file/group → dimension/coordinate | variables, dimensions, calibration, uncertainty, QC | `scientific_array` |
| Biomedical/genomic | medicine, biology, omics | study → subject/sample → assay/sequence/structure | specimen, assay, feature, ontology, genome build, batch, consent | `biomedical` |
| Knowledge graph | scholarly, biomedical, semantic systems | graph → class/property → edge pattern | identifiers, predicates, ontology mappings, snapshots | `knowledge_graph` |
| Document/media corpus | humanities, communication, AI | corpus → item → segment/annotation | text fields, media metadata, annotations, labels, rights | `corpus_multimodal` |
| Secure/restricted microdata | census, clinical, commercial | catalog plus controlled environment | disclosure controls, application, linkage rules, permitted outputs | `restricted_access` |

## Primary and secondary data

Classify origin at both Source and work-unit levels.

- `primary`: the source directly operates the instrument, experiment, sensor, transaction, clinical process, or observation program.
- `secondary`: the source republishes, mirrors, harmonizes, models, aggregates, or derives data produced elsewhere.
- `hybrid`: the boundary contains both.

For secondary data, trace the original producer, upstream dataset/version, transformation or harmonization, revision behavior, and whether the source is an official harmonizer, curated repository, mirror, or derivative aggregator. Do not transfer authority or methodology claims from the aggregator to the original producer or vice versa.

## Discipline overlays

- Social and economic data: sampling, weights, population universe, waves, classifications, deflators, seasonal adjustment, and country comparability.
- Health and clinical data: patient/event grain, coding systems, cohort inclusion, consent, privacy, missingness, and clinical versus modeled values.
- Life science data: organism, specimen, assay, feature identifiers, ontology, reference build, batch, and processing pipeline.
- Earth and environmental data: CRS, grid, spatial/temporal resolution, sensor/platform, calibration, cloud/quality masks, and reprocessing vintage.
- Physical and engineering data: instrument/run/event hierarchy, calibration, uncertainty, units, simulation versus observation, and quality flags.
- Humanities and text/media data: item provenance, transcription/OCR, language, segmentation, annotation protocol, rights, and representativeness.
- Business and finance data: entity identity, transaction grain, corporate actions, survivorship, vendor derivations, revisions, currency, and licensing.

An interdisciplinary database may use several overlays. Record them per work unit rather than forcing one portal-wide assumption.
