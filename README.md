# GRDR Core

GRDR Core is the database-independent engine for the Global Research Data Registry: an AI-agent-native, all-discipline infrastructure for data-source registration, deep mapping, research matching, and distributed snapshot storage.

This repository contains no database snapshot, database-specific adapter, canonical source record, source-archive card, project state, or observation data. Mutable registry and project state lives under external `GRDR_STATE_ROOT`; every selected database is stored in its own private source repository.

## Three-step database factory

GRDR Core fixes the workflow as three independent, Agent-callable Skills:

1. `grdr-plan-database-deep-map` diagnoses an unknown database, defines its bounded work-unit universe, composes route obligations, and fingerprint-locks the Plan.
2. `grdr-execute-database-deep-map` follows the deterministic queue, reconstructs native structure and disciplinary semantics, builds the DataElement → Variable → Construct bridge, and seals the execution without canonical writes.
3. `grdr-store-database-deep-map` transactionally promotes sealed records, creates the source-specific private repository, publishes one complete callable Release per snapshot, materializes the matching Elements copy, verifies SHA-256 parity and the source runtime, writes the central source card, and issues the final Storage receipt.

These three Skills are the database production plane. The independent GRDR Agent Runtime is the use plane: it searches central and distributed variable indexes, mounts a verified snapshot, resolves a variable to its source-native access plan, and invokes the source-specific runtime. Storage packages and tests the runtime artifact; it does not own search, matching, or retrieval behavior.

## Research use plane

GRDR has six formal Skills in total. `grdr` is the coordinator; the three Skills above produce database snapshots; `grdr-indicator-builder` converts a research question and literature into evidence-linked leaf indicators; and `grdr-resolve-research-semantics` persists the missing R→B entry bridge, traverses the stored B→A graph, evaluates variable fit, explains every selected route, and invokes official data through the source runtime. Agent Runtime and source-specific runtimes are versioned execution code rather than additional Skills.

## Core architecture

The complete architecture is shown in three linked views so that every element remains readable at normal GitHub width: the system overview, the database production plane, and the research use plane. The production view is divided into Plan, Execute, and Storage panels without changing the single three-step workflow.

### 1. End-to-end system overview

```mermaid
flowchart TB
    CORE["GRDR Core v4.0.0<br/><b>database-independent · AI-agent-native</b>"]:::core
    COORD["<b>Skill 1 · grdr</b><br/>coordinate · discover · assess · audit · expand"]:::coreSkill
    SHARED["Shared foundation<br/>ontology · schemas · route contracts · CLI/Runtime<br/>validators · tests · documentation · index-card schema"]:::shared

    subgraph PROD["DATABASE PRODUCTION PLANE"]
        direction LR
        PLAN_OV["<b>Skill 2 · Plan</b><br/>diagnose · bound · compose routes<br/>lock Plan / Scope / Unit manifest"]:::plan
        EXEC_OV["<b>Skill 3 · Execute</b><br/>deterministic deep map<br/>A spine + B spine + measurement bridge"]:::execute
        STORE_OV["<b>Skill 4 · Storage</b><br/>promote · package · publish · verify"]:::storage
        PLAN_OV -->|"locked project"| EXEC_OV -->|"sealed execution"| STORE_OV
    end

    SNAP["One Source → one private repository<br/>One snapshot → one GitHub Release + one Elements copy<br/>external source card · exact fingerprint · callable runtime"]:::artifact

    subgraph USE["RESEARCH USE PLANE"]
        direction LR
        BUILD_OV["<b>Skill 5 · Indicator Builder</b><br/>question + literature → evidence-linked R"]:::research
        SEM_OV["<b>Skill 6 · Semantic Resolver</b><br/>recall → R→B → B→A → fit → invocation"]:::semantic
        RUN_OV["Agent Runtime + source runtime<br/><i>execution code, not additional Skills</i><br/>search · mount · resolve · call"]:::runtime
        OUT_OV["Official data<br/>+ path + provenance + uncertainty"]:::result
        BUILD_OV --> SEM_OV --> RUN_OV --> OUT_OV
    end

    GAP_OV["Data-gap loop<br/>missing variable/dimension → discover or deepen source<br/>→ rebuild snapshot → rerun matching"]:::gap

    CORE --> COORD
    CORE --> SHARED
    COORD --> PLAN_OV
    STORE_OV --> SNAP
    SNAP --> SEM_OV
    SNAP --> RUN_OV
    SEM_OV -->|"not found / incompatible"| GAP_OV

    classDef core fill:#173B57,stroke:#0B2538,color:#FFFFFF,stroke-width:2px;
    classDef coreSkill fill:#245B78,stroke:#173B57,color:#FFFFFF,stroke-width:2px;
    classDef shared fill:#E8F1F5,stroke:#5E879A,color:#173B57,stroke-width:1.5px;
    classDef plan fill:#DCEAFF,stroke:#477BD1,color:#173B57,stroke-width:2px;
    classDef execute fill:#DDF7EE,stroke:#2F8F72,color:#123E34,stroke-width:2px;
    classDef storage fill:#FFE4C7,stroke:#C56A1B,color:#69370F,stroke-width:2px;
    classDef artifact fill:#FFF2E5,stroke:#D48638,color:#69370F,stroke-width:2px;
    classDef research fill:#F8DCE6,stroke:#B84A6C,color:#6E243D,stroke-width:2px;
    classDef semantic fill:#E6DEFF,stroke:#6F4FC2,color:#3F2A72,stroke-width:2px;
    classDef runtime fill:#E5F3FF,stroke:#4787B8,color:#173B57,stroke-width:2px;
    classDef result fill:#DDF7E7,stroke:#3D9158,color:#1F5A31,stroke-width:2px;
    classDef gap fill:#FFF0F0,stroke:#C65C5C,color:#722E2E,stroke-width:2px;
    style PROD fill:#F7FAFC,stroke:#8AA4B4,stroke-width:2px
    style USE fill:#FFF8FC,stroke:#BE7790,stroke-width:2px
```

