---
name: grdr-resolve-research-semantics
description: Resolve GRDR research indicators through the persisted scientific-semantic B spine to callable A-side variables, data elements, structures, datasets, and official source runtimes. Use when a persisted GRDR research project already has leaf indicators from a topic scaffold or literature-grounded Indicator Builder and Codex must perform full-text candidate recall, evidence-constrained ResearchIndicator-to-Construct/SemanticNode alignment, auditable multi-hop graph traversal, variable-fit classification, match explanation, data-gap diagnosis, or indicator-scoped official data invocation.
---

# GRDR Research Semantic Resolver

## Preserve the boundary

Treat this Skill as the GRDR use-plane bridge:

```text
R: ResearchQuestion / ResearchIndicator
  -> persisted R-to-B semantic alignment
B: stored SemanticNode / Construct spine
  -> stored B-to-A graph relationships
A: Variable / DataElement / DataStructure / Dataset
  -> verified source runtime
official data
```

Use the B created by Plan -> Execute -> Storage. Never create a second B, write project judgments into `registry/*.jsonl`, or promote a missing construct into canonical Storage. Keep candidate recall, alignments, paths, and mappings under the research project.

Use `$grdr-indicator-builder` first when the research question has not yet been converted into leaf indicators. Use this Skill only after a persisted project contains `indicators.jsonl`.

## Locate Core

Resolve the absolute directory containing this active `SKILL.md`, then set `GRDR_LAUNCHER` to its bundled `scripts/grdr.py`. It finds Core through `GRDR_ROOT`, the portable Codex pointer, current ancestors, or a bundled checkout and selects Core's `.venv/bin/python` when present. Skipped JSON Schema validation is a failure:

```bash
python3 "$GRDR_LAUNCHER" <command> ...
```

## Run the five-layer resolver

### 1. Recall full-text B candidates

Read every leaf indicator's name, definition, synonyms, operational specification, and evidence. Generate multilingual or disciplinary query expansions when the registry terminology differs. Optional query JSONL records contain only:

```json
{"indicator_id":"grdr:research-indicator:example-leaf","query_terms":["energy dependence","fossil fuel share","能源依赖"]}
```

Run:

```bash
python3 "$GRDR_LAUNCHER" prepare-semantic-candidates <project> --queries <queries.jsonl>
```

Without `--queries`, Core derives terms from the indicators. Candidate recall searches Construct, SemanticNode, and Variable full text across central and callable distributed indexes; Variable hits resolve back to B targets. Treat `semantic_candidates.jsonl` as recall only, never as a semantic conclusion.

### 2. Align R to the existing B

Read [references/semantic-alignment-contract.md](references/semantic-alignment-contract.md) completely before deciding alignments. Compare the research definition and operational requirement with the stored target definition, source-bounded scope, evidence, measurement meaning, population, unit, denominator, time, and space.

Write one decision JSONL file following [references/alignment-decisions.example.jsonl](references/alignment-decisions.example.jsonl). Every leaf requires exactly one `primary` decision. Prefer a Construct target for an operational leaf; use SemanticNode targets for justified broader routing. Use `no_match` when no candidate has defensible semantic correspondence. Do not align on label similarity alone.

Run:

```bash
python3 "$GRDR_LAUNCHER" align-research-indicators <project> <decisions.jsonl>
```

This creates `semantic_alignments.jsonl`. Non-exact relations and SemanticNode targets remain contested Agent candidates; the Agent must not approve them on the human's behalf.

### 3. Traverse B to A

Run:

```bash
python3 "$GRDR_LAUNCHER" traverse-semantic-paths <project>
```

Persist every valid route in `semantic_paths.jsonl`, including alignment, SemanticNode, Construct, Variable, DataElement, DataStructure, Dataset, source snapshot, relationship edges, callability, and fingerprint. An alignment with no path is unresolved; do not invent a Variable link.

### 4. Judge variable fit and persist mappings

For the first attempt run:

```bash
python3 "$GRDR_LAUNCHER" match-indicators <project>
```

After rebuilding recall against expanded or updated snapshots, run:

```bash
python3 "$GRDR_LAUNCHER" rerun-matching <project>
```

The matcher evaluates construct, population, unit, time, and space and emits only the existing GRDR mapping outcomes. `proxy_candidate` and `definition_conflict` require the contested-mappings human gate. `not_found_registry_snapshot` means only that the current distributed registry has no defensible path.

Explain one result with:

```bash
python3 "$GRDR_LAUNCHER" explain-indicator-match <project> <indicator-id>
```

The explanation must expose recall, alignment decision, graph edges, selected variable, fit, snapshot, and uncertainty rather than return an opaque score.

### 5. Invoke official data through the selected path

Resolve a single-variable mapping through its verified source runtime:

```bash
python3 "$GRDR_LAUNCHER" fetch-indicator-data <project> <indicator-id> --dry-run
```

Add source-supported country, period, output, or timeout arguments when needed. For composite mappings, select each mapped `--variable-id` explicitly and retain the approved transformation formula. Refuse to invoke an unapproved contested mapping. Preserve returned source, snapshot, Variable, alignment, path, and upstream provenance.

## Recover and expand

Use `--replace` only to rebuild the corresponding candidate, alignment, or path snapshot deliberately. Rebuilding candidates invalidates later semantic artifacts. After `not_found_registry_snapshot`, use `$grdr` to expand from data gaps or deepen candidate sources through the three-step database factory, then rebuild:

```text
prepare-semantic-candidates --replace
  -> align-research-indicators --replace
  -> traverse-semantic-paths --replace
  -> rerun-matching
```

Never bypass authentication, payment, consent, ethics review, data-use agreements, rate limits, or source access controls.

## Completion contract

Report semantic resolution complete only when:

- every leaf has exactly one primary persisted R-to-B decision;
- every non-`no_match` selected alignment has a stored B-to-A path or is explicitly unresolved;
- every leaf has a schema-valid mapping outcome;
- every selected variable is tied to an exact source snapshot and provenance path;
- contested mappings remain human-gated;
- official invocation is callable or its concrete access blocker is reported;
- `research-project-status` contains no semantic-file validation errors.
