# GRDR Core

GRDR Core is the database-independent engine for the Global Research Data Registry: an AI-agent-native, all-discipline infrastructure for data-source registration, deep mapping, research matching, and distributed snapshot storage.

This repository contains no database snapshot, database-specific adapter, canonical source record, or observation data. Every selected database is processed in a separate project and stored in its own private source repository.

## Three-step database factory

GRDR Core fixes the workflow as three independent, Agent-callable Skills:

1. `grdr-plan-database-deep-map` diagnoses an unknown database, defines its bounded work-unit universe, composes route obligations, and fingerprint-locks the Plan.
2. `grdr-execute-database-deep-map` follows the deterministic queue, reconstructs native structure and disciplinary semantics, builds the DataElement → Variable → Construct bridge, and seals the execution without canonical writes.
3. `grdr-store-database-deep-map` transactionally promotes sealed records, creates the source-specific private repository, publishes one complete callable Release per snapshot, materializes the matching Elements copy, verifies SHA-256 parity and the source runtime, writes the central source card, and issues the final Storage receipt.

These three Skills are the database production plane. The independent GRDR Agent Runtime is the use plane: it searches central and distributed variable indexes, mounts a verified snapshot, resolves a variable to its source-native access plan, and invokes the source-specific runtime. Storage packages and tests the runtime artifact; it does not own search, matching, or retrieval behavior.

## Research use plane

GRDR has six formal Skills in total. `grdr` is the coordinator; the three Skills above produce database snapshots; `grdr-indicator-builder` converts a research question and literature into evidence-linked leaf indicators; and `grdr-resolve-research-semantics` persists the missing R→B entry bridge, traverses the stored B→A graph, evaluates variable fit, explains every selected route, and invokes official data through the source runtime. Agent Runtime and source-specific runtimes are versioned execution code rather than additional Skills.

## Core architecture: two spines and one bridge

```mermaid
flowchart TB
    subgraph PLAN["1. Plan — 诊断、定界与锁定"]
        direction TB
        INTAKE["Database intake<br/>name, URL, catalog or Source ID"] --> DIAG["Multidimensional diagnosis"]
        DIAG --> DISC["Discipline membership<br/>multi-parent, non-exclusive"]
        DIAG --> SHAPE["Generation process + native structure<br/>origin, modality, hierarchy, tables, cubes, graphs..."]
        DIAG --> GOVERN["Lifecycle + governance<br/>versioning, access, sensitivity, scale, metadata maturity"]
        DISC --> BOUND["Bounded work-unit universe<br/>identity rule + denominator + ordering"]
        SHAPE --> BOUND
        GOVERN --> BOUND
        BOUND --> ROUTES["Composable route contracts<br/>structure + semantics + access + lifecycle + provenance"]
        ROUTES --> GATES["Resolve required human gates"]
        GATES --> LOCKS["Three fingerprint locks<br/>Plan + Scope + Unit manifest"]
    end

    subgraph EXECUTE["2. Execute — 确定性深读与证据闭合"]
        direction TB
        QUEUE["Dependency-valid deterministic queue<br/>checkpoint + resume + deviation rejection"]

        subgraph STRUCT["主干一：数据库原生结构 / Source-native structural spine"]
            direction LR
            INST["Institution"] --> SRC["Source"] --> DATASET["Dataset"] --> DSTRUCT["Recursive DataStructure"] --> ELEMENT["5A DataElement"] --> VARIABLE["5B Variable"]
        end

        subgraph SEMANTIC["主干二：多父学科与科学语义 / Multi-parent semantic spine"]
            direction TB
            SEM_A["SemanticNode<br/>discipline / topic A"] --> CONSTRUCT["Construct"]
            SEM_B["SemanticNode<br/>discipline / topic B"] --> CONSTRUCT
        end

        RESOURCE["Resource<br/>API, files, access, license"] -. "access sidecar" .-> SRC
        RESOURCE -. "access sidecar" .-> DSTRUCT

        QUEUE --> INST
        QUEUE --> SEM_A
        QUEUE --> SEM_B
        VARIABLE -->|"变量—构念桥梁 / measurement, proxy, index or estimate"| CONSTRUCT
        VARIABLE --> SEALED["Fingerprint-sealed execution handoff<br/>staging only; no canonical writes"]
        CONSTRUCT --> SEALED
    end

    LOCKS --> QUEUE
    SEALED --> STORE["3. Storage<br/>promote, package, publish and verify"]

    STORE --> CARD["GRDR Core<br/>central source card only"]
    STORE --> REPO["Private source Git repository<br/>config, adapters, Plan and receipts"]
    STORE --> RELEASE["GitHub Release<br/>knowledge + Agent runtime/index + observations"]
    STORE --> ELEMENTS["Elements<br/>same logical snapshot, expanded"]
    RELEASE <-->|"same logical snapshot + SHA-256 parity"| ELEMENTS

    subgraph RUNTIME["Research use plane — 研究调用面"]
        direction LR
        QUESTION["Research question + literature"] --> INDICATOR["Indicator Builder<br/>research-side R"] --> SEMRES["Research Semantic Resolver<br/>R→B alignment + B→A traversal"] --> FIT["Variable fit + explainable path"] --> MOUNT["Locate or materialize verified snapshot"] --> RESOLVE["Resolve source-native access plan"] --> FETCH["Call official upstream and return data + provenance"]
    end
    CARD --> SEMRES
    STORE --> SEMRES
    RELEASE --> MOUNT
    ELEMENTS --> MOUNT
```

