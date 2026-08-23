# GRDR research projects

This directory contains question-specific literature evidence, research-indicator hierarchies, and mappings to canonical GRDR variables. These artifacts are deliberately separate from the global source registry.

Each project uses:

```text
<project-id>/
├── project.json
├── literature.jsonl
├── evidence_units.jsonl
├── indicators.jsonl
├── mappings.jsonl
├── workflow.json
├── data_gaps.jsonl
├── semantic_candidates.jsonl
├── semantic_alignments.jsonl
└── semantic_paths.jsonl
```

The first five files preserve the research definition, literature, evidence, hierarchy, and mappings. `workflow.json` records resumable execution state and history; `data_gaps.jsonl` turns current-registry misses into bounded deep-profiling or source-discovery tasks. The three semantic files preserve full-text B recall, evidence-constrained R→B decisions, and deterministic B→A paths without mutating canonical registry records.

Follow `docs/INDICATOR_BUILDER_PROTOCOL.md`, the semantic-resolution Skill, and the research-project schemas. A project-level `README.md` may summarize the machine records for human review. Do not commit copyrighted full texts, credentials, sensitive research material, or restricted data.
