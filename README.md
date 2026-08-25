# GRDR Core

GRDR Core is the database-independent engine for the Global Research Data Registry: an AI-agent-native, all-discipline infrastructure for data-source registration, deep mapping, research matching, and distributed snapshot storage.

This repository contains no database snapshot, database-specific adapter, canonical source record, source-archive card, project state, or observation data. Mutable registry and project state lives under external `GRDR_STATE_ROOT`; every selected database is stored in its own private source repository.

## Three-step database factory

GRDR Core fixes the workflow as three independent, Agent-callable Skills:

1. `grdr-plan-database-deep-map` diagnoses an unknown database, defines its bounded work-unit universe, composes route obligations, and fingerprint-locks the Plan.
2. `grdr-execute-database-deep-map` follows the deterministic queue, reconstructs native structure and disciplinary semantics, builds the DataElement → Variable → Construct bridge, and seals the execution without canonical writes.
3. `grdr-store-database-deep-map` transactionally promotes sealed records, inherits the locked knowledge scope, selects full-mirror, partitioned-mirror, or federated observation handling, publishes the callable knowledge and Runtime artifacts, verifies every declared location, writes the central source card, and issues the final Storage receipt.

These three Skills are the database production plane. The independent GRDR Agent Runtime is the use plane: it searches central and distributed variable indexes, performs full manifest and SHA-256 verification before treating a snapshot as callable, resolves a variable to its source-native access plan, and passes the sealed observation-route context to the source-specific runtime. Storage packages and tests the runtime artifact; it does not own search, matching, or retrieval behavior.

## Research use plane

GRDR has six formal Skills in total. `grdr` is the coordinator; the three Skills above produce database snapshots; `grdr-indicator-builder` converts a research question and literature into evidence-linked leaf indicators; and `grdr-resolve-research-semantics` persists the missing R→B entry bridge, traverses the stored B→A graph, evaluates variable fit, explains every selected route, and invokes the verified local, mounted, or official observation route through the source runtime. Agent Runtime and source-specific runtimes are versioned execution code rather than additional Skills.

## Core architecture

The complete architecture is shown in three linked views so that every element remains readable at normal GitHub width: the system overview, the database production plane, and the research use plane. The production view is divided into Plan, Execute, and Storage panels without changing the single three-step workflow.

### 1. End-to-end system overview

