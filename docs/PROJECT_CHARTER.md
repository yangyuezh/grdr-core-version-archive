# Project Charter

## Mission

Build the most comprehensive, evidence-backed, machine-actionable global data-source registry, dataset knowledge graph, and research-data infrastructure for AI agents across all scientific and scholarly domains.

GRDR maps scientific questions to constructs and data requirements, discovers and assesses suitable source combinations, checks compatibility, diagnoses gaps, and continuously expands its evidence-backed source knowledge base.

## Primary users

The primary users are AI agents, including Codex and Claude. Researchers, data stewards, librarians, and domain experts are secondary users who audit, correct, and extend the registry.

## Scope

GRDR covers, without a fixed numerical ceiling:

- natural sciences;
- engineering and computer science;
- medicine and life sciences;
- agricultural and environmental sciences;
- social sciences, economics, and management;
- humanities and digital humanities;
- interdisciplinary and applied industrial research.

Eligible source classes include official statistics, scientific observations, administrative records, censuses, surveys, experiments, clinical data, remote sensing, sensors, business and market data, scholarly and patent metadata, knowledge graphs, archives, multimodal corpora, subjective measures, and digital trace data.

## Product definition

GRDR consists of coordinated registry, research-data infrastructure, and Skill layers:

1. **Registry:** machine-readable records for institutions, sources, datasets, resources, variables, constructs, and evidence.
2. **Knowledge graph:** typed relationships among producers, publishers, mirrors, derived datasets, measures, proxies, and joinable resources.
3. **Assessment engine:** separate evaluations for intrinsic source quality and task-specific fitness.
4. **Access and ingestion layer:** CLI, SDK, MCP operations, source-specific adapters, federated queries, and versioned local snapshots where access and licensing permit.
5. **Monitoring layer:** releases, revisions, migrations, stale records, deprecations, and provenance changes.
6. **Matching layer:** question-to-data mapping, compatibility checks, and gap diagnosis over registered sources and datasets.

Registry breadth and depth, evidence quality, and matching capability develop together. During the current first phase, foundation stability and broad source construction take precedence over large-scale data ingestion.

## Required agent behavior

An agent operating GRDR should:

1. search the local registry before repeating external discovery;
2. discover new sources when disciplinary, geographic, temporal, modality, or access coverage is missing;
3. distinguish original producers, official harmonizers, repositories, mirrors, and derivative aggregators;
4. attach suitable evidence to authority, methodology, access, license, version, and provenance claims;
5. register sources, datasets, resources, variables, versions, adapters, storage state, and relationships at the appropriate granularity;
6. use local snapshots, federated access, or controlled-access pointers according to law, licensing, privacy, scale, and cost;
7. preserve upstream vintages, retrieval dates, transformations, and historical provenance;
8. detect stale records, revisions, migrations, replacements, and access changes;
9. express uncertainty and leave unsupported fields unknown;
10. use question-to-data matching as a core Agent capability grounded in registered evidence.

When matching a scientific question, additionally distinguish constructs from measurements, evaluate task fit separately from authority, test compatibility, and label direct measures, constructed measures, proxies, estimates, forecasts, and missing coverage.

## Success criteria

GRDR succeeds when an agent can reliably discover, verify, access, and maintain research-data knowledge across disciplines. GRDR should:

- cover domain-appropriate original producers, official harmonizers, scientific curators, repositories, and academically valuable derivative sources;
- expose dataset depth rather than source-homepage links alone;
- provide lawful machine access or accurate controlled-access instructions;
- maintain adapters, versions, snapshots, provenance, licenses, and citations;
- detect changes and refresh stale records;
- remain usable from a versioned local registry when upstream services are unavailable;
- support auditable question-to-data matching over registered sources, datasets, and variables.

Coverage volume is an operational metric, not the mission. A large collection of unverified links does not count as success.

## Governance principles

- Every material metadata claim must have a verification status and evidence.
- Automated discovery may nominate records but cannot silently promote them to verified status.
- Domain expertise overrides generic institutional rankings when supported by evidence.
- Restricted, sensitive, or licensed data are described without bypassing access controls.
- Updates are additive and reviewable; removals and supersessions retain historical provenance.
- Conflicting claims coexist until adjudicated, with evidence attached to each claim.

## Versioning

Registry releases use semantic versions. Every agent response should be able to record:

- registry version or commit;
- query timestamp;
- source record version;
- upstream source verification date;
- dataset release or vintage when known.
