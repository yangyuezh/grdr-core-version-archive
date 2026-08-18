# GRDR Database Deep-Mapping Standard

## Main content chain

| Layer | Entity and question answered | Required mapping | Preferred evidence |
|---|---|---|---|
| 1 | Institution — who produces, publishes, maintains, funds, or governs it? | role-specific organization links, mandate, jurisdiction | official mandate and institutional pages |
| 2 | Database / Source — what authoritative system is being mapped? | canonical identity, scope, authority, provenance, lifecycle | official homepage, catalog, policy documents |
| 3 | Dataset — which versionable collection inside the database? | population, unit, coverage, release, method, limitations, citation | official catalog record, methodology, data paper |
| 4 | DataStructure — how is that dataset organized internally? | native hierarchy/schema/table/dataflow/instrument identity, version, nesting | schema, DSD, codebook, API structure, questionnaire |
| 5A | DataElement — what native components does the structure define? | fields, dimensions, measures, identifiers, attributes, weights, flags, code lists | schema/DSD, dictionary, codebook, instrument |
| 5B | Variable — which operational quantity can research matching use? | element composition, dimensions, definition, unit, population, resolution, comparability, join keys | official definition plus structural evidence |
| 6 | Construct — what research concept does the variable measure? | construct definition, measurement class, directness, proxy/model limits | standard, official or peer-reviewed definition |

DataElement and Variable are two representations inside layer 5, so the model has six content layers and seven entity types.

## Cross-cutting records

- `Resource` attaches API, download, query, documentation, authentication, rate-limit, license, and secure-access information to a Dataset or DataStructure. It does not occupy a layer.
- `Evidence` and `Verification` support every factual claim.
- `SourceProfile` declares pass scope, completeness boundaries, per-entity claims, access status, blockers, and review time.
- `Relationship` makes the map traversable: Dataset `organized_as` DataStructure; DataStructure `defines` DataElement; Variable is derived from elements and `measures` Construct; content is `accessed_via` Resource.

## Scope modes

- `identity_only`: layers 1–2 only.
- `representative_chain`: one or more defensible chains through layer 6.
- `question_driven`: structures and variables selected for a declared scientific question.
- `priority_catalog`: a declared high-value subset.
- `catalog_level`: reproducible enumeration of the official dataset catalog.
- `exhaustive_snapshot`: a dated, versioned inventory of every item enumerable within the boundary.

## Integrity gates

1. A homepage is not a Dataset.
2. An API or CSV is not a DataStructure; it is an access attachment.
3. A topic tag is not evidence that a Variable exists.
4. A measure without meaning-bearing dimensions is not a multidimensional research Variable.
5. A label match does not establish comparable definitions.
6. A populated layer does not establish complete inventory coverage.
7. Unknown means not established, not absent.
8. Restricted and commercial databases remain eligible, but controls must be preserved.

Always report scope, enumeration method, layer counts, access-sidecar count, verification distribution, unresolved gaps, blockers, and whether the pass is representative or complete within its declared boundary.