### 2. Database production plane: Plan → Execute → Storage

#### 2A. Plan — 诊断、定界、路线组合与三重锁定

```mermaid
flowchart TB
    %% ───────────────────────── Production plane ─────────────────────────
    INTAKE["Selected authoritative database<br/>name · URL · catalog · Source ID"]:::external

        subgraph PLAN["Skill 2 · grdr-plan-database-deep-map — PLAN"]
            direction LR
            P_DIAG["Identity + multidimensional diagnosis<br/>producer · governance · lifecycle · access<br/>scale · metadata/observation entry"]:::plan
            P_DISC["Disciplinary position<br/>multi-parent · non-exclusive<br/>field · object · method · application"]:::plan
            P_SHAPE["Data-generating process + native shape<br/>catalog · table · cube · survey · graph · corpus<br/>array · stream · experiment · simulation · custom"]:::plan
            P_BOUND["Honest dated boundary<br/>identity rule · denominator · ordered work units"]:::planStrong
            P_ROUTE["Composable route obligations<br/>structure · semantics · access · lifecycle · provenance"]:::planStrong
            P_GATE["Required human gates<br/>and unresolved constraints"]:::gate
            P_LOCK["Fingerprint-locked project<br/>Plan lock · Scope lock · Unit-manifest lock"]:::handoff

            P_DIAG --> P_BOUND
            P_DISC --> P_BOUND
            P_SHAPE --> P_BOUND
            P_BOUND --> P_ROUTE --> P_GATE --> P_LOCK
        end

    INTAKE --> P_DIAG
    INTAKE --> P_DISC
    INTAKE --> P_SHAPE

    classDef external fill:#FFFFFF,stroke:#64748B,color:#263849,stroke-width:1.5px;
    classDef plan fill:#EAF2FF,stroke:#5B8DEF,color:#173B57,stroke-width:1.5px;
    classDef planStrong fill:#D7E7FF,stroke:#356FD1,color:#173B57,stroke-width:2px;
    classDef gate fill:#FFF1C7,stroke:#C78A1D,color:#664500,stroke-width:1.5px;
    classDef handoff fill:#263849,stroke:#17212B,color:#FFFFFF,stroke-width:2px;
    style PLAN fill:#F4F8FF,stroke:#6B97DB,stroke-width:1.5px
```

