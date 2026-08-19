# Strict Database Completion Contract

## What 100% means

GRDR may claim 100% only inside an explicit, dated boundary. Every upstream work unit in that boundary must be present in the ledger, and every required stage must be either `verified_complete` or evidenced as `not_applicable`.

The following are not completion:

- one representative six-layer chain;
- all Dataset names registered but internal structures missing;
- a schema parsed but code lists or variables sampled;
- all objects mapped but verification incomplete;
- a working metadata endpoint with observation access untested;
- an inaccessible item omitted from the denominator;
- an unknown expected count;
- an Agent assertion without reproducible enumeration evidence.

## Stage gates

For `mapped_complete`:

1. `expected_count` is known;
2. `registered_ids` contains exactly that number of canonical records;
3. the completion basis describes how the universe was enumerated;
4. evidence supports the boundary and count.

For `verified_complete`, all mapped gates apply and `verified_count == expected_count`.

For `not_applicable`, expected count is zero, no IDs are registered for the stage, and evidence demonstrates why the stage does not apply. Convenience is not non-applicability.

For `blocked`, list the exact legal, ethical, access, authentication, payment, technical, metadata, or scale condition. Blocked work remains outside strict completion.

## Project gates

Before `complete-database-deep-map`:

- source identity and primary/secondary provenance are verified;
- database shape and route classification are verified;
- boundary and snapshot are reproducible;
- work-unit count equals the expected count;
- all required unit stages are closed;
- no required stage is blocked;
- all registered IDs exist and have the correct entity type;
- canonical registry validation passes with the `jsonschema` package present; a skipped Schema pass is not strict validation;
- the generated catalog is current.

Git records versions; the current project files describe the current snapshot. A later upstream release starts a new bounded pass or explicitly updates the snapshot and reopens affected stages.
