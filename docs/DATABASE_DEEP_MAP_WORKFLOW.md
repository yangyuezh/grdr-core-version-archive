# GRDR 数据库三步工厂

## 唯一正式流程

面对一个被选中深入收录的数据库，GRDR 固定执行：

```text
Step 1 Plan
诊断数据库 → 固定边界与分母 → 生成工作单元 → 锁定指纹
        ↓ locked_deep_map_project
Step 2 Execute
逐单元深读 → 恢复两根主干和一座桥 → 暂存规范记录 → 密封执行包
        ↓ sealed_deep_map_execution
Step 3 Storage
中央入库 → 继承知识范围 → 完成全部变量的在线调用 → 独立选择观测复制与位置
→ 独立源仓库 → 完整知识包 → Agent Runtime 2.0／索引 → 双清单与审计
→ 发布核验 → 中央卡片 → Storage回执
        ↓ versioned_database_snapshot
```

三个独立Skill是：

- `$grdr-plan-database-deep-map`
- `$grdr-execute-database-deep-map`
- `$grdr-store-database-deep-map`

原来的Archive只是Storage内部的“中央注册表事务归档”，不再是第三个公开Skill，也不能单独代表数据库已经完成存储。

三步工厂是数据库生产面。统一检索、变量匹配、快照挂载、访问计划解析和实际数据调用属于独立的GRDR Agent Runtime使用面，不是第四个生产步骤，也不并入Storage。Storage负责把来源专属 Runtime 作为快照制品保存，并在交付前验证全部已登记变量既能离线解析访问计划，也至少拥有一条已经测试的在线执行路线。

## Step 1：Plan

Plan负责数据库身份、学科多父归属、数据生成过程、原生结构、版本生命周期、元数据与观测数据入口、规模、边界、工作单元和路线契约。结构与学科均为可组合多标签，不使用互斥分类树；未知形态使用`open_world_custom`。

```bash
.venv/bin/python scripts/grdr.py plan-database-deep-map <intake.json> --output <plan.json>
.venv/bin/python scripts/grdr.py audit-database-deep-map-plan <plan.json>
.venv/bin/python scripts/grdr.py start-database-deep-map <start-spec.json>
```

交付物是schema 4.1工程、锁定Plan、固定边界、稳定有序的`units.jsonl`、路线义务`checks.jsonl`和空的暂存清单。Plan不读取工作单元内容、不写暂存记录、不写中央注册表。

## Step 2：Execute

Execute只在Plan锁定边界内运行，每次从机器状态返回唯一的`next_target`。六个内容阶段是Dataset、递归DataStructure、5A DataElement、5B Variable、Construct和Access；同时闭合：

- 原生结构主干：Dataset → DataStructure → DataElement → Variable；
- 学科与科学语义主干：多父SemanticNode → Construct；
- 变量桥梁：DataElement/DataStructure上下文 → Variable → Construct。

```bash
.venv/bin/python scripts/grdr.py audit-database-deep-map-execution <project>
.venv/bin/python scripts/grdr.py resume-database-deep-map <project>
.venv/bin/python scripts/grdr.py stage-database-deep-map-records <project> <records.jsonl>
.venv/bin/python scripts/grdr.py record-database-deep-map-execution-batch <project> <batch.json>
.venv/bin/python scripts/grdr.py prepare-database-deep-map-storage <project>
```

Execute只写工程内部`staging/`及账本。`execution_ready_for_storage: true`表示密封执行可以交给Storage，不表示中央入库、GitHub Release或Elements已经完成。

## Step 3：Storage

### 固定存储位置

| 位置 | 保存内容 | 完整数据 |
|---|---|---|
| 外部GRDR状态目录 | Source卡片、独立仓库、最新快照、Release、清单、指纹和状态 | 否 |
| 数据库独立私有Git仓库 | Core版本引用、配置、适配器、源运行时代码、Plan、快照清单、README、测试、中央入库回执 | 只保存小型可审查内容 |
| 数据库GitHub Release | 完整知识快照、Execute工程、规范记录、证据、Agent运行时与SQLite索引、清单、回执；仅在策略指定时保存观测数据 | 知识与Agent完整 |
| Elements磁盘 | 完整知识与Agent展开目录；仅在策略指定时保存观测数据 | 知识与Agent完整 |
| 大型数据存储 | 完整或分区观测镜像及逐文件哈希 | 按完整性声明 |
| 官方上游 | 所有数据库都必须建设和测试的首选在线调用路线；可为API、整表下载或网页自动化 | 不属于复制位置 |

一个Source对应一个独立仓库；一个快照对应一个Release和一个Elements快照目录。独立仓库引用GRDR Core版本，不复制Core Skill。

### 三个独立判断轴

Storage必须保存：

