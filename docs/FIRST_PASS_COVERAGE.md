# First-Pass Coverage Plan

The first pass aims for approximately 100 high-value sources to test the ontology across domains. The numbers below are balancing heuristics, not quotas or collection limits. Sources can belong to multiple tracks.

## Coverage tracks

| Track | Initial emphasis |
|---|---|
| Cross-domain and official statistics | Global, regional, national, and subnational statistical systems |
| Earth, climate, ocean, and space | Observations, reanalysis, remote sensing, models, and planetary data |
| Biology and biomedicine | Sequences, structures, omics, organisms, clinical research, and public health |
| Physics and chemistry | Experiments, observatories, particle data, materials, and chemical references |
| Engineering and manufacturing | Materials, standards, infrastructure, energy systems, and industrial measurements |
| Computer and information science | Benchmarks, software, models, networks, security, and computational traces |
| Agriculture, food, and environment | Production, land, biodiversity, forestry, fisheries, pollution, and ecosystems |
| Social science, economics, and policy | Aggregate statistics, surveys, microdata, administration, markets, institutions, and conflict |
| Humanities and cultural heritage | Text corpora, archives, language, archaeology, art, media, and digitized collections |
| Scholarly communication and innovation | Publications, citations, grants, patents, researchers, institutions, and research infrastructure |
| General-purpose repositories | Cross-domain repositories with persistent identifiers and documented stewardship |
| Restricted and commercial sources | High-value sources whose access constraints must be represented accurately |

## Diversity requirements

The pass is incomplete unless it includes meaningful variation in:

- original producers, official harmonizers, repositories, and derivative aggregators;
- global, regional, national, subnational, site, and non-geographic coverage;
- aggregate, micro, event, network, sequence, image, sensor, document, and grid-level observations;
- objective, subjective, administrative, experimental, modeled, and proxy measurements;
- open, registration-based, application-based, secure, and commercial access;
- English and non-English systems;
- current observations, historical archives, forecasts, and revision vintages.

## Work packages

### WP1 — Verify bootstrap seeds

For each bootstrap nomination:

1. confirm canonical identity and maintainer;
2. locate mandate, catalog, methodology, access, API, and license evidence;
3. distinguish source-wide claims from dataset-specific claims;
4. identify major contained datasets;
5. set an evidence-based review interval.

### WP2 — Expand the cross-disciplinary source registry

Build the first approximately 100-source pass across every coverage track. Treat 100 as workload planning, not a completion threshold. Include non-English, restricted, commercial, and non-tabular sources rather than collecting only easy open-data portals.

### WP3 — Add dataset depth

Create dataset records for at least one canonical dataset within each verified source. Capture version, coverage, observation unit, methodology, access resources, citation, and provenance.

Use `$grdr-source-profiler` and `docs/SOURCE_PROFILING_PROTOCOL.md` to declare whether each pass is representative, question-driven, priority-catalog, catalog-level, or exhaustive. A single six-layer chain tests the ontology but does not establish catalog completeness.

### WP4 — Build access adapters and storage decisions

For representative sources, implement and test APIs, bulk-download adapters, catalog harvesters, application instructions, or secure-access pointers. Assign `local_snapshot`, `federated_access`, or `controlled_access_pointer` deliberately.

### WP5 — Add monitoring and version control

Track upstream releases, revisions, checksums, URL migrations, API changes, license changes, replacements, and deprecations. Preserve historical provenance.

### WP6 — Add variable and construct depth

For representative scientific questions, map variables to constructs and label direct measures, subjective measures, constructed indices, modeled estimates, forecasts, and proxies.

### WP7 — Exercise secondary matching workflows

Use benchmark questions from every coverage track to test search, source fit, joinability, data-gap diagnosis, and supplementation recommendations.

### WP8 — Trigger snowball expansion

Expand from verified institutions, upstream producers, contained catalogs, dataset citations, data papers, and unresolved benchmark gaps.

## Exit criteria

The first pass ends when the ontology and agent contract have been tested across all tracks and major source classes. It does not end merely because the registry reaches 100 records.
