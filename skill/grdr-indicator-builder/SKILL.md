---
name: grdr-indicator-builder
description: Build evidence-constrained, multi-level research indicator systems from a research question, topic scaffold, and substantial literature corpus. Use when Codex needs to parse lawful full texts by section, extract citable evidence, perform theory deduction, content analysis, grounded-theory coding, thematic synthesis, construct operational requirements, enforce human approval gates, audit every indicator's provenance, or prepare leaf indicators for matching to GRDR variables.
---

# GRDR Indicator Builder

## Preserve the system boundary

Treat this Skill as the research-side chain of GRDR:

```text
research question -> literature evidence -> indicator hierarchy -> operational requirements
                                                                  |
GRDR source profile -> official datasets -> official variables ----+-> variable matching
```

Use `$grdr-plan-database-deep-map`, `$grdr-execute-database-deep-map`, and `$grdr-store-database-deep-map` in sequence to establish and store a database's native structure-to-variable mapping topology. Use `$grdr` to coordinate registry search, source expansion, gap diagnosis, and final matching. Do not write question-specific indicators, literature evidence, or mappings into the canonical global `registry/*.jsonl` collections.

Store each project under:

```text
research_projects/<project-id>/
  project.json
  literature.jsonl
  evidence_units.jsonl
  indicators.jsonl
  mappings.jsonl
  workflow.json
  data_gaps.jsonl
```

Follow the five research-content schemas plus the workflow and data-gap schemas in GRDR's `schemas/` directory. The last two files coordinate resumable execution; they do not add content layers to the indicator hierarchy.

## Choose the evidence stage

There are two production stages, not three competing analysis modes.

### Topic scaffold

When only a research topic or question is available, the Agent may automatically:

1. decompose the question into candidate domains, constructs, mechanisms, controls, contexts, and outcomes;
2. propose a provisional multi-level hierarchy and operational requirements;
3. set every node's `provenance_type` to `topic_scaffold` and `review_status` to `agent_candidate`;
4. identify literature and data gaps.

Never attach invented citations or describe this output as literature-grounded, validated, exhaustive, or final. Set the corpus-boundary gate to `exploratory_only` or `not_required`.

### Corpus-grounded construction

When a substantial literature corpus is available, use the formal workflow below. The corpus has no universal minimum count. Judge adequacy by declared search coverage, relevance, diversity, contradiction handling, and conceptual saturation rather than an arbitrary paper count.

## Run the formal workflow

### 1. Define the question and corpus protocol

Record the research question, analysis methods, search sources, inclusion and exclusion criteria, languages, date boundary, and stopping or saturation rule in `project.json`.

Deduplicate documents at the study level as well as the report level. Record excluded and pending documents; do not silently discard them.

### 2. Pause at human gate 1

Ask the human to approve the corpus boundary before treating extraction as formal evidence work. The Agent should prepare the candidate boundary and explain omissions, but must not approve its own boundary.

Exploratory work may continue without approval, but remains a topic scaffold.

### 3. Parse and extract evidence

Use only lawfully accessible content. Process title, abstract, introduction, literature review or theory, methods, results, discussion, conclusion, tables, figures, appendices, supplements, and references when present.

Create atomic evidence units with:

- document ID and exact section;
- a page, paragraph, table, figure, heading, or other reproducible locator;
- a faithful paraphrase;
- an optional short excerpt within the project schema limit;
- an evidence role such as construct definition, theoretical relation, operationalization, finding, limitation, or contradiction.

Read [references/evidence-standard.md](references/evidence-standard.md) before extraction.

### 4. Build the multi-level indicator hierarchy

Apply the declared methods—such as theory deduction, content analysis, grounded-theory coding, or thematic synthesis—to move from evidence to:

```text
domain -> construct -> subconstruct -> indicator -> operational requirement
```

Classify every formal node as:

- `source_reported`: explicitly named or defined in a source;
- `normalized`: terminology harmonized across sources without changing the supported meaning;
- `agent_synthesized`: an Agent synthesis supported by multiple evidence units.

