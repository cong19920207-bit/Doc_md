# 本仓库工程文档

> 人和 AI 维护 **本仓库工具与流程** 的入口。最后更新：2026-10-04。\
> 仓库总入口：[`../../INDEX.md`](../../INDEX.md)。Hayyo 产品规则不在这里，默认去 [`../core-docs/prd/INDEX.md`](../core-docs/prd/INDEX.md)。

## 怎么读

- 改 Hayyo 某个功能：打开 [`../core-docs/prd/INDEX.md`](../core-docs/prd/INDEX.md) 对应 `PRD.md`。
- 改本仓库 H5 关系图 / 文档索引：打开 H5 知识库工程 PRD；实现已含「客户端 ↔ 后台」「客户端交叉」「文档索引」三个 Tab。
- 改本仓库「知识问答」主链路（向量检索 + 多轮回答）：检索基线读 kb-qa PRD（v3）；多轮任务、消息事实和 Memory 增量读 kb-qa-multdesign Phase1 v1.10。当前行为先查对应正式契约；按 STEP 继续工作时读当前收尾与剩余项。那是独立文档，不以 h5-kb 的 L3 附录为基线。旧版 PRD、STEP 草稿、审查过程在 `design/kb-qa/history/`，**不默认读**。要理解单路 / 多意图、K 与 n、案例接口打印：读仓库根 [`../../knowledge/INDEX.md`](../../knowledge/INDEX.md)（讲解稿，**不是** PRD）。
- 改多轮对话编排或知识问答管理后台：打开 [`design/kb-qa-multdesign/`](design/kb-qa-multdesign/INDEX.md)。`history/` **不默认读**。
- 改问答反馈 / 刷新 / 对话区样式：打开独立专题 [`design/kb-qa-feedback/`](design/kb-qa-feedback/INDEX.md)，不要把该增量写进 `design/kb-qa/`。
- 查本站实现契约 / 越权：打开 [`contracts/`](contracts/INDEX.md)，按功能分子目录；不要把正式契约再写进 `design/<功能>/`。
- 改本仓库账号 / 独立管理模块 / 证书启用：打开 [`design/kb-auth/`](design/kb-auth/INDEX.md)，不要写进 `site/core-docs/prd/design/auth-login` 或 `site/core-docs/prd/design/admin`。改管理站页面结构或加管理页：先打开 [`design/kb-admin-ui/INDEX.md`](design/kb-admin-ui/INDEX.md)。
- 改本仓库 H5 工作台配色主题：打开 [`design/h5-theme/`](design/h5-theme/INDEX.md)，不要写进 h5-kb / kb-qa 正文。
- 看本仓库最近改了什么：打开 [`开发记录.md`](开发记录.md)（给人看的简报；不进机器默认扫描）。
- 记本仓库未立项事项（需求 / 想法 / 优化 / bug）：打开 [`inbox/INDEX.md`](inbox/INDEX.md)。**不当合同**；`条目/` 不默认读。Hayyo 产品缺口去 [`../core-docs/prd/inbox/INDEX.md`](../core-docs/prd/inbox/INDEX.md)。
- 仓库层机器路由：[`../../llm-manifest.json`](../../llm-manifest.json)。产品权威扫描仍以 [`../core-docs/prd/llm-manifest.json`](../core-docs/prd/llm-manifest.json) 为准；本目录不进该产品扫描列表。

## 任务 → 当前文档