#### 2B. Execute — 两根主干、一座桥梁和确定性执行

```mermaid
flowchart TB
        LOCKED["Locked deep-map project<br/>Plan + Scope + Unit-manifest fingerprints"]:::handoff

        subgraph EXECUTE["Skill 3 · grdr-execute-database-deep-map — EXECUTE"]
            direction TB
            E_QUEUE["Deterministic dependency-valid queue<br/>one next target · checkpoint/resume · drift rejection<br/>complete only inside the locked dated boundary"]:::executeStrong
            E_EVID["Evidence + provenance + typed relationships<br/>applies to every entity and edge<br/>entity counts · topology closure · route-contract checks"]:::evidence

            subgraph A_SPINE["A · Source-native data spine（数据库事实与结构）"]
                A_CHAIN["Institution → Source → Dataset → recursive DataStructure<br/>→ <b>5A DataElement</b> → <b>5B Variable</b><br/><i>provenance context → versionable observations → native hierarchy/schema<br/>→ measure/dimension/ID/unit/weight/flag → definition/population/unit/coverage</i>"]:::aStrong
            end

            subgraph B_SPINE["B · Multi-parent scientific-semantic spine（学科与理论语义）"]
                B_CHAIN["Multi-parent SemanticNodes → <b>Construct</b><br/><i>discipline · field · object · system · phenomenon · process<br/>population · observation/analysis unit · method · application<br/>→ theoretical or substantive meaning</i>"]:::bStrong
            end

            BRIDGE["A—B measurement bridge<br/>direct measure · transformed measure · composite<br/>proxy · index · model estimate · forecast"]:::bridge
            RESOURCE["Access Resource sidecar<br/>API · download · query · auth · license · documentation"]:::sidecar
            E_SEAL["Sealed Execute handoff<br/>staged canonical candidates + ledgers + evidence<br/>fingerprinted · no canonical writes"]:::handoff

            E_QUEUE --> A_CHAIN
            E_QUEUE --> B_CHAIN
            E_QUEUE --> E_EVID
            A_CHAIN --> BRIDGE --> B_CHAIN
            RESOURCE -. "access mechanics; not a content layer" .-> A_CHAIN
            E_EVID -. "audits bridge closure" .-> BRIDGE
            A_CHAIN --> E_SEAL
            B_CHAIN --> E_SEAL
            RESOURCE --> E_SEAL
            E_EVID --> E_SEAL
        end

        LOCKED --> E_QUEUE

    classDef executeStrong fill:#DDF7EE,stroke:#2F8F72,color:#123E34,stroke-width:2px;
    classDef evidence fill:#FFF8D8,stroke:#C79A2A,color:#5D4700,stroke-width:1.5px;
    classDef aStrong fill:#CFF1E7,stroke:#247A64,color:#123E34,stroke-width:2px;
    classDef bStrong fill:#E3D8FF,stroke:#6F4FC2,color:#3F2A72,stroke-width:2px;
    classDef bridge fill:#FFE3EC,stroke:#C4557B,color:#6E243D,stroke-width:2px;
    classDef sidecar fill:#F8FAFC,stroke:#94A3B8,color:#475569,stroke-width:1.5px,stroke-dasharray:5 3;
    classDef handoff fill:#263849,stroke:#17212B,color:#FFFFFF,stroke-width:2px;
    style EXECUTE fill:#F3FCF8,stroke:#57A58F,stroke-width:1.5px
    style A_SPINE fill:#F8FFFC,stroke:#71B7A4,stroke-width:1px
    style B_SPINE fill:#FCFAFF,stroke:#9C85D6,stroke-width:1px
```

#### 2C. Storage — 四个存储位置、双表示一致性和最终回执

