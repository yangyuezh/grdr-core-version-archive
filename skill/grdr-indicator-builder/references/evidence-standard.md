# GRDR literature evidence standard

## 1. Claim boundary

Every formal indicator node must be supported by evidence from an included document. Evidence supports only the claim actually made by the source. Do not turn correlation into causation, context-specific findings into universal rules, or a cited reference into evidence that was directly inspected.

## 2. Evidence unit

An evidence unit is the smallest auditable passage, table, figure, or appendix element needed to support one analytical claim. Record:

- document and study identity;
- section and exact locator;
- evidence role;
- faithful paraphrase;
- optional short excerpt;
- Agent or human review status.

Use `construct_definition` for what a concept means, `theory_relation` for proposed relationships, `indicator_name` for named indicators, `operationalization` and `measurement_method` for how concepts become measurable, `empirical_finding` for results, and `limitation` or `contradiction` for boundary conditions.

## 3. Section use

- Abstract: screening and concise claims; warn when it is the only substantive text.
- Introduction, literature review, and theory: definitions, mechanisms, prior debates, and proposed relationships.
- Methods: sampling, coding, variables, measurement, instrument, model, and operationalization.
- Results: empirical patterns and reported indicator performance.
- Discussion and conclusion: interpretation, scope, limitations, and implications.
- Tables, figures, appendices, and supplements: measurement detail and additional findings.
- References: discovery only until the cited document is separately ingested.

## 4. Synthesis types

- `source_reported`: retain the source's meaning and cite the relevant evidence unit.
- `normalized`: document terminology changes and cite all sources whose meanings are being harmonized.
- `agent_synthesized`: explain the synthesis logic and cite multiple supporting evidence units. Do not hide conflicting evidence.
- `topic_scaffold`: no evidentiary claim; use only before formal corpus-grounded construction.

Theory deduction, content analysis, grounded-theory coding, and thematic synthesis are methods that may be combined. They do not waive citation requirements.

## 5. Corpus adequacy

Do not set one fixed minimum number of papers for all research questions. Declare:

- databases and other search sources;
- search expressions and dates;
- inclusion and exclusion criteria;
- languages and publication boundaries;
- deduplication and study-family rules;
- coverage or saturation stopping rule;
- inaccessible, excluded, and unresolved material.

The human approves this boundary. The Agent may recommend expansion when concepts continue to emerge, major literatures are missing, conclusions conflict, or full text is insufficient.

## 6. Indicator hierarchy

Use domain, construct, subconstruct, indicator, and operational-requirement nodes as needed; do not force every branch to use every level. Parent nodes need evidence as well as leaves. A leaf must specify, where applicable, unit, denominator, population, observation unit, spatial scope, temporal scope, direction, and whether a proxy is admissible.

## 7. Contradictions and quality

Keep contradictory definitions or findings visible. Record the quality-appraisal status for each included document, but do not automatically erase evidence from a weaker study. Explain how quality, applicability, and contradiction affect the indicator definition or confidence.

## 8. Data matching

Match only leaf indicators to GRDR variables. A label similarity is insufficient. Compare definition, measurement method, unit, denominator, population, observation unit, time, space, and provenance. Proxy candidates and definition conflicts require explicit human approval.

`not_found_registry_snapshot` means only that the current GRDR registry contains no compatible variable. It should trigger database discovery or deeper source profiling.

## 9. Access and quotation

Use content only under a lawful access basis. Retain citations and locators, but avoid unnecessary reproduction of copyrighted text. Prefer paraphrases; keep excerpts short and within the schema limit. Never store credentials or restricted full text in the registry.
