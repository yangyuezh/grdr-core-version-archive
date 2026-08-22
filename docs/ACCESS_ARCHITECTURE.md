# GRDR Access and Distributed Storage Architecture

This document separates broad Source registration from the full three-step database factory. The Data Source Registry may register sources without copying them; a database selected for Plan → Execute → Storage must finish as a complete distributed snapshot.

GRDR separates its registered knowledge from the optional mechanisms that retrieve or store upstream data. The GRDR Skill operates both when appropriate.

## Registered knowledge and access layers

The architecture contains seven layers:

1. **Institution registry** — who produces, governs, funds, or maintains data.
2. **Source registry** — databases, portals, repositories, programs, and collections.
3. **Dataset catalog** — versioned collections, methodology, coverage, and citations.
4. **Access catalog** — APIs, bulk files, query systems, application routes, secure enclaves, and commercial access.
5. **Data-structure, variable, and semantic index** — source-native dimensions, measures, attributes, fields, indicators, constructs, units, definitions, classifications, and join keys.
6. **Adapters and storage** — retrieval code plus local snapshots, caches, indexes, or federated queries where permitted.
7. **Monitoring and provenance** — revisions, upstream producers, transformations, migrations, licenses, and historical versions.

The repository implements layers 1–5 globally and the first source-scoped implementation of layers 6–7 through the Storage Skill.

## Skill layer

The Skill tells an AI agent how to operate GRDR. Its core operations are:

- inspect registry coverage;
- discover and nominate new sources;
- verify and promote records;
- register datasets, resources, data elements, variables, and relationships;
- build or run access adapters;
- ingest or refresh permitted data;
- detect changes and stale records;
- query the registry and permitted access extensions;
- match a research question to available data as a downstream capability.

## Storage policy

The broad registry retains three access descriptions:

- `local_snapshot`: store a versioned copy when licensing, privacy, cost, and scale permit;
- `federated_access`: retain metadata and query the authoritative upstream system when copying is unsuitable;
- `controlled_access_pointer`: retain metadata, application instructions, and governance constraints without attempting unauthorized retrieval.

These modes do not define completion for the three-step factory. A source that is only federated or externally controlled may remain registered, but it is not eligible to receive a complete Storage receipt. The factory's selected databases require a full local snapshot, complete Release assets, and the matching Elements copy.

## Distributed snapshot topology

- GRDR Core stores shared schemas, Skills, programs, global search, and one latest-snapshot card per stored Source.
- Each stored Source has one private Git repository containing small reviewable configuration and manifests.
- Each snapshot has one GitHub Release containing complete knowledge, Agent index, and observations.
- Each snapshot has one Elements directory containing the same logical files in expanded form.

## Canonical local locations

- GRDR project: `/Users/jasper/Documents/codex/grdr`
- Installed Skill: `/Users/jasper/.codex/skills/grdr`

The Skill may use the `GRDR_ROOT` environment variable to override the GRDR project path.
