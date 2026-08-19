# 数据库深度映射工程流程

## 为什么需要持久化工程

六层模型规定“登记什么”，本流程规定“怎样逐项推进到可证明完成”。每个数据库建立一个 `deep_map_projects/<source>/` 工程，避免Agent只完成方便的样例后失去进度、遗漏异构结构或误报完整度。

```text
数据库身份与来源性质
  → 数据形态/学科路线分类
  → 固定日期和边界
  → 枚举全部工作单元
  → 每单元六阶段映射
  → 引用、数量、访问与证据验证
  → 严格完成审计
```

## 固定项目阶段

1. `identity`：核验数据库、机构及一手/二手来源关系；
2. `classification`：判定生产方式、结构类型、访问制度和路线模块；
3. `boundary`：固定范围、日期、版本和枚举方法；
4. `inventory`：建立完整工作单元清单并核对预期数量；
5. `deep_mapping`：逐单元执行Dataset、DataStructure、DataElement、Variable、Construct、Access；
6. `validation`：验证Schema、外键、证据、数量、关系与人类目录；
7. `completion_audit`：确认所有必需阶段闭合且无阻塞。

每个工作单元通常对应一个上游Dataset；对于知识图谱、文件库、语料库或仪器系统，可对应一个有稳定身份和边界的Collection、Graph、Corpus、Study或Instrument。

## 可执行命令

```bash
python3 scripts/grdr.py start-database-deep-map <spec.json>
python3 scripts/grdr.py database-deep-map-status <project>
python3 scripts/grdr.py resume-database-deep-map <project>
python3 scripts/grdr.py record-database-deep-map-phase <project> <update.json>
python3 scripts/grdr.py record-database-deep-map-stage <project> <update.json>
python3 scripts/grdr.py audit-database-deep-map <project>
python3 scripts/grdr.py complete-database-deep-map <project>
```

`resume`返回确定的下一个工作单元、阶段和路线，不依赖Agent临时记忆。更新命令只有在GRDR ID存在、类型正确、数量一致且完成声明有证据时才接受。

`database-deep-map-status`和`audit-database-deep-map`为只读命令，同样返回`next_target`和`queue_preview`；`resume`会写入一次恢复历史并刷新人类报告。工作单元内部必须采用官方顺序，若官方未定义则按完整原生ID稳定排序，并在阶段备注中保存`completed_native`、`last_native`、`next_native`和快照。这样既固定“下一个阶段”，也固定“阶段内下一项”。

## 两种进度

- **映射进度**：包含 `mapped_complete`，表示预期对象都已登记，但可能仍需充分核验；
- **严格完成度**：只包含 `verified_complete` 和有证据的 `not_applicable`。

预期工作单元数未知时，不能宣称百分比完整。阻塞、抽样、代表性链、部分码表或访问失败都不能进入严格完成度。

## 异构数据库适配

主阶段不变，路线可以组合：`catalog`、`sdmx_cube`、`table_schema`、`api_schema`、`survey_instrument`、`administrative_provenance`、`geospatial`、`scientific_array`、`biomedical`、`knowledge_graph`、`corpus_multimodal`、`restricted_access`、`derived_provenance`。

数据库整体可能是混合形态，因此路线在Source级初判，在每个工作单元级重新确认。一手数据重点登记采集或生成过程；二手数据必须追溯原始生产者、上游版本、加工转换、协调规则和修订链。

## 完成定义

“100%”只对明确日期与边界成立。只有 `complete-database-deep-map` 可以写入完成状态。它要求：

- 工作单元数与预期数量一致；
- 身份、分类、边界和清单阶段已经核验；
- 每个工作单元的所有必需阶段已经核验完成或有证据证明不适用；
- 没有阻塞；
- 注册表Schema、外键和目录检查通过。

上游版本更新后，应开启新的快照轮次或重新打开受影响阶段，不能沿用旧的100%声明。
