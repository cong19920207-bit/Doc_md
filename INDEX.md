# Hayyo 文档工作台

> 人和 AI 打开本仓库的默认入口。最后更新：2026-09-20。  
> 机器先读本页与 [`llm-manifest.json`](llm-manifest.json)；改产品规则再打开 [`prd/llm-manifest.json`](prd/llm-manifest.json)。  
> 产品名：Hayyo（早期原文为 Samer）。当前产品主线：V1.4.0（已收录）。V1.5.0 为工作区文档，非权威。版本三态见 [`prd/VERSIONS.md`](prd/VERSIONS.md)。  
> 本地站点：在 [`site/`](site/docker-compose.yml) 执行 `docker compose up -d`（仓库根则 `docker compose -f site/docker-compose.yml up -d`），打开 http://127.0.0.1:18765/feature-interaction/ 。配置只在 `site/docker-compose.yml`。

## 怎么读

权威按工作类型分开，不要混用：

1. **产品规则** → [`prd/INDEX.md`](prd/INDEX.md)；日常打开功能 `PRD.md`。拍板账本 [`prd/CONFIRMED.md`](prd/CONFIRMED.md)。未立项产品缺口 → [`prd/inbox/INDEX.md`](prd/inbox/INDEX.md)（不当合同）
2. **运营后台页长什么样** → [`workspace/_kit/admin-skin/INDEX.md`](workspace/_kit/admin-skin/INDEX.md)；规则仍跟 [`prd/design/admin/PRD.md`](prd/design/admin/PRD.md)
3. **本仓库 H5 / 文档索引 / 知识问答** → [`site/docs/INDEX.md`](site/docs/INDEX.md)，实现在 [`site/feature-interaction/`](site/feature-interaction/index.html)。未立项工程事项 → [`site/docs/inbox/INDEX.md`](site/docs/inbox/INDEX.md)（不当合同）
4. **本仓库方法与讲解** → [`knowledge/INDEX.md`](knowledge/INDEX.md)（不是合同）
5. **数据 / 运营复盘** → [`reviews/INDEX.md`](reviews/INDEX.md)
6. **Word / Excel 原文** → [`Aold_D/`](Aold_D/)（旧文档里的 `demo/` 即此目录；**不默认读**）
7. **工作区文档，非权威** → [`workspace/`](workspace/INDEX.md)（版本草稿不默认读；共享底稿 `_kit` 要读）

同一条产品规则只以各功能 `prd/design/<功能>/PRD.md` 为准。H5、原型、复盘都不另写第二套规则。

## 任务 → 打开哪一份

| 你要做的事 | 打开 |
|---|---|
| 改某个 App / 后台功能规则 | [`prd/INDEX.md`](prd/INDEX.md) |
| 问某版本发了什么 | [`prd/VERSIONS.md`](prd/VERSIONS.md) |
| 看本仓库最近改了什么（简报） | [`site/docs/开发记录.md`](site/docs/开发记录.md) |
| 记本仓库未立项事项（不当合同） | [`site/docs/inbox/INDEX.md`](site/docs/inbox/INDEX.md) |
| 记产品未立项缺口（不当合同） | [`prd/inbox/INDEX.md`](prd/inbox/INDEX.md) |
| 看文档怎么洗、怎么切、问答怎么走（方法，非 PRD） | [`knowledge/INDEX.md`](knowledge/INDEX.md) → [`knowledge/工作流程-文档工作台.md`](knowledge/工作流程-文档工作台.md) |
| 术语 / 缺口 | [`prd/PROJECT_OVERVIEW.md`](prd/PROJECT_OVERVIEW.md) |
| 改运营后台某一页的皮或字段对照 | [`workspace/_kit/admin-skin/INDEX.md`](workspace/_kit/admin-skin/INDEX.md) |
| 改功能关系图 / 文档索引 H5 | [`site/docs/design/h5-kb/PRD-H5知识库-v1.md`](site/docs/design/h5-kb/PRD-H5知识库-v1.md) → 实现 [`site/feature-interaction/index.html`](site/feature-interaction/index.html) |
| 改知识问答（向量检索 + 多轮回答） | [`site/docs/design/kb-qa/PRD-知识问答-v3.md`](site/docs/design/kb-qa/PRD-知识问答-v3.md) → 实施 [`site/docs/design/kb-qa/Hayyo-知识问答-STEP-验证版.md`](site/docs/design/kb-qa/Hayyo-知识问答-STEP-验证版.md) → 阶段 [`site/docs/design/kb-qa/Hayyo-知识问答-实施计划.md`](site/docs/design/kb-qa/Hayyo-知识问答-实施计划.md) |
| 改知识问答反馈 / 刷新 / 对话区样式 | [`site/docs/design/kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md`](site/docs/design/kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md) |
| 改本仓库账号 / 管理模块 / 证书启用 | [`site/docs/design/kb-auth/PRD-账号体系与管理模块-v2.md`](site/docs/design/kb-auth/PRD-账号体系与管理模块-v2.md) |
| 理解知识问答链路 / 案例 / K 与 n（讲解，非 PRD） | [`knowledge/INDEX.md`](knowledge/INDEX.md) |
| 看或追加数据复盘 | [`reviews/INDEX.md`](reviews/INDEX.md) |
| 对 Word / Excel 原文 | [`Aold_D/<版本>/`](Aold_D/) |
| 看工作区文档（非权威） | [`workspace/`](workspace/INDEX.md)（版本草稿不默认读） |

