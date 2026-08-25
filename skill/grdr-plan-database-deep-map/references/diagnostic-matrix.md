# Open-World Database Diagnostic Matrix

The diagnostic intake is a preflight investigation, not a questionnaire filled from guesswork. Use official documentation, machine metadata, dated probes, licenses, terms, methodology, codebooks, manifests, schemas, and repository records. Mark unresolved dimensions as `unknown`; do not select a convenient answer.

## Required dimensions

| Dimension | Questions | Why it changes execution |
|---|---|---|
| Identity and authority | What is the canonical database boundary? Who produces, publishes, maintains, funds, and governs it? | Prevents mirrors, portals, datasets, and institutions from being conflated. |
| Origin and provenance | Primary, secondary, or hybrid? Original producer, official harmonizer, curated repository, mirror, aggregator, or federation? | Determines whether acquisition/process evidence or upstream transformation lineage is required. |
| Production process | Survey, census, administration, transaction, experiment, sensor, observation, collection, simulation, indexing, crawl, clinical care, qualitative research, or other? | Identifies data-generating assumptions not recoverable from file format. |
| Internal structure | Catalog, table, cube, API, questionnaire, event system, geospatial layer, array, stream, graph, corpus, specimen collection, experiment, model run, software workflow, federation, legacy system, or unknown? | Selects route contracts and work-unit boundaries. |
| Content modality | Metadata, tabular, multidimensional, time series, events, geospatial, sequence, 3D structure, graph, text, document, image, audio, video, code, model, synthetic, composite, or unknown? | Determines parsers, units, native elements, quality checks, and storage limits. |
| Lifecycle | Snapshot, versioned release, revised release, mutable, append-only, rolling window, real-time stream, deleted/ephemeral, or unknown? | Determines fingerprints, refresh rules, temporal boundaries, and whether a static denominator is meaningful. |
| Version model | Immutable release, dated snapshot, revision chain, semantic/schema version, event/processing version, per-member version, none, or unknown? | Prevents data and metadata from different vintages being combined silently. |
| Access regime | Open, API, registered, licensed, commercial, application, restricted, secure environment, physical access, or unknown? | Creates access routes and authorization gates; access never defines content depth. |
| Sensitivity and governance | Public, personal, health, genetic, financial, commercial, security, community/Indigenous governed, confidential, or unknown? | Triggers privacy, ethics, sovereignty, storage, disclosure, and output-review controls. |
| Scale and compute | Small, medium, large, very large, or unbounded stream? Can metadata be enumerated without mirroring observations? | Determines batching, partitions, manifests, checksums, probes, and safe compute strategy. |
| Metadata maturity | Machine-readable, human-documented, partial, inferred, undocumented, or unknown? | Determines whether structures can be parsed or must remain inferred and reviewable. |
| Language and encoding | Which languages, scripts, encodings, controlled vocabularies, and translations occur? | Prevents label loss, false deduplication, and unmarked translation. |
| Goal and claim | Representative, question-fit, priority subset, catalog-only, bounded partition, exhaustive snapshot, or rolling-current? | Defines what “complete” may mean and which denominator is required. |
| Work units | What stable object can be counted, ordered, partitioned, resumed, and cited? | Makes progress persistent across Agents and sessions. |
| Constraints | What access and computation are authorized? What actions are prohibited? | Prevents a route plan from silently expanding permissions. |

## Decision rule

1. Resolve critical dimensions with evidence.
2. If origin, structure, lifecycle, versioning, access, boundary, denominator, or identity rule remains unknown, retain `needs_evidence`.
3. Compose all applicable route modules; do not select a single “closest discipline.”
4. Add human gates before protected operations.
5. If no known route explains the observations, use `open_world_custom` and record the mismatch.

`examples/intakes/` contains regression fixtures for restricted federated clinical data, rolling sensor/array/geospatial data, multilingual scholarly graph/corpus/model systems, and an unresolved legacy archive.
