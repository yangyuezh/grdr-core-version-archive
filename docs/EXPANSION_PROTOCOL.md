# Expansion Protocol

GRDR has no fixed source-count ceiling. Expansion proceeds through repeated, evidence-backed passes.

## Pass 1: Cross-domain skeleton

Start with approximately 100 high-value sources distributed across disciplines, source classes, regions, modalities, and access models. This is a coverage target for the first pass, not a final scope.

The first pass tests:

- ontology adequacy;
- authority and fit distinctions;
- evidence capture;
- duplicate detection;
- agent retrieval;
- cross-domain classification;
- source-to-dataset decomposition.

## Pass 2: Institution snowball

For each verified seed, discover:

- other data programs maintained by the institution;
- upstream primary producers;
- official harmonized derivatives;
- linked repositories and catalogs;
- retired or superseded systems;
- methodological and standards bodies.

## Pass 3: Discipline coverage audit

For each discipline and subdiscipline, evaluate whether GRDR covers:

- canonical sources;
- primary observations;
- aggregate and microdata;
- longitudinal and cross-sectional data;
- spatial, temporal, experimental, and multimodal data;
- subjective and objective measurements;
- standards, benchmarks, reference databases, and negative results where applicable;
- regional and non-English sources.

## Pass 4: Scientific-question stress testing

Run a diverse benchmark set of real scientific questions. Each unresolved construct, observation level, geography, period, or modality creates a targeted discovery task.

## Continuous expansion

New candidates are discovered through:

- official institutional catalogs;
- source documentation and provenance statements;
- dataset citations and data papers;
- repository registries;
- standards organizations;
- scholarly reviews;
- domain-expert nominations;
- agent failure and data-gap logs.

## Candidate lifecycle

```text
nominated
  → identity_checked
  → partially_verified
  → verified
  → monitored
  → stale / conflicted / deprecated / unavailable
```

Automation may perform nomination, deduplication, link checks, metadata extraction, and change detection. Promotion to `verified` requires the evidence checks defined for the source class.

## Deduplication

Duplicate detection considers:

- canonical domain and redirect chain;
- institution and source identity;
- persistent identifiers;
- official renaming or migration;
- shared dataset inventories;
- mirror and derivative relationships.

Duplicates should usually become explicit relationships rather than destructive merges when provenance differs.

## Coverage metrics

Track multiple coverage dimensions instead of a single source count:

- disciplines and subdisciplines;
- countries, territories, oceans, and extra-terrestrial domains where applicable;
- historical and current periods;
- observation units and scales;
- modalities and measurement types;
- source authority roles;
- open, restricted, application-based, and commercial access;
- API, bulk-download, query, and physical-access modes;
- verified versus nominated records;
- dataset- and variable-level depth;
- unresolved scientific-question gaps.

## Update monitoring

Each source has a review interval based on volatility and importance. Monitoring checks:

- URL and redirect changes;
- source retirement or replacement;
- documentation changes;
- access and license changes;
- API and format changes;
- latest release and revision policy;
- institution or mandate changes.

Historical facts must not be overwritten silently. Material changes create a new record revision and, where appropriate, typed `supersedes` or `replaced_by` relationships.