25 个功能的任务表只写在 `prd/INDEX.md`，这里不重复。

## 目录地图

| 目录 | 放什么 | 权威 | 默认读 |
|---|---|---|---|
| [`prd/`](prd/INDEX.md) | 产品规则、版本、功能图；立项前缺口在 [`prd/inbox/`](prd/inbox/INDEX.md) | 产品 canonical；inbox 不当合同 | 改规则时必读；记缺口时打开 inbox 看板 |
| [`knowledge/`](knowledge/INDEX.md) | 本仓库方法与讲解（工作流程 / 经验 / 教训 / 讲解 / 案例 / 示意） | explainer；不是合同 | 做文档工作或理解问答链路时读 |
| [`site/docs/`](site/docs/INDEX.md) | 本仓库工程（H5 文档索引 PRD / 知识问答 PRD / STEP）；立项前事项在 [`inbox/`](site/docs/inbox/INDEX.md) | 工程 canonical；inbox 不当合同 | 改本仓库工具时读；记事项时打开 inbox 看板 |
| [`site/feature-interaction/`](site/feature-interaction/index.html) | 功能关系 + 文档索引 +（本期）知识问答 H5 | 实现 | 改 H5 时读 |
| [`site/`](site/docker-compose.yml) | 网站实现、工程文档、Docker | 工具 | 改站点时读 |
| [`workspace/_kit/admin-skin/`](workspace/_kit/admin-skin/INDEX.md) | 后台现网皮、对照表、金标准 | 视觉 / 现网页 reference | 改后台页时读 |
| [`reviews/`](reviews/INDEX.md) | 按分析分类的数据 / 运营复盘 | 分析；不是需求 | 做复盘时读 |
| [`Aold_D/`](Aold_D/) | 已迁入 `prd/` 的 Word / Excel 原文 | archive | 不对齐规则、不默认读 |
| [`workspace/v*`](workspace/INDEX.md) | 未升格版本的正文、原型、截图、工作稿 | 工作区文档，非权威 | 不默认读 |

## 默认不读

- `Aold_D/`
- `workspace/v*`（工作区文档，非权威；升格前不当事实）
- `prd/**/history/`、`prd/archive/`
- `prd/inbox/条目/`、`site/docs/inbox/条目/`（立项前单条证据，不当合同；看板 `INDEX.md` 可读）
- `site/docs/design/h5-kb/steps-draft.md`（草案；验证版才是 `steps-verified.md`）
- `site/docs/design/kb-qa/history/`（知识问答旧版 PRD、STEP 草稿、审查过程；当前权威是 `PRD-知识问答-v3.md`、STEP 验证版与实施计划）
- `site/docs/design/kb-auth/history/`（账号体系 v1；当前权威是 `PRD-账号体系与管理模块-v2.md`）
- `site/feature-interaction/vendor/`
- `reviews/*/source/`（复盘原始表）
- 旧路径 `demo/`、`垃圾桶/`、`referral-ops-review/`、`docs/`、`feature-interaction/`、`admin-skin-demo/`：磁盘上已迁走。浏览器 URL `/feature-interaction/`、`/docs/`、`/admin-skin-demo/` 仍由 nginx 别名指向新位置。`demo/` 已对应 `Aold_D/`；拉新复盘在 `reviews/referral/`。

非当前资料只有在明确要求对原文、版本对比、迁移或审计时再打开。

## 维护

- 仓库层路由只写在本页和根 `llm-manifest.json`；产品扫描仍以 `prd/llm-manifest.json` 为准。
- 子目录已有 INDEX 的，根上只做指针，不复制正文。
- 新工作区先登记本表，再放文件。复盘类一律进 `reviews/<分析>/`，原始表进 `source/`，汇总进 `summary/`。
- 缺证据标 `needs-input` / `needs-review`。
- [`site/docs/开发记录.md`](site/docs/开发记录.md) 给人看本仓库工具简报，不进根 `llm-manifest.json` 扫描。
