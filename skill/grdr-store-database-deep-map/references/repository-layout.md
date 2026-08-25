# Source Repository and Snapshot Layout

## Private source Git repository

```text
grdr-source-<slug>/
├── README.md
├── grdr-source.json
├── adapters/
├── runtime/
├── plan/<snapshot-id>/
│   ├── diagnostic_plan.json
│   ├── scope.json
│   └── units.jsonl
├── snapshots/<snapshot-id>/
│   ├── manifest.json
│   └── canonical_archive_receipt.json
└── tests/test_snapshot_manifest.py
```

`.grdr-release-assets/` is a local ignored build directory. Its contents are uploaded to the GitHub Release, not committed as ordinary Git files.

## GitHub Release

```text
<slug>-<snapshot>-knowledge.tar.gz
<slug>-<snapshot>-agent-runtime.tar.gz
<slug>-<snapshot>-observations-<partition>.tar.gz  # only when placed on GitHub
manifest.json
storage_receipt.json
```

Knowledge and Agent assets are mandatory. Observation assets are mode- and placement-dependent. Asset logical memberships must be disjoint.

## Elements

```text
<elements-root>/sources/<slug>/snapshots/<snapshot-id>/
├── knowledge/
│   └── storage/observation_manifest.json
├── agent/
│   ├── grdr-agent-index.sqlite
│   ├── runtime.json
│   ├── <source-runtime>.py
│   └── runtime_audit.json
├── observations/<partition>/...       # only when placed on Elements
└── receipts/
    ├── manifest.json
    └── storage_receipt.json
```

The receipt and manifest are provenance sidecars and are excluded from the logical inventory.

## Mounted large-data store

```text
<object-store-root>/sources/<slug>/snapshots/<snapshot-id>/
└── observations/<partition>/...
```

Storage copies and hashes this representation before completion. The GitHub manifest records its URI, mounted path, logical paths, and observation fingerprint.

## Federated and research-project data

Federated snapshots hold no canonical observation files. Their manifest records the official upstream URI and verified Runtime.

An on-demand research fetch may create:

```text
<research-project>/data_snapshots/<variable>/<capture-id>/
├── data/
│   ├── runtime_result.json
│   └── <returned files>
└── manifest.json
```

`data_snapshot_index.jsonl` indexes those query-scoped captures. They are derived research artifacts, not additions to the source snapshot.
