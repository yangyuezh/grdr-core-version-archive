# Agent Research Data Protocol

GRDR enables an AI agent to move from a scientific question to an auditable data-source plan while continuously expanding the underlying registry and knowledge graph.

## Standard workflow

```text
scientific question
  → concepts, mechanisms, population, and unit of analysis
  → candidate empirical structure
  → data-requirement matrix
  → registry and knowledge-graph retrieval
  → source authority and task-fit assessment
  → temporal, spatial, level, definition, and identifier compatibility
  → candidate source combination
  → variable and dimension gap diagnosis
  → additional-source or alternative-measurement recommendations
  → evidence, access, provenance, and citation output
```

The registry must also support direct source discovery and curation without requiring a scientific question.

## Core operations

### Registry discovery

- `search_sources`
- `get_source`
- `search_datasets`
- `search_variables`
- `trace_provenance`
- `get_access_instructions`
- `get_citation`

### Assessment and connection

- `assess_source_quality`
- `assess_fit`
- `find_joinable_sources`
- `compare_measurements`
- `identify_original_producer`

### Research-design support

- `build_data_requirements`
- `diagnose_data_gaps`
- `recommend_measurements`
- `recommend_source_combination`
- `identify_missing_dimensions`

### Registry expansion and maintenance

- `nominate_source`
- `audit_source_depth`
- `audit_all_source_depth`
- `declare_source_profile_scope`
- `decompose_source_six_layers`
- `register_institution`
- `register_source`
- `register_dataset`
- `register_resource`
- `register_variable`
- `register_relationship`
- `attach_evidence`
- `verify_record`
- `detect_duplicate`
- `mark_superseded`
- `check_links`

### Optional access extensions

- `run_adapter`
- `query_federated_source`
- `create_lawful_snapshot`
- `monitor_upstream_change`

The current CLI implements a subset. These operation names define the intended capability surface for CLI, SDK, and MCP delivery.

## Research request contract

Progressively resolve:

- scientific question and intended inference;
- target population and unit of analysis;
- temporal and spatial scope;
- outcome, exposure, mechanisms, confounders, moderators, and context;
- objective, subjective, administrative, experimental, observational, and multimodal requirements;
- privacy, licensing, compute, registration, and language constraints.

Use `schemas/research_request.schema.json` for structured requests.

## Separate authority from task fit

Assess source-intrinsic quality independently from the current question.

Intrinsic assessment includes authority role, originality, methodology transparency, quality control, comparability, coverage, timeliness, reproducibility, academic adoption, and access.

Task fit includes construct, population, observation unit, time, geography, granularity, design, joinability, coverage, access, reproducibility, and bias risk.

Do not combine both into one unexplained prestige score.

## Recommendation states

Label every proposed source or variable as:

- `verified_available`
- `partially_verified_available`
- `reported_available_unverified`
- `constructible_from_fields`
- `proxy_candidate`
- `conceptually_required_not_found`
- `incompatible`
- `access_unknown`

An empty search result means `not_found_in_registry_snapshot`, not `does_not_exist`.

## Minimum output

Return:

- registry version;
- interpretation of the question;
- empirical requirements;
- candidate sources, datasets, and variables;
- source authority and task-fit evidence;
- proposed source combinations;
- compatibility and join-key findings;
- missing variables and dimensions;
- recommended supplements or alternative measures;
- access, license, and governance constraints;
- provenance, citation, and uncertainty.

## Integrity requirements

- Do not fabricate coverage, variables, identifiers, endpoints, versions, or licenses.
- Do not infer variable availability from source-level topic tags.
- Do not present a proxy as a direct measure.
- Do not treat modeled estimates as raw observations.
- Do not treat a repository or aggregator as the original producer without evidence.
- Do not merge sources solely on labels when identity or provenance differs.
- Do not bypass authentication, payment, consent, ethics review, or data-use agreements.
- Do not equate a catalog record with row-level access.

## Delivery interfaces

Expose the same semantics through:

- a local, versioned registry and index;
- CLI;
- Python SDK;
- MCP server for Codex, Claude, and other agents;
- optional HTTP services.

Keep live source retrieval separable from the readable offline registry.
