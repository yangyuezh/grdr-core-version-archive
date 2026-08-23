# Source Repository and Snapshot Layout

## Private source Git repository

```text
grdr-source-<slug>/
├── README.md
├── grdr-source.json
├── adapters/
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
<slug>-<snapshot>-agent-index.sqlite
<slug>-<snapshot>-observations-<partition>.tar.gz
manifest.json
storage_receipt.json
```

Observation assets may be partitioned, but their union must equal the complete observation inventory declared by the snapshot.

## Elements

```text
<elements-root>/sources/<slug>/snapshots/<snapshot-id>/
├── knowledge/
├── agent/grdr-agent-index.sqlite
├── observations/<partition>/...
└── receipts/storage_receipt.json
```

Elements adds the final receipt after publication. The receipt is a provenance sidecar; logical parity is computed across `knowledge/`, `agent/`, and `observations/`.
