# Six-Layer Profiling Standard

## Layer checklist

| Layer | Required identity | Required dimensions | Preferred evidence |
|---|---|---|---|
| Institution | producer, publisher, maintainer, governor | type, jurisdiction, mandate, role | official mandate, official institutional page |
| Source | canonical database identity | disciplines, topics, geography, time, units, modalities, authority, provenance, access, license | official homepage, catalog, access and license documentation |
| Dataset | versionable collection | population, unit, spatial and temporal coverage, release, methodology, limitations, citation | official catalog record, methodology, data paper |
| Resource | concrete access object | URL, type, format, authentication, machine access, rate limits, license | API, download, application, or access documentation |
| Data element & variable | source-native component and research-matchable operational variable | native hierarchy, dimension/measure/attribute type, code lists, definition, unit, denominator, population, resolutions, measurement, comparability, join keys | data structure, dictionary, codebook, questionnaire, schema, API metadata |
| Construct | research concept | definition, domains, type, boundaries, directness | standard, controlled vocabulary, official or peer-reviewed definition |

## Scope modes

- `identity_only`: layers 1–2 only.
- `representative_chain`: at least one defensible chain through all six layers.
- `question_driven`: datasets and variables selected for a declared scientific question.
- `priority_catalog`: a declared high-value subset of the source catalog.
- `catalog_level`: reproducible enumeration of the official catalog.
- `exhaustive_snapshot`: a bounded, dated, versioned inventory of all enumerable items.

## Integrity rules

1. A homepage is not a dataset.
2. A catalog entry is not row-level access.
3. A topic tag is not evidence that a variable exists.
4. Identical labels do not prove comparable definitions.
5. A repository is not automatically the original producer.
6. A populated layer does not prove full catalog completeness.
7. Unknown means not established, not absent.
8. Restricted and commercial sources remain eligible but access controls must be preserved.
9. A multidimensional observation value without its dimension selections is not a research variable.
10. Data elements are a 5A substructure of layer 5; they do not create a seventh GRDR layer.

## Evidence promotion

Keep discovery candidates unverified. Promote identity and scope only after checking appropriate official evidence. Verify datasets and variables independently; source-level verification never automatically propagates downward.

Persist one current declared scope per source in `registry/source_profiles.jsonl` under `schemas/source_profile.schema.json`; update it as later passes supersede it and rely on Git for history. The profile record is the authoritative statement of inventory boundaries; populated entity records alone do not establish catalog completeness.

## Completion report

Always state the declared scope, enumeration method, six layer counts, verification distribution, unresolved gaps, blockers, and whether the result is representative or catalog-level.
