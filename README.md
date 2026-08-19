# Global Research Data Registry (GRDR)

GRDR is AI-agent-native, all-discipline infrastructure for global data-source registration, discovery, assessment, connection, and research design.

**Current status:** foundation, the first persistent database deep-mapping project, and the first executable research-question closed loop. The repository provides the evidence model, ontology, schemas, initial registry, Agent commands, all 36 UNdata datamarts, deep Energy/GHG multidimensional examples, a resumable work-unit ledger, strict completion gates, and persisted indicator matching with data-gap-driven source expansion. The immediate goal is a verified first-round registry of approximately 100 cross-disciplinary sources, followed by multi-round snowball expansion. See [North Star](docs/NORTH_STAR.md).

It is not primarily a website and does not initially copy every upstream dataset. It combines:

- a versioned data-source registry;
- a dataset and measurement knowledge graph;
- task-specific source-fit and data-gap assessment;
- stable interfaces for Codex, Claude, and other agents;
- optional adapters for representative sources with stable programmatic access.

Research-question matching, source combination, and data-gap diagnosis are central Agent capabilities built on top of the registry. Local snapshots and federated access are later extensions where licensing, privacy, cost, and scale permit.

## 数据库六层拆解

GRDR uses the dedicated `$grdr-deep-map-database` Skill to deep-read a registered database into Institution → Source → Dataset → DataStructure → 5A DataElement / 5B Variable → Construct records. `DataStructure` restores the database's own catalog, schema, table, dataflow, questionnaire, array, or other internal organization before variables are formed. API、CSV、下载、认证与许可作为 Resource 旁路挂接，不占第4层。The workflow declares whether a pass is representative, question-driven, priority-catalog, catalog-level, or exhaustive; one populated chain is never reported as a complete upstream inventory. See [the database deep-mapping protocol](docs/SOURCE_PROFILING_PROTOCOL.md).

Every nontrivial pass is now a persistent engineering project under `deep_map_projects/<source>/`. The workflow classifies primary/secondary origin, disciplinary and storage archetypes, fixes a dated work-unit universe, tracks six required stages per unit, reports mapped versus strictly verified progress, and rejects completion while any count is unknown or any required stage is open or blocked. See [the executable deep-map workflow](docs/DATABASE_DEEP_MAP_WORKFLOW.md).

```bash
python3 scripts/grdr.py database-deep-map-status deep_map_projects/undata
python3 scripts/grdr.py resume-database-deep-map deep_map_projects/undata
python3 scripts/grdr.py audit-database-deep-map deep_map_projects/undata
```

## 研究指标构建器

GRDR uses the dedicated `$grdr-indicator-builder` Skill to connect research questions and literature to the database registry. With a topic alone, the Agent can automatically generate an explicitly exploratory indicator scaffold. With a substantial literature corpus, it extracts section-level evidence, constructs a cited multi-level indicator hierarchy, operationalizes leaf indicators, and matches them to GRDR variables. See [the indicator-builder protocol](docs/INDICATOR_BUILDER_PROTOCOL.md).

AI performs document organization, evidence extraction, coding, synthesis, operationalization, registry retrieval, and mapping proposals. Human input is concentrated at two mandatory formal-research gates—corpus boundary and final indicator framework—and at a third conditional gate for proxy candidates or definition conflicts. The Agent never infers approval from silence.

Question-specific work remains separate from the canonical source registry:

```text
research_projects/<project-id>/
├── project.json
├── literature.jsonl
├── evidence_units.jsonl
├── indicators.jsonl
├── mappings.jsonl
├── workflow.json
└── data_gaps.jsonl
```

Audit a project with:

```bash
python3 scripts/grdr.py audit-indicator-project research_projects/<project-id>
python3 skill/grdr-indicator-builder/scripts/audit_project.py research_projects/<project-id>
```

## 研究项目闭环

The seven project commands turn an AI-generated topic scaffold into a persisted, resumable matching cycle. The Agent may automate scaffolding, direct matching, gap diagnosis, candidate-source retrieval, and rematching. `approve-human-gate` only records an approval explicitly supplied by a named human reviewer; the Agent must never call it on the reviewer's behalf.

```bash
python3 scripts/grdr.py start-research-project examples/population_energy_income_industry_co2_project.json
python3 scripts/grdr.py research-project-status population-energy-income-industry-co2
python3 scripts/grdr.py resume-research-project population-energy-income-industry-co2
python3 scripts/grdr.py match-indicators population-energy-income-industry-co2
python3 scripts/grdr.py expand-from-data-gaps population-energy-income-industry-co2
python3 scripts/grdr.py rerun-matching population-energy-income-industry-co2

# Only after an actual human decision:
python3 scripts/grdr.py approve-human-gate <project-id> indicator_framework \
  --reviewer "<name>" --notes "<explicit decision and scope>"
```

