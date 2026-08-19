# Strict Database Completion Contract

## What 100% means

GRDR may claim 100% only inside an explicit, dated boundary. Every upstream work unit in that boundary must be present in the ledger, and every required stage must be either `verified_complete` or evidenced as `not_applicable`.

The claim itself must be named: `representative_only`, `question_fit`, `catalog_only`, `bounded_partition`, `exhaustive_snapshot`, or `rolling_current`. “100%” without the claim and boundary is invalid.

The following are not completion:

- one representative six-layer chain;
- all Dataset names registered but internal structures missing;
- a schema parsed but code lists or variables sampled;
- all objects mapped but verification incomplete;
- a working metadata endpoint with observation access untested;
- an inaccessible item omitted from the denominator;
- an unknown expected count;
- an Agent assertion without reproducible enumeration evidence.
- all six stages closed while one or more route-contract facets remain open;
- unresolved or Agent-self-approved human gates;
- a rolling window presented as all-time coverage;
- a stale plan whose route-contract version no longer matches the registry.

## Stage gates

For `mapped_complete`:

1. `expected_count` is known;
2. `registered_ids` contains exactly that number of canonical records;
3. the completion basis describes how the universe was enumerated;
4. evidence supports the boundary and count.

For `verified_complete`, all mapped gates apply and `verified_count == expected_count`.

For `not_applicable`, expected count is zero, no IDs are registered for the stage, and evidence demonstrates why the stage does not apply. Convenience is not non-applicability.

For `blocked`, list the exact legal, ethical, access, authentication, payment, technical, metadata, or scale condition. Blocked work remains outside strict completion.

## Route-check gates

Every applicable facet materialized in `checks.jsonl` must be `passed` or evidenced `not_applicable`. A unit-scoped check cannot close before the associated unit stage is at least mapped. The check's requirement, scope, stage, and route membership must match the active route registry; hand-edited or deleted obligations fail audit.

`failed`, `blocked`, and `needs_human_review` remain open. A fallback route may produce new evidence, but it does not erase the original obligation until equivalence or non-applicability is evidenced.

## Project gates

Before `complete-database-deep-map`:

- source identity and primary/secondary provenance are verified;
- database shape and route classification are verified;
- the diagnostic plan is `ready`, matches the current route-contract version, and has no unresolved critical dimensions;
- boundary and snapshot are reproducible;
- work-unit count equals the expected count;
- all required unit stages are closed;
- no required stage is blocked;
- every required route-contract check is passed or evidenced not applicable;
- every human gate is resolved by a named human, with no rejection;
- all registered IDs exist and have the correct entity type;
- canonical registry validation passes with the `jsonschema` package present; a skipped Schema pass is not strict validation;
- the generated catalog is current.

Git records versions; the current project files describe the current snapshot. A later upstream release, schema fingerprint change, rolling window, or federation-membership change starts a new bounded pass or explicitly updates the boundary and reopens affected stages and checks.
