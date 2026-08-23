# Release Process

Every completed development batch produces a new version and is published to GitHub.

## Versioning

Use Semantic Versioning:

- patch: fixes, evidence corrections, and compatible metadata improvements;
- minor: new source batches, schemas, commands, matching capabilities, or compatible interfaces;
- major: incompatible schema, protocol, or storage changes.

The canonical version is stored in `VERSION`.

## Required release steps

1. Complete one coherent development batch.
2. Update `VERSION`.
3. Add a dated entry to `CHANGELOG.md`.
4. Create `.venv` if needed, install `requirements-validation.txt`, and run the strict registry validator and all tests with `.venv/bin/python`.
5. Inspect the Git diff and stage only GRDR files.
6. Commit with the version and concise scope.
7. Create an annotated `vX.Y.Z` Git tag.
8. Push the branch and tag to GitHub.
9. Create or update the GitHub release or pull request for that version.
10. Report the version, commit, tag, validation results, and GitHub URL.

Do not publish a version when required validation fails. Do not include unrelated workspace files.
