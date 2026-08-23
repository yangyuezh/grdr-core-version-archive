# UNdata Plan — 2026-08-23-r1

此目录是 Step 1 Plan 的可审查副本，内容来源于指纹锁定的 `grdr:deep-map-project:undata-2026-08-21`，未在 Storage 阶段重新规划。

- 官方工作单元分母：36 个 UNdata datamart。
- 范围模式与完成声明：`exhaustive_snapshot`。
- 边界：完整枚举 2026-08-21 官方 Sources catalog 暴露的 36 个 datamart 元数据；六份 glossary 作为侧车证据。
- 数据库形态：层级目录、扁平表集合、统计立方体、文件归档的混合结构。
- 生产方式：官方统计、人口普查、调查、行政记录和模型估计。
- 必需路线：`core_metadata`、`catalog`、`file_archive`、`table_schema`、`api_schema`、`sdmx_cube`、`corpus_multimodal`、`derived_provenance`。
- 访问制度：`mixed`；动态端点、计算/分区要求和上游来源责任均被保留为风险标记。
- 待人工审批门：0；未解决必需诊断维度：0。

`diagnostic_plan.json` 保存诊断、数据库形态组合和路线契约；`scope.json` 保存完成声明、枚举方法和边界；`units.jsonl` 是 36 个工作单元的确定性队列。三者均由 Execute 项目的计划锁、范围锁和工作单元清单锁约束。