The first persisted test project is [population, energy, income, industrial structure, and CO2 emissions](research_projects/population-energy-income-industry-co2/README.md). It is intentionally marked `topic_scaffold`: three of five leaf requirements have direct registered-variable matches, while income per capita and industrial structure remain current-snapshot registry gaps that now drive bounded source-deepening work.

## 已收录数据库

<!-- GRDR_SOURCE_CATALOG_START -->
当前注册表共收录 **19** 个数据库/数据平台。每个数据库均有独立六层详情页；“待验证候选”仅表示已经登记，不表示其覆盖与使用条件已经核验。

| 数据库 | 发布/维护机构 | 主要领域 | 拆解范围 | 拆解阶段 | 严格完成度 | 验证状态 | 六层详情 |
|---|---|---|---|---|---:|---|---|
| [CERN Open Data Portal](https://opendata.cern.ch/) | European Organization for Nuclear Research | particle physics | `undeclared` | `source_only` | 0.0% | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/cern-open-data/README.md) |
| [Copernicus Climate Data Store](https://cds.climate.copernicus.eu/) | Copernicus Climate Change Service | climate science、earth science | `undeclared` | `source_only` | 0.0% | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/copernicus-climate-data-store/README.md) |
| [Eurostat Database](https://ec.europa.eu/eurostat/) | Eurostat | multidisciplinary | `undeclared` | `source_only` | 0.0% | 部分验证 (`partially_verified`) | [查看六层目录](catalog/sources/eurostat/README.md) |
| [FAOSTAT](https://www.fao.org/faostat/) | Food and Agriculture Organization of the United Nations | agriculture、food science、environmental science、economics | `undeclared` | `source_only` | 0.0% | 部分验证 (`partially_verified`) | [查看六层目录](catalog/sources/faostat/README.md) |
| [GBIF](https://www.gbif.org/) | Global Biodiversity Information Facility | biodiversity science、ecology、conservation biology | `undeclared` | `source_only` | 0.0% | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/gbif/README.md) |
| [ICPSR Data Archive](https://www.icpsr.umich.edu/) | Inter-university Consortium for Political and Social Research | social science、public health | `undeclared` | `source_only` | 0.0% | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/icpsr/README.md) |
| [ILOSTAT](https://ilostat.ilo.org/data/) | International Labour Organization | labour economics、social science | `undeclared` | `source_only` | 0.0% | 部分验证 (`partially_verified`) | [查看六层目录](catalog/sources/ilostat/README.md) |
| [IMF Data](https://data.imf.org/) | International Monetary Fund | economics、finance | `undeclared` | `source_only` | 0.0% | 部分验证 (`partially_verified`) | [查看六层目录](catalog/sources/imf-data/README.md) |
| [NASA Earthdata](https://www.earthdata.nasa.gov/) | NASA Earth Science Data and Information System | earth science、climate science、environmental science | `undeclared` | `source_only` | 0.0% | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/nasa-earthdata/README.md) |
| [NCBI Databases](https://www.ncbi.nlm.nih.gov/guide/all/) | National Center for Biotechnology Information | biology、genomics、medicine、bioinformatics | `undeclared` | `source_only` | 0.0% | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/ncbi-databases/README.md) |
| [NOAA National Centers for Environmental Information Data Access](https://www.ncei.noaa.gov/) | NOAA National Centers for Environmental Information | climate science、oceanography、geophysics、meteorology | `undeclared` | `source_only` | 0.0% | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/noaa-ncei/README.md) |
| [OECD Data Explorer](https://data-explorer.oecd.org/) | Organisation for Economic Co-operation and Development | multidisciplinary | `undeclared` | `source_only` | 0.0% | 部分验证 (`partially_verified`) | [查看六层目录](catalog/sources/oecd-data-explorer/README.md) |
| [OpenAlex](https://openalex.org/) | OurResearch | multidisciplinary、science studies | `undeclared` | `source_only` | 0.0% | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/openalex/README.md) |
| [RCSB Protein Data Bank](https://www.rcsb.org/) | Research Collaboratory for Structural Bioinformatics Protein Data Bank | structural biology、biochemistry、bioinformatics | `undeclared` | `source_only` | 0.0% | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/rcsb-pdb/README.md) |
| [UN Comtrade](https://comtradeplus.un.org/) | United Nations Statistics Division | economics、international trade | `undeclared` | `source_only` | 0.0% | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/un-comtrade/README.md) |
| [UNdata](https://data.un.org/) | Food and Agriculture Organization of the United Nations<br>International Labour Organization<br>International Monetary Fund<br>International Telecommunications Union<br>Organisation for Economic Co-operation and Development<br>United Nations Population Division<br>World Tourism Organization<br>Joint United Nations Programme on HIV/AIDS<br>United Nations Development Programme<br>UNESCO Institute for Statistics<br>United Nations Framework Convention on Climate Change<br>United Nations High Commissioner for Refugees<br>United Nations Children's Fund<br>United Nations Industrial Development Organization<br>United Nations Office on Drugs and Crime<br>United Nations Statistics Division<br>World Health Organization<br>World Meteorological Organization<br>World Bank | multidisciplinary | `catalog_level` | `six_layer_chain_present` | 0.93% | 部分验证 (`partially_verified`) | [查看六层目录](catalog/sources/undata/README.md) |
| [UNESCO UIS Data Browser](https://databrowser.uis.unesco.org/) | UNESCO Institute for Statistics | education、science studies、culture | `undeclared` | `source_only` | 0.0% | 部分验证 (`partially_verified`) | [查看六层目录](catalog/sources/unesco-uis-data/README.md) |
| [WHO Data](https://data.who.int/) | World Health Organization | medicine、public health | `undeclared` | `source_only` | 0.0% | 部分验证 (`partially_verified`) | [查看六层目录](catalog/sources/who-data/README.md) |
| [World Bank Open Data](https://data.worldbank.org/) | World Bank | multidisciplinary | `representative_chain` | `six_layer_chain_present` | 0.0% | 部分验证 (`partially_verified`) | [查看六层目录](catalog/sources/world-bank-open-data/README.md) |

完整的人机双读索引见 [GRDR数据库目录](catalog/README.md)。
<!-- GRDR_SOURCE_CATALOG_END -->

## Core GRDR questions

GRDR should help an agent determine:

1. Which authoritative and academically valuable data sources exist in each discipline?
2. Who produces and maintains them, what do they contain, and how are they related?
3. How can they be accessed, queried, downloaded, licensed, versioned, and refreshed?
4. Which data can be stored locally, which should remain federated, and which require controlled access?
5. Where are the registry’s disciplinary, geographic, temporal, modality, and access gaps?
6. For a specific scientific question, which registered sources are suitable and what additional data are needed?

## Design principles

- **Task fit is separate from source authority.** An authoritative source may still be unsuitable for a particular question.
- **Claims require evidence.** Authority, coverage, access, and methodological claims must point to verifiable evidence.
- **Unknown is a valid value.** The registry must not turn unverified assumptions into facts.
- **Metadata before mirroring.** GRDR catalogs and connects data before considering storage or redistribution.
- **Dataset and variable granularity matter.** A source-level URL list is insufficient for research design.
- **Provenance is preserved.** Original production, harmonization, publication, and mirroring are distinct relationships.
- **Expansion has no fixed ceiling.** Initial seeds support iterative, audited snowball expansion.
- **Agent-first, human-auditable.** Machine interfaces are primary, while every recommendation remains inspectable.

## Initial repository layout

```text
grdr/
├── catalog/
│   ├── README.md
│   └── sources/
│       └── <database>/README.md
├── docs/
│   ├── PROJECT_CHARTER.md
│   ├── ONTOLOGY.md
│   ├── ASSESSMENT_FRAMEWORK.md
│   ├── AGENT_PROTOCOL.md
│   ├── DATABASE_DEEP_MAP_WORKFLOW.md
│   ├── INDICATOR_BUILDER_PROTOCOL.md
│   └── EXPANSION_PROTOCOL.md
├── deep_map_projects/
│   └── <source-slug>/
│       ├── project.json
│       ├── units.jsonl
│       └── README.md
├── examples/
│   └── population_emissions_request.json
├── registry/
│   ├── institutions.jsonl
│   ├── sources.jsonl
│   ├── datasets.jsonl
│   ├── data_structures.jsonl
│   ├── resources.jsonl
│   ├── data_elements.jsonl
│   ├── source_profiles.jsonl
│   ├── constructs.jsonl
│   ├── variables.jsonl
│   ├── adapters.jsonl
│   ├── storage.jsonl
│   ├── monitors.jsonl
│   └── relationships.jsonl
├── schemas/
│   ├── institution.schema.json
│   ├── source.schema.json
│   ├── dataset.schema.json
│   ├── data_structure.schema.json
│   ├── resource.schema.json
│   ├── data_element.schema.json
│   ├── source_profile.schema.json
│   ├── variable.schema.json
│   ├── construct.schema.json
│   ├── adapter.schema.json
│   ├── storage.schema.json
│   ├── monitor.schema.json
│   ├── relationship.schema.json
│   ├── research_request.schema.json
│   ├── indicator_project.schema.json
│   ├── literature_document.schema.json
│   ├── evidence_unit.schema.json
│   ├── research_indicator.schema.json
│   ├── indicator_mapping.schema.json
│   ├── research_workflow.schema.json
│   ├── data_gap.schema.json
│   ├── database_deep_map_project.schema.json
│   ├── database_deep_map_unit.schema.json
│   ├── database_deep_map_phase_update.schema.json
│   └── database_deep_map_stage_update.schema.json
├── research_projects/
│   └── <project-id>/
│       ├── project.json
│       ├── literature.jsonl
│       ├── evidence_units.jsonl
│       ├── indicators.jsonl
│       ├── mappings.jsonl
│       ├── workflow.json
│       └── data_gaps.jsonl
├── scripts/
│   ├── build_catalog.py
│   ├── curate_undata.py
│   ├── indicator_builder.py
│   ├── database_deep_map.py
│   ├── research_project.py
│   ├── grdr.py
│   └── validate_registry.py
├── skill/
│   ├── grdr/
│   ├── grdr-deep-map-database/
│   └── grdr-indicator-builder/
└── tests/
    ├── test_catalog.py
    ├── test_cli.py
    ├── test_database_deep_map.py
    └── test_indicator_builder.py
```

## Current phase

Version `1.1.0` turns `$grdr-deep-map-database` into a persistent execution system. Every database can now be classified, bounded, divided into ordered work units, resumed deterministically, audited by counted stages, and completed only through a strict evidence gate. UNdata is the first real project: 36 bounded datamarts, 216 required unit stages, 19.44% mapped and 0.93% strictly complete at migration. These figures deliberately expose the remaining work instead of treating a few deep examples as a finished database. The target of roughly 100 high-value sources remains a first pass, not a collection limit.

Every completed development batch increments `VERSION`, updates `CHANGELOG.md`, passes validation, and is published to GitHub according to [the release process](docs/RELEASE_PROCESS.md).

## Local agent access

The foundation release includes a dependency-free JSON CLI so an agent can inspect the registry immediately:

```bash
python3 scripts/grdr.py stats
python3 scripts/grdr.py search-sources --query climate
python3 scripts/grdr.py search-sources --discipline medicine --verification unverified
python3 scripts/grdr.py search-datasets --topic population
python3 scripts/grdr.py search-variables --construct population
python3 scripts/grdr.py get-source grdr:source:undata
python3 scripts/grdr.py get-dataset grdr:dataset:world-development-indicators
python3 scripts/grdr.py get-data-structure grdr:data-structure:undata-energy-sdmx
python3 scripts/grdr.py get-data-element grdr:data-element:undata-energy-transaction
python3 scripts/grdr.py get-variable grdr:variable:undata-energy-ga
python3 scripts/grdr.py trace-provenance grdr:variable:wdi-sp-pop-totl
python3 scripts/grdr.py list-adapters --status operational
python3 scripts/grdr.py list-storage --mode federated_access
python3 scripts/grdr.py list-monitors --status passing
python3 scripts/grdr.py diagnose-coverage examples/population_emissions_request.json
python3 scripts/grdr.py audit-source-depth grdr:source:undata
python3 scripts/grdr.py audit-all-source-depth
python3 scripts/grdr.py start-database-deep-map examples/world_bank_deep_map_spec.json
python3 scripts/grdr.py database-deep-map-status deep_map_projects/undata
python3 scripts/grdr.py resume-database-deep-map deep_map_projects/undata
python3 scripts/grdr.py audit-database-deep-map deep_map_projects/undata
python3 scripts/grdr.py complete-database-deep-map deep_map_projects/<source-slug>
python3 scripts/grdr.py audit-indicator-project research_projects/<project-id>
python3 scripts/grdr.py research-project-status research_projects/<project-id>
python3 scripts/validate_registry.py
python3 scripts/build_catalog.py --check
python3 scripts/check_release.py
python3 -m unittest discover -s tests
```

All command output is JSON except validation diagnostics. Search results always include verification status; unverified bootstrap nominations are never presented as verified sources.

## Non-goals for the foundation phase

- copying or redistributing all underlying datasets;
- treating institutional prestige as a universal authority ranking;
- generating empirical claims without inspecting dataset-level methodology;
- promising automatic access where registration, payment, ethics review, or data-use agreements are required;
- presenting proxy variables as direct measurements.
