# GRDR 软件版本工程化归档规范

## 1. 目标

本规范保证任何 GRDR 历史版本都能够被识别、下载、核验、比较和恢复，同时不篡改原始开发历史。它适用于 GRDR，也可作为其他 AI Agent 项目的软件审计模板。

## 2. 四类必须分开的对象

1. **运行产品**：当前可执行的 GRDR Core。
2. **数据库产品**：UNdata、UNESCO UIS 等引用 Core 生产的独立数据库仓库和快照。
3. **Git 历史证据**：原始 commit、tree、parent、作者和时间。
4. **审计制品**：本仓库的审计标签、归档 Release、账本、校验和与恢复说明。

数据库观测数据不得为了软件版本审计而复制进本仓库。

## 3. 版本身份

一个审计节点至少由以下内容共同确定：

- `record_id`；
- 产品版本号；
- 历史状态；
- canonical 标记；
- 产品形态；
- 审计标签；
- 精确 commit SHA；
- Git tree SHA；
- 原始仓库、ref 和子路径；
- 原始 commit 时间与主题。

版本号相同但 tree、产品形态或谱系不同的对象必须分别登记，不能覆盖。

## 4. 历史状态

- `release`：原项目中的正式版本节点；
- `pre_1_0_provenance`：1.0之前有版本号且可核验的演进节点；
- `candidate`：内容可恢复但没有正式发布证据的候选版本；
- `historical_variant`：同版本号下的不同历史产品形态；
- `equivalent_tree_variant`：文件树相同但提交谱系不同；
- `post_release_docs`：正式 tag 之后的纯文档快照。

状态描述的是原始历史，不能根据后来补建的 GitHub Release 反向改变。

## 5. Git 标签与 GitHub Release

- `audit/...` tag 锁定软件内容，是审计身份的核心。
- `lineage/...` branch 保存可阅读的父子谱系。
- 每个 `audit/...` tag 建立一个 GitHub 审计归档 Release，提供下载入口。
- 审计 Release 必须声明其为后补归档制品，并显示原始历史状态。
- `release` 状态使用普通 Release；其他状态使用 prerelease。
- `archive-vX.Y.Z` 是审计仓库自身的发布版本，不等于 GRDR Core 版本。

旧标签永不移动。文档修订产生独立 post-release snapshot 或新的审计仓库版本。

## 6. 最低验证标准

每次归档更新必须同时通过：

1. `git fsck --full --strict`；
2. `python3 scripts/audit_archive.py`；
3. `python3 scripts/audit_remote_releases.py`；
4. GitHub Actions；
5. 从 GitHub 全新 clone 后重复执行本地核验；
6. 人工检查 README 的版本表、状态和产品边界。

## 7. 完整性边界

“全部版本已保存”是指：所有能从现存原始 Git 对象、`VERSION`、`CHANGELOG.md`、tag、仓库谱系和发布记录相互印证的版本都已登记。不能凭空创造从未存在的版本号，也不能把无法证明的中间提交宣布为版本。

## 8. 新版本归档清单

- [ ] 原 Core 测试通过；
- [ ] 原 Core `VERSION` 与 `CHANGELOG.md` 已更新；
- [ ] 原 Core commit、tag、Release 已发布；
- [ ] 原始对象已 fetch 到审计仓库；
- [ ] `version-map.jsonl` 已登记；
- [ ] `audit/...` tag 已创建；
- [ ] README 已说明本版特征、相对上一版的变化及真实数据库验证；
- [ ] 机器账本和 SHA-256 已重新生成；
- [ ] 审计归档 Release 已创建；
- [ ] 本地、远端、CI 和全新克隆核验均通过；
- [ ] 审计仓库自身的新版本已经发布。
