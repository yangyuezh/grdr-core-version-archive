# Curation Standard

## Record lifecycle

```text
nominated → identity_checked → partially_verified → verified → monitored
                                                        ↓
                              stale / conflicted / deprecated / unavailable
```

Automated discovery may nominate records. Promote them only after checking suitable evidence.

## Evidence priority

Prefer, in order appropriate to the claim:

1. official mandate or governance documentation;
2. official data catalog and dataset record;
3. official methodology, codebook, dictionary, or standard;
4. official API, download, access, and license documentation;
5. data papers and peer-reviewed validation;
6. credible secondary material for discovery only.

Do not use search snippets as final evidence when the primary document is available.

## Minimum source record

Capture canonical name and URL, maintainer, source class, disciplines and topics, authority role, provenance position, access modes, machine access, license status, verification status, review interval, and supporting evidence.

## Minimum dataset record

Capture parent source, scope, population, observation unit, spatial and temporal coverage, modality, release and revision information, methodology, limitations, access resources, citation, and evidence.

## Minimum deep-map chain

Use `$grdr-deep-map-database` to recover a Dataset's native DataStructure before registering DataElements and research-matchable Variables. Keep APIs, files, authentication, and licenses as access Resources attached to the content chain; never substitute them for the database-internal structure.

## Unknowns and conflicts

Use explicit unknown or null values. Never convert missing metadata into a negative claim. Preserve conflicting evidence and mark the record `conflicted` until adjudicated.

## Authority

Assess authority by domain and role. Separate original production, statutory mandate, official harmonization, scientific curation, repository stewardship, commercial production, and derivative aggregation.

## Required validation

After edits, run the registry validator and tests. Confirm unique IDs, valid schemas, valid foreign keys, and explicit evidence for promoted claims.
