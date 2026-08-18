# Population, energy, income, industrial structure, and carbon emissions

This is GRDR's first persisted end-to-end research-question test.

## Research question

Across countries over time, how are population size, final energy consumption, income per capita, and industrial structure associated with carbon dioxide emissions excluding LULUCF?

## Current state

- Evidence stage: `topic_scaffold`
- Workflow state: `expansion_planned`
- Matching attempts: 2
- Data-gap expansion rounds: 2
- Formal evidence ready: no
- Indicator-framework human gate: `pending`

This project is exploratory. No literature corpus was supplied, no citations were fabricated, and no Agent-issued approval has been recorded.

## Matching result

| Leaf requirement | Outcome | Registered variable |
|---|---|---|
| Carbon dioxide emissions excluding LULUCF | Direct match | `grdr:variable:undata-ghg-en-atm-co2e-xlulucf` |
| Population size | Direct match | `grdr:variable:wdi-sp-pop-totl` |
| Final energy consumption | Direct match | `grdr:variable:undata-energy-na` |
| Income per capita | Current-snapshot gap | None |
| Industrial structure | Current-snapshot gap | None |

Coverage is 3 of 5 leaf requirements. A direct construct match does not erase the separately recorded population, unit, time, or spatial-fit assessment.

## Expansion plan

Both unresolved requirements point first to deeper profiling of registered national-accounts catalogs, especially `grdr:dataset:undata-national-accounts-estimates-of-main-aggregates`. These are search leads, not assertions that compatible variables have already been verified.

The machine-readable records are the source of truth: `project.json`, `indicators.jsonl`, `mappings.jsonl`, `workflow.json`, and `data_gaps.jsonl`. `literature.jsonl` and `evidence_units.jsonl` are empty because this test did not receive a literature corpus.
