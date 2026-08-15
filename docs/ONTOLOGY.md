# Registry Ontology

## Entity hierarchy

GRDR models research data at multiple levels:

```text
Institution
  └── Source
        └── Dataset
              └── Resource
                    └── Variable
                          └── Construct
```

The hierarchy expresses containment, not provenance. Provenance and other semantics are represented by typed relationships.

## Entity definitions

### Institution

An organization or durable collaboration that produces, maintains, publishes, funds, or governs data. Examples include statutory statistical offices, intergovernmental organizations, scientific consortia, universities, companies, and archives.

### Source

A recognizable data service, portal, repository, program, collection, or database family maintained over time. A source can contain multiple datasets and access systems.

### Dataset

A versionable collection of observations produced under a defined methodology and scope. Dataset records are planned after the foundation source registry stabilizes.

### Resource

A concrete access object such as an API endpoint, downloadable file, table, database view, cloud bucket, query service, or application procedure.

### Variable

A recorded or computable field with a definition, unit, population, observation unit, coverage, and measurement method.

### Construct

A theoretical or substantive concept that may have one or more operational measurements. Examples include socioeconomic status, biodiversity, temperature, institutional trust, gene expression, and firm productivity.

### Relationship

A typed edge between registry entities, qualified by evidence, dates, and verification state.

## Required distinctions

GRDR must preserve these distinctions:

- producer versus publisher;
- source versus dataset;
- dataset versus access resource;
- variable versus theoretical construct;
- direct measure versus proxy;
- reported value versus modeled estimate versus forecast;
- objective measurement versus subjective response;
- public access versus machine access;
- institutional authority versus task fitness;
- missing metadata versus confirmed absence.

## Controlled relationship types

Initial relationship types are:

- `produced_by`
- `maintained_by`
- `published_by`
- `funded_by`
- `governed_by`
- `contains`
- `derived_from`
- `harmonizes`
- `mirrors`
- `supersedes`
- `replaced_by`
- `documents`
- `measures`
- `proxy_for`
- `joinable_with`
- `complements`
- `overlaps_with`
- `cites`

Relationships such as `joinable_with` must specify the proposed keys and compatibility limitations. They are not implied merely because two datasets share a country name or calendar year.

## Observation dimensions

Dataset and variable records should describe dimensions using controlled fields:

- unit of analysis;
- population or universe;
- entity identifiers;
- spatial coverage and resolution;
- temporal coverage and resolution;
- sampling or census status;
- modality;
- measurement type;
- aggregation level;
- data-generating process;
- release and revision vintage.

Example units include country-year, region-month, facility-day, person-wave, household, firm-year, transaction, event, document, scholarly work, biological sample, species occurrence, image tile, sensor reading, and genomic sequence.

## Evidence model

Every material claim may include one or more evidence objects:

```json
{
  "url": "https://example.org/methodology",
  "title": "Official methodology",
  "publisher": "Example institution",
  "evidence_type": "official_methodology",
  "supports": ["coverage", "methodology", "update_frequency"],
  "retrieved_at": "2026-08-14T00:00:00Z",
  "archived_url": null,
  "quote": null
}
```

Preferred evidence order depends on the claim, but normally favors official methodology, official catalog records, technical documentation, data papers, and peer-reviewed validation. Search snippets and third-party summaries can nominate a record but should not establish high-confidence claims.

## Verification states

- `unverified`: discovered but not checked against an authoritative source;
- `partially_verified`: identity and primary URL checked, other claims incomplete;
- `verified`: required claims checked against suitable evidence;
- `stale`: last verification exceeds the relevant refresh interval;
- `conflicted`: credible evidence disagrees;
- `deprecated`: upstream source is retired or replaced;
- `unavailable`: access was confirmed unavailable at the latest check.

Unknown fields remain `null` or an explicit `unknown` enum. Empty values must not be interpreted as negative claims.

