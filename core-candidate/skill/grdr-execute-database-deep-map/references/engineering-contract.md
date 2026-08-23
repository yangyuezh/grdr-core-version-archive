# GRDR Deep-Map Engineering Contract

## Hard guarantees inside GRDR

For an executable deep-map project, the Agent must be able to stop at any bounded batch and continue without reconstructing intent from conversation. The machine state, not prose memory, is authoritative.

1. **Diagnose first.** A database with unresolved critical identity, structure, provenance, boundary, denominator, authorization, or lifecycle facts cannot enter execution as `ready`.
2. **Lock intent.** `project.json` stores SHA-256 fingerprints of the audited plan and declared scope. `units.jsonl` stores the stable work-unit universe whose manifest fingerprint is also locked.
3. **Reject drift.** Audit recomputes all three fingerprints. A silent change to plan, boundary, denominator, unit identity, order, or route assignment is an error, not an update.
4. **Issue one deterministic next target.** Queue order is stable. A graph-spine task is not actionable until its prerequisite content stages are mapped. An Agent may not substitute an easier unit, stage, spine, or check.
5. **Checkpoint native enumeration.** Every open content stage and graph spine preserves the source-native universe, ordering rule, completed count, last item, next item, snapshot/version, and checksum needed to resume.
6. **Write recoverably.** Step 2 writes only project-local staging and ledgers through atomic operations. A rejected update is rolled back. A high-cardinality execution batch may combine schema-valid phase, stage, spine, and check updates into one audited transaction, but it cannot stage records, alter locks, skip obligations, or write canonical state. After interruption, audit runs before new work and the same locked queue determines continuation.
7. **Prove both trunks and the bridge.** Counts alone do not complete a unit. Connected node and relationship sets, roots, leaves, topology fingerprints, ownership checks, and canonical verification counts must close the source-native structure spine, scientific-semantic spine, and variable bridge.
8. **Close database-shape obligations.** Route checks remain separate from entity counts and graph closure. A statistical cube, survey, experiment, graph, corpus, array, simulation, clinical system, or other shape must discharge its own contract.
9. **Use evidence, never assertion.** Machine closure requires evidence, reproducible denominators, valid staged candidate IDs, current schemas, and zero unresolved blockers.
10. **Execution readiness is not completion.** Only Step 3 archival with a valid receipt declares completion. Human prose, a populated sample, a high progress percentage, or a successful access probe cannot do so.

## External boundary

GRDR cannot guarantee facts or observations that the upstream system does not lawfully expose, does not document, has removed, changes outside a fixed window, or cannot define as a finite universe. The hard guarantee is that GRDR will not hide that condition: it records the smallest truthful blocker or bounded completion claim, preserves all independently completable work, and refuses a false complete state.

## Required recovery sequence

After a process interruption, model change, or handoff:

```bash
python3 "$GRDR_LAUNCHER" audit-database-deep-map-execution <project>
python3 "$GRDR_LAUNCHER" database-deep-map-status <project>
python3 "$GRDR_LAUNCHER" resume-database-deep-map <project>
```

If audit reports lock drift, do not overwrite the lock. Compare the current plan, scope, and manifest with the recorded fingerprints. A legitimate scope change starts a new bounded pass or uses an explicit migration operation with its own history and tests.
