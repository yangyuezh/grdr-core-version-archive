# GRDR 数据库深度映射工程

每个子目录是一项持久化数据库深度映射工程。工程把数据库拆成有边界的工作单元，并分别跟踪Dataset、DataStructure、DataElement、Variable、Construct和Access阶段。

GRDR Core不保存任何真实数据库工程。Agent运行Plan时可以在工作目录创建临时工程；完成Storage后，工程及其制品进入该数据库自己的独立仓库。

状态查询：

```bash
python3 scripts/grdr.py database-deep-map-status deep_map_projects/<source>
python3 scripts/grdr.py resume-database-deep-map deep_map_projects/<source>
```

映射进度不等于严格完成度。只有有效的最终Storage回执才能声明三步工厂完成。
