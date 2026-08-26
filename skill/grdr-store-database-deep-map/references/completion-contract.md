# Strict Storage Completion Contract

Step 3 is complete only when all of the following hold:

1. the Plan, scope, and work-unit locks remain current;
2. Execute is fully closed and its staging package is sealed;
3. the internal canonical archive receipt is valid;
4. the snapshot manifest inherits the exact Plan knowledge scope and states online access, observation replication, completeness, and placement separately;
5. the complete knowledge artifact exists and contains no declared raw-observation path;
6. knowledge and observations share zero content hashes, and Release assets have disjoint logical memberships;
7. full mirrors contain nonzero files and match the declared file denominator; partitioned mirrors additionally match every partition boundary, member path, size, SHA-256, and denominator in the Schema-valid partition manifest; no-mirror snapshots contain zero observation inputs and zero replication placements;
8. the Agent SQLite index and source Runtime 2.0 exist in the GitHub Release, and the sealed offline runtime audit proves every indexed Variable resolves with zero unresolved Variables;
9. `online_access.json` declares official availability, tested routes, and latest/reproducible/offline policies; `online_runtime_audit.json` proves every indexed Variable maps to one or more ready routes and reports zero unresolved online Variables;
10. `invocation_acceptance_audit.json` proves a real registered Variable passed a Core-standard parameterized `latest` fetch with nonzero rows and output artifacts; when an offline route exists it proves an `offline` fetch too;
11. every copied logical file has an exact SHA-256, size, and location list;
12. every declared Release and mounted object-store inventory matches the manifest exactly; an optional local cache is not a declared canonical location;
13. the private source Git repository contains its config, adapters, Plan, manifest, README, tests, and canonical archive receipt;
14. the GitHub Release repository, tag, exact commit, URL, asset names, sizes, and hashes have been verified;
15. `storage_receipt.json` is valid, uploaded to the Release, read back with the exact hash, and only then stored in local project state;
16. the GRDR central `source_archives.jsonl` card identifies the same repository, latest snapshot, Release, Core version, knowledge fingerprint, observation fingerprint, snapshot profile, online access, Runtime protocol, and logical fingerprint.

The following are explicitly incomplete:

- a mirror mode with zero observation rows or a false denominator;
- any registered Variable without a tested online route;
- any nonempty Variable index without a passing Core-driven parameterized invocation probe, or any mirrored snapshot without a passing offline probe;
- a no-mirror mode that declares observation inputs or replication placements;
- a knowledge archive containing an original observation file;
- the same logical file stored in multiple Release assets;
- a declared location whose files, sizes, or hashes do not match;
- uploaded assets without read-back verification;
- a source repository that copies GRDR Core;
- a metadata manifest that claims files not present at the named locations;
- a canonical archive receipt without a final Storage receipt;
- an Agent index without a callable source Runtime 2.0, an offline runtime audit with unresolved Variables, or an online runtime audit with unresolved online Variables.
