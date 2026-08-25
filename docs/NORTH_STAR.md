# GRDR North Star

## Final positioning

GRDR is an AI-agent-native, all-discipline infrastructure for global data-source registration, discovery, assessment, connection, and research design.

It combines:

- a versioned Data Source Registry;
- a Dataset Knowledge Graph;
- Agent Research Data Infrastructure;
- question-to-data matching and data-gap diagnosis;
- literature-grounded, multi-level research-indicator construction;
- continuous, evidence-backed snowball expansion.

GRDR is not primarily a website and never combines every upstream source into one monolithic warehouse. It keeps a broad global registry and knowledge graph, while every database selected for full deep reading is stored as its own distributed, versioned snapshot. Every completed snapshot preserves complete knowledge within its locked Plan boundary, proves tested online callability for every registered Variable, and independently declares whether observations are fully mirrored, partition-mirrored, or not mirrored, plus the exact locations that hold any copied bytes.

## Core capabilities

GRDR must enable an AI agent to:

1. turn a scientific question into an exploratory indicator scaffold or, when a substantial literature corpus is supplied, an evidence-linked multi-level indicator system;
2. translate approved leaf indicators into variables, populations, units, and data dimensions;
3. discover and assess the most suitable authoritative data-source combination;
4. determine whether sources can be connected across time, space, observational levels, definitions, and identifiers;
5. diagnose missing variables, measurements, mechanisms, and design dimensions;
6. recommend additional objective, subjective, administrative, experimental, observational, or multimodal data;
7. continuously extend the registry through verifiable snowball discovery.

Indicator construction, matching, and research-design reasoning are central capabilities, but they operate with a broad and well-curated source registry. They do not replace registry expansion.

## Current phase

The current phase is foundation and first-pass source construction:

1. stabilize the project charter, ontology, schemas, evidence model, evaluation dimensions, and Agent interfaces;
2. build the first approximately 100-source cross-disciplinary seed registry;
3. verify source authority, scope, access, licensing, methodology, and provenance;
4. test representative source, dataset, variable, and construct chains;
5. create local structured indexes for fast Agent retrieval.

The first 100 sources are a workload target, not a collection ceiling.

## Expansion sequence

### Round 1 — Cross-disciplinary skeleton

Register approximately 100 core sources spanning every major discipline and source class.

### Round 2 — Institution snowball

Follow maintainers, upstream producers, related catalogs, mirrors, official derivatives, API directories, and methodology references.

### Round 3 — Discipline coverage

Audit each discipline for aggregate and microdata, longitudinal and spatial coverage, experiments, surveys, standards, knowledge bases, and objective and subjective measurements.

### Round 4 — Scientific-question expansion

Use real questions to expose missing variables and data dimensions, then add the corresponding sources.

### Continuous expansion

Track upstream releases, new repositories, citations, data papers, standards, expert nominations, and unresolved Agent search failures.

## Authority principle

Authority is domain-specific. Prefer original legally mandated producers, internationally recognized domain authorities, official harmonizers, or scientifically governed curators. Retain academically valuable derivative and commercial sources when appropriate, but label their provenance and role accurately.

Never collapse source authority and task-specific fitness into one opaque score.

## Long-term evolution

As the registry expands, GRDR adds more independently versioned source snapshots without copying the shared Core into those repositories. The central registry remains the unified Agent entry point; source repositories and snapshot artifacts provide the durable database-specific storage layer. Knowledge depth must never be weakened merely because observations are large, and raw observations must never be duplicated inside the knowledge artifact.

## Production and use planes

Plan → Execute → Storage is the three-step database production factory. It ends with a verified, callable source snapshot; it does not itself answer research queries.

The independent GRDR Agent Runtime is the use plane. The `grdr-resolve-research-semantics` Skill connects research-side indicators to the same persisted B spine, traverses B→A relationships, evaluates variable fit, and supplies an auditable selected path. Runtime then searches central and distributed indexes, resolves the selected Variable through source Runtime 2.0, and applies an explicit `latest`, `reproducible`, or `offline` route policy. It can use an authoritative official API, official bulk download, official browser workflow, verified GRDR Release snapshot, an optional Release-materialized local cache, or mounted object-store mirror, records every attempted route, and seals query-scoped data under the research project when requested. Storage is responsible for proving complete online Variable coverage as well as packaging the knowledge and independently selected observation replicas; local and research-project caches are derived use-plane artifacts.
