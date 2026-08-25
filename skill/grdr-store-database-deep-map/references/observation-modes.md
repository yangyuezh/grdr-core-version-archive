# Observation Mode Selection

Choose after Execute is sealed. Do not use database size to weaken `knowledge_scope`; size affects only observation replication and placement.

## Deployment-local capacity policy

Run `scripts/configure_core.py --github-observation-max-gib 5 --elements-full-mirror-max-gib 10` to set adjustable deployment thresholds. Storage measures the actual captured bytes before copying and rejects a GitHub or Elements placement that exceeds its configured limit. It also records the exact thresholds and decision in `snapshot_profile.capacity_assessment`.

GitHub's platform limit is separate: every Release asset must remain below 2 GiB. The configurable GitHub observation threshold controls the total observation bytes assigned to one database Release; it does not override the per-file platform limit.

For partitioned or federated sources, optionally add this to `observation_policy` so classification uses the estimated full upstream size instead of the captured subset:

```json
"capacity_estimate": {
  "estimated_total_bytes": 53687091200,
  "basis": "Official catalog inventory measured on the snapshot date."
}
```

## Full mirror

Use when every observation file inside the locked scope will be copied.

```json
{
  "replication_mode": "full_mirror",
  "placements": ["github_release", "elements"],
  "completeness": {
    "claim": "complete_within_knowledge_scope",
    "basis": "Explain the authoritative file denominator.",
    "expected_file_count": 12,
    "expected_partition_count": null
  },
  "partition_manifest": null,
  "external_locations": [],
  "cache": {
    "mode": "disabled",
    "research_project_snapshots": false,
    "root": null
  }
}
```

GitHub is optional. For larger full mirrors, use `elements` or `object_store` without `github_release`.

## Partitioned mirror

Use when the snapshot deliberately copies a declared partition set.

```json
{
  "replication_mode": "partitioned_mirror",
  "placements": ["elements", "research_project_cache"],
  "completeness": {
    "claim": "complete_declared_partition_set",
    "basis": "Explain which official partitions are included and why.",
    "expected_file_count": 24,
    "expected_partition_count": 6
  },
  "partition_manifest": "/absolute/path/partition-manifest.json",
  "external_locations": [],
  "cache": {
    "mode": "on_demand",
    "research_project_snapshots": true,
    "root": "research_project"
  }
}
```

Every `observation_inputs[].name` is one captured partition. The partition manifest is copied into knowledge and fingerprinted.

The manifest must validate against `observation_partition_manifest.schema.json`. Its Source and snapshot IDs, partition names, machine-readable boundary descriptions, relative file paths, sizes, SHA-256 values, partition count, and file count must exactly match the captured observation inventory.

## Federated on demand

Use when observations remain at the official service.

```json
{
  "replication_mode": "federated_on_demand",
  "placements": ["official_upstream", "research_project_cache"],
  "completeness": {
    "claim": "knowledge_complete_observations_federated",
    "basis": "State that knowledge is complete inside the Plan scope and observations are retrieved by the verified official Runtime.",
    "expected_file_count": null,
    "expected_partition_count": null
  },
  "partition_manifest": null,
  "external_locations": [{
    "type": "official_upstream",
    "uri": "https://official.example/api",
    "local_path": null,
    "verification": "official_runtime_verified"
  }],
  "cache": {
    "mode": "on_demand",
    "research_project_snapshots": true,
    "root": "research_project"
  }
}
```

`observation_inputs` must be empty. List any raw files temporarily retained inside the deep-map project under `raw_observation_exclusions` so they cannot enter knowledge.

## Mounted object storage

Add an external location only when the storage is mounted and writable:

```json
{
  "type": "object_store",
  "uri": "s3://bucket/grdr",
  "local_path": "/mounted/object-store/grdr",
  "verification": "copied_and_hashed"
}
```

Storage copies the declared observations under `sources/<slug>/snapshots/<snapshot-id>/observations/` and verifies that inventory before completion.
