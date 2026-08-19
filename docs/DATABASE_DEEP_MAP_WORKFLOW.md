# GRDR 开放世界数据库深读工程流程

## 目标

六层模型规定“进入 GRDR 后登记什么”；本流程规定“面对任意数据库，Agent 怎样诊断、制定路线、持续推进并证明完成”。它不假设数据库一定是表格、API 或统计库，也不把有限类型清单冒充全世界数据库的封闭分类。

```text
证据化预诊断
  → 生成可审计执行计划
  → 固定完成声明与边界
  → 建立稳定工作单元清单
  → 六个内容阶段 × 可组合路线契约
  → 异常恢复与人工门控
  → 严格完成审计
```

每个非平凡数据库建立一个 `deep_map_projects/<source-or-pass>/` 持久工程，避免 Agent 只做方便样例、遗漏异构结构、在会话切换后丢失进度，或者把局部链条误报为完整数据库。

严格规划与审计要求 `jsonschema`。首次运行先创建项目本地环境：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-validation.txt
```

后续严格命令使用 `.venv/bin/python`；依赖缺失时工具必须失败，不能把跳过 Schema 校验报告为通过。

## 第一阶段：开放世界预诊断

先建立 `database_deep_map_intake`，至少调查：

- 数据库规范身份、机构角色与权威边界；
- 一手、二手或混合来源，生产者、协调者、镜像、聚合者或联邦角色；
- 数据生成过程；
- 内部结构与内容模态；
- 快照、版本、修订、追加、滚动、流式、删除等生命周期；
- 版本模型；
- 开放、注册、商业、受限或安全环境等访问制度；
- 隐私、伦理、安全、社区主权与其他治理属性；
- 规模、计算约束、元数据成熟度、语言和编码；
- 本轮研究目的、完成声明、边界、工作单元、分母和授权约束。

```bash
python3 scripts/grdr.py list-database-route-modules
python3 scripts/grdr.py plan-database-deep-map <intake-or-start-spec.json> --output <plan.json>
python3 scripts/grdr.py audit-database-deep-map-plan <plan.json>
```

计划状态只有四种：

- `ready`：可以执行；
- `ready_with_gates`：可以执行不受保护的部分，敏感操作等待具名人工决定；
- `needs_evidence`：关键诊断仍未知，继续只读调查，不启动正式工程；
- `blocked`：当前约束禁止必要操作。

规划器永远加入通用义务，并从机器可读路线契约中组合适配模块。如果现有模块不能解释数据库，使用 `open_world_custom` 保留观察事实和缺口，不能强行塞入最相似类别。

## 第二阶段：固定真实的完成边界

完成必须说明是哪一种：代表性链、研究问题适配、目录级、高价值子集、边界分区、完整快照或滚动当前窗口。

可枚举数据库应固定日期/版本、枚举规则、稳定身份、顺序和预期数量。完整快照的分母包括废弃、空、受限和暂时不可访问条目。动态流、联邦库和不可枚举系统改用可审计的窗口、成员清单、查询计划或逻辑工作单元，不能用“当前能抓到多少”代表数据库全体。

## 第三阶段：建立执行工程

```bash
python3 scripts/grdr.py start-database-deep-map <start-spec.json>
python3 scripts/grdr.py upgrade-database-deep-map <legacy-project>
```

工程含四个核心文件：

- `project.json`：诊断计划、范围、阶段、门槛、历史和状态；
- `units.jsonl`：有顺序的工作单元及六阶段状态；
- `checks.jsonl`：数据库形态特有的路线义务、证据和类型化阻塞；
- `README.md`：供人查看的自动生成进度报告。

工作单元通常是 Dataset，也可以是稳定的 Collection、Study、Site extract、Graph、Corpus、Instrument、Model experiment、Catalog partition 或 Rolling window partition。混合门户在每个工作单元重新确认路线，不能只用门户级标签覆盖全部单元。

## 第四阶段：按确定队列深读

```bash
python3 scripts/grdr.py database-deep-map-status <project>
python3 scripts/grdr.py resume-database-deep-map <project>
```

`status`和`audit`只读；`resume`写入恢复历史。Agent 必须执行返回的 `next_target`，并在阶段内部按官方顺序或完整原生 ID 稳定顺序推进。

每个工作单元固定执行：

1. `dataset`：身份、生产者、总体、观察单位、方法、覆盖、版本、质量、限制、引用；
2. `data_structure`：数据库原生目录、模式、表、数据流、问卷、仪器、数组、图、语料、运行或文件拓扑；
3. `data_element`：字段、测度、维度、标识符、题项、代码、权重、属性、标记、坐标、片段、注释；
4. `variable`：定义、单位、总体、分辨率、维度选择、可比性、身份与连接键完整的操作变量；
5. `construct`：有证据的研究含义及直接、自陈、行政、构造、模型、预测、代理或潜变量性质；
6. `access`：分别测试元数据与观测数据，登记文件/API/查询器/安全环境、认证、许可、限流与复现条件。

Resource 仍是 Dataset 或 DataStructure 的访问旁路，不占内容层级。

## 第五阶段：同时闭合“对象阶段”和“路线契约”

```bash
python3 scripts/grdr.py record-database-deep-map-stage <project> <stage-update.json>
python3 scripts/grdr.py record-database-deep-map-phase <project> <phase-update.json>
python3 scripts/grdr.py record-database-deep-map-check <project> <check-update.json>
```

阶段记录回答“登记了哪些规范对象，数量是否闭合”；路线检查回答“该数据库形态独有的义务是否完成”。例如，统计立方体必须恢复有序维度和代码表；实验库必须恢复设计、对照、样品、运行与校准；模拟库必须恢复模型版本、情景、集合、参数与输出链；定性档案必须保存个案、文本片段、编码和构念来源。两者缺一不可。

路线契约保存在 `config/database_route_contracts.json`。当前覆盖通用元数据、目录、文件、表、API、SDMX、多阶段调查、行政事件、空间数据、科学数组、流、生命医学、临床、知识图谱、多模态语料、实验、仪器测量、模拟、实体馆藏、定性档案、学术传播、数字平台、机器学习、软件流程、受限访问、二手来源、联邦、遗留格式和开放未知路线。它是可扩展注册表，不是封闭世界宣言。

## 第六阶段：异常恢复和人工门控

超时、限流、访问失败、格式错误、规模过大、元数据缺失、语义冲突、版本漂移和上游删除都要写成最小作用域的类型化 blocker，并说明可恢复性与下一操作。能够独立继续的工作不能停。

Agent 不能自行批准隐私、伦理、社区主权、访问授权、争议语义或研究问题发布范围：

```bash
python3 scripts/grdr.py record-database-deep-map-human-gate <project> <gate-id> --decision <approved|rejected|not_applicable> --reviewer <name> --notes <basis>
```

访问失败不等于不适用，受限数据不等于数据库不存在，AI 推断不等于官方语义。

## 第七阶段：严格完成

```bash
python3 scripts/grdr.py audit-database-deep-map <project>
python3 scripts/grdr.py complete-database-deep-map <project>
```

完成要求：计划已解析且契约版本匹配，人工门槛全部由具名人工解决，项目阶段闭合，所有必需工作单元阶段均为 `verified_complete` 或有证据的 `not_applicable`，所有路线检查均为 `passed` 或有证据的 `not_applicable`，无阻塞或失败，规范 ID、Schema、外键和人类目录全部通过验证。

系统分别报告阶段映射进度、严格阶段完成度和路线契约完成度。任何百分比都必须和完成声明、边界、日期/版本/窗口同时解释。