```mermaid
flowchart TB
    CORE["GRDR Core v4.2.0<br/><b>database-independent · AI-agent-native</b>"]:::core
    COORD["<b>Skill 1 · grdr</b><br/>coordinate · discover · assess · audit · expand"]:::coreSkill
    SHARED["Shared foundation<br/>ontology · schemas · route contracts · CLI/Runtime<br/>validators · tests · documentation · index-card schema"]:::shared

    subgraph PROD["DATABASE PRODUCTION PLANE"]
        direction LR
        PLAN_OV["<b>Skill 2 · Plan</b><br/>diagnose · bound · compose routes<br/>lock Plan / Scope / Unit manifest"]:::plan
        EXEC_OV["<b>Skill 3 · Execute</b><br/>deterministic deep map<br/>A spine + B spine + measurement bridge"]:::execute
        STORE_OV["<b>Skill 4 · Storage</b><br/>promote · package · publish · verify"]:::storage
        PLAN_OV -->|"locked project"| EXEC_OV -->|"sealed execution"| STORE_OV
    end

    SNAP["One Source → one private repository<br/>One snapshot → knowledge scope + observation replication + placement<br/>location manifest · exact fingerprints · callable runtime"]:::artifact

    subgraph USE["RESEARCH USE PLANE"]
        direction LR
        BUILD_OV["<b>Skill 5 · Indicator Builder</b><br/>question + literature → evidence-linked R"]:::research
        SEM_OV["<b>Skill 6 · Semantic Resolver</b><br/>recall → R→B → B→A → fit → invocation"]:::semantic
        RUN_OV["Agent Runtime + source runtime<br/><i>execution code, not additional Skills</i><br/>search · mount · resolve · call"]:::runtime
        OUT_OV["Verified observations<br/>local · mounted · official upstream<br/>+ path + provenance + uncertainty"]:::result
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

#### 2C. Storage — 三属性快照、三种观测模式、位置清单和最终回执

```mermaid
flowchart TB
        SEALED["Sealed Execute handoff<br/>staged candidates + ledgers + evidence<br/>fingerprinted · no canonical writes"]:::handoff

        subgraph STORAGE["Skill 4 · grdr-store-database-deep-map — STORAGE"]
            direction TB
            S_PROMOTE["Transactional external-state promotion<br/>audit sealed execution · Core remains byte-identical"]:::storage
            S_PROFILE["Three immutable snapshot properties<br/><b>knowledge scope</b> inherited from Plan<br/><b>observation replication</b> + <b>observation placement</b> decided by Storage"]:::storageStrong
            S_CAPACITY["Deployment-local capacity assessment<br/>measure bytes before copying · optional upstream estimate<br/>adjustable GitHub + Elements thresholds<br/><i>size never reduces knowledge depth</i>"]:::storage
            S_PACKAGE["Build one source-scoped callable snapshot<br/>knowledge graph + Execute project + standards/evidence<br/>Agent SQLite index + source runtime"]:::storageStrong
            S_MODES["Observation replication modes<br/><b>full mirror</b> · <b>partitioned mirror</b> · <b>federated on demand</b><br/>each with an explicit completeness claim"]:::storage

            S_REPO["Private source Git repository<br/>Core version reference · config · adapters · runtime code<br/>Plan · manifests · README · tests · archive receipts"]:::artifact
            S_RELEASE["GitHub Release · compressed distribution<br/><b>knowledge/ + agent/ always</b><br/>observations only when explicitly placed here"]:::artifactStrong
            S_ELEMENTS["Elements · expanded callable copy<br/><b>knowledge/ + agent/ always</b><br/>observations only when explicitly placed here"]:::artifactStrong
            S_LARGE["Large-data placement<br/>mounted object store / large disk<br/>partition inventory + SHA-256"]:::artifact
            S_UPSTREAM["Official upstream<br/>federated observations remain authoritative<br/>verified source runtime + access routes"]:::external
            S_CACHE["Use-plane derivative after Storage<br/>on-demand research-project data snapshot<br/>source/snapshot/Variable/arguments/hashes"]:::artifact
            S_MANIFEST["Location-aware manifest<br/>every logical file → exact locations + SHA-256<br/><b>knowledge never contains raw observations</b><br/>no logical file appears in two packages accidentally"]:::verify
            S_VERIFY["Read-back publication verification<br/>repository · tag → exact commit · every asset hash<br/>upload + read back final Storage receipt"]:::verify
            S_RECEIPT["Receipt verified remotely, then sealed locally<br/><b>versioned_database_snapshot</b>"]:::handoff
            S_CARD["External GRDR state source-archive card<br/>Source ID · repository · snapshot · Release<br/>fingerprint · completion status"]:::shared

            SEALED --> S_PROMOTE --> S_PROFILE --> S_CAPACITY --> S_PACKAGE
            S_CAPACITY --> S_MODES
            S_PACKAGE --> S_REPO
            S_PACKAGE --> S_RELEASE
            S_PACKAGE --> S_ELEMENTS
            S_MODES --> S_LARGE
            S_MODES --> S_UPSTREAM
            S_RELEASE --> S_MANIFEST
            S_ELEMENTS --> S_MANIFEST
            S_LARGE --> S_MANIFEST
            S_UPSTREAM --> S_MANIFEST
            S_REPO --> S_VERIFY
            S_MANIFEST --> S_VERIFY
            S_VERIFY --> S_RECEIPT --> S_CARD
            S_CARD -. "later Agent query" .-> S_CACHE
        end

    classDef shared fill:#E8F1F5,stroke:#5E879A,color:#173B57,stroke-width:1.5px;
    classDef handoff fill:#263849,stroke:#17212B,color:#FFFFFF,stroke-width:2px;
    classDef storage fill:#FFF0DF,stroke:#D48638,color:#69370F,stroke-width:1.5px;
    classDef storageStrong fill:#FFE0BF,stroke:#C56A1B,color:#69370F,stroke-width:2px;
    classDef artifact fill:#FFF7ED,stroke:#D48638,color:#69370F,stroke-width:1.5px;
    classDef artifactStrong fill:#FFEAD4,stroke:#C56A1B,color:#69370F,stroke-width:2px;
    classDef external fill:#FFFFFF,stroke:#64748B,color:#263849,stroke-width:1.5px;
    classDef verify fill:#E7F6EC,stroke:#4D9B63,color:#204F2D,stroke-width:2px;
    style STORAGE fill:#FFFAF3,stroke:#D99A5D,stroke-width:1.5px
