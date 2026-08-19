# GRDR 数据库深度映射工程

每个子目录是一项持久化数据库深度映射工程。工程把数据库拆成有边界的工作单元，并分别跟踪Dataset、DataStructure、DataElement、Variable、Construct和Access阶段。

当前工程：

- [UNdata](undata/README.md) — 36个datamart的完整工作清单；深层映射仍在进行。

状态查询：

```bash
python3 scripts/grdr.py database-deep-map-status deep_map_projects/<source>
python3 scripts/grdr.py resume-database-deep-map deep_map_projects/<source>
```

映射进度不等于严格完成度。只有全部必需阶段核验闭合后，`complete-database-deep-map` 才能声明完成。
