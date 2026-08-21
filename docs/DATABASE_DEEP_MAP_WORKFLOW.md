# GRDR 数据库三步深读工厂

## 总则

面对一个数据库，GRDR 固定执行：

```text
Step 1 Plan：诊断 → 定边界 → 建工作单元 → 锁定计划
      ↓ 指纹锁定的工程
Step 2 Execute：逐单元深读 → 两根主干/一座桥 → 暂存规范记录
      ↓ 密封且带指纹的归档包
Step 3 Archive：冲突审计 → 正式入库 → 重建人类目录 → 签发收据
```

三个步骤分别由独立 Skill 承担：

- `$grdr-plan-database-deep-map`
- `$grdr-execute-database-deep-map`
- `$grdr-archive-database-deep-map`

`$grdr` 是全库控制器，负责先登记 Source、选择上述步骤、研究问题匹配和数据缺口扩展。

最重要的工程隔离是：Step 2 只能写项目内 `staging/`；只有 Step 3 能写 `registry/*.jsonl`。没有有效归档收据，就不能宣称数据库已正式读入 GRDR。

严格规划和审计需要 `jsonschema`：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-validation.txt
```

## Step 1：Plan

### 1. 证据化诊断

调查数据库的规范身份、维护者和各类生产/聚合/镜像角色；一手、二手或混合来源；数据生成过程；学科归属；原生结构和内容模态；版本、修订、追加、滚动与删除；元数据和观测数据访问；认证、付费、许可、隐私、伦理、主权；规模、分区、限流、语言和元数据成熟度。

学科和结构都是多标签。一个库可以同时服务经济、环境、能源和公共政策，也可以同时含目录、统计立方体、文件与调查。类型注册表是可组合路线，不是互斥分类树。未知形态使用 `open_world_custom`。

```bash
.venv/bin/python scripts/grdr.py list-database-route-modules
.venv/bin/python scripts/grdr.py plan-database-deep-map <intake.json> --output <plan.json>
.venv/bin/python scripts/grdr.py audit-database-deep-map-plan <plan.json>
```

状态只有：

- `ready`：可建立执行工程；
- `ready_with_gates`：只能做未受保护部分；
- `needs_evidence`：继续只读调查；
- `blocked`：当前约束禁止必要工作。

### 2. 锁定完成边界

完整不是一句“100%”，而是一个带日期、版本或窗口的声明，例如代表性链、问题适配、目录级、边界分区、完整快照或滚动当前窗口。

可枚举边界必须固定分母、身份、顺序和快照；完整快照的分母包括废弃、空、受限和暂时不可访问条目。动态、联邦、虚拟或真实不可枚举系统使用可复现的窗口、成员清单、查询计划或稳定分区，不能把当前抓到的内容冒充全库。

### 3. 建立锁定工程

未知数据库要先由 `$grdr` 解析并登记规范 Source 身份。然后：

```bash
.venv/bin/python scripts/grdr.py start-database-deep-map <start-spec.json>
.venv/bin/python scripts/grdr.py upgrade-database-deep-map <legacy-project>
.venv/bin/python scripts/grdr.py database-deep-map-status <project>
```

Step 1 交付：

- `project.json`：schema 3、三步合同、计划、边界、阶段、人工门和三类锁；
- `units.jsonl`：稳定有序的工作单元；
- `checks.jsonl`：适用路线的全部义务；
- `staging_manifest.json`：空且开放；
- `README.md`：人类可读进度。

Step 1 不提取内容、不写暂存记录、不写正式注册表。

## Step 2：Execute

### 1. 按机器状态恢复

```bash
.venv/bin/python scripts/grdr.py audit-database-deep-map-execution <project>
.venv/bin/python scripts/grdr.py database-deep-map-status <project>
.venv/bin/python scripts/grdr.py resume-database-deep-map <project>
```

每次只执行返回的 `next_target`。不得换成容易样例。计划、范围、分母、工作单元身份/顺序或路线变化会触发指纹错误。

### 2. 六个执行阶段

每个工作单元通常以 Dataset 为锚点：

1. `dataset`：生产者、方法、总体、观察/分析单位、覆盖、版本、质量、限制和引用；
2. `data_structure`：递归恢复目录、集合、模式、表、视图、数据流、立方体、问卷、仪器、图、语料、数组、流、运行、实验或文件层级；
3. `data_element`（5A）：原生测度、字段、维度、标识符、题项、代码、权重、属性、标记、坐标、片段、注释和派生字段；
4. `variable`（5B）：可研究匹配的操作量，包含单位、总体、分辨率、维度选择、可比性、身份和连接键；
5. `construct`：有证据的理论/科学含义及直接、自陈、行政、构造、模型、预测、代理或潜变量性质；
6. `access`：分别测试元数据与观测数据，记录 API、文件、查询器、安全环境、认证、许可、限流和复现条件。

Resource 是访问旁路，不是第4层。

### 3. 两根主干和一座桥

- 数据库原生结构主干：Dataset → 递归 DataStructure → DataElement → Variable；
- 学科与科学语义主干：多父节点 SemanticNode → Construct；
- 变量桥梁：DataElement/DataStructure 上下文 → Variable → Construct。

Institution 和 Source 是项目级来源上下文。对象计数、图谱连通、路线义务分别验收，不能互相替代。

### 4. 暂存后闭合账本

先生成符合 Schema 的候选记录并暂存：

```bash
.venv/bin/python scripts/grdr.py stage-database-deep-map-records <project> <records.jsonl>
```

系统验证候选记录和“正式库 + 暂存区”的合并前景，记录基础/暂存指纹，只写 `<project>/staging/*.jsonl`，失败则回滚。此时 `registry/*.jsonl` 必须不变。

再登记证据化阶段、主干和路线检查：

```bash
.venv/bin/python scripts/grdr.py record-database-deep-map-stage <project> <stage-update.json>
.venv/bin/python scripts/grdr.py record-database-deep-map-spine <project> <spine-update.json>
.venv/bin/python scripts/grdr.py record-database-deep-map-phase <project> <phase-update.json>
.venv/bin/python scripts/grdr.py record-database-deep-map-check <project> <check-update.json>
```

阶段内保存原生枚举规则、已完成数、最后/下一个 ID、日期/版本、分区和校验值。受限、付费、动态、删除或真实不可枚举内容不承诺上游完整，但必须精确保留 blocker 或有边界声明，其余合法可做分支继续推进。

### 5. 密封交接

当 `execution_ready_for_archive: true`：

```bash
.venv/bin/python scripts/grdr.py prepare-database-deep-map-archive <project>
.venv/bin/python scripts/grdr.py audit-database-deep-map-archive <project>
```

生成 `archive_package.json` 并密封暂存清单。密封后不得修改内容账本和候选记录。

## Step 3：Archive

先只读审计：

```bash
.venv/bin/python scripts/grdr.py database-deep-map-archive-status <project>
.venv/bin/python scripts/grdr.py audit-database-deep-map-archive <project>
```

审计重新计算计划、范围、工作单元、执行账本、暂存清单和包指纹，并检查每个 create/update/unchanged 候选的基础版本是否与当前正式库一致。冲突必须回到新一轮 Execute，不得手改包或正式记录。

只有 `ready_to_archive: true` 才运行：

```bash
.venv/bin/python scripts/grdr.py archive-database-deep-map <project>
```

归档以事务方式写正式集合、验证全库、重建和检查人类目录、签发 `archive_receipt.json`。任何写后门槛失败都回滚正式集合、目录、项目、清单和收据。有效收据使重复调用幂等。

最终核验：

```bash
.venv/bin/python scripts/grdr.py database-deep-map-archive-status <project>
.venv/bin/python scripts/grdr.py audit-database-deep-map <project>
.venv/bin/python scripts/validate_registry.py
.venv/bin/python scripts/build_catalog.py --check
```

只有 `archive_complete: true` 且 `completion_ready: true` 才表示本轮边界正式入库完成。

## 人工门控

Agent 不能自行批准隐私、伦理、社区主权、访问授权、争议语义或发布范围。只有用户明确给出具名决定后才能记录：

```bash
.venv/bin/python scripts/grdr.py record-database-deep-map-human-gate <project> <gate-id> --decision <approved|rejected|not_applicable> --reviewer <name> --notes <basis>
```

沉默不是批准，访问失败不是不适用，AI 推断不是官方定义。
