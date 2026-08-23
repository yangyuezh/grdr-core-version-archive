# GRDR Access, State, and Distributed Storage Architecture

GRDR separates immutable execution code from mutable database knowledge and observation artifacts.

## Immutable Core

GRDR Core contains only shared Skills, schemas, route contracts, programs, empty Registry filename templates, validators, tests, and documentation. Core never stores a real Source, Dataset, Variable, source-archive card, project, adapter, or observation file.

Configure an installed clone once with `python3 scripts/configure_core.py`, or set `GRDR_ROOT` explicitly. The six Skill launchers then locate the same Core without assuming a working directory or machine-specific path.

## External mutable state

`GRDR_STATE_ROOT` identifies the mutable operational state and defaults to `~/.grdr`. It contains:

- `registry/`: canonical records and completed source-archive cards;
- `deep_map_projects/`: locked Plan and resumable Execute/Storage projects;
- `research_projects/`: indicator and semantic-resolution projects;
- `elements/`: the default expanded snapshot root when `GRDR_ELEMENTS_ROOT` is unset.

`GRDR_STATE_ROOT` must resolve outside the Core repository. Storage must leave every Core file byte-identical.

## Six content layers and access sidecars

The database content model remains:

1. Institution;
2. Source;
3. Dataset;
4. recursive DataStructure;
5. 5A DataElement and 5B Variable;
6. Construct, positioned through the multi-parent scientific-semantic spine.

Resource, Evidence, Verification, adapters, authentication, license, rate limits, and access methods are cross-cutting sidecars rather than content layers.

## Distributed snapshot topology

- One deeply stored Source owns one private source repository.
- One snapshot owns one GitHub Release containing complete knowledge, Agent Runtime, observations, manifest, and receipt.
- The same snapshot owns one expanded Elements directory with identical logical files and SHA-256 values.
- External central state owns the latest-snapshot card used for cross-source discovery.
- Source repositories reference a Core version; they never copy Core Skills.

Storage may promote sealed records into external state after validation. It must never promote them into the immutable Core checkout.
