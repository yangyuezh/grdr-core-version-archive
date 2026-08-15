# Global Research Data Registry (GRDR)

GRDR is AI-agent-native, all-discipline infrastructure for global data-source registration, discovery, assessment, connection, and research design.

**Current status:** foundation and first-pass source construction. The repository provides the evidence model, ontology, schemas, initial registry, and Agent commands. The immediate goal is a verified first-round registry of approximately 100 cross-disciplinary sources, followed by multi-round snowball expansion. See [North Star](docs/NORTH_STAR.md).

It is not primarily a website and does not initially copy every upstream dataset. It combines:

- a versioned data-source registry;
- a dataset and measurement knowledge graph;
- task-specific source-fit and data-gap assessment;
- stable interfaces for Codex, Claude, and other agents;
- optional adapters for representative sources with stable programmatic access.

Research-question matching, source combination, and data-gap diagnosis are central Agent capabilities built on top of the registry. Local snapshots and federated access are later extensions where licensing, privacy, cost, and scale permit.

## 已收录数据库

<!-- GRDR_SOURCE_CATALOG_START -->
当前注册表共收录 **19** 个数据库/数据平台。每个数据库均有独立六层详情页；“待验证候选”仅表示已经登记，不表示其覆盖与使用条件已经核验。

| 数据库 | 发布/维护机构 | 主要领域 | 验证状态 | 六层详情 |
|---|---|---|---|---|
| [UNdata](https://data.un.org/) | United Nations Statistics Division | multidisciplinary | 部分验证 (`partially_verified`) | [查看六层目录](catalog/sources/undata/README.md) |
| [World Bank Open Data](https://data.worldbank.org/) | World Bank | multidisciplinary | 部分验证 (`partially_verified`) | [查看六层目录](catalog/sources/world-bank-open-data/README.md) |
| [IMF Data](https://data.imf.org/) | International Monetary Fund | economics、finance | 部分验证 (`partially_verified`) | [查看六层目录](catalog/sources/imf-data/README.md) |
| [OECD Data Explorer](https://data-explorer.oecd.org/) | Organisation for Economic Co-operation and Development | multidisciplinary | 部分验证 (`partially_verified`) | [查看六层目录](catalog/sources/oecd-data-explorer/README.md) |
| [Eurostat Database](https://ec.europa.eu/eurostat/) | Eurostat | multidisciplinary | 部分验证 (`partially_verified`) | [查看六层目录](catalog/sources/eurostat/README.md) |
| [ILOSTAT](https://ilostat.ilo.org/data/) | International Labour Organization | labour economics、social science | 部分验证 (`partially_verified`) | [查看六层目录](catalog/sources/ilostat/README.md) |
| [WHO Data](https://data.who.int/) | World Health Organization | medicine、public health | 部分验证 (`partially_verified`) | [查看六层目录](catalog/sources/who-data/README.md) |
| [FAOSTAT](https://www.fao.org/faostat/) | Food and Agriculture Organization of the United Nations | agriculture、food science、environmental science、economics | 部分验证 (`partially_verified`) | [查看六层目录](catalog/sources/faostat/README.md) |
| [UNESCO UIS Data Browser](https://databrowser.uis.unesco.org/) | UNESCO Institute for Statistics | education、science studies、culture | 部分验证 (`partially_verified`) | [查看六层目录](catalog/sources/unesco-uis-data/README.md) |
| [UN Comtrade](https://comtradeplus.un.org/) | United Nations Statistics Division | economics、international trade | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/un-comtrade/README.md) |
| [NASA Earthdata](https://www.earthdata.nasa.gov/) | NASA Earth Science Data and Information System | earth science、climate science、environmental science | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/nasa-earthdata/README.md) |
| [NCBI Databases](https://www.ncbi.nlm.nih.gov/guide/all/) | National Center for Biotechnology Information | biology、genomics、medicine、bioinformatics | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/ncbi-databases/README.md) |
| [RCSB Protein Data Bank](https://www.rcsb.org/) | Research Collaboratory for Structural Bioinformatics Protein Data Bank | structural biology、biochemistry、bioinformatics | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/rcsb-pdb/README.md) |
| [GBIF](https://www.gbif.org/) | Global Biodiversity Information Facility | biodiversity science、ecology、conservation biology | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/gbif/README.md) |
| [Copernicus Climate Data Store](https://cds.climate.copernicus.eu/) | Copernicus Climate Change Service | climate science、earth science | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/copernicus-climate-data-store/README.md) |
| [OpenAlex](https://openalex.org/) | OurResearch | multidisciplinary、science studies | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/openalex/README.md) |
| [ICPSR Data Archive](https://www.icpsr.umich.edu/) | Inter-university Consortium for Political and Social Research | social science、public health | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/icpsr/README.md) |
| [CERN Open Data Portal](https://opendata.cern.ch/) | European Organization for Nuclear Research | particle physics | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/cern-open-data/README.md) |
| [NOAA National Centers for Environmental Information Data Access](https://www.ncei.noaa.gov/) | NOAA National Centers for Environmental Information | climate science、oceanography、geophysics、meteorology | 待验证候选 (`unverified`) | [查看六层目录](catalog/sources/noaa-ncei/README.md) |

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
│   └── EXPANSION_PROTOCOL.md
├── examples/
│   └── population_emissions_request.json
├── registry/
│   ├── institutions.jsonl
│   ├── sources.jsonl
│   ├── datasets.jsonl
│   ├── resources.jsonl
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
│   ├── resource.schema.json
│   ├── variable.schema.json
│   ├── construct.schema.json
│   ├── adapter.schema.json
│   ├── storage.schema.json
│   ├── monitor.schema.json
│   ├── relationship.schema.json
│   └── research_request.schema.json
├── scripts/
│   ├── build_catalog.py
│   ├── grdr.py
│   └── validate_registry.py
└── tests/
    └── test_cli.py
```

## Current phase

Version `0.2.0` defines the project charter, registry ontology, evidence rules, assessment framework, Agent contract, seed-expansion process, and a generated human-readable catalog. Every source appears in the root README and in an independent six-layer detail directory. It also includes the first end-to-end source–dataset–resource–variable–construct chain and a registry-coverage diagnostic for structured research requests. Seed records are deliberately small and evidence-conscious; the target of roughly 100 high-value sources is a first coverage pass, not a collection limit. The Codex Skill is installed and invoked consistently as `GRDR` / `$grdr`.

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
python3 scripts/grdr.py trace-provenance grdr:variable:wdi-sp-pop-totl
python3 scripts/grdr.py list-adapters --status operational
python3 scripts/grdr.py list-storage --mode federated_access
python3 scripts/grdr.py list-monitors --status passing
python3 scripts/grdr.py diagnose-coverage examples/population_emissions_request.json
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
