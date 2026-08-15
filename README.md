# Global Research Data Registry (GRDR)

GRDR is AI-agent-native, all-discipline infrastructure for global data-source registration, discovery, assessment, connection, and research design.

**Current status:** foundation and first-pass source construction. The repository provides the evidence model, ontology, schemas, initial registry, and Agent commands. The immediate goal is a verified first-round registry of approximately 100 cross-disciplinary sources, followed by multi-round snowball expansion. See [North Star](docs/NORTH_STAR.md).

It is not primarily a website and does not initially copy every upstream dataset. It combines:

- a versioned data-source registry;
- a dataset and measurement knowledge graph;
- task-specific source-fit and data-gap assessment;
- stable interfaces for Codex, Claude, and other agents;
- optional adapters for representative sources with stable programmatic access.

Research-question matching, source combination, and data-gap diagnosis are central Agent capabilities built on top of the registry. Local snapshots and federated access are later extensions where licensing, privacy, cost, and scale permit.

## Core warehouse questions

GRDR should help an agent determine:

1. Which authoritative and academically valuable data sources exist in each discipline?
2. Who produces and maintains them, what do they contain, and how are they related?
3. How can they be accessed, queried, downloaded, licensed, versioned, and refreshed?
4. Which data can be stored locally, which should remain federated, and which require controlled access?
5. Where are the warehouse’s disciplinary, geographic, temporal, modality, and access gaps?
6. For a specific scientific question, which warehouse contents are suitable and what additional data are needed?

## Design principles

- **Task fit is separate from source authority.** An authoritative source may still be unsuitable for a particular question.
- **Claims require evidence.** Authority, coverage, access, and methodological claims must point to verifiable evidence.
- **Unknown is a valid value.** The registry must not turn unverified assumptions into facts.
- **Metadata before mirroring.** GRDR catalogs and connects data before considering storage or redistribution.
- **Dataset and variable granularity matter.** A source-level URL list is insufficient for research design.
- **Provenance is preserved.** Original production, harmonization, publication, and mirroring are distinct relationships.
- **Expansion has no fixed ceiling.** Initial seeds support iterative, audited snowball expansion.
- **Agent-first, human-auditable.** Machine interfaces are primary, while every recommendation remains inspectable.

## Initial repository layout

```text
grdr/
├── docs/
│   ├── PROJECT_CHARTER.md
│   ├── ONTOLOGY.md
│   ├── ASSESSMENT_FRAMEWORK.md
│   ├── AGENT_PROTOCOL.md
│   └── EXPANSION_PROTOCOL.md
├── examples/
│   └── population_emissions_request.json
├── registry/
│   ├── institutions.jsonl
│   ├── sources.jsonl
│   ├── datasets.jsonl
│   ├── resources.jsonl
│   ├── constructs.jsonl
│   ├── variables.jsonl
│   ├── adapters.jsonl
│   ├── storage.jsonl
│   ├── monitors.jsonl
│   └── relationships.jsonl
├── schemas/
│   ├── institution.schema.json
│   ├── source.schema.json
│   ├── dataset.schema.json
│   ├── resource.schema.json
│   ├── variable.schema.json
│   ├── construct.schema.json
│   ├── adapter.schema.json
│   ├── storage.schema.json
│   ├── monitor.schema.json
│   ├── relationship.schema.json
│   └── research_request.schema.json
├── scripts/
│   ├── grdr.py
│   └── validate_registry.py
└── tests/
    └── test_cli.py
```

## Current phase

Version `0.1.0` defines the project charter, registry ontology, evidence rules, assessment framework, Agent contract, and seed-expansion process. It also includes the first end-to-end source–dataset–resource–variable–construct chain and a registry-coverage diagnostic for structured research requests. Seed records are deliberately small and evidence-conscious; the target of roughly 100 high-value sources is a first coverage pass, not a collection limit.

Every completed development batch increments `VERSION`, updates `CHANGELOG.md`, passes validation, and is published to GitHub according to [the release process](docs/RELEASE_PROCESS.md).

## Local agent access

The foundation release includes a dependency-free JSON CLI so an agent can inspect the registry immediately:

```bash
python3 scripts/grdr.py stats
python3 scripts/grdr.py search-sources --query climate
python3 scripts/grdr.py search-sources --discipline medicine --verification unverified
python3 scripts/grdr.py search-datasets --topic population
python3 scripts/grdr.py search-variables --construct population
python3 scripts/grdr.py get-source grdr:source:undata
python3 scripts/grdr.py get-dataset grdr:dataset:world-development-indicators
python3 scripts/grdr.py trace-provenance grdr:variable:wdi-sp-pop-totl
python3 scripts/grdr.py list-adapters --status operational
python3 scripts/grdr.py list-storage --mode federated_access
python3 scripts/grdr.py list-monitors --status passing
python3 scripts/grdr.py diagnose-coverage examples/population_emissions_request.json
python3 scripts/validate_registry.py
python3 scripts/check_release.py
python3 -m unittest discover -s tests
```

All command output is JSON except validation diagnostics. Search results always include verification status; unverified bootstrap nominations are never presented as verified sources.

## Non-goals for the foundation phase

- copying or redistributing all underlying datasets;
- treating institutional prestige as a universal authority ranking;
- generating empirical claims without inspecting dataset-level methodology;
- promising automatic access where registration, payment, ethics review, or data-use agreements are required;
- presenting proxy variables as direct measurements.
