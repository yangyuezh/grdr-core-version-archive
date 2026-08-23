# Release Process

Every completed functional or contract-changing development batch produces a new version and is published to GitHub. Documentation-only corrections may be committed to `main` without changing `VERSION`; they do not move or recreate an existing immutable tag.

## Versioning

Use Semantic Versioning:

- patch: fixes, evidence corrections, and compatible metadata improvements;
- minor: new source batches, schemas, commands, matching capabilities, or compatible interfaces;
- major: incompatible schema, protocol, or storage changes.

README wording, diagram layout, spelling, and link-only corrections do not require a version bump when they change no executable behavior, schema, Skill contract, or packaged artifact. If a released tag must contain those documentation changes exactly, publish a new patch version rather than moving the old tag.

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
