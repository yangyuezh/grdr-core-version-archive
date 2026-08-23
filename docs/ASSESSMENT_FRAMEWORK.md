# Assessment Framework

GRDR never treats authority and task fitness as the same score.

## A. Intrinsic source assessment

These dimensions describe a source independently of a particular research question.

### A1. Mandate and domain authority

Questions:

- Does the institution have a statutory, treaty-based, scientific-curatorial, or otherwise documented mandate?
- Is it the original producer, an official harmonizer, a repository, or a downstream aggregator?
- Does the mandate cover the specific domain represented by the dataset?

This dimension is categorical and evidence-backed. It is not a prestige ranking.

Initial authority roles:

- `statutory_primary_producer`
- `intergovernmental_domain_authority`
- `official_harmonizer`
- `scientific_curator_or_consortium`
- `research_institution_producer`
- `commercial_producer`
- `repository_or_archive`
- `derivative_aggregator`
- `community_maintained`
- `unknown`

### A2. Originality and provenance clarity

Assess whether the source documents original production, transformations, harmonization, estimation, and upstream dependencies.

### A3. Methodological transparency

Assess definitions, collection design, sampling, instruments, models, validation, revision policy, and known limitations.

### A4. Quality assurance

Assess documented validation, error correction, audit procedures, peer review, national or international statistical standards, and release controls.

### A5. Comparability

Assess standardization across entities, places, populations, instruments, and time. Comparability is never inferred from identical column labels alone.

### A6. Coverage and completeness

Assess population, temporal, spatial, topical, and modality coverage together with missingness and reporting bias.

### A7. Timeliness and revision practice

Assess update frequency, publication lag, revision history, vintages, and whether historical releases remain accessible.

### A8. Reproducibility and stability

Assess persistent identifiers, versioning, stable downloads, machine access, documentation, and reproducible query behavior.

### A9. Scholarly and operational adoption

Assess documented use in research, standards, official reporting, benchmarking, or operational decision-making. Popularity alone is not validation.

### A10. Access and reuse

Assess cost, registration, application, ethics review, data-use agreements, licensing, redistribution, computational access, and rate limits.

## B. Task-specific fitness assessment

These dimensions are evaluated for each research request.

- `construct_fit`: Does the variable measure the intended concept?
- `population_fit`: Does the observed population match the target population?
- `unit_fit`: Does the unit of analysis match the estimand and design?
- `temporal_fit`: Do period, frequency, lag, and historical coverage fit?
- `spatial_fit`: Do geography and resolution fit?
- `granularity_fit`: Is aggregation appropriate for the inference?
- `design_fit`: Does the data support the proposed descriptive, predictive, causal, or mechanistic design?
- `joinability_fit`: Are stable identifiers and compatible definitions available?
- `coverage_fit`: Is sample size and variation sufficient in principle?
- `access_fit`: Can the authorized agent and researcher lawfully obtain and process it?
- `reproducibility_fit`: Can the analysis be repeated against a known release?
- `bias_risk`: Which selection, reporting, measurement, survivorship, or model-based biases matter?

## C. Measurement classification

Each recommended variable must be labeled as one of:

- `direct_observation`
- `self_report`
- `informant_report`
- `administrative_measure`
- `instrument_or_sensor_measure`
- `coded_or_annotated_measure`
- `constructed_index`
- `modelled_estimate`
- `forecast`
- `proxy`
- `latent_variable_estimate`
- `unknown`

Objective and subjective are recorded independently because a self-report can be the direct measurement of a subjective construct, while an administrative record can still contain systematic bias.

## D. Recommendation output

Assessments should return dimension-level judgments, supporting evidence, uncertainty, and disqualifying conditions. A composite score may be provided for ranking candidates only if:

1. all component dimensions remain visible;
2. weights are declared and task-specific;
3. unknown values do not silently become zero;
4. hard incompatibilities can override a high average score;
5. the score is not called an absolute authority score.

## E. Data-gap taxonomy

Gap diagnosis uses the following initial categories:

- missing outcome or exposure;
- missing confounder;
- missing mediator or mechanism;
- missing moderator or heterogeneity dimension;
- missing temporal depth or frequency;
- missing spatial coverage or resolution;
- missing population or unit level;
- missing subjective or objective counterpart;
- missing multimodal evidence;
- weak construct validity;
- proxy-only measurement;
- incompatible identifiers;
- incompatible definitions or denominators;
- selection or coverage bias;
- insufficient variation or statistical power;
- inaccessible or legally unusable data;
- stale or non-versioned data;
- missing policy, intervention, or event timing;
- missing validation or robustness measure.
