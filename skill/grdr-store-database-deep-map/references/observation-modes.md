# Online Access and Observation Replication

Choose after Execute is sealed. Do not use database size to weaken `knowledge_scope` or online Variable coverage. Capacity affects only copied observation bytes and placements.

## Compose the independent policy

Schema 4.0 requires three siblings under `observation_policy`:

```json
{
  "replication": {},
  "online_access": {},
  "cache": {}
}
```

`replication` describes custody of original observations. `online_access` describes executable online routes. `cache` describes optional research-project captures. Never use one as evidence for another.

## Universal online access

Every snapshot must declare online access regardless of replication mode:

```json
"online_access": {
  "completion_requirement": "all_registered_variables_online_callable",
  "official_access": {
    "status": "callable",
    "basis": "The official interface passed a dated Runtime test."
  },
  "routes": [{
    "route_id": "official-api",
    "access_method": "official_api",
    "authority": "official",
    "uri": "https://official.example/api",
    "freshness": "current_upstream",
    "coverage_claim": "all_registered_variables",
    "verification": "live_runtime_test"
  }]
}
```

Supported methods are `official_api`, `official_bulk_download`, `official_browser_automation`, and `grdr_release_snapshot`. Authority, freshness, and verification must agree with the route. If the official source is unavailable, state `official_access.status: unavailable` and provide a verified GRDR Release route that covers every registered Variable. Storage calls Runtime 2.0 `self-test-online`; it rejects any failed route or Variable without a ready route ID.

Both `latest` and `reproducible` policies must be nonempty. A current-only unversioned official API can satisfy `latest`, but not `reproducible`; pair it with a frozen GRDR Release route, a copied mirror, or a version-pinned/frozen official route.

## GitHub replication capacity

Run `scripts/configure_core.py --github-observation-max-gib 5` to set the adjustable total-observation threshold for one database Release. Storage measures captured bytes before packaging and rejects a GitHub observation placement that exceeds this limit. It records the exact threshold and decision in `snapshot_profile.capacity_assessment`.

GitHub's platform limit is separate: every Release asset must remain below 2 GiB. The configurable GitHub threshold controls total observation bytes assigned to one database Release; it does not override the per-file platform limit.

For a partitioned or no-mirror source, optionally add this inside `replication` so classification uses the estimated full upstream size instead of the captured subset:

```json
"capacity_estimate": {
  "estimated_total_bytes": 53687091200,
  "basis": "Official catalog inventory measured on the snapshot date."
}
```

## Full mirror

Use when every observation file inside the locked scope will be copied.

```json
"replication": {
  "mode": "full_mirror",
  "placements": ["github_release"],
  "completeness": {
    "claim": "complete_within_knowledge_scope",
    "basis": "Explain the authoritative file denominator.",
    "expected_file_count": 12,
    "expected_partition_count": null
  },
  "partition_manifest": null,
  "external_locations": []
}
```

GitHub observation placement is optional. For observations above the configured Release total, use a declared mounted `object_store`, copy a bounded partition, or choose `no_mirror`. Knowledge and Agent assets still publish to GitHub.

## Partitioned mirror

Use when the snapshot deliberately copies a declared partition set.

```json
"replication": {
  "mode": "partitioned_mirror",
  "placements": ["github_release"],
  "completeness": {
    "claim": "complete_declared_partition_set",
    "basis": "Explain which official partitions are included and why.",
    "expected_file_count": 24,
    "expected_partition_count": 6
  },
  "partition_manifest": "/absolute/path/partition-manifest.json",
  "external_locations": []
}
```

Every `observation_inputs[].name` is one captured partition. The partition manifest is copied into knowledge and fingerprinted. It must validate against `observation_partition_manifest.schema.json`; Source and snapshot IDs, partition names, boundaries, paths, sizes, hashes, partition count, and file count must exactly match the captured inventory.

## No mirror

Use when the canonical snapshot should copy no original observation files. This does not weaken online access.

```json
"replication": {
  "mode": "no_mirror",
  "placements": [],
  "completeness": {
    "claim": "observations_not_replicated",
    "basis": "Capacity policy selects online access without canonical observation replication.",
    "expected_file_count": null,
    "expected_partition_count": null
  },
  "partition_manifest": null,
  "external_locations": [],
  "capacity_estimate": {
    "estimated_total_bytes": 53687091200,
    "basis": "Dated official size estimate."
  }
}
```

`observation_inputs` and replication placements must both be empty. Temporary raw files retained inside the deep-map project must still appear under `raw_observation_exclusions` so they cannot enter knowledge.

## Runtime invocation acceptance probes

Self-tests and route coverage are necessary but not sufficient. For every nonempty Variable index, declare `runtime.acceptance_probes` that drive the staged source Runtime through Core's public argument names:

```json
"runtime": {
  "descriptor": "/absolute/path/runtime.json",
  "files": ["/absolute/path/source_runtime.py"],
  "acceptance_probes": [{
    "probe_id": "population-online",
    "variable_id": "grdr:variable:example-population",
    "route_policy": "latest",
    "parameters": {
      "country": "USA",
      "start_period": "2023",
      "end_period": "2024"
    },
    "expected": {
      "minimum_row_count": 1,
      "selected_routes": ["official_upstream"]
    }
  }]
}
```

The `latest` probe is always required. If `online_access.route_policies.offline` is nonempty, add a second probe whose expected route is a local or mounted mirror. Storage supplies its own temporary output directory, requires `status=fetched`, verifies Source and Variable identity, checks nonzero rows and files, and seals only the result summary and output fingerprint—not the temporary probe data.

## Cache policy

Cache is independent of both online access and canonical replication:

```json
"cache": {
  "mode": "on_demand",
  "research_project_snapshots": true,
  "root": "research_project"
}
```

Use `disabled`, `false`, and `null` when research-project captures are forbidden.

## Mounted object storage

Add an external replication location only when the storage is mounted and writable:

```json
{
  "type": "object_store",
  "uri": "s3://bucket/grdr",
  "local_path": "/mounted/object-store/grdr",
  "verification": "copied_and_hashed"
}
```

Storage copies declared observations under `sources/<slug>/snapshots/<snapshot-id>/observations/` and verifies that inventory before completion.
