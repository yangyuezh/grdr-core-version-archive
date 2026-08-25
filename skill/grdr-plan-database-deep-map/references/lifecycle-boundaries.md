# Lifecycle and Completion Boundaries

Completion is always relative to a declared claim. Choose the boundary before enumerating work.

## Static and versioned systems

- **Catalog snapshot:** capture every catalog entry visible under a dated, reproducible enumeration rule.
- **Release version:** pin database, dataset, schema, code list, and observation vintages; record later corrections separately.
- **Partition manifest:** use stable non-overlapping ranges, object lists, or checksums for very large stores.
- **API namespace:** pin endpoint family, query parameters, pagination order, metadata version, and retrieval time.

An upstream release or schema fingerprint change starts a new pass or reopens affected checks and stages. Git history alone does not make old content current.

## Dynamic, rolling, and streaming systems

Do not seek a timeless denominator for an unbounded stream. Define:

- event-time and retrieval-time window;
- timezone and watermark/lateness rule;
- stream/schema/processing version;
- partition identity and ordering;
- late correction, deletion, tombstone, and replay behavior;
- when a window is considered closed;
- refresh cadence and fingerprint.

`rolling_current` means complete for the declared current window and rule, not complete for all past or future events.

## Federated and virtual systems

Separate the virtual query layer from member databases. Pin:

- participating members and membership date;
- member schema/version and availability;
- query plan, cohort or selection definition;
- identity-resolution and duplicate rules;
- partial-response and failure semantics;
- whether observations move or only aggregates/results return.

A successful federated query does not prove every member was queried or comparable.

## Non-enumerable or restricted systems

Use a logical, stable work unit at the highest auditable level—for example, approved site extract, secure-environment dataset, collection, model experiment, or question-bounded query. State that the underlying observation universe is unavailable or non-enumerable. Metadata mapping may complete while observation access remains blocked; do not omit the blocked obligation.

## Question-bounded and representative passes

- `representative_only`: proves the mapped chain, never database-wide coverage.
- `question_fit`: covers only the structures and variables required by the approved question or indicator framework.
- `catalog_only`: proves catalog identity coverage, not internal variables or observations.
- `bounded_partition`: proves one declared subset or manifest.
- `exhaustive_snapshot`: requires a reproducible full denominator inside a date/version boundary.

Question-bounded publication requires a human semantic-scope decision so the result is not promoted to an exhaustive claim.
