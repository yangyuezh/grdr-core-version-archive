# GRDR Access, State, and Distributed Storage Architecture

GRDR separates immutable execution code from mutable database knowledge and observation artifacts.

## Immutable Core

GRDR Core contains only shared Skills, schemas, route contracts, programs, empty Registry filename templates, validators, tests, and documentation. Core never stores a real Source, Dataset, Variable, source-archive card, project, adapter, or observation file.

Configure an installed clone once with `python3 scripts/configure_core.py`, or set `GRDR_ROOT` explicitly. The six Skill launchers then locate the same Core without assuming a working directory or machine-specific path.

## External mutable state

`GRDR_STATE_ROOT` identifies the mutable operational state and defaults to `~/.grdr`. It contains:

- `registry/`: canonical records and completed source-archive cards;
- `deep_map_projects/`: locked Plan and resumable Execute/Storage projects;
- `research_projects/`: indicator and semantic-resolution projects;
- `elements/`: the default expanded snapshot root when `GRDR_ELEMENTS_ROOT` is unset.

`GRDR_STATE_ROOT` must resolve outside the Core repository. Storage must leave every Core file byte-identical.

## Six content layers and access sidecars

The database content model remains:

1. Institution;
2. Source;
3. Dataset;
4. recursive DataStructure;
5. 5A DataElement and 5B Variable;
6. Construct, positioned through the multi-parent scientific-semantic spine.

Resource, Evidence, Verification, adapters, authentication, license, rate limits, and access methods are cross-cutting sidecars rather than content layers.

## Distributed snapshot topology

- One deeply stored Source owns one private source repository.
- One snapshot owns one GitHub Release containing complete knowledge, Agent Runtime, manifest, receipt, and only those observations explicitly assigned to GitHub.
- The same snapshot owns one expanded Elements directory containing complete knowledge and Agent Runtime plus only those observations explicitly assigned to Elements.
- Large observation bytes may instead live on a mounted object store or remain only at the official upstream; this replication decision does not remove the online-callability requirement.
- A location-aware manifest maps every logical file to its actual locations and SHA-256. Knowledge and Agent files must match across Release and Elements; observation parity is checked only across locations that claim a copy.
- Raw observation files are excluded from `knowledge/`; identical content across `knowledge/` and `observations/` is a hard failure.
- External central state owns the latest-snapshot card used for cross-source discovery.
- Source repositories reference a Core version; they never copy Core Skills.
- External runtime configuration owns adjustable GitHub-observation and Elements-full-mirror thresholds. The snapshot records the exact policy and measured bytes used for its decision.

Storage may promote sealed records into external state after validation. It must never promote them into the immutable Core checkout.

## Three independent snapshot axes

Every new snapshot persists three separate conclusions:

1. `knowledge_scope`: inherited unchanged from the locked Plan;
2. `online_access`: a tested route graph that covers every registered Variable;
3. `observation_replication`: copied bytes and placements selected under the deployment capacity policy.

The second axis is mandatory and size-independent. The third axis is optional in quantity but exact in its claims.

## Observation replication modes

- `full_mirror`: capture every declared observation file within the locked knowledge scope and verify the declared file denominator.
- `partitioned_mirror`: capture the complete declared partition set and require exact agreement among its Schema-valid partition manifest, boundary descriptions, input names, member paths, sizes, hashes, and denominators.
- `no_mirror`: copy no canonical observation files while still preserving complete knowledge and complete tested online callability.

Every mode records a separate observation-completeness claim and placement list. These claims do not replace knowledge scope or online access.

## Universal online access

Storage must produce `online_access.json` and `online_runtime_audit.json`. The first records official availability, executable route definitions, and route orders. The second records live or staged route tests and an exact Variable-to-route map. Completion requires `unresolved_online_variable_count: 0`.

Supported online methods are official API, official bulk download, official browser automation, and a verified GRDR GitHub Release observation snapshot. Bulk-only and browser-only sources require source-specific adapters that download or operate the official interface, normalize the result, and preserve parameters and evidence. If the official source is unavailable, a verified GRDR Release route may serve as the online fallback. If no online route covers all registered Variables, Storage must remain incomplete.

Agent Runtime applies one of three route policies:

- `latest`: official online, then GRDR GitHub Release, then Elements or mounted replicas;
- `reproducible`: frozen GRDR or source snapshot, then Elements or mounted replicas, then a version-checked official route;
- `offline`: Elements or mounted replicas only.

A no-mirror snapshot backed only by an unversioned current API has no reproducible route. It must add a frozen online snapshot or version-pinned official route before Storage can complete.

Before every local operation, Agent Runtime verifies the complete manifest-bound inventory. During invocation it passes the selected route context to the source-specific Runtime, tries candidates in policy order, records failures, and falls back only to another declared and verified route. A missing location that claims a copy is an error, not a warning.

## On-demand research data

`fetch-variable --research-project-dir` and `fetch-indicator-data --seal-data-snapshot` create query-scoped snapshots under a research project. Each capture records Source, source snapshot, Variable, arguments, returned files, result, timestamps, SHA-256 values, and a fingerprinted manifest. These captures do not mutate the canonical source snapshot.