| 任务 | 打开这一份 |
|---|---|
| 看本仓库最近改了什么（简报） | [`开发记录.md`](开发记录.md) |
| 记本仓库未立项事项（不当合同） | [`inbox/INDEX.md`](inbox/INDEX.md) |
| H5 工作台主题切换 | [`design/h5-theme/PRD-H5工作台主题切换-v1.md`](design/h5-theme/PRD-H5工作台主题切换-v1.md) |
| H5 关系图 / 文档索引（阅读 + 关键词） | [`design/h5-kb/PRD-H5知识库-v1.md`](design/h5-kb/PRD-H5知识库-v1.md) |
| H5 STEP 验证版（文档索引） | [`design/h5-kb/steps-verified.md`](design/h5-kb/steps-verified.md) |
| 知识问答（混合检索 / 重排 / DeepSeek 多轮 / 多意图） | [`design/kb-qa/PRD-知识问答-v3.md`](design/kb-qa/PRD-知识问答-v3.md) |
| 本轮开发收尾 / 契约落点 / 回归结果 | [多轮编排收尾记录](design/kb-qa-multdesign/steps-verified.md#2026-10-03-开发收尾与正式契约整合) |
| 多轮对话编排 / 知识问答管理后台 | [`design/kb-qa-multdesign/INDEX.md`](design/kb-qa-multdesign/INDEX.md) |
| 知识问答 · 反馈与对话样式 | [`design/kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md`](design/kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md) |
| 账号体系 / 独立管理模块 / 证书启用 | [`design/kb-auth/PRD-账号体系与管理模块-v2.md`](design/kb-auth/PRD-账号体系与管理模块-v2.md) |
| 管理站页面结构（工作区、壳、以后加页） | [`design/kb-admin-ui/INDEX.md`](design/kb-admin-ui/INDEX.md) |
| 本站实现契约（按功能） | [`contracts/INDEX.md`](contracts/INDEX.md) |
| 账号体系实现契约（鉴权 / 越权） | [`contracts/kb-auth/contract.md`](contracts/kb-auth/contract.md) |
| 知识问答主链路实现契约 | [`contracts/kb-qa/contract.md`](contracts/kb-qa/contract.md) |
| 问答反馈实现契约 | [`contracts/kb-qa-feedback/contract.md`](contracts/kb-qa-feedback/contract.md) |
| H5 关系图 / 文档索引实现契约 | [`contracts/h5-kb/contract.md`](contracts/h5-kb/contract.md) |
| 核心文档路径 / 发布清单 / 本地刷新契约 | [H5 契约 §8](contracts/h5-kb/contract.md#8-核心文档与受控发布) |
| H5 主题实现契约 | [`contracts/h5-theme/contract.md`](contracts/h5-theme/contract.md) |
| 知识问答 · 反馈 STEP / 实施计划 | [`design/kb-qa-feedback/steps-verified.md`](design/kb-qa-feedback/steps-verified.md) · [`design/kb-qa-feedback/实施计划.md`](design/kb-qa-feedback/实施计划.md) |
| 知识问答 STEP 验证版 | [`design/kb-qa/Hayyo-知识问答-STEP-验证版.md`](design/kb-qa/Hayyo-知识问答-STEP-验证版.md) |
| 知识问答实施计划 | [`design/kb-qa/Hayyo-知识问答-实施计划.md`](design/kb-qa/Hayyo-知识问答-实施计划.md) |
| 知识问答 · 专题入口 | [`design/kb-qa/INDEX.md`](design/kb-qa/INDEX.md) |
| 本仓库方法 / 问答讲解（非 PRD） | [`../../knowledge/INDEX.md`](../../knowledge/INDEX.md) |
| 功能交互 / 知识库页（实现） | [`../feature-interaction/index.html`](../feature-interaction/index.html) |
| 运营后台现网皮 / 对照 | [`../../workspace/_kit/admin-skin/INDEX.md`](../../workspace/_kit/admin-skin/INDEX.md) |
| 数据 / 运营复盘 | [`../../reviews/INDEX.md`](../../reviews/INDEX.md) |
| Hayyo 产品规则 | [`../core-docs/prd/INDEX.md`](../core-docs/prd/INDEX.md) |

## 迁移阶段边界（2026-10-04）

产品文档唯一源为 `site/core-docs/prd/`。本地 API 用 `CORE_DOCS_ROOT=/core-docs` 读取，只读挂载 `site/core-docs`；异常缺失或空语料先报错，不据此删除旧索引。Web 只读挂载发布器生成的 `site/release/www`，保留 `/prd/...` URL 与知识块标识，禁止目录列表。文档与前端改动需重新生成并重建 Web 容器；运行 `sh site/preview.sh`，仅文档/前端更新可加 `--no-build`。TLS 使用独立 `kb-tls-data` 卷，Web 不再读取整个 API 数据卷。生产尚未部署；本轮证据与浏览器验收状态见[执行记录](design/core-docs-migration/execution/核心文档迁移开发执行记录.md)。

正式条款与实现落点见[迁移契约路由](contracts/INDEX.md#核心文档迁移整合)，不以本段摘要替代完整发布规则。原型与复盘汇总页只有 `publish-files.json` 列出的文件保留；工作区、工程资料及新分类不会因目录存在而自动发布。

## 目录约定

| 目录 | 放什么 |
|---|---|
| `site/core-docs/prd/` | Hayyo 产品权威（功能 PRD、图、版本、归档） |
| `knowledge/` | 本仓库方法与讲解（不是合同；入口 [`../../knowledge/INDEX.md`](../../knowledge/INDEX.md)） |
| `site/docs/` | 本仓库开发与维护文档（[`开发记录.md`](开发记录.md) 给人看的简报；[`inbox/`](inbox/INDEX.md) 立项前收件箱，不当合同；[`contracts/`](contracts/INDEX.md) 按功能分的实现契约；`design/h5-kb/` 文档索引；`design/kb-qa/` 知识问答主链路 PRD + STEP；`design/kb-qa-multdesign/` 多轮编排与管理后台；`design/kb-qa-feedback/` 反馈与对话样式；`design/kb-auth/` 账号与管理模块；`design/kb-admin-ui/` 管理站页面规则；`design/h5-theme/` 工作台主题切换；旧稿在各专题 `history/`，不默认读） |
| `site/feature-interaction/` | H5 实现（关系图 + 知识库） |
| `site/docker-compose.yml` 与 `site/docker/` | 本地部署入口为 `sh site/preview.sh`（先生成再启动）；Web 只挂发布产物，API 只挂核心文档，证书独立卷。禁止重新将仓库或整个 site 设为 Web 根 |
| `workspace/_kit/admin-skin/` | 运营后台原型底稿（现网皮、对照表、金标准） |
| `reviews/` | 按分析分类；`source/` 原始表，`summary/` 汇总 |
| `Aold_D/` | Word / Excel 原文（旧称 `demo/`），不默认读 |
