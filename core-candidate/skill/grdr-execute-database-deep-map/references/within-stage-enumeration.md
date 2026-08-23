# Deterministic Within-Stage Enumeration

The project queue selects the next work unit and stage. Inside that stage, use a reproducible source-native order so a later Agent can identify the next item without guessing.

## Fix the native universe first

For the active stage, identify an official, versioned or dated universe:

- catalog entries for Dataset;
- schemas, dataflows, tables, instruments, arrays, graphs, or collections for DataStructure;
- fields, dimensions, measures, items, code lists, attributes, flags, weights, coordinates, or annotation classes for DataElement;
- official indicators, measures, series, transaction codes, survey items, assay features, bands, or operational combinations for Variable;
- the distinct evidenced research meanings required by the completed Variable universe for Construct;
- every documented access route and governance condition for Access.

Do not begin a completion claim while this universe or its count is unknown.

## Choose one ordering rule

Record the rule in the stage `notes` while work is open:

1. preserve official document, catalog, schema, questionnaire, codelist, or manifest order when it is stable;
2. otherwise sort by the complete source-native identifier using Unicode code-point order;
3. for very large stores, partition the same order into stable non-overlapping ranges and record the range boundary, manifest URL or path, checksum, and next cursor;
4. never prioritize an item merely because it is easy or already relevant to one research question during an exhaustive pass.

Use this exact progress line in open-stage notes:

```text
enumeration=<official universe>; order=<rule>; completed_native=<count>; last_native=<id-or-none>; next_native=<id-or-none>; snapshot=<date-or-version>
```

The next native item is the first item in the declared order that lacks a complete staged mapping. If several native items map to one Construct, retain each native-to-Construct relationship; the Construct count is the number of distinct evidenced constructs, not automatically the Variable count.

## Batch checkpoints

After each bounded batch:

1. stage GRDR candidate records and relationships with `stage-database-deep-map-records`;
2. recompute `registered_ids`, `verified_count`, and the progress line;
3. record the stage with `record-database-deep-map-stage`;
4. run the read-only `database-deep-map-status` to confirm the next work-unit stage;
5. preserve the native cursor in notes even if the same stage remains active.

For `mapped_complete`, `next_native` must be `none`, the expected count must equal the registered staged-or-canonical count, and evidence must support the complete native universe. For `verified_complete`, every registered mapping must additionally have passed the declared verification rule.

## Spine checkpoints

After the prerequisite content stages are mapped, enumerate each graph product separately:

- structural nodes and edges in source-native hierarchy/order;
- semantic nodes, construct nodes, and classification edges in stable canonical-ID order unless an official classification supplies order;
- variable-to-construct bridge nodes and edges in stable variable-native order.

Record roots, leaves, node and edge denominators, completed node count, last/next native identity, snapshot, and evidence in `spines.<name>.checkpoint`. The recording command recomputes the checkpoint checksum, topology fingerprint, and canonical verification counts. A disconnected graph or stale fingerprint cannot close.
