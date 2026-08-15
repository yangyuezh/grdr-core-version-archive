---
name: grdr
description: Operate and expand GRDR, an AI-agent-native, all-discipline global Data Source Registry, Dataset Knowledge Graph, and Agent Research Data Infrastructure. Use when Codex needs to discover, verify, register, classify, assess, connect, cite, or update authoritative and academically valuable databases; audit disciplinary coverage; trace provenance, methodology, access, or licensing; or map a scientific question to compatible data sources, variables, and unresolved data gaps.
---

# Global Research Data Registry

## Preserve the project definition

Treat GRDR as:

- a versioned Data Source Registry;
- a Dataset Knowledge Graph;
- Agent Research Data Infrastructure;
- a source-matching and data-gap reasoning system;
- a continuously expanding cross-disciplinary knowledge base.

Do not redefine the current project as a physical warehouse that copies every upstream dataset. Add adapters or snapshots only as representative or later-phase extensions.

## Follow the current phase

Prioritize:

1. stabilizing schemas, evidence standards, evaluation dimensions, and Agent interfaces;
2. constructing the first approximately 100-source cross-disciplinary registry;
3. verifying source authority, scope, access, methodology, license, and provenance;
4. deepening representative sources to dataset and variable level;
5. preparing fast local indexes for Agent retrieval.

Treat 100 as a first-round workload target, never a collection limit. Continue later through institution, discipline, and scientific-question snowball expansion.

## Locate the project

Use `${GRDR_ROOT}` when set. Otherwise use:

```text
/Users/jasper/Documents/codex/grdr
```

Before modifying records, read `docs/NORTH_STAR.md`, the relevant schema, and [references/curation-standard.md](references/curation-standard.md).

## Search before expanding

Run the bundled wrapper:

```bash
python3 scripts/grdr.py stats
python3 scripts/grdr.py search-sources --query climate
python3 scripts/grdr.py search-datasets --topic population
python3 scripts/grdr.py search-variables --construct population
python3 scripts/grdr.py trace-provenance grdr:variable:wdi-sp-pop-totl
```

Treat unverified records as candidates. Treat an empty result as `not_found_in_registry_snapshot`, not proof that no external source exists.

## Discover and curate sources

Read [references/domain-coverage.md](references/domain-coverage.md). Search official catalogs, primary producers, disciplinary repositories, standards, data papers, upstream provenance, citations, and non-English systems.

For each candidate:

1. Resolve canonical identity and maintainer.
2. Classify the authority and provenance role.
3. Collect evidence for scope, methods, coverage, access, license, versioning, and citation.
4. Register only defensible facts; leave unresolved fields unknown.
5. Add explicit provenance, containment, derivation, mirror, and replacement relationships.
6. Validate before promoting verification status.

Separate institutional authority from task-specific fitness. Do not rank every field by one universal prestige score.

## Match scientific questions

When the user provides a scientific question:

1. identify constructs, outcomes, exposures, mechanisms, confounders, moderators, population, unit, time, and geography;
2. create a data-requirement matrix;
3. retrieve candidate sources, datasets, and variables;
4. assess construct, population, time, space, granularity, access, and joinability fit;
5. distinguish direct measures, constructed measures, modeled estimates, forecasts, and proxies;
6. diagnose missing objective, subjective, administrative, experimental, observational, or multimodal data;
7. recommend additional sources without claiming unfound data already exists.

Use:

```bash
python3 scripts/grdr.py diagnose-coverage /absolute/path/to/request.json
```

Matching is a core value of GRDR, but it depends on continued registry breadth and depth.

## Use access extensions carefully

Read [references/access-architecture.md](references/access-architecture.md) only when adding an API adapter, federated query, or lawful snapshot. Keep source discovery and metadata separate from data retrieval.

Never bypass authentication, payment, consent, ethics review, data-use agreements, rate limits, or access controls.

## Release every completed batch

Read `docs/RELEASE_PROCESS.md`. For each completed development batch:

1. bump `VERSION`;
2. update `CHANGELOG.md`;
3. validate the registry and tests;
4. commit only GRDR files;
5. tag the version;
6. push the branch and tag to GitHub;
7. report the version and GitHub URL.

## Validate changes

```bash
cd "${GRDR_ROOT:-/Users/jasper/Documents/codex/grdr}"
python3 scripts/validate_registry.py
python3 -m unittest discover -s tests
```

Report added coverage, verification levels, unresolved evidence, matching limitations, version, and release status.