Every formal node, including parent concepts, must cite one or more evidence-unit IDs. Every leaf must include an operational specification. Preserve disagreements instead of manufacturing consensus.

### 5. Pause at human gate 2

Present the complete hierarchy, definitions, evidence trace, conflicts, and coverage gaps. Ask the human to approve or revise the indicator framework. The Agent may generate and audit everything beforehand, but must not mark its own formal framework approved.

### 6. Match leaf indicators to GRDR variables

Only map leaf indicators. Compare construct definition, population, unit, time, space, denominator, observation unit, and measurement class.

Use exactly one outcome per mapping:

- `direct_match`
- `transform_required`
- `composite_required`
- `proxy_candidate`
- `definition_conflict`
- `not_found_registry_snapshot`

Treat not-found as a GRDR snapshot gap, not proof that external data does not exist. Send proxy candidates and definition conflicts to the contested-mapping human gate. Direct, reproducible transformations, composites, and explicit not-found outcomes may remain Agent decisions unless the research protocol requires additional review.

If registry matching has not yet been performed, create no placeholder mapping and report the mapping count as zero. The evidence stage, rather than a fabricated mapping status, records that work is still pending.

### 7. Audit before reporting readiness

Run:

```bash
python3 scripts/audit_project.py /absolute/path/to/research_projects/<project-id>
```

Do not report `formal_evidence_ready` or `mapping_ready` unless the audit returns that exact state with no errors.

The deterministic evidence audit applies to the five persisted research-content files; the resumable GRDR orchestrator additionally requires `workflow.json` and `data_gaps.jsonl`. For an in-memory exploratory response where the user did not request files, report `audit not run`, `formal_evidence_ready: false`, and `mapping_ready: false`; do not imply that an audit succeeded.

For persisted orchestration, use the main GRDR CLI:

```bash
python3 scripts/grdr.py start-research-project <spec.json>
python3 scripts/grdr.py research-project-status <project-id>
python3 scripts/grdr.py resume-research-project <project-id>
python3 scripts/grdr.py match-indicators <project-id>
python3 scripts/grdr.py expand-from-data-gaps <project-id>
python3 scripts/grdr.py rerun-matching <project-id>
```

The Agent owns these automatic operations. It may invoke `approve-human-gate` only to record an approval the human has explicitly given with a reviewer identity and notes; it must never infer or manufacture that decision.

## Divide AI and human work

The Agent owns routine execution:

- question decomposition and provisional scaffolding;
- document organization, deduplication proposals, section parsing, and evidence extraction;
- coding, synthesis, hierarchy generation, operationalization, and internal consistency checks;
- GRDR retrieval, compatibility comparison, mapping proposals, and gap diagnosis;
- citations, audit files, provenance, and revision history.

The human owns judgment gates:

1. approve the corpus boundary for formal work;
2. approve the final indicator framework;
3. approve proxy candidates and definition conflicts when they occur.

Humans may review more, but should not need to perform routine extraction or coding outside the system. Record reviewer, time, and notes for every approval. Never infer approval from silence.

## Handle references and access correctly

Use a paper's reference list for snowball discovery. A cited work becomes substantive evidence only after that work itself is ingested and analyzed. Do not cite a reference-list entry as if its contents had been read.

Do not bypass authentication, licenses, paywalls, consent, ethics review, data-use agreements, or technical access controls. Metadata-only and abstract-only documents may support discovery or limited claims, but disclose the limitation and do not treat them as equivalent to full text.

## Report the result

Return:

- project ID, evidence stage, analysis methods, and corpus boundary;
- document, evidence-unit, total hierarchy-node, leaf-indicator, and mapping counts reported separately;
- hierarchy with evidence links and provenance type;
- all contradictions, unsupported gaps, and incomplete full-text warnings;
- corpus, framework, and contested-mapping gate status;
- GRDR mapping outcomes and additional database-profiling needs;
- exact audit result and whether the output is exploratory or formal.
