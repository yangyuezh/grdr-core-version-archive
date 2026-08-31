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
- `indexes/`: derived, rebuildable global discovery and routing SQLite plus its status manifest;
- `cache/`: optional, disposable Release expansions and persisted verification receipts.

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
- Agent Runtime normally materializes only the verified Agent asset, manifest, and receipt into a lightweight local cache. This is sufficient for global indexing, semantic traversal, routing, and official online invocation. A complete expansion of GitHub-hosted knowledge and observations is explicit and reserved for local/offline use. Both cache scopes are disposable, rebuildable, and not owned by the canonical snapshot.
- Large observation bytes may instead live on a mounted object store or remain only at the official upstream; this replication decision does not remove the online-callability requirement.
- A location-aware manifest maps every logical file to its canonical locations and SHA-256. Observation parity is checked only across locations that claim a normative copy; a local cache is checked against the Release manifest when present.
- Raw observation files are excluded from `knowledge/`; identical content across `knowledge/` and `observations/` is a hard failure.
- External central state owns the latest-snapshot card used for cross-source discovery.
- Agent Runtime derives one global index from central records and the latest locally callable Agent shards. Missing shards are automatically materialized in lightweight `agent` scope from verified Releases during index refresh. The index stores only search summaries, exact entity locators, Variable-to-Construct links, and Variable-to-route links; it is never canonical and may be deleted and rebuilt.
- Source repositories reference a Core version; they never copy Core Skills.
- External runtime configuration owns the adjustable GitHub-observation total threshold. GitHub's under-2-GiB per-asset limit is always enforced. The snapshot records the exact policy and measured bytes used for its decision.

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

Storage must produce `online_access.json`, `online_runtime_audit.json`, and `invocation_acceptance_audit.json`. The first records official availability, executable route definitions, and route orders. The second records live or staged route tests and an exact Variable-to-route map. The third proves that Core's public `fetch-variable` argument protocol can retrieve nonempty observations and output artifacts for a real Variable, using an entity `identifier`, `country`, and/or period selector appropriate to the source. A `latest` probe is mandatory; when an offline route exists, an `offline` probe is mandatory too. Completion requires `unresolved_online_variable_count: 0` and a ready invocation-acceptance audit.

Supported online methods are official API, official bulk download, official browser automation, and a verified GRDR GitHub Release observation snapshot. Bulk-only and browser-only sources require source-specific adapters that download or operate the official interface, normalize the result, and preserve parameters and evidence. If the official source is unavailable, a verified GRDR Release route may serve as the online fallback. If no online route covers all registered Variables, Storage must remain incomplete.

Agent Runtime applies one of three route policies:

- `latest`: official online, then GRDR GitHub Release, then a materialized local cache or mounted replica;
- `reproducible`: frozen GRDR or source snapshot, then a materialized local cache or mounted replica, then a version-checked official route;
- `offline`: materialized local cache or mounted replicas only.

Before applying a source route policy, Agent Runtime performs two-stage cross-source routing: query the global index, select the candidate Source and exact snapshot, then open only that source's Agent SQLite and Runtime 2.0. Ordinary queries compare central registry and source-card fingerprints and incrementally refresh changed shards. `rebuild-global-index` recreates all derived state; `audit-global-index --verify-sources` additionally performs fresh source-level verification. If the global index cannot be opened or refreshed, the legacy distributed scan remains an explicit fallback rather than turning an infrastructure failure into an empty-result claim.

A no-mirror snapshot backed only by an unversioned current API has no source-wide reproducible route. It may complete only when all Variables remain callable through `latest`, the on-demand research-project cache is enabled, and the manifest states `research_snapshot_required`. The first research fetch must then be sealed into that research project's data snapshot; Storage must not relabel the current API as version-pinned. If a frozen or version-pinned source route exists, ordinary source-level `reproducible` routing remains available.

On first materialization, after file changes, and during explicit audit, Agent Runtime verifies the complete inventory for the declared cache scope. `agent` scope must match every Agent logical file and contain no knowledge or observation payload; `full` scope must match the complete GitHub location inventory. The cache profile is bound to Source, snapshot, and logical fingerprint. A filesystem-bound verification receipt prevents unchanged shards from being rehashed on every new CLI process. During invocation Runtime prefilters routes with the Variable-to-route map, passes the selected route context to the source-specific Runtime, performs bounded retry only for transient online failures, records every attempt, and falls back only to another declared and verified route. A missing canonical location that claims a copy is an error; an absent derived cache is rebuildable.

## On-demand research data

`fetch-variable --research-project-dir` and `fetch-indicator-data --seal-data-snapshot` create query-scoped snapshots under a research project. Both commands accept the same standard selectors, including `--identifier`, `--country`, and period boundaries. Each capture records Source, source snapshot, Variable, arguments, returned files, result, timestamps, SHA-256 values, and a fingerprinted manifest. These captures do not mutate the canonical source snapshot.