1. `knowledge_scope`：直接继承Plan的范围、完成声明、边界和范围指纹，Storage不得修改；
2. `online_access`：覆盖全部已登记Variable的可执行路线、官方可用状态、路线优先级和实际在线测试证据；
3. `observation_replication`：`full_mirror`、`partitioned_mirror`或`no_mirror`，以及GitHub Release、Elements、挂载对象存储中的实际复制位置。

快照还必须保存`capacity_assessment`：实际捕获字节数、可选的上游总体量估计、当时启用的外部容量阈值、策略相对的规模分类和最终模式。默认GitHub观测总量阈值为5 GiB、Elements完整镜像阈值为10 GiB；两者都可随硬件调整。GitHub每个Release文件必须严格小于2 GiB。

知识拆解是否完整、在线调用是否完整、观测数据复制多少是三个独立结论。容量阈值只能改变第三项；不能降低知识深度，也不能豁免在线变量覆盖。

### 逻辑快照与去重

Release是压缩分发形式，Elements是展开工作形式。两者始终共同覆盖：

```text
knowledge/
agent/grdr-agent-index.sqlite
agent/runtime.json
agent/<source-runtime>.py
agent/runtime_audit.json
agent/online_access.json
agent/online_runtime_audit.json
```

`observations/`只出现在策略指定的位置。清单逐文件保存逻辑路径、实际位置、SHA-256与字节数，并保存每个Release资产的SHA-256与展开成员。

`knowledge/`不得包含任何原始观测文件。Storage会按输入路径排除工程内的原始观测目录，并检查knowledge与observations之间的内容哈希交集；发现重复即阻止完成。GitHub与Elements不再要求拥有相同的全部观测文件，只要求各自与位置清单完全一致。

### 执行命令

先写Schema 4.0 Storage specification，明确Source、快照、Core版本、独立私有仓库、Release、Elements根目录、三个判断轴、观测数据输入、在线路线、适配器和来源专属Runtime：

```bash
.venv/bin/python scripts/grdr.py prepare-database-storage <project> <storage-spec.json>
.venv/bin/python scripts/grdr.py audit-database-storage <project>
.venv/bin/python scripts/grdr.py publish-database-storage <project>
.venv/bin/python scripts/grdr.py database-storage-status <project>
```

也可以端到端运行：

```bash
.venv/bin/python scripts/grdr.py store-database-deep-map <project> <storage-spec.json>
```

完整镜像和分区镜像拒绝零观测文件、零总字节数和声明分母不一致；分区镜像还要求Schema有效的分区清单逐项匹配分区边界、名称、成员路径、大小和SHA-256；`no_mirror`要求零观测输入和零复制位置。三种复制模式一律要求Runtime 2.0在线自检：路线清单与测试结果完全对应，每个已登记Variable至少映射一条可执行路线，未解决数量必须为零。所有模式都拒绝超出所选位置容量阈值、Runtime不能解析全部索引变量、在线覆盖不完整、knowledge与observations重复、复用已有但内容不同的快照路径、非GRDR文件覆盖、位置清单不一致、未验证GitHub发布、失效回执或中央卡片不一致。

发布顺序是硬约束：先上传并核验知识、Agent和可选观测资产，再生成并上传最终Storage回执；只有从GitHub重新读取并核验回执、Release标签、精确提交和所有资产哈希以后，才能写本地／Elements回执、中央卡片和`complete`状态。

## 独立Agent Runtime使用面

Storage完成后，Core按以下链路使用快照：

```text
research question
→ search-variables（中央记录 + 本地分布式索引）
→ source-snapshot-status / materialize-source-snapshot
→ resolve-variable-access
→ fetch-variable --route-policy latest|reproducible|offline
→ 按策略尝试官方在线／GRDR Release／Elements／挂载镜像
→ 原始字节、筛选结果与provenance
```

GitHub Release是在线知识与Agent分发版，也可在观测资产实际放入Release且路线通过测试时充当在线数据后备。Elements是本地可调用展开版。`latest`默认先尝试官方在线路线，`reproducible`优先冻结快照，`offline`只允许本地或挂载复制；每次回退均写入调用结果。研究调用可用`fetch-variable --research-project-dir`或`fetch-indicator-data --seal-data-snapshot`生成带路由策略、实际选中路线、查询参数、来源、快照、变量和逐文件哈希的项目级数据快照。

## 完成定义

机器状态依次区分：

1. `execution_ready_for_storage`：Execute已密封；
2. `canonical_archive_complete`：知识记录已事务写入中央GRDR；
3. `ready_for_publish`：源仓库、Release资产和Elements已在本地构建并一致，全部变量的在线路线测试通过；
4. `storage_complete`：GitHub仓库和Release已验证，Elements存在，在线清单／审计、中央卡片与Storage回执有效；
5. `completion_ready`：Plan、Execute和Storage全部通过。

只有第4和第5项同时为真，才能说某个数据库已经按照GRDR三步工厂完整收录并存档。核心仓库不保存任何真实数据库工程，因此这里不声明任何具体数据库已经完成。
