# Composable Route Contracts

## Fixed stages, adaptable obligations

Every work unit keeps the same six stages, source-native structure spine, scientific-semantic spine, and variable bridge. Route contracts add database-shape-specific obligations to those stages, graph products, and the project. `config/database_route_contracts.json` is the machine source of truth; do not copy a static route list into Agent logic.

```bash
python3 scripts/grdr.py list-database-route-modules
```

The registry includes a universal route plus composable modules for catalogs, files, tables, APIs, statistical cubes, surveys, administrative systems, geospatial data, scientific arrays, streams, biomedical and clinical systems, graphs, multimodal corpora, experiments, instrument measurements, simulations, physical collections, qualitative archives, scholarly communication, digital platforms, ML assets, software workflows, restricted access, secondary provenance, federations, legacy/proprietary systems, and unknown/custom structures.

Route modules also declare a `module_kinds` dimension. Structural templates, generation-process templates, disciplinary semantic extensions, access/lifecycle/governance/provenance sidecars, technical recovery, and open-world fallback are different axes; do not present them as one mutually exclusive taxonomy.

## Selection

- Select routes from observed structure and generating process, not the database name or research topic.
- A database and one work unit may use several routes.
- Project routes are the available contract set; unit routes are the subset that actually applies to that unit.
- `core_metadata` always applies.
- `open_world_custom` is a safe fallback, not a waiver of evidence or completion.
- Access and sensitivity routes supplement content routes; they do not replace them.

## Facets and checks

Each route contains facets with:

- stable facet ID;
- project or unit scope;
- associated stage;
- requirement;
- acceptable completion evidence;
- fallback routes and suggested inspection methods.

Starting a project materializes every applicable facet in `checks.jsonl`. A route check is independent of the stage count. For example:

- Stage: all declared DataElements have canonical IDs.
- Route check: an SDMX cube's ordered dimensions, codelists, attachment levels, units, multipliers, and flags were recovered.

Both must close. Use `passed` only with evidence and an explicit completion basis. Use `not_applicable` only when evidence shows the obligation truly does not apply. Use `blocked`, `failed`, or `needs_human_review` with a typed blocker and recovery path.

## Extending the route registry

When `open_world_custom` reveals a recurring source shape:

1. preserve observed facts and examples;
2. explain why existing route composition is insufficient;
3. define a reusable structural or generating-process contract, not a discipline label;
4. add narrowly testable facets and fallbacks;
5. validate the route registry Schema;
6. add positive, negative, and mixed-shape planner tests;
7. bump the route-contract version;
8. re-audit affected plans and reopen changed checks.

Never edit a generated plan merely to remove a difficult facet. The plan audit reconstructs expected facets from the route registry and rejects omissions.
