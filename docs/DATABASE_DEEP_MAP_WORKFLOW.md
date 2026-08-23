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
中央入库 → 独立源仓库 → 完整知识包 → Agent索引 → 观测数据
→ GitHub Release → Elements展开镜像 → 一致性核验 → 中央卡片 → Storage回执
        ↓ versioned_database_snapshot
```

三个独立Skill是：

- `$grdr-plan-database-deep-map`
- `$grdr-execute-database-deep-map`
- `$grdr-store-database-deep-map`

原来的Archive只是Storage内部的“中央注册表事务归档”，不再是第三个公开Skill，也不能单独代表数据库已经完成存储。

## Step 1：Plan

Plan负责数据库身份、学科多父归属、数据生成过程、原生结构、版本生命周期、元数据与观测数据入口、规模、边界、工作单元和路线契约。结构与学科均为可组合多标签，不使用互斥分类树；未知形态使用`open_world_custom`。

```bash
.venv/bin/python scripts/grdr.py plan-database-deep-map <intake.json> --output <plan.json>
.venv/bin/python scripts/grdr.py audit-database-deep-map-plan <plan.json>
.venv/bin/python scripts/grdr.py start-database-deep-map <start-spec.json>
```

交付物是schema 3.2工程、锁定Plan、固定边界、稳定有序的`units.jsonl`、路线义务`checks.jsonl`和空的暂存清单。Plan不读取工作单元内容、不写暂存记录、不写中央注册表。

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
| GRDR核心仓库 | Source卡片、独立仓库、最新快照、Release、清单、指纹和状态 | 否 |
| 数据库独立私有Git仓库 | Core版本引用、配置、适配器、Plan、快照清单、README、测试、中央入库回执 | 只保存小型可审查内容 |
| 数据库GitHub Release | 完整知识快照、Execute工程、规范记录、证据、Agent SQLite索引、全部观测数据和Storage回执 | 是 |
| Elements磁盘 | 与Release相同逻辑快照的完整展开目录 | 是 |

一个Source对应一个独立仓库；一个快照对应一个Release和一个Elements快照目录。独立仓库引用GRDR Core版本，不复制Core Skill。

### 逻辑快照

Release是压缩分发形式，Elements是展开工作形式。两者物理形态不同，但必须覆盖完全相同的：

```text
knowledge/
agent/grdr-agent-index.sqlite
observations/
```

清单逐文件保存逻辑路径、SHA-256与字节数，并保存每个Release资产的SHA-256与展开成员。任何缺失、额外文件或哈希差异均阻止完成。

### 执行命令

先写Storage specification，明确Source、快照、Core版本、独立私有仓库、Release、Elements根目录、观测数据输入和适配器：

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

Storage拒绝零观测文件、观测数据总字节数为零、复用已有但内容不同的快照路径、非GRDR文件覆盖、Release与Elements不一致、未验证GitHub发布、失效回执或中央卡片不一致。

## 完成定义

机器状态依次区分：

1. `execution_ready_for_storage`：Execute已密封；
2. `canonical_archive_complete`：知识记录已事务写入中央GRDR；
3. `ready_for_publish`：源仓库、Release资产和Elements已在本地构建并一致；
4. `storage_complete`：GitHub仓库和Release已验证，Elements存在，中央卡片与Storage回执有效；
5. `completion_ready`：Plan、Execute和Storage全部通过。

只有第4和第5项同时为真，才能说某个数据库已经按照GRDR三步工厂完整收录并存档。核心仓库不保存任何真实数据库工程，因此这里不声明任何具体数据库已经完成。
