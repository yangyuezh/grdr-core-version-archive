# Semantic alignment contract

## Purpose

This contract governs the project-scoped `ResearchIndicator -> B` decision. B is the same persisted `SemanticNode / Construct` spine created by database Plan -> Execute -> Storage. The decision never changes canonical B.

## Required comparison

For each leaf indicator, compare:

1. research definition and intended construct;
2. target definition and source-bounded scope;
3. direct, constructed, modeled, forecast, index, or proxy meaning;
4. population and observation unit;
5. unit, denominator, direction, and aggregation;
6. temporal and spatial scope or resolution;
7. literature evidence on the research side and registry evidence on the target side;
8. known conflicts, exclusions, and context dependence.

Labels and embedding similarity are recall signals only.

## Mapping relations

- `exact_match`: meanings are equivalent for the stated research use; different wording alone is harmless.
- `close_match`: meanings substantially overlap but one retains a material qualification.
- `broader_match`: the stored B target is broader than the research indicator.
- `narrower_match`: the stored B target is narrower than the research indicator.
- `related_match`: scientifically related but not a hierarchical or equivalent meaning.
- `no_match`: no recalled B target is defensible.

Only `exact_match` is non-contested by default. A SemanticNode target is contested even when the label appears exact because one node may route to many constructs.

## Alignment roles

- `primary`: the main interpretation. Exactly one is required for every leaf.
- `component`: one required part of a composite operationalization. Use at least two component decisions.
- `alternative`: a defensible alternative retained for comparison; it is not selected automatically.

`no_match` must be the sole decision for its indicator and must use `primary` with null target fields.

## Decision integrity

- Select only a target present in that indicator's `semantic_candidates.jsonl` snapshot.
- Expand and rebuild recall instead of manually inventing an unregistered ID.
- State why the relation holds; do not merely repeat labels.
- Preserve the research indicator's evidence IDs automatically in the persisted alignment.
- Treat confidence as the Agent's calibrated decision confidence, not source authority or variable fitness.
- Do not use one universal threshold to collapse disciplinary meaning.
- Do not approve contested alignments or mappings on behalf of the human.

## Files

The resolver adds three project-scoped files:

```text
semantic_candidates.jsonl  full-text recall snapshot
semantic_alignments.jsonl  Agent R-to-B decisions
semantic_paths.jsonl       deterministic B-to-A traversal results
```

`mappings.jsonl` remains the final leaf-to-Variable result and records the selected alignment and path IDs.
