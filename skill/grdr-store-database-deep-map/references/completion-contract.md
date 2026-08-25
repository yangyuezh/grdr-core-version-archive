# Strict Storage Completion Contract

Step 3 is complete only when all of the following hold:

1. the Plan, scope, and work-unit locks remain current;
2. Execute is fully closed and its staging package is sealed;
3. the internal canonical archive receipt is valid;
4. the snapshot manifest inherits the exact Plan knowledge scope and states observation replication, completeness, and placement separately;
5. the complete knowledge artifact exists and contains no declared raw-observation path;
6. knowledge and observations share zero content hashes, and Release assets have disjoint logical memberships;
7. full mirrors contain nonzero files and match the declared file denominator; partitioned mirrors additionally preserve and match the partition manifest; federated snapshots contain zero local observation inputs and identify the official upstream;
8. the Agent SQLite index and source runtime exist in the Release and Elements, and the sealed runtime audit proves every indexed Variable resolves with zero unresolved Variables;
9. every copied logical file has an exact SHA-256, size, and location list;
10. every declared Release, Elements, and mounted object-store inventory matches the manifest exactly;
11. the private source Git repository contains its config, adapters, Plan, manifest, README, tests, and canonical archive receipt;
12. the GitHub Release repository, tag, commit, URL, asset names, sizes, and hashes have been verified;
13. `storage_receipt.json` is valid and stored with the Release and Elements snapshot;
14. the GRDR central `source_archives.jsonl` card identifies the same repository, latest snapshot, Release, Core version, knowledge fingerprint, observation fingerprint, snapshot profile, and logical fingerprint.

The following are explicitly incomplete:

- a mirror mode with zero observation rows or a false denominator;
- a federated mode without an official route or fully resolvable runtime;
- a knowledge archive containing an original observation file;
- the same logical file stored in multiple Release assets;
- a declared location whose files, sizes, or hashes do not match;
- uploaded assets without read-back verification;
- a source repository that copies GRDR Core;
- a metadata manifest that claims files not present at the named locations;
- a canonical archive receipt without a final Storage receipt;
- an Agent index without a callable source runtime, or a runtime audit with unresolved Variables.