```mermaid
flowchart TB
        SEALED["Sealed Execute handoff<br/>staged candidates + ledgers + evidence<br/>fingerprinted · no canonical writes"]:::handoff

        subgraph STORAGE["Skill 4 · grdr-store-database-deep-map — STORAGE"]
            direction TB
            S_PROMOTE["Transactional external-state promotion<br/>audit sealed execution · Core remains byte-identical"]:::storage
            S_PACKAGE["Build one source-scoped snapshot<br/>knowledge graph + Execute project + standards/evidence<br/>Agent SQLite index + source runtime + observations"]:::storageStrong

            S_REPO["Private source Git repository<br/>Core version reference · config · adapters · runtime code<br/>Plan · manifests · README · tests · archive receipts"]:::artifact
            S_RELEASE["GitHub Release · compressed distribution<br/><b>knowledge/ + agent/ + observations/</b><br/>manifest + Storage receipt"]:::artifactStrong
            S_ELEMENTS["Elements · expanded working copy<br/><b>the same knowledge/ + agent/ + observations/</b><br/>receipts/Storage receipt"]:::artifactStrong
            S_PARITY["Release ↔ Elements parity<br/>same ordered logical inventory + SHA-256"]:::verify
            S_VERIFY["Read-back publication verification<br/>source runtime resolves every indexed Variable"]:::verify
            S_RECEIPT["Valid Storage receipt<br/><b>versioned_database_snapshot</b>"]:::handoff
            S_CARD["External GRDR state source-archive card<br/>Source ID · repository · snapshot · Release<br/>fingerprint · completion status"]:::shared

            SEALED --> S_PROMOTE --> S_PACKAGE
            S_PACKAGE --> S_REPO
            S_PACKAGE --> S_RELEASE
            S_PACKAGE --> S_ELEMENTS
            S_RELEASE --> S_PARITY
            S_ELEMENTS --> S_PARITY
            S_REPO --> S_VERIFY
            S_PARITY --> S_VERIFY
            S_VERIFY --> S_RECEIPT --> S_CARD
        end

    classDef shared fill:#E8F1F5,stroke:#5E879A,color:#173B57,stroke-width:1.5px;
    classDef handoff fill:#263849,stroke:#17212B,color:#FFFFFF,stroke-width:2px;
    classDef storage fill:#FFF0DF,stroke:#D48638,color:#69370F,stroke-width:1.5px;
    classDef storageStrong fill:#FFE0BF,stroke:#C56A1B,color:#69370F,stroke-width:2px;
    classDef artifact fill:#FFF7ED,stroke:#D48638,color:#69370F,stroke-width:1.5px;
    classDef artifactStrong fill:#FFEAD4,stroke:#C56A1B,color:#69370F,stroke-width:2px;
    classDef verify fill:#E7F6EC,stroke:#4D9B63,color:#204F2D,stroke-width:2px;
    style STORAGE fill:#FFFAF3,stroke:#D99A5D,stroke-width:1.5px
```

### 3. Research use plane: R → B → A → official data

