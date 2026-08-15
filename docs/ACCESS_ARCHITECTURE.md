# Later-Phase Access and Storage Architecture

This document describes optional later-phase access and storage extensions. It is not the current project center. The current foundation is the Data Source Registry, Dataset Knowledge Graph, and Agent Research Data Infrastructure defined in `NORTH_STAR.md`.

GRDR separates its registered knowledge from the optional mechanisms that retrieve or store upstream data. The GRDR Skill operates both when appropriate.

## Registered knowledge and access layers

The architecture contains seven layers:

1. **Institution registry** — who produces, governs, funds, or maintains data.
2. **Source registry** — databases, portals, repositories, programs, and collections.
3. **Dataset catalog** — versioned collections, methodology, coverage, and citations.
4. **Access catalog** — APIs, bulk files, query systems, application routes, secure enclaves, and commercial access.
5. **Variable and semantic index** — fields, indicators, constructs, units, definitions, classifications, and join keys.
6. **Adapters and storage** — retrieval code plus local snapshots, caches, indexes, or federated queries where permitted.
7. **Monitoring and provenance** — revisions, upstream producers, transformations, migrations, licenses, and historical versions.

The current repository implements the foundation of layers 1–5. Layers 6–7 are the next major engineering work.

## Skill layer

The Skill tells an AI agent how to operate GRDR. Its core operations are:

- inspect registry coverage;
- discover and nominate new sources;
- verify and promote records;
- register datasets, resources, variables, and relationships;
- build or run access adapters;
- ingest or refresh permitted data;
- detect changes and stale records;
- query the registry and permitted access extensions;
- match a research question to available data as a downstream capability.

## Storage policy

Use three storage modes:

- `local_snapshot`: store a versioned copy when licensing, privacy, cost, and scale permit;
- `federated_access`: retain metadata and query the authoritative upstream system when copying is unsuitable;
- `controlled_access_pointer`: retain metadata, application instructions, and governance constraints without attempting unauthorized retrieval.

GRDR must never equate “not locally copied” with “not included.” A restricted clinical cohort, commercial financial database, or physical archive can be fully registered while remaining externally controlled.

## Canonical local locations

- GRDR project: `/Users/jasper/Documents/codex/grdr`
- Installed Skill: `/Users/jasper/.codex/skills/grdr`

The Skill may use the `GRDR_ROOT` environment variable to override the GRDR project path.