Resources such as APIs, downloads, authentication, and licenses are access sidecars rather than content levels.

## Repository boundary

GRDR Core keeps only:

- shared Skills, schemas, route contracts, programs, and documentation;
- empty canonical registry templates and the central source-archive index format;
- generic, synthetic tests that do not identify a real database.

Each deeply processed database keeps its own configuration, adapters, Plan, Execute package, full knowledge snapshot, Agent index, captured observations, Release history, and expanded Elements copy outside this repository. Source repositories reference a Core version; they never copy the Core.

## Central source index

The isolated milestone starts with an empty central index. Completed source repositories add only validated central cards through Storage.

<!-- GRDR_SOURCE_CATALOG_START -->
当前注册表共收录 **0** 个数据库/数据平台。每个数据库均有独立六层详情页；“待验证候选”仅表示已经登记，不表示其覆盖与使用条件已经核验。

| 数据库 | 发布/维护机构 | 主要领域 | 拆解范围 | 拆解阶段 | 严格完成度 | 验证状态 | 六层详情 |
|---|---|---|---|---|---:|---|---|

完整的人机双读索引见 [GRDR数据库目录](catalog/README.md)。
<!-- GRDR_SOURCE_CATALOG_END -->

## Commands

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-validation.txt

.venv/bin/python scripts/grdr.py list-database-route-modules
.venv/bin/python scripts/grdr.py plan-database-deep-map <intake.json> --output <plan.json>
.venv/bin/python scripts/grdr.py start-database-deep-map <spec.json>
.venv/bin/python scripts/grdr.py database-deep-map-status <project>
.venv/bin/python scripts/grdr.py resume-database-deep-map <project>
.venv/bin/python scripts/grdr.py audit-database-deep-map-execution <project>
.venv/bin/python scripts/grdr.py prepare-database-deep-map-storage <project>
.venv/bin/python scripts/grdr.py prepare-database-storage <project> <storage-spec.json>
.venv/bin/python scripts/grdr.py publish-database-storage <project>
.venv/bin/python scripts/grdr.py database-storage-status <project>
.venv/bin/python scripts/grdr.py source-snapshot-status --source-id <source-id> --verify
.venv/bin/python scripts/grdr.py prepare-semantic-candidates <research-project>
.venv/bin/python scripts/grdr.py align-research-indicators <research-project> <decisions.jsonl>
.venv/bin/python scripts/grdr.py traverse-semantic-paths <research-project>
.venv/bin/python scripts/grdr.py match-indicators <research-project>
.venv/bin/python scripts/grdr.py explain-indicator-match <research-project> <indicator-id>
.venv/bin/python scripts/grdr.py fetch-indicator-data <research-project> <indicator-id> --dry-run
.venv/bin/python scripts/grdr.py search-variables --construct <construct>
.venv/bin/python scripts/grdr.py resolve-variable-access <variable-id>
.venv/bin/python scripts/grdr.py fetch-variable <variable-id> --dry-run
```

See [the database factory workflow](docs/DATABASE_DEEP_MAP_WORKFLOW.md) and [the North Star](docs/NORTH_STAR.md).

## Validation

```bash
.venv/bin/python scripts/validate_registry.py
.venv/bin/python scripts/build_catalog.py --check
.venv/bin/python scripts/check_release.py
.venv/bin/python -m unittest discover -s tests -v
```

Version `3.4.0` adds the sixth formal Skill and the persisted, explainable R→B→A research-semantic resolution workflow. Plan → Execute → Storage remains the three-step production factory; Indicator Builder, Research Semantic Resolver, and Runtime form the separate AI-use plane.
