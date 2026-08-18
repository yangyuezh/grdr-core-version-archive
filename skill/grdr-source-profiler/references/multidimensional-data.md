# Multidimensional Data Profiling

## Why structure comes before variables

Many authoritative statistical systems do not expose a flat table. They expose a cube whose observation value is meaningful only after selecting dimensions such as area, commodity, transaction, indicator, unit, frequency, and time. Flattening the cube directly into a list of labels loses identity, units, join keys, and comparability boundaries.

Within GRDR layer 5, keep two linked representations:

1. **5A DataElement** mirrors the upstream structure.
2. **5B Variable** is a research-matchable operational variable defined by a measure plus required dimension selections.

Example:

```text
OBS_VALUE
+ REF_AREA=<country>
+ COMMODITY=<energy product>
+ TRANSACTION=GA (Total energy supply)
+ TIME_PERIOD=<year>
+ UNIT_MEASURE=<unit>
= research variable: Total energy supply by country, commodity, and year
```

## SDMX route

1. Enumerate dataflows and record the dated count.
2. Resolve each selected dataflow to its Data Structure Definition (DSD).
3. Register dimensions, time dimensions, primary measures, and attributes as DataElements.
4. Resolve referenced codelists and retain agency, ID, version, and code count.
5. Identify which dimension codes produce meaningful research variables.
6. Create Variable records that point to the measure element and list their exact dimension selections.
7. Retain unit, multiplier, status, confidentiality, conversion, and footnote attributes needed to interpret observations.
8. Test metadata and observation endpoints separately; a working DSD does not prove that data queries work.

The completion gate is mechanical: without a resolved measure element and at least one meaning-bearing dimension selection, retain the candidate only as 5A structure metadata. Record separate 5A and 5B counts and boundaries in `source_profile.layer_5_details`.

## Other multidimensional systems

- **DCAT/data catalogs:** catalog → dataset → distribution/resource → schema/field.
- **JSON/JSON Schema:** object → nested property/array → field constraints and enumerations.
- **Relational systems:** database → schema → table/view → column/key/constraint.
- **Questionnaires:** study → instrument → section → question/item → response codes and derived variables.
- **Scientific arrays:** collection → granule/file → group → dimension/coordinate → data variable → quality flags.

Preserve upstream identifiers and ordering even when GRDR adds normalized labels. Do not infer a variable from a source topic, and do not claim exhaustive variable coverage merely because the structural metadata has been parsed.
