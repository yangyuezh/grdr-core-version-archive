# GRDR 数据库深度映射协议

## 目的

数据库进入 GRDR 不能止于名称和主页。`$grdr-plan-database-deep-map` → `$grdr-execute-database-deep-map` → `$grdr-store-database-deep-map` 三步工厂把一个数据库深读、存储并正式建立为 AI Agent 可检索、可核验、可连接的六层内容脉络：

```text
1 机构 → 2 数据库 → 3 数据集 → 4 数据库内部结构
                              ↓
                 5A 数据元素 → 5B 研究变量 → 6 理论构念
```

API、CSV、下载、查询器、认证、许可和安全环境属于访问旁路 `Resource`，挂接到 Dataset 或 DataStructure，但不占第4层，也不决定内容深度。

六层对象必须组成两根主干和一座桥梁，而不是只在清单里出现：

- 数据库原生结构主干：项目级 Institution → Source 上下文，以及每个工作单元的 Dataset → DataStructure → DataElement → Variable；
- 学科与科学语义主干：允许多父节点的 SemanticNode → Construct；
- 变量—构念桥梁：Variable → Construct，并保留测量、代理、模型、预测和必要的原生结构上下文。

对象数量、图谱连通和数据库形态契约分别验收。

“GRDR 当前没有登记”只表示当前快照覆盖不足，不表示上游不存在。

## 先声明本轮边界

正式深读前先用 `database_deep_map_intake` 对来源、生成过程、结构、模态、生命周期、版本、访问、敏感性、规模、元数据成熟度、语言、工作单元与授权约束做证据化预诊断，并生成可审计路线计划。关键诊断未解决时状态为 `needs_evidence`，不得启动执行；未知结构进入 `open_world_custom`，不得强行归类。

每次深度映射必须选择一种范围：

- `identity_only`：只核验机构和数据库；
- `representative_chain`：建立至少一条有证据的完整链；
- `question_driven`：围绕科学问题优先展开相关结构和变量；
- `priority_catalog`：展开已声明的高价值子集；
- `catalog_level`：可复现地枚举官方数据集目录；
- `exhaustive_snapshot`：对特定日期或版本内所有可枚举对象做完整快照。
- `rolling_window`：对明确事件时间、处理版本和闭窗规则下的当前滚动窗口完成映射；
- `bounded_partition`：对稳定清单或非重叠分区完成映射。

`registry/source_profiles.jsonl` 为每个已启动数据库保留一条当前记录。它必须说明范围、清单声明、各实体进度、访问旁路进度、枚举方法、上游数量、快照边界、阻塞和复核时间。Git 保存历史轮次。

## 六层内容要求

### 第1层：机构（Institution）

区分生产者、发布者、维护者、资助者和治理者，核验身份、职责、管辖与官方授权。

### 第2层：数据库（Source）

确定规范身份、别名、官方入口、主题范围、权威角色、来源位置、生命周期、许可与更新政策。

### 第3层：数据集（Dataset）

从官方目录枚举本轮范围内的版本化集合，记录总体、观察单位、空间和时间覆盖、方法、版本、修订、限制、引用和证据。

### 第4层：数据库内部结构（DataStructure）

还原数据集内部怎样组织数据。对象可以是目录层级、数据流、多维模式、表/视图、API Schema、文件布局、问卷、仪器、科学数组或知识图谱模式。必须保留上游系统、机构标识、对象类别、原生 ID、版本、父结构、关联数据集及证据。

这一层回答“变量来自数据库内部哪个结构”。API 地址或下载文件本身不能代替 DataStructure。

### 第5层：数据元素与研究变量

- **5A DataElement**：忠实保存结构定义的测度、维度、标识符、时间维度、属性、权重、标记、单位、代码表、顺序和附着层级。每个元素必须指向 DataStructure。
- **5B Variable**：从官方元数据中形成可用于研究匹配的操作变量。在多维系统中，它通常是“测度 + 赋予含义的维度选择”；在表、问卷或模式中，它可以是有定义的字段、题项、派生项或序列。每个变量必须指向 DataStructure、Dataset 和 Construct，并保存单位、总体、分辨率、测量类型、可比性、连接键和证据。

结构或含义尚未确定时停在5A，不创建5B。主题标签不能证明变量存在。`layer_5_details` 分别报告5A和5B的数量、范围和边界。

### 第6层：理论构念（Construct）

说明变量测量的概念，并区分直接观察、自陈、行政测量、构造指数、模型估计、预测、代理和潜变量；保留定义边界、适用范围与不确定性。

## 访问旁路

`Resource` 登记 API、文件、批量下载、查询系统、目录、文档、云集合、安全环境、申请入口、格式、认证、机器访问、限流、许可和使用条件。用 `accessed_via` 将其挂接到 Dataset 或 DataStructure。

结构元数据与观测数据必须分别测试。DSD/Schema 可访问不等于数据查询可用；故障写入 Resource/Adapter/Monitor 和 SourceProfile 的 `access` blocker。

## 状态与主链关系

- `source_only`：只有机构/数据库；
- `dataset_depth_started`：已有数据集；
- `data_structure_depth_started`：已恢复第4层但尚无可匹配变量；
- `variable_depth_started`：已有5A或5B但主链尚不完整；
- `six_layer_chain_present`：至少存在一条到构念的六层链，不代表目录或变量全集已完成。

Resource 不会使阶段前进。

## 标准执行顺序

1. 在 GRDR 搜索并解析数据库身份，避免重复。
2. 运行 `python3 scripts/grdr.py audit-source-depth <source-id>`。
3. 声明本轮范围和停止条件，更新 SourceProfile。
4. 优先使用官方目录、Schema、字典、代码本、问卷、方法、API与许可文件。
5. 按 Institution → Source → Dataset → DataStructure → DataElement → Variable → Construct 生成记录和关系，并使用 `stage-database-deep-map-records` 写入项目暂存区；Step 2 不得直接写正式注册表。
6. 独立登记和测试访问旁路。
7. 使用 `record-database-deep-map-spine` 闭合数据库原生结构主干、学科语义主干和变量—构念桥梁。
8. 同时闭合 `checks.jsonl` 中由数据库形态决定的路线契约；六层对象齐全或主干连通均不能替代路线义务。
9. 运行执行审计并生成带指纹的密封归档包。
10. 由 Storage Skill检查正式库冲突、事务性写入中央注册表，再生成独立源仓库、完整知识与观测制品、Agent索引和GitHub Release，通过一致性核验后签发Storage回执；本地展开副本仅是可重建缓存。
11. 报告新增 ID、层级数量、双主干、桥梁、路线检查、证据、边界、人工门槛、阻塞、包/收据指纹与下一轮。

一轮只有在范围已声明、结构化记录通过验证、人类目录同步、验证升级有证据、未覆盖内容明确、没有夸大完整度并且存在有效 `archive_receipt.json` 时才完成。
