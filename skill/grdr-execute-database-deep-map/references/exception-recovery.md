# Exception and Recovery Playbook

Failures are state, not reasons to abandon the project or invent completion. Record the smallest affected scope, keep independent work moving, and return a deterministic recovery action.

| Condition | Record | Continue | Never do |
|---|---|---|---|
| Timeout, transient server error, rate limit | retryable `technical` or `rate_limit` blocker, timestamp, route, response | metadata, documentation, cached lawful manifests; retry with bounded backoff | treat one failure as permanent absence |
| Endpoint or format failure | `alternative_route` blocker and tested fallback | official bulk file, catalog, schema, mirror only if provenance is explicit | assume fallback content is identical |
| Authentication, application, payment, license | authorization blocker and official procedure | public metadata, methods, codebooks, access documentation | create accounts, accept terms, pay, or self-authorize beyond scope |
| Privacy, ethics, security, sovereignty | human-decision blocker and required gate | public metadata and non-sensitive structure where authorized | expose records, infer consent, or approve the gate as an Agent |
| Missing or contradictory metadata | `missing_metadata` or `semantic_ambiguity` blocker | preserve source-native elements and conflicting evidence | promote ambiguous elements to Variables/Constructs |
| Unknown or proprietary format | `format` blocker, file signature/version, lawful sample, decoder provenance | manifests, documentation, vendor metadata, `open_world_custom` | reverse engineer unlawfully or present inferred fields as official |
| Very large store | `scale` blocker or partition plan | stable ranges, manifests, checksums, bounded probes | mirror the full store when metadata enumeration suffices |
| Schema/version drift | drift blocker, before/after fingerprints, affected units/facets | unaffected units; create a new boundary or reopen affected work | combine incompatible vintages silently |
| Deleted or ephemeral objects | lifecycle evidence, tombstone/deletion state, retrieval date | remaining objects and deletion-aware counts | remove the item from an exhaustive denominator |
| Mixed producers or mirrors | provenance blocker per work unit | independently verified units | transfer authority, license, or method claims across producers |
| AI-derived semantic proposal | `needs_human_review` when consequential | retain 5A elements and evidence-linked candidate mapping | label AI inference as source-authored semantics |

## Recovery sequence

1. Capture the exact operation, target, time, response or observed state, and evidence.
2. Type recoverability: `retryable`, `alternative_route`, `requires_authorization`, `requires_human_decision`, `upstream_only`, or `unknown`.
3. State the next lawful action and success criterion.
4. Record the check update; do not close the related stage if its required obligation remains open.
5. Continue all independent queue targets.
6. Re-test after the stated external condition changes.

If diagnosis itself changes, regenerate and audit the plan before changing route obligations. Preserve old evidence and explain which checks must reopen. Do not hand-edit `checks.jsonl` to make an error disappear.
