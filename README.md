# GRDR Core Version Audit Archive

本仓库是 GRDR 的软件版本审计档案库，不是运行时 Core、数据库仓库或观测数据镜像。

它保存 GRDR 从早期一体化原型到独立 Core `v4.5.0` 的精确 Git 对象、版本标签、文件树指纹、来源谱系和可重复核验方法。UNdata 专属仓库仍保留项目从 `v0.1.0` 起的原始演化历史；本仓库引用并固化其中的软件版本，不复制当前 UNdata 观测数据。

## 审计结论

- `v1.0.0–v3.1.0`：来自 UNdata 仓库保留的早期一体化 GRDR 历史。
- `v3.2.0–v3.4.0`：项目从一体化仓库向数据库无关 Core 分离；同一版本号出现过不同谱系时，档案同时保存 canonical Core 与 historical variant。
- `v4.0.0`：只发现并保存了可核验的 candidate，没有把它冒充为正式 Release。
- `v4.0.1–v4.5.0`：来自独立 GRDR Core 的正式发布历史。
- `v0.1.0–v0.6.0`：作为 `v1.0.0` 之前的来源证据一并保留。

## 正式版本覆盖

| 主版本 | 已归档的正式版本 |
|---|---|
| 1.x | `v1.0.0`, `v1.1.0`, `v1.2.0` |
| 2.x | `v2.0.0` |
| 3.x | `v3.0.0`, `v3.1.0`, `v3.2.0`, `v3.2.1`, `v3.2.2`, `v3.3.0`, `v3.4.0` |
| 4.x | `v4.0.1`, `v4.0.2`, `v4.1.0`, `v4.1.1`, `v4.2.0`, `v4.3.0`, `v4.4.0`, `v4.5.0` |

`v4.0.0-candidate` 单独保存；正式 4.x 发布线从 `v4.0.1` 开始。

## 仓库结构

```text
audit/version-map.jsonl       人工核定的版本—提交—来源映射
audit/version-ledger.jsonl    由 Git 对象生成的机器审计账本
audit/version-ledger.csv      便于人工查看的同源表格
audit/archive-manifest.json   覆盖范围与文件指纹
audit/SHA256SUMS              审计文件校验值
scripts/audit_archive.py      生成或只读核验全部标签、提交和 VERSION
docs/RESTORE.md               提取、比较与恢复任一版本
```

软件本体不在 `main` 上重复复制。每个版本由 `audit/...` Git tag 直接锁定精确提交；原始谱系由 `lineage/...` 分支保存。这比把每个版本再复制成一个目录更适合软件审计，因为提交、父子关系、作者时间和文件树都不会丢失。

## 核验

```bash
python3 scripts/audit_archive.py
```

核验器会检查：

1. 每个账本 tag 是否仍指向规定提交；
2. 提交绑定的 Git tree 是否与账本一致；
3. 根目录 `VERSION` 是否与档案声明一致；
4. `v4.0.0 candidate` 的提取树是否与 UNdata 原始 `core-candidate/` 子树一致；
5. 账本、清单和 SHA256 文件是否可重复生成。

## 边界

- 不把历史一体化版本中的数据库记录解释成当前 Core 架构。
- 不复制 UNdata、UNESCO UIS 的观测数据或 GitHub Release 资产。
- 不移动现有发布 tag，不伪造缺失 Release。
- 当前可运行 Core 仍是独立仓库 [`yangyuezh/grdr-core`](https://github.com/yangyuezh/grdr-core) 的 `v4.5.0`。
