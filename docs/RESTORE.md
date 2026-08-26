# Restore and compare archived versions

## Inspect one version

```bash
git show audit/v1.0.0:VERSION
git show --stat audit/v3.4.0
git ls-tree -r --name-only audit/v4.5.0
```

## Export one exact source tree

```bash
git archive --format=tar.gz \
  --output=grdr-core-v4.5.0.tar.gz \
  audit/v4.5.0
```

For the historical `v4.0.0` candidate, `audit/v4.0.0-candidate` points to an audit extraction commit whose root tree is byte-identical to `core-candidate/` in the recorded UNdata source commit. The ledger preserves both identifiers.

## Compare releases

```bash
git diff --stat audit/v3.1.0 audit/v3.2.0
git diff --stat audit/v4.4.0 audit/v4.5.0
```

## Preserve the complete audit database

Clone all branches and tags, not only `main`:

```bash
git clone --mirror git@github.com:yangyuezh/grdr-core-version-archive.git
```

Run `python3 scripts/audit_archive.py` after cloning into a normal working tree to verify the committed ledger.