```mermaid
flowchart TB
    QUESTION["Research question / topic<br/>population · unit · time · geography · intended inference"]:::research
    LITERATURE["Optional substantial literature corpus<br/>abstract · introduction · methods · results<br/>discussion · conclusion · references"]:::research
    BUILDER["<b>Skill 5 · grdr-indicator-builder</b><br/>theory deduction · content analysis · grounded coding<br/>evidence-linked multi-level indicator construction"]:::researchStrong
    R_TREE["R · ResearchProject + hierarchical ResearchIndicators<br/>domain → construct → subconstruct → indicator<br/>→ leaf operational requirement"]:::rNode
    HUMAN["Explicit human gates when required<br/>corpus boundary · indicator framework · contested mappings"]:::gate

    QUESTION --> BUILDER
    LITERATURE --> BUILDER
    HUMAN -. "human decision; never Agent self-approval" .-> BUILDER
    BUILDER --> R_TREE

    SNAPSHOT["Callable distributed snapshot entry<br/>central source card + semantic/variable index<br/>verified Release/Elements + exact snapshot fingerprint"]:::runtime

    subgraph FIVE["Skill 6 · grdr-resolve-research-semantics — persisted five-layer resolver"]
        direction LR
        RECALL["1 · Full-text candidate recall<br/>Construct · SemanticNode · Variable<br/><i>candidate ≠ conclusion</i>"]:::resolver
        ALIGN["2 · Evidence-constrained R→B<br/>exact · close · broader · narrower<br/>related · no-match"]:::resolver
        TRAVERSE["3 · Auditable B→A traversal<br/>SemanticNode / Construct → Variable<br/>→ DataElement → DataStructure → Dataset → snapshot"]:::resolver
        FIT["4 · Variable-fit classification + explanation<br/>construct · population · unit · time · space<br/>direct · transformed · composite · proxy · conflict"]:::resolver
        INVOKE["5 · Indicator-scoped invocation<br/>locate/mount verified snapshot<br/>resolve source-native access plan"]:::resolverStrong
        RECALL --> ALIGN --> TRAVERSE --> FIT --> INVOKE
    end

    R_TREE --> RECALL
    SNAPSHOT -. "central + distributed recall" .-> RECALL
    SNAPSHOT --> INVOKE
    HUMAN -. "approve contested decisions" .-> FIT

    SOURCE_RUNTIME["Source-specific callable runtime<br/>verified adapter + exact snapshot + access plan"]:::runtime
    UPSTREAM["Authoritative upstream route<br/>official API · file · query service"]:::external
    RESULT["Research-ready output<br/>data + source + snapshot + Variable<br/>alignment/path + provenance + uncertainty"]:::result
    GAP["Data-gap diagnosis<br/>missing construct · variable · population · unit<br/>time · space · modality · joinability"]:::gap
    EXPAND["Expansion and rerun<br/>discover or deepen source → Plan → Execute → Storage<br/>→ rebuild recall/alignment/path → rerun matching"]:::shared

    INVOKE --> SOURCE_RUNTIME --> UPSTREAM --> RESULT
    FIT -->|"not_found_registry_snapshot / incompatible"| GAP --> EXPAND

    classDef research fill:#FDECF1,stroke:#C76884,color:#6E243D,stroke-width:1.5px;
    classDef researchStrong fill:#F8D8E3,stroke:#B84A6C,color:#6E243D,stroke-width:2px;
    classDef rNode fill:#FFF0F5,stroke:#C4557B,color:#6E243D,stroke-width:2px;
    classDef gate fill:#FFF1C7,stroke:#C78A1D,color:#664500,stroke-width:1.5px;
    classDef resolver fill:#EEE9FF,stroke:#7B62C5,color:#3F2A72,stroke-width:1.5px;
    classDef resolverStrong fill:#DED3FF,stroke:#6646B7,color:#3F2A72,stroke-width:2px;
    classDef runtime fill:#E5F3FF,stroke:#4787B8,color:#173B57,stroke-width:2px;
    classDef external fill:#FFFFFF,stroke:#64748B,color:#263849,stroke-width:1.5px;
    classDef result fill:#DDF7E7,stroke:#3D9158,color:#1F5A31,stroke-width:2px;
    classDef gap fill:#FFF0F0,stroke:#C65C5C,color:#722E2E,stroke-width:2px;
    classDef shared fill:#E8F1F5,stroke:#5E879A,color:#173B57,stroke-width:1.5px;
    style FIVE fill:#FAF8FF,stroke:#8A74CA,stroke-width:1.5px
```

Resources such as APIs, downloads, authentication, and licenses are access sidecars rather than content levels.

## Repository boundary

GRDR Core keeps only:

- shared Skills, schemas, route contracts, programs, and documentation;
- empty canonical Registry filename templates and the source-archive card schema;
- generic, synthetic tests that do not identify a real database.

Each deeply processed database keeps its own configuration, adapters, Plan, Execute package, full knowledge snapshot, Agent index, captured observations, Release history, and expanded Elements copy outside this repository. Source repositories reference a Core version; they never copy the Core.

## Central source index

Core always keeps an empty index template. Completed source repositories add validated central cards only to external `GRDR_STATE_ROOT/registry/source_archives.jsonl` through Storage.

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
python3 scripts/configure_core.py

# Optional: choose another external mutable-state location.
export GRDR_STATE_ROOT=/absolute/path/outside/grdr-core

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

Version `4.0.0` freezes the immutable-Core boundary: Plan, Execute, Storage, research projects, source cards, and every canonical database record are written only to external state or source repositories. All six Skills now use location-independent launchers, while the persisted and explainable R→B→A workflow connects research indicators to callable source variables without placing any database trace in Core.