```

#### 2D. 不同规模数据库的统一处理规则

数据库规模只影响**原始观测数据的复制方式与物理存放位置**，不得降低知识解析深度。无论数据库通常被称为小型、中型还是大型，GRDR 都必须在 Plan 锁定、Execute 验证的知识范围内，完整保存数据库结构、变量语义、方法证据和 Agent 调用能力。这里的“完整”始终对应快照中明确声明的 `knowledge_scope`，不能把局部样本冒充整个上游数据库。

“小型／中型／大型”是当前部署容量策略根据字节数计算出的可调建议，不是数据库固有身份，也不改变三项核心快照属性。实际快照必须记录 Plan 继承的 `knowledge_scope`、Storage 选择的 `observation_replication`、可多选的 `observation_placement`，并附带 `capacity_assessment`，保存当时实际使用的阈值、测量字节数、估计依据、分类和决策。以后硬件升级只需调整外部参数，不需要修改 Skill。

当前默认参数如下。前两项可以在外部配置中调整；第三项是 GitHub 平台的单文件硬约束，不能通过 GRDR 参数突破。

| 参数 | 当前默认值 | 超过后的实际行为 | 是否可调 |
|---|---:|---|---|
| `github_release_observation_max_bytes` | 5 GiB | 不允许把该快照的观测数据配置到 GitHub Release；知识和 Agent 制品仍照常发布 | 是 |
| `elements_full_mirror_max_bytes` | 10 GiB | 不允许继续选择 Elements 完整镜像；改用分区镜像、联邦调用或具备容量的挂载存储 | 是 |
| `github_release_asset_max_bytes` | 严格低于 2 GiB／文件 | 任何知识、Agent 或观测 Release 文件超限都必须重新分包，不能发布 | 只能调低，不能超过平台上限 |

默认推荐分类为：不超过 GitHub 阈值是“小型”；超过 GitHub 阈值但不超过 Elements 完整镜像阈值是“中型”；超过 Elements 阈值是“大型”。分区或联邦快照如果没有可靠的上游总体量估计，则分类明确记为 `unknown`，不会用已经复制的局部数据量冒充整个数据库规模。

| 内容或能力 | 所有数据库的硬性规则 | 常见小型数据库 | 常见中型数据库 | 常见大型或持续更新数据库 |
|---|---|---|---|---|
| 机构、发布者与数据源身份 | 在锁定范围内完整保存，并保留官方来源和版本证据 | 完整保存 | 完整保存 | 完整保存 |
| 数据集目录与包含关系 | 完整保存 Dataset 及其父子、版本和派生关系 | 完整保存 | 完整保存 | 完整保存 |
| 数据库原生结构 | 完整保存表、目录、主题、立方体、序列、文件、字段等递归 `DataStructure` | 完整保存 | 完整保存 | 完整保存 |
| 5A 数据元素 | 完整保存指标、测度、维度、标识符、单位、权重、状态标记和派生元素 | 完整保存 | 完整保存 | 完整保存 |
| 5B 变量 | 完整保存定义、总体、观察单位、分析单位、时间、地理和适用范围 | 完整保存 | 完整保存 | 完整保存 |
| 学科语义与理论构念 | 完整保存多父节点 B 主干、Construct 和适用学科语境 | 完整保存 | 完整保存 | 完整保存 |
| A—B 映射桥梁 | 完整保存 DataElement → Variable → Construct 的可追溯关系 | 完整保存 | 完整保存 | 完整保存 |
| 方法、口径、质量与证据 | 完整保存方法说明、分类标准、修订、限制、来源和证据定位 | 完整保存 | 完整保存 | 完整保存 |
| 访问方式 | 作为 Resource 侧车保存 API、下载、查询器、许可和访问约束，不占用内容层级 | 完整保存 | 完整保存 | 完整保存 |
| Agent 知识制品 | 必须保存知识图谱、Agent SQLite 索引、变量访问计划和来源专属 Runtime | 完整保存 | 完整保存 | 完整保存 |
| 原始观测数据复制 | 只允许由观测策略决定；不得混入 `knowledge/` | 通常完整镜像 | 完整镜像或按年份、国家、主题等分区镜像 | 通常保留在官方上游，按需调用；条件允许时仍可镜像 |
| 未复制的原始观测数据 | 必须保留可验证的官方位置和可执行访问路径 | 通常没有 | 未镜像部分保留在官方上游 | 保留在官方上游 |
| 研究项目数据快照 | 按需把一次查询的参数、结果、来源快照、变量 ID 和哈希封存到研究项目 | 可选 | 推荐 | 推荐 |
| 完整性声明 | 必须明确知识边界、观测复制边界、文件或分区数量及其依据 | 完整范围声明 | 完整范围或声明分区集 | 知识完整、观测联邦调用声明 |

因此，大型数据库不是“少解析一部分”，而是**完整理解以后不重复搬走全部数值**；中型数据库也不必强制复制。如果某个中型数据库无法合理镜像，就使用联邦按需调用；如果某个大型数据库实际能够完整复制，也可以选择完整镜像。

##### 三种原始观测数据处理模式

| Storage 模式 | 适用判断 | 快照中的原始观测数据 | 允许的主要位置 | 强制完整性声明 | Agent 使用方式 | 完成前必须核验 |
|---|---|---|---|---|---|---|
| `full_mirror` 完整镜像 | 锁定范围内的全部观测文件能够复制和持续管理，且所选物理位置没有超过其配置阈值 | 声明范围内全部复制 | GitHub Release、Elements、挂载对象存储，可多选；GitHub 不是必选 | `complete_within_knowledge_scope` | Runtime 获得位置上下文并使用已核验的 Elements 或挂载镜像 | 权威文件分母、预期与实际文件数、实际字节数、逐文件 SHA-256、所选位置和容量策略 |
| `partitioned_mirror` 分区镜像 | 只复制明确且有研究价值的年份、国家、主题或其他分区 | 仅复制分区清单中声明的完整分区 | GitHub Release、Elements、挂载对象存储，可配研究项目缓存 | `complete_declared_partition_set` | Runtime 优先使用已核验的本地／挂载分区；范围外数据只有在登记了官方路径时才联邦调用 | Schema 有效的分区清单；每个分区的边界、名称、成员路径、大小、SHA-256；预期与实际分区数和文件数完全一致 |
| `federated_on_demand` 联邦按需调用 | 整体复制不合理、数据持续更新，或官方查询服务更适合调用 | 规范快照中不复制原始观测文件 | `official_upstream`，可声明未来允许 `research_project_cache`；不得伪装为本地镜像 | `knowledge_complete_observations_federated` | Runtime 从已核验的官方服务按变量和参数获取；查询发生后才可封存研究项目快照 | **Storage 完成时**只核验官方地址、来源专属 Runtime 和全部变量可解析；查询结果和项目快照哈希属于以后实际调用的验收，不是 Storage 完成条件 |

选择顺序是：先锁定并完成同等深度的知识解析，再根据观测数据的实际体量、分区性、更新频率、官方接口和可维护性选择模式。不得先用“数据库很大”作为理由缩减知识范围，也不得为了宣称完整而把未复制的数据写成已经镜像。

##### 知识、观测与备份的关系

`knowledge/` 与 `observations/` 在逻辑上必须彻底分离，但通过 Source ID、Snapshot ID、Dataset／Variable ID、位置清单和 SHA-256 精确连接。Agent 的标准调用顺序是：检索知识索引 → 解析变量和访问计划 → 定位并核验观测资产 → 获取数值 → 必要时封存研究项目数据快照。

- 原始观测文件不得同时混入知识包和观测包；跨逻辑包出现相同内容哈希时，Storage 必须失败。
- 同一观测资产可以在 GitHub Release、Elements 或对象存储中保留经过核验的物理镜像。多份镜像提高在线可得性、本地速度和灾难恢复能力，但不会改变数据本身的统计准确性。
- `location-aware manifest` 必须记录每个逻辑文件的实际位置和哈希，使 Agent 能确认不同位置对应同一快照，而不是两个互相冲突的版本。
- 研究项目缓存是带查询范围和来源证据的派生快照，不得冒充数据库的规范观测镜像。

### 3. Research use plane: R → B → A → verified observation route

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
        RECALL["1 · Full-text candidate recall<br/>Construct · SemanticNode · Variable<br/><i>latest callable by default · history only when explicit<br/>candidate ≠ conclusion</i>"]:::resolver
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
    ROUTER["Location-aware observation router<br/>sealed mode + placements + verified paths"]:::runtime
    LOCAL["Verified Elements mirror<br/>full or declared partitions"]:::local
    MOUNTED["Verified mounted mirror<br/>object store / large disk"]:::local
    UPSTREAM["Authoritative upstream route<br/>official API · file · query service"]:::external
    RESULT["Research-ready output<br/>data + source + snapshot + Variable<br/>alignment/path + provenance + uncertainty"]:::result
    GAP["Data-gap diagnosis<br/>missing construct · variable · population · unit<br/>time · space · modality · joinability"]:::gap
    EXPAND["Expansion and rerun<br/>discover or deepen source → Plan → Execute → Storage<br/>→ rebuild recall/alignment/path → rerun matching"]:::shared

    INVOKE --> SOURCE_RUNTIME --> ROUTER
    ROUTER -->|"elements_mirror"| LOCAL --> RESULT
    ROUTER -->|"mounted_object_store"| MOUNTED --> RESULT
    ROUTER -->|"official_upstream"| UPSTREAM --> RESULT
    FIT -->|"not_found_registry_snapshot / incompatible"| GAP --> EXPAND

    classDef research fill:#FDECF1,stroke:#C76884,color:#6E243D,stroke-width:1.5px;
    classDef researchStrong fill:#F8D8E3,stroke:#B84A6C,color:#6E243D,stroke-width:2px;
    classDef rNode fill:#FFF0F5,stroke:#C4557B,color:#6E243D,stroke-width:2px;
    classDef gate fill:#FFF1C7,stroke:#C78A1D,color:#664500,stroke-width:1.5px;
    classDef resolver fill:#EEE9FF,stroke:#7B62C5,color:#3F2A72,stroke-width:1.5px;
    classDef resolverStrong fill:#DED3FF,stroke:#6646B7,color:#3F2A72,stroke-width:2px;
    classDef runtime fill:#E5F3FF,stroke:#4787B8,color:#173B57,stroke-width:2px;
    classDef local fill:#E7F6EC,stroke:#4D9B63,color:#204F2D,stroke-width:2px;
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

Each deeply processed database keeps its own configuration, adapters, Plan, Execute package, full knowledge snapshot, Agent index, source runtime, observation-location manifest, and Release history outside this repository. Full and partitioned mirrors keep the declared observation bytes only at their selected locations; federated snapshots keep official routes and create query-scoped research-project data snapshots on demand. Source repositories reference a Core version; they never copy the Core.

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

# Persist an external Elements root once for all Agent Runtime commands.
python3 scripts/configure_core.py --elements-root /absolute/path/to/GRDR

# Optional deployment policy; change these values later as storage hardware changes.
python3 scripts/configure_core.py \
  --github-observation-max-gib 5 \
  --elements-full-mirror-max-gib 10

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
.venv/bin/python scripts/grdr.py prepare-semantic-candidates <research-project> --snapshot-policy latest_callable
.venv/bin/python scripts/grdr.py prepare-semantic-candidates <research-project> --snapshot-policy history  # explicit longitudinal use only
.venv/bin/python scripts/grdr.py align-research-indicators <research-project> <decisions.jsonl>
.venv/bin/python scripts/grdr.py traverse-semantic-paths <research-project>
.venv/bin/python scripts/grdr.py match-indicators <research-project>
.venv/bin/python scripts/grdr.py explain-indicator-match <research-project> <indicator-id>
.venv/bin/python scripts/grdr.py fetch-indicator-data <research-project> <indicator-id> --dry-run
.venv/bin/python scripts/grdr.py fetch-indicator-data <research-project> <indicator-id> --seal-data-snapshot
.venv/bin/python scripts/grdr.py search-variables --construct <construct>
.venv/bin/python scripts/grdr.py resolve-variable-access <variable-id>
.venv/bin/python scripts/grdr.py fetch-variable <variable-id> --dry-run
.venv/bin/python scripts/grdr.py fetch-variable <variable-id> --research-project-dir <research-project>
```

See [the database factory workflow](docs/DATABASE_DEEP_MAP_WORKFLOW.md) and [the North Star](docs/NORTH_STAR.md).

## Validation

```bash
.venv/bin/python scripts/validate_registry.py
.venv/bin/python scripts/build_catalog.py --check
.venv/bin/python scripts/check_release.py
.venv/bin/python -m unittest discover -s tests -v
```

Version `4.2.0` closes the scalable-Storage and Runtime trust boundary: deployment-local capacity thresholds are adjustable and sealed into each snapshot decision; partition manifests must exactly match their copied members; every normal Runtime operation fully verifies the local manifest-bound inventory; mirror, mounted, and upstream routes are explicit; and a snapshot cannot become complete until its final Storage receipt has been uploaded to GitHub and verified by read-back. Knowledge scope remains locked to Plan, and raw observations remain forbidden from the knowledge package.
