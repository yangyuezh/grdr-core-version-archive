# Strict Storage Completion Contract

Step 3 is complete only when all of the following hold:

1. the Plan, scope, and work-unit locks remain current;
2. Execute is fully closed and its staging package is sealed;
3. the internal canonical archive receipt is valid;
4. at least one actual observation file with nonzero total bytes is present;
5. the complete knowledge artifact exists;
6. the Agent SQLite index and source runtime exist in both representations, and the sealed runtime audit proves that every indexed Variable resolves with zero unresolved Variables;
7. every logical file has an exact SHA-256 and size;
8. Release archive membership expands to exactly the Elements logical inventory;
9. the private source Git repository contains its config, adapters, Plan, manifest, README, tests, and canonical archive receipt;
10. the GitHub Release repository, tag, commit, URL, asset names, sizes, and hashes have been verified;
11. `storage_receipt.json` is valid and stored with the Release and Elements snapshot;
12. the GRDR central `source_archives.jsonl` card identifies the same repository, latest snapshot, Release, Core version, and logical fingerprint.

The following are explicitly incomplete:

- a deep-map archive containing zero observation rows;
- an Elements-only copy;
- uploaded assets without read-back verification;
- a GitHub Release without the expanded Elements counterpart;
- a source repository that copies GRDR Core;
- a metadata manifest that claims files not present in the artifacts;
- a canonical archive receipt without a final Storage receipt.
- an Agent index without a callable source runtime, or a runtime audit with unresolved Variables.
