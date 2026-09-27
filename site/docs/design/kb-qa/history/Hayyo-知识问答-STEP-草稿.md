---
title: "Hayyo 知识问答 STEP 草稿"
status: "draft"
stage_result: "PASS_WITH_RISKS"
prd: "site/docs/design/kb-qa/PRD-知识问答-v3.md"
prd_sha256: "52e7b5b6f0876cf28defcbeeaf3bdc46c71d90de028c29bebf92e1b725e28965"
created: "2026-09-17"
note: "本文件是草稿，未经 step-doc-review 完整复审前不得当作已验证或可执行计划。"
---

# Hayyo 知识问答 STEP 草稿

> 本文已迁入 `history/`，**不默认读**。现行实施输入：[`../Hayyo-知识问答-STEP-验证版.md`](../Hayyo-知识问答-STEP-验证版.md)。  
> 权威需求：[`../PRD-知识问答-v3.md`](../PRD-知识问答-v3.md)。

## 来源摘要

事实标签只用：`USER_DECISION`、`PRD`、`CONTRACT`、`REPO_BASELINE`、`RUNTIME`、`PLANNED`、`UNVERIFIED`。本轮无 `RUNTIME`。仓库根无 `package.json`（`REPO_BASELINE`）。无 `kb-api` / Qdrant / MySQL 服务（`REPO_BASELINE`）。

| source_id | 路径 | 状态 | SHA-256 | 本轮核实 |
|---|---|---|---|---|
| SRC-PRD-V3 | `site/docs/design/kb-qa/PRD-知识问答-v3.md` | `existing` | `52e7b5b6f0876cf28defcbeeaf3bdc46c71d90de028c29bebf92e1b725e28965` | 全文；status=已确认；implementation=未实施 |
| SRC-PRD-V2 | `site/docs/design/kb-qa/history/PRD-知识问答-v2.md` | `existing` | `b3fa6bbd005490fa124698baa39c957465a5cea11402bd511d96a36493926b75` | 仅沿用 F1–F15、AC1–AC14、C1–C5/C7–C12/C14–C29、E1–E8、T4/T7；**不**沿用已废止的 v2 C6、v2 C13 |
| SRC-H5-HTML | `site/feature-interaction/index.html` | `existing` | `86e78657d417f738b5761bbe704b57af1a15ce290debbe44e8cc651039e24a92` | 三 Tab：`data-view` = `admin` \| `client` \| `kb`；无问答 Tab；`#kbWorkspace` |
| SRC-H5-APP | `site/feature-interaction/app.js` | `existing` | `cbc6a79a89524509117b921e05006383163d63ccab34ed0513da11e59e485f79` | `setView` 只识别 `kb` 与关系图；`/` 快捷键聚焦 `#search` / `#kbSearch` |
| SRC-H5-KB | `site/feature-interaction/kb.js` | `existing` | `a86a9d1721989d2344af20ff31a62cbb173646e8a95cb3680fee2c2e7e6cfb0e` | `window.KB.openDocument` / `scrollToTarget`；`search` 关键词、最多 20 条 |
| SRC-H5-MD | `site/feature-interaction/kb-md.js` | `existing` | `c39731cbba62477867d65d9cbe26aba4b702ea52b7554322a47b5cab57d09117` | `{#锚点}` 写成 heading `id`；HTML 注释（含 chunk 标记）渲染时丢掉 |
| SRC-H5-CSS | `site/feature-interaction/style.css` | `existing` | `c6651f39c81e869709d6affddf088fd5e123161ad4839571c939761a4aec6076` | 现网工作区样式；问答壳尚未接入 |
| SRC-COMPOSE | `site/docker-compose.yml` | `existing` | `f0dc5d8b02fe29c2c80ec49096f1adacfe6040eb8deb54544249a6422b6ec7e1` | 仅 `web`（nginx）；`127.0.0.1:18765:80`；备注 3306/3307 已占用 |
| SRC-NGINX | `site/docker/nginx.conf` | `existing` | `fc7558ffef014b956a35a6f89adbe6075ff154a74d809a30b5d7d831aca5d7bd` | 静态别名 `/feature-interaction/`、`/docs/`；无 kb-api 反代 |
| SRC-PRD-INDEX | `prd/INDEX.md` | `existing` | `7a4f22efcbd51ce34243dd19c6c17543cd4683e15407798f55c3356e7585cbed` | 权威是各功能 `PRD.md`；brief 派生 |
| SRC-BRIEF-VIP | `prd/design/vip/brief/current.md` | `existing` | `3a0c0dcdcf9eb1963f6ea7f44fbe2988f4a5e5888c5a5ceb91cb44923ac8d4c9` | `chunk:default` 含 `{#logic-wealth}` 保级/财富值 |
| SRC-BRIEF-ADMIN | `prd/design/admin/brief/current.md` | `existing` | `99a8846569df3aeedbc9c76c778e633ceaa7fa7b3b4e8574d37cd86efd5988aa` | `id: admin`；`chunk:default` 自 `admin.scope` 起 |
| SRC-BRIEF-MARK | `prd/design/auth-login/brief/current.md` | `existing` | — | 抽查：`chunk:default` / `chunk:no` / `chunk:related-row` 并存 |
| SRC-BRIEF-UL | `prd/design/user-level/brief/current.md` | `existing` | — | AC17 点名功能；`id=user-level.scope` |
| SRC-BRIEF-REF | `prd/design/referral/brief/current.md` | `existing` | — | AC17 点名功能；`id=referral.scope` |
| SRC-PROTO-B | `workspace/kb-qa-proto/demo-b/index.html` | `existing` | `040c60914bed77e0b2e4e99693107fe3a324411d2648a9761913bab386792d2b` | Demo B：左列表+中对话+右 `#qaProcess`；非正式 |
| SRC-PROTO-CORE | `workspace/kb-qa-proto/shared/qa-core.js` | `existing` | `14508b9c676f446a0e1bc7a42b58aea1cac4cbb44b0bda7530875889c6948335` | mock 多会话；`MAX_CONVS = 40`；非正式 |
| SRC-PROTO-UI | `workspace/kb-qa-proto/shared/proto-ui.js` | `existing` | `92013362cc8c75b002d438b4556c1e94d32f507d05777d031028bda36875cf54` | 阶段文案；空状态 chips；非正式 |

**发现门（未定位，不填具体值）：** kb-api 语言、HTTP 路径前缀、MySQL 宿主机端口、功能别名表文件位置、拟议后端目录。PRD §9.4 写明「实施时定」。相关 STEP 标 `PLANNED`，实施时按已核实的项目约定确定。

v2 T4 拟议 `site/kb/`：仓库中不存在（`REPO_BASELINE`），不得写成现网路径。

## 输入清单

### 本期有效需求

F1–F21。优先级沿用 PRD：F14 为 P1，其余为 P0。不另造排期。F2 / F3 / F5 以 **v3 表**为准（多会话、点名功能列表、单路仅在点名 0 或 1 个时）。

### 本期有效验收

AC1–AC14（v2 沿用；AC3/AC6 的「会话」= **当前对话**）。AC15–AC24（v3）。

### 需求确认台账（已确认，不新编号）

RQ-01～RQ-12.1（v2 沿用）、RQ-13～RQ-21（v3）。

### 未编号约束（CSTR）

| ID | 摘要 | 来源 |
|---|---|---|
| CSTR-001 | 权威是各功能 `PRD.md`；问答/向量/日志不能当需求合同 | R1、R2、R10；SRC-PRD-INDEX |
| CSTR-002 | 只切各功能 `brief/current.md` 的 `chunk:default`；不切 `PRD.md` / `history/` / changelog | R3、C10；§4.2 |
| CSTR-003 | 仅绑定 `127.0.0.1`，不映射 `0.0.0.0` | C15；G2 |
| CSTR-004 | `DASHSCOPE_API_KEY`、`DEEPSEEK_API_KEY` 不进 git、不进配置页明文、不进日志 | R6；F12 |
| CSTR-005 | 日志页 / 热度页不写入 `prd/design/admin/` | v3 §1、§4.2 |
| CSTR-006 | 明细 / 热度不是第 5 / 第 6 Tab | C36；RQ-18 |
| CSTR-007 | `named_feature_ids` 只允许仓库已有功能 ID，禁止发明 | v3 §6.2 步骤 3；A3 |
| CSTR-008 | 不编造时延 / 召回条数硬验收；默认 K=64、n=8、历史 5 轮可配、不进 AC | v2 §8；C18、C19；RQ-09 |
| CSTR-009 | 配置页不改关系图 / 文档索引参数 | v2 §4.2 |
| CSTR-010 | `workspace/kb-qa-proto/` 是 mock，不能替代 kb-api 或现网第四 Tab | v3 文首；T |
| CSTR-011 | 改写失败不降级用原句检索 | C24；§4.2 |
| CSTR-012 | 超长块不二次切、不截断；超限不入库并进失败清单 | C28 |
| CSTR-013 | 无用户勾选「只搜某功能」UI；F21 不是 D1 | RQ-10；D1 |
| CSTR-014 | brief 全文不上 MySQL；MySQL 只存轮次日志 | C13 v3；§4.2 |
| CSTR-015 | 写库失败不落本机日志副本、不自动回灌 | C37；RQ-20 |
| CSTR-016 | 正式问答页无右侧过程栏、无建议问法 chips | C31、C32；RQ-16 |
| CSTR-017 | MySQL 避开 3306/3307；具体端口实施时定 | v3 §9.1、§9.4 |
| CSTR-018 | 浏览器对话上限实施默认 40；非硬验收 | v3 T2、§9.4 |
| CSTR-019 | collection 实施默认 `hayyo-client` / `hayyo-admin`；配置页只读展示 | C22 |
| CSTR-020 | 日志保留天数未定，不编造硬验收 | v3 §9.4 |
| CSTR-021 | 后端语言、路径前缀实施时定 | v3 §9.4；C20 |
| CSTR-022 | 问答独立工作区，勿塞进 `#kbWorkspace` | v2 T1；SRC-H5-HTML |
| CSTR-023 | 出处定位用 `{#锚点}` 或标题；chunk 注释不能当 DOM id | R7；SRC-H5-MD |
| CSTR-024 | 功能别名 → `feature_id` 表实施时维护；来源为 `prd/design/*` 已有 ID | v3 §9.1 |
| CSTR-025 | 配置页抽屉或整页 overlay 均可，以 AC13 字段分层为准 | v3 §9.4 |
| CSTR-026 | 不以 `site/docs/design/h5-kb` 的 L3 为本期基线 | v2 §4.2；v3 文首 |
| CSTR-027 | 检索查询 = 本轮原句 + 改写句 | v3 §6.2 步骤 4–5 |
| CSTR-028 | `feature_id === admin` 入 admin 库，其余入 client 库 | v2 §6.2 索引步骤 6 |
| CSTR-029 | 强制全量重建仅用于换 embedding 型号/维度或库损坏 | C14 |
| CSTR-030 | embedding `text-embedding-v4`、1024 维，调用显式 `dimension=1024` | C17；RQ-01 |
| CSTR-031 | 改写与回答均 `thinking: disabled` | C8 |
| CSTR-032 | 发送即尝试写日志 `running` | C35；F18 |
| CSTR-033 | 中途失败 / 刷新丢弃半段正文，不把半段当成功答 | C21、C35 |
| CSTR-034 | 配置只对后续轮生效 | C38 |
| CSTR-035 | `/` 快捷键不要抢问答输入 | v2 T4 `app.js` |

### 决策

- **沿用（除非 v3 替代）**：C1–C5、C7–C12、C14–C29。
- **v3 有效（替代 v2）**：C6（两层会话）、C13（轮次日志上 MySQL）、C18′、C30–C38。
- **规则**：R1–R12（R5 以 v3 两层为准，废止 v2「刷新即无历史」）。

### 排除项 / 本期不做

| ID | 项 | 来源 |
|---|---|---|
| OUT-1 | 把问答或向量当权威 | §4.2 |
| OUT-2 | 默认切 `PRD.md` / `history/` / changelog | §4.2 |
| OUT-3 | 索引 `chunk:related-row`、`chunk:no` | §4.2 |
| OUT-4 | 把 brief 全文进 MySQL | §4.2 |
| OUT-5 | 本期账号 / 登录 / 权限实现 | §4.2；D3 |
| OUT-6 | 正式问答页展示过程栏 | §4.2；C31 |
| OUT-7 | 正式空状态建议问法 chips | §4.2；C32 |
| OUT-8 | 原型剧本条 | §4.2 |
| OUT-9 | 问答 Tab 内嵌第二套阅读器 | §4.2 |
| OUT-10 | 浏览器直连模型 / Qdrant | §4.2 |
| OUT-11 | 用检索或回答改仓库 PRD | §4.2 |
| OUT-12 | 公开站点、映射 0.0.0.0 | §4.2 |
| OUT-13 | 用户手动范围过滤 UI | §4.2；D1 |
| OUT-14 | 入索引全文快照 | §4.2 |
| OUT-15 | 配置页改锁死项或展示 Key 明文 | §4.2 |
| OUT-16 | 超长块二次切分 | §4.2 |
| OUT-17 | 改写失败降级原句检索 | §4.2 |
| OUT-18 | 把日志/热度做成 Hayyo 运营后台产品页 | §4.2 |
| OUT-19 | 明细 / 热度做成第 5 / 第 6 Tab | §4.2 |
| OUT-20 | 日志写失败落本地副本或自动回灌 | §4.2 |
| OUT-21 | 配置页改关系图 / 文档索引参数 | §4.2 |
| OUT-22 | 覆盖或当作旧 H5 L3 已批准实施 | v2 §4.2 |
| OUT-23 | 编造性能秒级门槛或日志保留天数硬验收 | v3 §2.3、§9.4 |

### 延期项（不实施、不新编号）

| ID | 项 | 来源 |
|---|---|---|
| D1 | 用户勾选「只搜某功能/某文档」 | v3 §9.3 |
| D2 | 文档索引默认可读改为 brief | v3 §9.3 |
| D3 | 登录与账号权益实现 | v3 §9.3 |

### 技术债（v2 T7 + v3 T7 增补；本期不另开修复 STEP）

- brief `pending-review`：问答可能落后 PRD；出处可跳转。
- 文档索引仍索引 PRD `scan_roots`：关键词搜 PRD、问答搜 brief。
- 无评测集：质量靠手工 AC。
- 账号未做 → D3。
- 无范围过滤 → D1。
- 改写漏点名则该功能无专路（v3 接受：原句仍参与检索；日志可核对 `named_feature_ids`）。

## 功能清单

本期实施：第四 Tab 知识问答（正式左列表+中对话）、切块索引、混合召回、多意图分路、重排、流式回答、出处跳转、配置页、轮次日志 MySQL、明细页、热度页、浏览器多会话。  
不实施：D1–D3、OUT-*、原型过程栏与 chips、Hayyo 运营后台产品页。

## STEP 总览

| STEP | 标题 | 需求 | 验收 | 前置 | 优先级（PRD 原值） |
|---|---|---|---|---|---|
| STEP-001 | 本机 Compose 增加问答依赖 | F12、G2 | AC7（服务可起停） | 无 | P0 |
| STEP-002 | 密钥仅服务端与 nginx 反代 | F12、R6 | AC7、AC13（Key） | STEP-001 | P0 |
| STEP-003 | 第四 Tab 独立工作区入口 | F1 | AC1 | 无 | P0 |
| STEP-004 | 正式问答壳：双栏、阶段、无过程栏/chips | F17、RQ-16 | AC21 | STEP-003 | P0 |
| STEP-005 | 浏览器多会话 + localStorage | F16、RQ-13 | AC15、AC16 | STEP-004 | P0 |
| STEP-006 | 生成中锁定本轮对话操作 | F16、RQ-21 | AC23 | STEP-005 | P0 |
| STEP-007 | 切块、两库、增量对账 | F11 | AC9、AC10（库侧） | STEP-001 | P0 |
| STEP-008 | 启动对账与重建索引按钮 | F11、RQ-02、RQ-11 | AC9 | STEP-007、STEP-004 | P0 |
| STEP-009 | 追问改写与换题 | F3、F4 | AC3、AC14 | STEP-002、STEP-005 | P0 |
| STEP-010 | 单路两库混合召回 | F5 | AC2（召回段）、AC10 | STEP-007、STEP-009 | P0 |
| STEP-011 | 多意图分路检索 | F21、RQ-15 | AC17 | STEP-009、STEP-010 | P0 |
| STEP-012 | 重排、同主题并入、多意图保底 | F6 | AC2（重排段）、AC17（保底） | STEP-010、STEP-011 | P0 |
| STEP-013 | 流式回答与出处折叠 | F7、F17 | AC2、AC8 | STEP-012 | P0 |
| STEP-014 | 拒答与冲突并列 | F8、F9 | AC4、AC5 | STEP-012、STEP-013 | P0 |
| STEP-015 | 出处跳转文档索引 | F10 | AC6、AC22（出处段） | STEP-013 | P0 |
| STEP-016 | 本机配置页分层 | F15、RQ-12.1 | AC13 | STEP-002、STEP-004 | P0 |
| STEP-017 | 轮次日志存法 B 与写失败降级 | F18、RQ-14、RQ-20 | AC18、AC24 | STEP-001、STEP-009～STEP-014 | P0 |
| STEP-018 | 问答明细页 | F19、RQ-18 | AC19、AC22 | STEP-017、STEP-004 | P0 |
| STEP-019 | 功能热度页 | F20、RQ-19 | AC20、AC22 | STEP-017、STEP-018 | P0 |
| STEP-020 | 现网三 Tab 不被破坏；鉴权预留 | F13、F14 | AC7、AC11、AC12 | STEP-003、STEP-015 | P0；F14 为 P1 |

## 需求映射

| ID | 映射 STEP | 映射方式 |
|---|---|---|
| F1 | STEP-003 | 直接：第四 Tab 入口 |
| F2 | STEP-005、STEP-009、STEP-013 | 子条款：当前对话发送；改写；回答+出处 |
| F3 | STEP-009 | 直接 |
| F4 | STEP-009、STEP-012 | 改写返回换题；重排不并入上轮块 |
| F5 | STEP-010 | 直接（点名 0 或 1） |
| F6 | STEP-012 | 直接 |
| F7 | STEP-013 | 直接 |
| F8 | STEP-014 | 直接 |
| F9 | STEP-014 | 直接 |
| F10 | STEP-015 | 直接 |
| F11 | STEP-007、STEP-008 | 切块对账；按钮与变更清单 |
| F12 | STEP-001、STEP-002 | 绑定；密钥 |
| F13 | STEP-020 | 直接 |
| F14 | STEP-020 | 直接（P1） |
| F15 | STEP-016 | 直接 |
| F16 | STEP-005、STEP-006 | 多会话；生成中锁定 |
| F17 | STEP-004、STEP-013 | 阶段文案；出处折叠/复制 |
| F18 | STEP-017 | 直接 |
| F19 | STEP-018 | 直接 |
| F20 | STEP-019 | 直接 |
| F21 | STEP-011 | 直接 |
| RQ-01 | STEP-007 | embedding 型号/维度 |
| RQ-02 | STEP-007、STEP-008 | 增量含删旧点；强制全量条件 |
| RQ-03 | STEP-009 | 改写失败整轮失败 |
| RQ-04 | STEP-013 | 生成失败仍列出处 |
| RQ-05 | STEP-014 | 仅空结果系统拒答 |
| RQ-06 | STEP-009、STEP-012 | 同主题布尔 |
| RQ-07 | STEP-013 | stream |
| RQ-08 | STEP-007 | 超长块 |
| RQ-09 | STEP-010、STEP-012、STEP-016 | 默认 64/8/5 可配不进 AC |
| RQ-10 | 无开发 STEP | OUT-13；D1 |
| RQ-11 | STEP-008 | 变更清单、不存全文快照 |
| RQ-12 / RQ-12.1 | STEP-016 | 配置页分层 |
| RQ-13 | STEP-005 | 多会话 |
| RQ-14 | STEP-017、STEP-018、STEP-019 | 日志+两页 |
| RQ-15 | STEP-011 | 分路 |
| RQ-16 | STEP-004 | 无过程栏/chips |
| RQ-17 | STEP-020 | 预留字段本期空 |
| RQ-18 | STEP-018、STEP-019 | 顶栏入口 |
| RQ-19 | STEP-017、STEP-019 | 摘录与热度口径 |
| RQ-20 | STEP-017 | 写库失败 |
| RQ-21 | STEP-006 | 生成中锁定 |
| G1 | STEP-003、STEP-013、STEP-015 | 目标约束 |
| G2 | STEP-001 | 目标约束 |
| G3 | STEP-015 | 目标约束 |
| G4 | STEP-014 | 目标约束 |
| G5 | STEP-007、STEP-017 | 目标约束 |
| G6 | STEP-017、STEP-018 | 目标约束 |
| G7 | STEP-011 | 目标约束 |
| C1 | STEP-010～STEP-013 | 检索+重排+回答都要 |
| C2、C8、C21 | STEP-013 | 回答模型与 stream |
| C3 | STEP-010 | 混合召回 |
| C4 | STEP-012 | 重排型号 |
| C5 | STEP-005、STEP-009 | 多轮 |
| C6（v3） | STEP-005、STEP-017 | 两层会话 |
| C7、C26 | STEP-014 | 拒答/冲突 |
| C9、C10、C16、C17、C22、C28 | STEP-007 | 索引 |
| C11 | STEP-003 | Tab |
| C12 | STEP-015 | 出处 |
| C13（v3） | STEP-017、STEP-020 | 日志上库；账号不实现 |
| C14、C29 | STEP-008 | 重建 |
| C15 | STEP-001、STEP-002 | 本机绑定 |
| C18、C18′、C27 | STEP-012 | 条数与并入 |
| C19、C24、C30 | STEP-009 | 历史轮数、改写失败、点名列表 |
| C20 | STEP-001 | kb-api+Qdrant |
| C23 | STEP-016 | 配置页 |
| C25 | STEP-013 | 生成失败列出处 |
| C31、C32 | STEP-004 | 正式 UI |
| C33、C35、C37 | STEP-017 | 日志 |
| C34 | STEP-019 | 热度 |
| C36 | STEP-018、STEP-019 | 入口 |
| C38 | STEP-006 | 锁定 |
| R1、R2、R10 | 相关 STEP「不做」 | 权威约束 |
| R3 | STEP-007 | 切块 |
| R4、CSTR-027 生成侧 | STEP-013、STEP-011 | 不得补写 |
| R5 | STEP-005、STEP-017 | 两层 |
| R6 | STEP-002 | 密钥 |
| R7 | STEP-015 | 锚点 |
| R8 | STEP-016 | 配置分层 |
| R9 | STEP-011 | 未点名不保证专路 |
| R11 | STEP-006 | 锁定 |
| R12 | STEP-019 | 热度命中 |
| E1、E2 | STEP-002、STEP-020 | AC7 |
| E3 | STEP-010、STEP-012、STEP-008 | 检索/重排/重建失败 |
| E4 | STEP-013 | 生成失败 |
| E5、E6 | STEP-014 | 拒答/冲突 |
| E7 | STEP-009 | 改写失败 |
| E8 | STEP-007 | 超长块 |
| E9 | STEP-017 | interrupted |
| E10 | STEP-005 | 配额 |
| E11 | STEP-011 | 空路 |
| E12 | STEP-017 | 库挂 |
| D1–D3 | 无开发 STEP | 延期 |
| OUT-1～OUT-23 | 各 STEP「不做」+ 总排除 | 不实施 |
| T7 | 无修复 STEP | 接受项 |

## 验收映射

| AC | 映射 STEP | 对象比较方法 |
|---|---|---|
| AC1 | STEP-003 | 顶栏「文档索引」右侧出现「知识问答」，可进入独立工作区（不是 `#kbWorkspace`） |
| AC2 | STEP-010、STEP-012、STEP-013 | 问「保级扣的是财富值还是金币」：流式回答基于 VIP brief 块，结束后有可点出处 |
| AC3 | STEP-009 | 刚问过保级且改写成功后追问「那退款呢」：按 VIP 退款相关块，不当成全新无关问题 |
| AC4 | STEP-014 | 问 brief 未写的具体数字表：拒答或声明文档未写，不编造表 |
| AC5 | STEP-014 | 互斥块同入 Top：并列摘录，不宣称其中一条为唯一现行 |
| AC6 | STEP-015 | 点出处切到文档索引落到对应 brief 节；切回问答，当前对话仍在 |
| AC7 | STEP-001、STEP-002、STEP-020 | 不配 Key 或停 Qdrant：失败说明可读；文档索引仍能打开文档 |
| AC8 | STEP-013 | 外网模型 5xx：无无出处完整规则答；已有重排块则只列出处 |
| AC9 | STEP-007、STEP-008 | 改/删某 `chunk:default` 后重建：回答反映新文；被删块不再召回；变更清单含增/改/删 |
| AC10 | STEP-007、STEP-010 | 问纯后台字段：出处路径含 `admin/brief` |
| AC11 | STEP-020 | 切回「客户端 ↔ 后台」：与现网一致，不被问答破坏 |
| AC12 | STEP-020 | 文档索引顶栏关键词仍只做现有关键词检索，不强制走向量 |
| AC13 | STEP-016、STEP-002 | 只读项不可改；可改项保存后用于后续提问；看不到 Key 明文 |
| AC14 | STEP-009 | 改写失败：无本轮检索出处、无完整回答；可重试；上一轮对话仍在 |
| AC15 | STEP-005 | 新建、各问一句、切换：标题来自首问；不串；刷新后仍在 |
| AC16 | STEP-005 | 删除一条：列表与 localStorage 去掉；日志明细旧轮次仍在（依赖 STEP-017 已写入） |
| AC17 | STEP-011、STEP-012 | 问「用户等级 2、VIP5，在拉新页能获得什么 / 能做什么」：`user-level`、`vip`、`referral` 各至少一路 |
| AC18 | STEP-017 | 生成未结束刷新（MySQL 可用）：明细为 `interrupted` 或等价错误态；无半段成功气泡 |
| AC19 | STEP-018 | 写库成功的一轮：明细可见原句、改写句、点名功能、每路条数/是否空、进生成块摘录（≤500 字）、回答或错误态 |
| AC20 | STEP-019 | 跨功能进生成块：各 `feature_id` +1 降序；空路不计；无进生成块且写库成功 →「未归类」 |
| AC21 | STEP-004 | 正式空会话：无 chips、无右侧过程栏 |
| AC22 | STEP-018、STEP-019、STEP-015 | 顶栏进独立工作区可回问答；无第 5/第 6 Tab；明细出处跳文档索引后再回，当前对话仍在 |
| AC23 | STEP-006 | 生成未结束：输入禁用；切对话有提示且不切换、本轮不中断；可切文档索引；结束后切换不串 |
| AC24 | STEP-017 | MySQL 停或本轮写库失败：主路径仍可按既有口径作答；提示本轮日志未写入；明细/热度无该轮 |

---

## 完整 STEP 提示词

### [STEP-001] 本机 Compose 增加问答依赖

**阶段状态**：`draft`

**目标**：在现有仅 nginx 的 compose 上增加 Qdrant、kb-api、MySQL，与静态站一并只绑定 127.0.0.1，避开本机已占用的 3306/3307。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F12 | 配 Key、起容器；服务绑 127.0.0.1 | `PRD` |
| 需求 ID | G2 | 仓库根 Docker Compose 拉起静态站 + 问答依赖 + 日志库；仅绑定 127.0.0.1 | `PRD` |
| 验收 ID | AC7 | 故意不配 Key 或停 Qdrant 时，本 STEP 保证这些服务可被停掉且不映射公网 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| 无 | — | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `site/docker-compose.yml` `services.web` | `existing` | `REPO_BASELINE` | SRC-COMPOSE / `ports: "127.0.0.1:18765:80"`；注释写明 3306、3307 已占用 | 保留静态站 |
| `site/docker/nginx.conf` | `existing` | `REPO_BASELINE` | SRC-NGINX / `listen 80`；无反代 location | 本 STEP 不改反代细节（STEP-002） |
| qdrant / kb-api / mysql 服务 | `planned` | `PLANNED` | 不适用 | 新增依赖；名称/镜像/端口按项目约定确定 |
| 拟议目录 `site/kb/` | `planned` | `PLANNED` | v2 T4；仓库中不存在 | 可选落点，不强制该路径 |

**输入**：

- 现网 compose 仅 nginx。
- PRD：MySQL 新服务避开 3306/3307；只绑 127.0.0.1；Qdrant 仅内网。

**输出**：

- compose 可拉起静态站 + 问答依赖 + 日志库；宿主机不出现 0.0.0.0 映射。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 绑定 | 仅 127.0.0.1 | `C15` / `CSTR-003` |
| MySQL 用途 | 只存轮次日志，不存 brief 全文 | `C13` v3 / `CSTR-014` |
| 端口 | 避开 3306/3307；具体数字实施时定 | `CSTR-017` |

**开发任务**：

1. 在现有 `web` 服务之外增加 Qdrant、kb-api、MySQL；语言、镜像、服务名、路径前缀按已核实的项目约定确定，不编造。
2. 宿主机端口与管理面不映射 0.0.0.0；Qdrant 不对公网。
3. 仓库根仍可用现有 compose 命令拉起；静态站 18765 行为保持。

**不在本 STEP 范围内**：

- nginx 反代路径与 Key 注入（STEP-002）。
- 切块与索引逻辑（STEP-007）。
- 填写具体 MySQL 端口数字或后端语言。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 仓库根按现有 compose 方式 up | 静态站仍在 127.0.0.1:18765；问答依赖与日志库进程存在 | AC7 前置 |
| 异常 | 停 Qdrant | 问答主路径可失败；容器未把 Qdrant 打到 0.0.0.0 | AC7 |
| 边界 | 检查端口声明 | 无 3306/3307 冲突；无 0.0.0.0 映射 | AC7 / CSTR-003 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-001、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-002] 密钥仅服务端与 nginx 反代

**阶段状态**：`draft`

**目标**：浏览器只打 kb-api；两 Key 仅服务端环境变量；配置页与前端拿不到明文。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F12 | Key 仅服务端环境变量；前端与配置页拿不到 Key 明文 | `PRD` |
| 需求 ID | R6 | `DASHSCOPE_API_KEY`、`DEEPSEEK_API_KEY` 不进 git、不进配置页明文 | `PRD` |
| 验收 ID | AC7 | 故意不配 Key：失败说明可读 | `PRD` |
| 验收 ID | AC13 | 看不到 Key 明文 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | kb-api / Qdrant 服务定义存在 | compose 文件含这些服务 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `site/docker/nginx.conf` | `existing` | `REPO_BASELINE` | SRC-NGINX / 现仅静态 `location` | 增加反代；前缀实施时定 |
| kb-api 反代 location | `planned` | `PLANNED` | 不适用；发现门：路径前缀 | 浏览器不直连模型/Qdrant |
| 环境变量名 `DASHSCOPE_API_KEY`、`DEEPSEEK_API_KEY` | `existing`（名称） | `PRD` | SRC-PRD-V2 / R6 | 不进 git |

**输入**：STEP-001 的服务拓扑。  
**输出**：nginx 反代 kb-api；缺 Key 时可读失败；响应与静态资源不含 Key。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 密钥存放 | 仅服务端环境变量，不进仓库 | `R6` |
| 浏览器 | 不得直连百炼 / DeepSeek / Qdrant | `OUT-10` |

**开发任务**：

1. 为 kb-api 增加仅内网可达的反代；路径前缀按项目约定确定。
2. Key 从环境变量读取；未配置时不调用外网模型，返回可读说明（缺哪类 Key）。
3. 确认前端包、配置接口、日志都不回说明文。

**不在本 STEP 范围内**：配置页 UI（STEP-016）；索引（STEP-007）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | Key 已配 | 前端网络面板无 Key；请求只到本机反代 | AC13 |
| 异常 | 环境变量空 | 不调用外网模型；说明缺哪类 Key | AC7 |
| 边界 | 打开配置页接口 | 只显示已配置/未配置，无明文 | AC13 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-002、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-003] 第四 Tab 独立工作区入口

**阶段状态**：`draft`

**目标**：在「文档索引」右侧增加「知识问答」Tab，进入独立问答工作区，不塞进 `#kbWorkspace`。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F1 | 顶栏「文档索引」右侧「知识问答」；进入问答工作区 | `PRD` |
| 验收 ID | AC1 | 在「文档索引」右侧出现该 Tab，可进入会话 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| 无 | 现网三 Tab 仍在 | `index.html` 三个 `data-view` |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `site/feature-interaction/index.html` `.tabs` | `existing` | `REPO_BASELINE` | SRC-H5-HTML / 第 16–19 行三 Tab | 在 `kb` 右侧插入第四 Tab |
| `app.js` `setView` | `existing` | `REPO_BASELINE` | SRC-H5-APP / `function setView`；`target === "kb"` | 扩展第四视图；勿拆阅读器无关逻辑 |
| `#kbWorkspace` | `existing` | `REPO_BASELINE` | SRC-H5-HTML / `id="kbWorkspace"` | 问答不得塞入 |
| 问答工作区 DOM | `planned` | `PLANNED` | 不适用 | 独立壳 |
| `app.js` `/` 快捷键 | `existing` | `REPO_BASELINE` | SRC-H5-APP / `ev.key === "/"` 约第 482 行 | 问答输入时不要抢焦点（CSTR-035） |

**输入**：现网三 Tab。  
**输出**：第四 Tab 可进入空问答工作区；关系图/文档索引仍可切回。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| Tab 位置 | 「文档索引」右侧 | `C11` / `F1` |
| 工作区 | 独立，勿塞进 `#kbWorkspace` | `CSTR-022` |

**开发任务**：

1. 增加 `知识问答` Tab 与独立工作区显示/隐藏。
2. 扩展 `setView`（或等价）切到问答；切走时隐藏问答、不拆 kb 阅读器。
3. 问答输入框聚焦时 `/` 不抢到关系图/文档索引搜索框。

**不在本 STEP 范围内**：左列表多会话（STEP-005）；过程栏/chips 禁止项的完整空状态（STEP-004）；出处跳转（STEP-015）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 打开 H5 点「知识问答」 | Tab 在「文档索引」右侧；进入独立工作区 | AC1 |
| 异常 | 问答服务未就绪 | 仍能进入 Tab（失败提示可在后续 STEP）；不崩掉整页 | AC1 / AC7 前置 |
| 边界 | 从问答切回「文档索引」 | `#kbWorkspace` 仍是阅读器，不是问答 DOM | AC1 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-003、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-004] 正式问答壳：双栏、阶段、无过程栏/chips

**阶段状态**：`draft`

**目标**：正式页为左对话列表 + 中会话；有阶段文案槽位；无右侧过程栏；空状态无建议问法 chips。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F17 | 阶段文案：改写中→检索中→重排中→生成中；出处默认「N 条出处」可展开；可复制回答。正式页有阶段与出处，无过程栏 | `PRD` |
| 需求 ID | RQ-16 | 正式问答不展示过程栏 / 不做建议 chips | `PRD` |
| 验收 ID | AC21 | 打开空会话：无建议问法 chips；无右侧过程栏 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-003 | 第四 Tab 可进入 | 点 Tab 见到工作区 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| Demo B `#qaWorkspace.layout-b` | `existing` | `REPO_BASELINE` | SRC-PROTO-B / 左 `#qaConvPane`、中 `#qaMessages`、右 `#qaProcess` | **只借鉴左+中**；正式不接右栏 |
| `proto-ui.js` `STAGE_LABEL` | `existing` | `REPO_BASELINE` | SRC-PROTO-UI / `rewrite/retrieve/rerank/generate` 文案 | 阶段用词对齐 PRD |
| `proto-ui.js` `.qa-chips` | `existing` | `REPO_BASELINE` | SRC-PROTO-UI / `SUGGESTIONS` chips | 正式禁止 |
| 正式问答 DOM | `planned` | `PLANNED` | 不适用 | 左列表+中对话 |

**输入**：第四 Tab 壳。  
**输出**：正式双栏布局；空会话无 chips、无过程栏；阶段文案槽位存在（实际驱动在后续 STEP）。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 正式布局 | 左列表 + 中对话 | `C31` |
| 过程栏 | 正式不展示；过程只在明细页 | `C31` / `OUT-6` |
| chips | 正式空状态不做 | `C32` / `OUT-7` |
| 阶段文案 | 改写中→检索中→重排中→生成中 | `F17` |

**开发任务**：

1. 落地左列表栏 + 中会话栏（列表数据在 STEP-005）。
2. 确认 DOM 无右侧过程栏、空状态无 chips、无原型剧本条。
3. 预留阶段文案与「N 条出处」折叠、复制按钮的结构（行为在 STEP-013 接完）。

**不在本 STEP 范围内**：localStorage（STEP-005）；真正流式（STEP-013）；明细页过程展示（STEP-018）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 打开正式空会话 | 可见左栏+中栏；无右侧过程栏；无 chips | AC21 |
| 异常 | 对照 Demo B | 正式页不得出现 `#qaProcess` 等价栏 | AC21 |
| 边界 | 空状态文案 | 可有说明文字，但不是建议问法 chips | AC21 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-004、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-005] 浏览器多会话 + localStorage

**阶段状态**：`draft`

**目标**：新建 / 切换 / 删除 / 清空当前；标题取首条用户问句截断约 18 字；刷新恢复；删浏览器对话不删日志。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F16 | 新建 / 点列表 / 删除 / 清空当前；标题取首条用户问句截断约 18 字；会话隔离；刷新恢复 | `PRD` |
| 需求 ID | RQ-13 | 浏览器多会话 + localStorage | `PRD` |
| 验收 ID | AC15 | 新建、各问一句、切换：列表标题来自首问；内容不串；刷新后仍在 | `PRD` |
| 验收 ID | AC16 | 删除一条：列表与 localStorage 去掉该条；日志明细里旧轮次仍在 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-004 | 左列表 + 中会话 DOM | 正式页双栏可见 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `qa-core.js` `MAX_CONVS` / `titleFromText` / `CONV_KEY` | `existing` | `REPO_BASELINE` | SRC-PROTO-CORE / `MAX_CONVS = 40`；标题 >18 字截断 | mock 参考；正式键名按项目约定确定 |
| 浏览器对话字段 | `planned` | `PRD` / `PLANNED` | v3 T2：id、title、messages、上轮 chunk、`same_topic` 相关字段 | 存盘形状 |
| localStorage 键名 | `planned` | `PLANNED` | 不适用 | 不沿用原型键冒充契约 |

**输入**：STEP-004 壳。发送/回答管道可先用占位，AC15 需能各问一句（可与后续 STEP 联测）。  
**输出**：多会话隔离、刷新恢复、删除释放浏览器侧；配额失败有提示。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 会话两层 | 浏览器 localStorage 可恢复可删；删对话不删 MySQL 日志 | `C6` v3 / `R5` |
| 标题 | 首条用户问句截断约 18 字 | `F16` |
| 上限 | 实施默认 40；非硬验收 | `CSTR-018` |
| 配额 | 写失败或超条数：淘汰最旧非当前对话；仍失败则提示「对话未保存」 | `E10` |

**开发任务**：

1. 实现新建、切换、删除、清空当前；列表与当前对话隔离。
2. 持久化到 localStorage；刷新恢复；用户可删。
3. 超上限淘汰最旧非当前；写失败提示「对话未保存」。

**不在本 STEP 范围内**：生成中禁止切换（STEP-006）；日志是否仍在（STEP-017 联测 AC16）；正式过程栏。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 新建两个对话各问一句后切换 | 标题来自首问；内容不串；刷新后仍在 | AC15 |
| 异常 | localStorage 写失败 | 提示对话未保存 | AC15 / E10 |
| 边界 | 删除一条 | 列表与 localStorage 去掉；不要求本 STEP 删 MySQL | AC16 浏览器侧 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-005、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-006] 生成中锁定本轮对话操作

**阶段状态**：`draft`

**目标**：本轮未结束时禁止再发送、新建、切换、删除、清空；允许切其它 Tab 与打开配置 / 明细 / 热度；结束后切换不串。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F16 | 生成中禁止再发送、新建、切换、删除、清空；允许切其它 Tab 与打开配置 / 明细 / 热度；切对话被拒绝且不中断本轮 | `PRD` |
| 需求 ID | RQ-21 | 同上 | `PRD` |
| 验收 ID | AC23 | 输入禁用；切对话有提示且不切换、本轮不中断；可切文档索引；结束后切换不串 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-005 | 多会话列表可点 | 至少两条对话 |

依赖未满足时停止。完整 AC23 需发送后进入生成中（STEP-013）；本 STEP 先接锁，可与 STEP-013 联测。

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `proto-ui.js` toast「本轮生成中，请稍后再切换」 | `existing` | `REPO_BASELINE` | SRC-PROTO-UI / 约第 288 行 | 提示参考；正式文案以可理解为准，不新造业务状态 |
| `C38` | `existing` | `PRD` | SRC-PRD-V3 / 决策表 C38 | 锁定范围 |

**输入**：当前对话处于生成未结束。  
**输出**：对话操作被拒绝且本轮继续；其它 Tab / 配置 / 明细 / 热度可开；配置只对后续轮生效（CSTR-034）。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 锁定 | 禁止再发送、新建、切换、删除、清空 | `C38` / `R11` |
| 允许 | 切文档索引 / 关系图；开配置 / 明细 / 热度 | `C38` |
| 结束后 | 切换对话互不串 | `C38` |

**开发任务**：

1. 生成中禁用输入与发送，拦截新建/切换/删除/清空并提示，不中断本轮。
2. 允许切 `data-view=kb|admin|client` 与打开后续页入口（页本身可后做）。
3. 本轮结束后恢复操作；切换后消息不串。

**不在本 STEP 范围内**：实现明细/热度页（STEP-018/019）；配置保存语义（STEP-016）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 生成未结束点左侧其它对话 | 有提示、不切换、本轮不中断；输入禁用 | AC23 |
| 异常 | 生成未结束切「文档索引」 | 允许切走；回来本轮仍在 | AC23 |
| 边界 | 本轮结束后再切换 | 内容不串 | AC23 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-006、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-007] 切块、两库、增量对账

**阶段状态**：`draft`

**目标**：扫描各功能 `brief/current.md`，只切 `chunk:default`，按 content hash 增量 embedding 到两个 collection；超长块失败上报且不二次切。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F11 | 按内容 hash 增量切块/embedding/upsert；删除当前 brief 已无的点；超限块失败上报 | `PRD` |
| 验收 ID | AC9 | 改某个 `chunk:default` 正文或删除该块后，被删块不再被召回（库侧） | `PRD` |
| 验收 ID | AC10 | admin brief 进入独立 collection，问纯后台字段能命中 `admin/brief` | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | Qdrant 与 kb-api 可运行 | compose 中服务存在且可起 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `prd/design/*/brief/current.md` | `existing` | `REPO_BASELINE` | SRC-BRIEF-VIP `<!-- chunk:default ... id=vip.logic-wealth -->`；SRC-BRIEF-ADMIN `id: admin`；SRC-BRIEF-MARK `chunk:no` / `chunk:related-row` | 知识源；本期不改正文 |
| collection 名 `hayyo-client` / `hayyo-admin` | `planned` | `PRD` | C22；CSTR-019 | 实施默认，配置页只读 |
| embedding `text-embedding-v4` 1024 | `existing`（合同） | `PRD` | C17；RQ-01 | 显式 `dimension=1024` |

**输入**：磁盘上各 `brief/current.md`。  
**输出**：两 collection 中仅 default 块；hash 未变跳过 embed；陈旧点删除；超限进失败清单。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 切块 | 只切 `chunk:default` | `C10` / `R3` |
| 丢弃 | `chunk:no`、`chunk:related-row` | `OUT-3` |
| 路由 | `feature_id === admin` → admin 库，其余 → client 库 | `CSTR-028` |
| payload | path、feature_id、chunk_id、section、heading、anchor、content_hash、collection | v2 T2 |
| 超长 | 超过 embedding 上限（8192 token）不入库、不二次切、不截断 | `C28`；v2 索引步骤 5 |
| 快照 | 不把 brief 全文另存入索引 | `C29` / `OUT-14` |

**开发任务**：

1. 解析 `chunk:default`，保留 id、section、路径、标题、`{#锚点}`、`feature_id`。
2. hash 对账：未变跳过；变化则 embed upsert；解析结果没有的入库点删除。
3. admin / 非 admin 分库；超限写入失败清单。

**不在本 STEP 范围内**：重建按钮 UI（STEP-008）；检索（STEP-010）；改正文 PRD/brief。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 首次对账 | client 与 admin 两库都有点；VIP default 块在 client | AC9 前置 / AC10 |
| 异常 | 人为造超长 default 块 | 该块不入库；失败清单含 path/chunk_id | AC9 / E8 |
| 边界 | 同一 hash 再跑增量 | 不重复计费 embedding（v2 T3 幂等） | AC9 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-007、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-008] 启动对账与重建索引按钮

**阶段状态**：`draft`

**目标**：容器启动自动跑一轮增量对账；问答顶栏「重建索引」走同一路径；返回结构化变更清单；强制全量仅换型号/维度或库损坏。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F11 | 启动或按钮重建；结构化变更清单；失败则明确 path/chunk_id/原因 | `PRD` |
| 需求 ID | RQ-02 | 增量对账含删旧点；强制全量仅换模型/库损坏 | `PRD` |
| 需求 ID | RQ-11 | 不存全文快照；返回变更清单 | `PRD` |
| 验收 ID | AC9 | 点重建后再问：回答反映新文；清单含对应增/改/删 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-007 | 对账实现可调用 | 能跑一轮增量 |
| STEP-004 | 问答顶栏可放按钮 | 正式问答壳存在 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| Demo B `data-reindex` | `existing` | `REPO_BASELINE` | SRC-PROTO-B / 「重建索引」按钮 | 入口位置参考；非正式 |
| 变更清单字段 | `existing`（合同） | `PRD` | v3 §4.1 / v2 F11：path、chunk_id、旧/新 hash、动作=增/改/删、失败项 | 接口输出 |

**输入**：STEP-007 对账函数。  
**输出**：启动自动增量；按钮触发；返回清单；无全文快照。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 启动 | 自动跑一轮增量对账 | `C14` |
| 强制全量 | 仅换 embedding 型号/维度或库损坏 | `C14` / `CSTR-029` |
| 清单 | path、chunk_id、旧/新 hash、增/改/删、失败项 | `C29` |
| 入口 | 与配置并列的顶栏按钮，不是新 Tab | `C36` 相邻 |

**开发任务**：

1. kb-api 启动调用与按钮同一增量路径。
2. 返回结构化变更清单；失败项含原因。
3. 不把当时 brief 全文另存为快照。

**不在本 STEP 范围内**：配置页改 embedding 型号（锁死，OUT-15）；问答生成。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 改 VIP 某 default 正文后点重建再问保级 | 回答反映新文；清单含改 | AC9 |
| 异常 | embedding/重建 HTTP 失败 | 失败清单或明确原因；不编造已索引 | AC9 / E3 |
| 边界 | 删除某 default 后重建 | 该块不再被召回；清单含删 | AC9 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-008、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-009] 追问改写与换题

**阶段状态**：`draft`

**目标**：改写产出独立问句 + `same_topic` + `named_feature_ids`（仅已有功能 ID）；失败则整轮不检索不生成。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F3 | 独立问句 + `same_topic` + `named_feature_ids`；ID/数字原样 | `PRD` |
| 需求 ID | F4 | `same_topic=false` 不携带上一轮 chunk | `PRD` |
| 验收 ID | AC3 | 刚问过保级且改写成功，追问「那退款呢」按 VIP 退款相关块 | `PRD` |
| 验收 ID | AC14 | 改写失败：无本轮检索出处、无完整回答；可重试；上一轮对话仍在 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-002 | Key 与 kb-api 可达 | 改写调用能发出 |
| STEP-005 | 当前对话最近轮 | 能读默认最近 5 轮（可配，不进硬验收） |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| 改写模型 `deepseek-flash`、`thinking: disabled` | `existing`（合同） | `PRD` | C8；CSTR-031 | 改写调用 |
| 功能 ID 来源 `prd/design/*` | `existing` | `REPO_BASELINE` | 目录名即功能 ID，如 `vip`、`user-level`、`referral`、`admin` | 禁止发明 ID |
| 别名表 | `planned` | `PLANNED` | CSTR-024；实施时维护 | 口语→已有 ID |

**输入**：当前对话最近轮（默认 5，可配）+ 本轮原句。  
**输出**：独立问句、`same_topic`、`named_feature_ids`（可空）；或整轮失败态。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 改写产出 | 独立问句 + 是否同一主题 + 已有功能 ID 数组（可空） | `F3` / `C30` / `A3` |
| 禁止 | 发明功能 ID、版本号、数值 | `A3` / `CSTR-007` |
| 失败 | 不检索、不生成；不降级原句检索；上轮块仍在；可重试 | `C24` / `CSTR-011` |
| 历史长度 | 默认 5 轮，可配，不进 AC | `C19` / `CSTR-008` |

**开发任务**：

1. 调用改写；保留功能 ID/字段名/数字原样。
2. `named_feature_ids` 过滤为仓库已有 ID。
3. 失败：提示可重试；不出现本轮出处与完整回答。

**不在本 STEP 范围内**：真正检索（STEP-010/011）；并入上轮块（STEP-012）；日志 status（STEP-017 写 `rewrite_fail`）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 先问保级再问「那退款呢」且改写成功 | 独立问句指向 VIP 退款，非全新无关题 | AC3 |
| 异常 | 改写接口失败 | 无本轮检索出处、无完整回答；上一轮仍在 | AC14 |
| 边界 | 已独立的问句 | 原样；`named_feature_ids` 可空或 1 个 | AC3 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-009、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-010] 单路两库混合召回

**阶段状态**：`draft`

**目标**：改写成功且点名功能为 0 或 1 个时，用「原句+改写句」对两 collection 做 BM25+向量混合召回并合并。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F5 | 改写成功且点名功能 0 或 1 个：两 collection BM25+向量，合并约 K 条 | `PRD` |
| 验收 ID | AC2 | 问保级能基于 VIP brief 块（召回段） | `PRD` |
| 验收 ID | AC10 | 问纯后台字段能命中 admin brief | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-007 | 两库有点 | 对账后点数非 0 |
| STEP-009 | 改写成功产物 | 有独立问句；`named_feature_ids.length` 为 0 或 1 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| VIP `{#logic-wealth}` | `existing` | `REPO_BASELINE` | SRC-BRIEF-VIP / 「保级」「财富值」 | AC2 语料 |
| admin brief | `existing` | `REPO_BASELINE` | SRC-BRIEF-ADMIN | AC10 语料 |
| 默认 K=64 | `existing`（合同） | `PRD` | C18；不进硬验收 | 可配 |

**输入**：检索查询 = 原句 + 改写句。  
**输出**：合并去重后的候选块（约 K，可配）。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 单路条件 | `named_feature_ids` 为 0 或 1 | `F5` / `C30` |
| 查询 | 原句 + 改写句 | `CSTR-027` |
| 两库 | 都搜；不是用户勾选 | `CSTR-013` / `C9` |
| 空库 | Qdrant 未起或点数 0：不生成回答，提示索引未就绪 | `E2` |

**开发任务**：

1. 两库 BM25+向量召回后合并去重。
2. 点名 1 个时仍走本单路（不走 F21）。
3. 检索/embedding 失败本轮失败，不编造排序。

**不在本 STEP 范围内**：≥2 分路（STEP-011）；重排（STEP-012）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 问「保级扣的是财富值还是金币」 | 候选含 VIP brief 块 | AC2 |
| 异常 | 停 Qdrant | 不生成回答；可读失败 | AC7 / E2 |
| 边界 | 问纯后台字段 | 候选路径含 `admin/brief` | AC10 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-010、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-011] 多意图分路检索

**阶段状态**：`draft`

**目标**：`named_feature_ids.length ≥ 2` 时每个 ID 各做一轮混合召回（过滤该 `feature_id`），合并去重；空路不导致整轮失败，生成时须声明该功能未写。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F21 | 每个 ID 各做一轮混合召回；合并去重后再 F6；空路在回答里声明该功能文档未写 | `PRD` |
| 需求 ID | RQ-15 | 点名 ≥2 功能则每功能检索一轮 | `PRD` |
| 验收 ID | AC17 | 对 `user-level`、`vip`、`referral` 各至少一路检索；有块的功能出处能带到；不得只编其中一个冒充全部 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-009 | `named_feature_ids` ≥2 且均为已有 ID | 改写输出可断言 |
| STEP-010 | 单路混合召回可复用 | 能对一库过滤 `feature_id` |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `prd/design/user-level/brief/current.md` | `existing` | `REPO_BASELINE` | SRC-BRIEF-UL / `id=user-level.scope` | AC17 |
| `prd/design/vip/brief/current.md` | `existing` | `REPO_BASELINE` | SRC-BRIEF-VIP | AC17 |
| `prd/design/referral/brief/current.md` | `existing` | `REPO_BASELINE` | SRC-BRIEF-REF | AC17 |
| `notes/` 案例 | `existing` | `PRD` 冲突以 v3 为准 | 讲解，非合同 | 理解用，不映射需求 |

**输入**：改写成功且点名 ≥2。查询仍为原句+改写句。  
**输出**：每功能一路结果；合并去重候选；空路标记。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 分路条件 | `named_feature_ids.length ≥ 2` | `C30` |
| 过滤 | payload 限定该 `feature_id`；admin 点名为 `admin` | v3 §12 两 collection 行 |
| 空路 | 某路 0 块不导致整轮失败 | v3 §6.2 步骤 5；`E11` |
| 生成约束 | 不得用其它功能块编该功能规则 | `R4`；F21 |
| 未点名 | 不保证有专路；仍可能被单路召回（本 STEP 不适用单路） | `R9` |

**开发任务**：

1. 对每个点名 ID 各检索一轮后合并去重。
2. 记录每路条数 / 是否空，供日志（STEP-017）使用。
3. 空路信息传递给生成（STEP-013/014）：必须声明该功能文档未写。

**不在本 STEP 范围内**：用户勾选过滤（D1）；热度是否计空路（STEP-019 不计）；重排保底（STEP-012）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | AC17 问句且改写点名三功能 | 三路检索都发生；有块功能出处能带到 | AC17 |
| 异常 | 其中一路 0 块、其它路有块 | 整轮继续；回答声明空路功能未写；不编该功能完整规则 | AC17 / E11 |
| 边界 | 点名 1 个 | 不走本 STEP，走 STEP-010 | AC17 对照 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-011、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-012] 重排、同主题并入、多意图保底

**阶段状态**：`draft`

**目标**：对候选调用 `qwen3.7-text-rerank`；同主题可并入上轮 Top 块；换题不并入；多意图时每非空点名功能至少 1 块进生成，点名数 > n 则 n 提升为功能数。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F6 | `qwen3.7-text-rerank`；多意图时按 C18′ 保底；Top n 进生成 | `PRD` |
| 验收 ID | AC2 | 保级问句有基于 VIP 块的回答（重排后进生成） | `PRD` |
| 验收 ID | AC17 | 保底使有块的点名功能能进出处 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-010 | 单路候选 | 有合并列表或空 |
| STEP-011 | 分路合并候选（若走了分路） | ≥2 时有分路结果 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| 重排型号 `qwen3.7-text-rerank` | `existing`（合同） | `PRD` | C4 | 调用 |
| 默认 n=8，K=64 不进 AC | `existing`（合同） | `PRD` | C18、C18′、CSTR-008 | 可配 |

**输入**：本轮候选；若 `same_topic=true` 可含上轮 Top 块。  
**输出**：Top n 进生成集；0 块交给 STEP-014 系统拒答。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 同主题 | 并入上轮 Top 块再整体重排 | `C27` / `F4` 反面 |
| 换题 | 不并入上轮块 | `C27` / `F4` |
| 保底 | 每个点名功能在该路非空时至少 1 块进生成；点名数 > n 则 n 提升为功能数 | `C18′` |
| 默认 n | 8，可配，不进硬验收 | `C18` |
| 无分数门槛 | 不按 rerank 分数系统拒答 | `C26` |

**开发任务**：

1. 按独立问句重排。
2. 应用同主题并入 / 换题丢弃。
3. 多意图保底；n 提升规则按 C18′。

**不在本 STEP 范围内**：生成（STEP-013）；系统 0 块拒答文案（STEP-014）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 保级问句有候选 | VIP 相关块进入 Top n | AC2 |
| 异常 | 重排 HTTP 失败 | 本轮失败，不编造排序 | E3 / AC8 前置 |
| 边界 | 三功能分路且各非空、n=8 | 每功能至少 1 块进生成 | AC17 / C18′ |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-012、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-013] 流式回答与出处折叠

**阶段状态**：`draft`

**目标**：重排后有块则 `deepseek-flash` 流式回答（思考关），结束后挂可点出处；出处默认折叠为「N 条出处」；可复制；失败丢半段并列出重排出处。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F7 | `deepseek-flash` stream；思考关；结束后挂出处 | `PRD` |
| 需求 ID | F17 | 出处默认「N 条出处」可展开；可复制回答 | `PRD` |
| 验收 ID | AC2 | 流式回答 + 可点出处 | `PRD` |
| 验收 ID | AC8 | 外网 5xx：不出现无出处完整规则答；已有重排块则只列出处 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-012 | Top n 非空（有块路径） | 进生成集长度 > 0 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `deepseek-flash`、`thinking: disabled` | `existing`（合同） | `PRD` | C8、C21 | 生成 |
| 出处字段 path、标题、锚点、chunk id | `existing`（合同） | `PRD` | F7 | 挂载 |

**输入**：进生成 Top n 块（不得使用未进本集的块中的数字/字段/状态）。  
**输出**：流式气泡；结束后折叠出处；复制；或生成失败+出处列表（非回答气泡）。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 流式 | 回答走 stream；出处在生成结束后挂上 | `C21` |
| 失败 | 丢弃半段/完整失败正文；不展示假回答；列出本轮重排后可点出处；出处列表不是回答气泡 | `C25` / `CSTR-033` |
| 不得补写 | 不得添加未进本轮生成集的块中的数字、状态、接口、字段 | `R4` |
| 空路声明 | 某点名功能全程 0 块须声明该功能文档未写 | v3 §6.2 步骤 7 |
| 组合 | 不能把交叉组合写成文档没写的合成权益 | v3 A1 |

**开发任务**：

1. stream 展示阶段文案至「生成中」；成功后挂出处折叠与复制。
2. 失败/中断：UI 无半段成功气泡；若有重排块则列出处。
3. 生成指令包含空路声明与不得补写。

**不在本 STEP 范围内**：点出处跳转（STEP-015）；系统 0 块拒答（STEP-014）；写日志（STEP-017）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | AC2 问句且有块 | 流式回答；结束后「N 条出处」可展开 | AC2 |
| 异常 | DeepSeek 5xx 或断流 | 无完整无出处规则答；有块则只列出处 | AC8 |
| 边界 | 复制按钮 | 可复制回答正文 | F17 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-013、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-014] 拒答与冲突并列

**阶段状态**：`draft`

**目标**：重排 0 块由系统强制拒答；有块但模型认为未写则声明文档未写；互斥块并列摘录不选边。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F8 | 空结果或模型声明未写：不装完整规则；「文档未写」+ 候选 | `PRD` |
| 需求 ID | F9 | 互斥块同入 Top：并列、不选边 | `PRD` |
| 验收 ID | AC4 | 问 brief 未写的具体数字表：拒答或声明未写，不编造表 | `PRD` |
| 验收 ID | AC5 | 并列摘录，不宣称其中一条为唯一现行 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-012 | 重排结果（0 块或有块） | 可知是否空 |
| STEP-013 | 有块时的生成通道 | 模型可声明未写 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| VIP brief「财富值档位数字（原文未给出各等级财富表，不编造）」 | `existing` | `REPO_BASELINE` | SRC-BRIEF-VIP / 约第 33 行 | AC4 语料方向 |
| C26 | `existing` | `PRD` | 仅空结果系统强制拒答；无分数硬门槛 | 判定 |

**输入**：重排后 0 块，或有 Top 块。  
**输出**：系统拒答或模型拒答+候选；冲突时并列摘录。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 系统拒答 | 仅召回空或重排后 0 块 | `C26` / `E5` |
| 模型拒答 | 有 Top 块仍可声明文档未写并给候选 | `C26` / `F8` |
| 冲突 | 并列摘录，不选边，请读原文 | `C7` / `F9` / `E6` |
| 空结果候选 | 可空，引导文档索引 | `F8` |

**开发任务**：

1. 0 块走系统「文档未写」，不调用装完整规则的生成。
2. 有块生成时允许模型拒答并列出这些块。
3. 冲突并列，不宣称唯一现行。

**不在本 STEP 范围内**：编造分数门槛；手动范围过滤。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 问 brief 未写的具体数字表 | 拒答或声明未写，不编造表 | AC4 |
| 异常 | 重排 0 块 | 系统拒答；候选可空 | AC4 / E5 |
| 边界 | 互斥块同入 Top | 并列摘录，不选边 | AC5 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-014、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-015] 出处跳转文档索引

**阶段状态**：`draft`

**目标**：点击出处切到文档索引，按 `{#锚点}` 或标题打开对应 brief 节；当前对话仍在；不把 chunk 注释当 DOM id。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F10 | 切文档索引定位；当前对话仍在；可切回 | `PRD` |
| 验收 ID | AC6 | 点出处落到对应 brief 节；再切回问答，上一轮对话仍在 | `PRD` |
| 验收 ID | AC22 | 从明细点出处切到文档索引，再回问答，当前对话仍在（出处段） | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-013 | 可点出处 | 回答结束有出处 |

明细出处跳转在 STEP-018 复用本能力。

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `window.KB.openDocument` | `existing` | `REPO_BASELINE` | SRC-H5-KB / `async function openDocument`；`window.KB` 导出 | 打开 brief |
| `scrollToTarget(hash, highlightText)` | `existing` | `REPO_BASELINE` | SRC-H5-KB / 约第 278 行 | 锚点或标题定位 |
| `kb-md.js` `{#锚点}` → heading `id` | `existing` | `REPO_BASELINE` | SRC-H5-MD / `pushHeading`；注释丢掉 | 不能用 chunk 注释当 DOM id |
| `setView("kb")` | `existing` | `REPO_BASELINE` | SRC-H5-APP / `target === "kb"` | 切 Tab |

**输入**：出处上的 path、锚点、标题。  
**输出**：文档索引打开对应节；问答会话保留。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 跳转 | path + 标题 `{#锚点}`（有则必带）+ 标题文本；`chunk_id` 给人看 | v3 §4.1 / `C12` |
| 禁止 | 内嵌第二套阅读器；chunk 注释当 DOM id | `OUT-9` / `R7` / `CSTR-023` |

**开发任务**：

1. 点出处：`setView('kb')` + `KB.openDocument`（hash/headingText）。
2. 切回问答时当前对话仍在（含生成中允许切文档索引，STEP-006）。
3. 不为注入 chunk 注释 id 改 `kb-md.js` 默认行为。

**不在本 STEP 范围内**：改文档索引关键词算法（STEP-020 保持）；明细页 UI（STEP-018）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 点 VIP 出处 | 打开 vip brief 对应节（如 `{#logic-wealth}`） | AC6 |
| 异常 | 锚点缺失 | 按标题文本定位 | AC6 |
| 边界 | 切回问答 | 当前对话仍在 | AC6 / AC22 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-015、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-016] 本机配置页分层

**阶段状态**：`draft`

**目标**：锁死项只读展示；可改项保存到 volume 且只用于后续轮；Key 只显示是否已配置；缺文件用 PRD 默认值。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F15 | 只读/可改；保存后用于后续问；看不到 Key；不能改锁死型号/思考 | `PRD` |
| 需求 ID | RQ-12.1 | 锁死只读 / 可改清单 | `PRD` |
| 验收 ID | AC13 | 只读项可见且不可改（含 thinking 关闭、v4/1024、型号）；可改 K 等并保存后用于后续提问；看不到 Key 明文 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-002 | Key 状态接口无明文 | 配置接口可询已配置/未配置 |
| STEP-004 | 问答顶栏可放「配置」 | 与重建并列 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| Demo B `data-open-cfg` / `#cfgRoot` overlay | `existing` | `REPO_BASELINE` | SRC-PROTO-B | 形态参考；抽屉或 overlay 均可 |
| 只读/可改清单 | `existing`（合同） | `PRD` | v3 §6.1 配置页段落；v2 F15 | 字段分层 |

**输入**：volume 中可调配置或缺省。  
**输出**：配置页分层正确；保存后下一轮问答使用新值。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 只读 | embedding 型号与维度、重排型号、改写/回答型号、thinking=关闭、Key 状态、collection 名称、切块口径（仅 default、两库都搜；点名多功能时另走 F21，不是用户勾选过滤） | v3 §6.1 / `C23` |
| 可改 | 召回 K、重排 n、历史轮数、temperature、系统 Prompt、改写 Prompt | v3 §6.1 / `C23` |
| 缺省 | 缺文件用 PRD 默认值 | `R8` |
| 生效 | 只对后续轮 | `CSTR-034` |
| 形态 | 抽屉或 overlay 均可 | `CSTR-025` |
| 禁止 | 改关系图/文档索引参数；改锁死项；显示 Key 明文 | `CSTR-009` / `OUT-15` / `OUT-21` |

**开发任务**：

1. 顶栏打开配置；只读控件不可改。
2. 可改项写入 kb-api volume，不进 git。
3. 切块口径只读文案写明「默认两库都搜；点名多功能走 F21」。

**不在本 STEP 范围内**：实现 F21（STEP-011）；改文档索引。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 打开配置页 | 只读项可见不可改；无 Key 明文 | AC13 |
| 异常 | 试图改 thinking / v4/1024 | 不能改 | AC13 |
| 边界 | 改 K 保存后下一问 | 后续轮使用新 K；本轮进行中不改本轮 | AC13 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-016、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-017] 轮次日志存法 B 与写失败降级

**阶段状态**：`draft`

**目标**：每轮先插 `running` 再更新终态；存法 B；写库失败不阻断问答，只提示未写入，不落本地副本；该轮不进明细/热度。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F18 | 先插 running；结束更新终态；存法 B；写库失败不阻断；不存 Key | `PRD` |
| 需求 ID | RQ-20 | 库挂仍可问答；提示未写入；不落本地副本；该轮不进明细/热度 | `PRD` |
| 验收 ID | AC18 | 生成未结束刷新：明细 `interrupted` 或等价错误态；无半段成功气泡 | `PRD` |
| 验收 ID | AC24 | 写库失败：主路径仍可答；提示未写入；明细/热度无该轮 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | MySQL 服务 | compose 含日志库 |
| STEP-009～STEP-014 | 一轮问答状态机 | 能区分改写失败/空/成功/生成失败 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| 日志行字段 | `existing`（合同） | `PRD` | v3 T2 | 表结构依据 |
| status 枚举 | `existing`（合同） | `PRD` | `running` / `success` / `refuse` / `rewrite_fail` / `gen_fail` / `empty` / `interrupted` | 禁止另造状态名 |
| MySQL 端口 | `planned` | `PLANNED` | CSTR-017 | 不填具体数字 |

**输入**：每点发送的一轮过程数据。  
**输出**：写库成功则一行一轮；失败则提示且该轮不出现在明细/热度。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 存法 B | 回答全文 + 进生成 Top n 每块最多 500 字摘录 + path / chunk_id / 锚点 / feature_id / collection；分路只记 `named_feature_ids` 与每路条数/是否空，不把召回 K 条全文入库 | `C33` / `RQ-19` |
| 发送 | 即尝试写 `running`（有原句） | `C35` / `CSTR-032` |
| 刷新/断流 | 写库成功时记 `interrupted` 等错误态；UI 不展示半段当成功答 | `C35` / `E9` |
| 库挂 | 主路径仍可答；明确提示本轮日志未写入；不落本机副本、不回灌；该轮不进明细/热度；浏览器对话仍按 C6 | `C37` / `E12` / `CSTR-015` |
| 预留字段 | `user_id` / `owner_id` / `tenant_id` / `role` 本期空 | `C13` v3 |
| 不存 | Key；brief 知识源副本 | `F18` / `CSTR-004` / `CSTR-014` |

**开发任务**：

1. 发送插 `running`；终态更新为上表枚举之一。
2. 摘录仅进生成块，每块 ≤500 字；分路只存统计。
3. 写失败：问答继续；UI 提示；不写本地日志文件、不回灌。

**不在本 STEP 范围内**：明细/热度 UI（STEP-018/019）；登录。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | MySQL 可用，生成中刷新 | 明细为 `interrupted` 或等价错误态；无半段成功气泡 | AC18 |
| 异常 | 停 MySQL 后提问 | 主路径仍按既有成败口径作答；提示未写入；明细/热度无该轮 | AC24 |
| 边界 | 改写失败且写库成功 | 行为 `rewrite_fail`；无检索出处 | AC14 联测 / F18 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-017、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-018] 问答明细页

**阶段状态**：`draft`

**目标**：第四 Tab 顶栏「问答明细」进入独立工作区；筛选并打开一轮过程+回答或错误态；不是第 5 Tab。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F19 | 筛时间、原句、功能、结果类型；点开=过程+回答或错误态；出处可跳文档索引；筛选「功能」口径同 C34 | `PRD` |
| 需求 ID | RQ-18 | 顶栏与配置/重建并列；独立工作区；不是第 5/第 6 Tab | `PRD` |
| 验收 ID | AC19 | 可见原句、改写句、点名功能、每路条数/是否空、进生成块摘录（≤500 字）、回答或错误态 | `PRD` |
| 验收 ID | AC22 | 点顶栏进入独立工作区可回问答；顶栏无第 5、第 6 Tab | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-017 | 有写库成功的行 | 至少一轮 `success` 或错误态 |
| STEP-004 | 顶栏可放按钮 | 与配置/重建并列 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| 顶栏入口 | `planned` | `PRD` | C36 | 非新 Tab |
| 明细工作区 | `planned` | `PLANNED` | 不适用 | 可关可回问答 |
| `prd/design/admin/` | `existing` | `REPO_BASELINE` | 产品后台 PRD 目录 | **禁止**把本页写入该目录 |

**输入**：已写入的 F18 行。  
**输出**：可筛选的明细独立页；未写入轮次不出现。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 入口 | 知识问答顶栏与配置/重建并列 | `C36` / `CSTR-006` |
| 筛选功能 | 口径同 C34（进生成块上的 feature_id） | `F19` / `C34` |
| 点开 | 过程+回答或错误态 | `F19` / `C31`（过程在明细不在正式对话） |
| 非目标 | 第 5 Tab；Hayyo 运营后台产品页 | `OUT-19` / `OUT-18` / `CSTR-005` |

**开发任务**：

1. 顶栏按钮打开独立工作区，可关回问答。
2. 实现时间、原句、功能、结果类型筛选；详情展示 AC19 字段。
3. 出处复用 STEP-015；顶栏不增加与四主 Tab 平级的新 Tab。

**不在本 STEP 范围内**：热度聚合（STEP-019）；把过程栏加回正式问答。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 至少一轮写库成功 | 详情含 AC19 所列字段；摘录 ≤500 字 | AC19 |
| 异常 | 写库失败的一轮 | 列表不出现该轮 | AC24 |
| 边界 | 点顶栏「问答明细」再关闭 | 回到问答；无第 5 Tab | AC22 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-018、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-019] 功能热度页

**阶段状态**：`draft`

**目标**：按已写入日志、按 C34 聚合 feature_id 次数降序；未归类单独一行；空路不计。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F20 | 按已写入的 F18 行、按 C34 聚合；降序；未归类单独一行 | `PRD` |
| 需求 ID | RQ-19 | 摘录与热度只用进生成 Top n；无进生成块→未归类；空路不计热度 | `PRD` |
| 验收 ID | AC20 | 跨功能进生成块各 +1 降序；空路不计；无进生成块且写库成功时出现「未归类」 | `PRD` |
| 验收 ID | AC22 | 顶栏「功能热度」进入独立工作区可回问答；无第 6 Tab | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-017 | 写库成功行 | 有可聚合数据 |
| STEP-018 | 顶栏并列入口模式 | 明细入口已证明不是新 Tab |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| C34 | `existing` | `PRD` | SRC-PRD-V3 / 决策表 C34 | 命中口径 |
| 热度页 | `planned` | `PLANNED` | 不适用 | 独立工作区 |

**输入**：已写入且含进生成块元数据的日志行。  
**输出**：降序热度表 + 未归类行。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 命中 | 本轮进生成块上出现过的 `feature_id`（去重，各 +1） | `C34` / `R12` |
| 未归类 | 整轮无进生成块（改写失败、重排 0 块、重排前中断）且写库成功 | `C34` |
| 空路 | 点名但该路 0 块、其它路有块时**不计**空路 | `C34` |
| 排序 | 按次数降序 | `C34` / `F20` |

**开发任务**：

1. 顶栏「功能热度」独立工作区，可回问答。
2. 只聚合写库成功行；按 C34 计数。
3. 未归类单独一行；空路不计。

**不在本 STEP 范围内**：改 C34 口径；账号维度「谁问的」（接受无登录）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 一轮进生成含多个 feature_id | 这些 ID 各 +1，降序 | AC20 |
| 异常 | 分路一空两有且写库成功 | 空路 feature 不计 | AC20 |
| 边界 | 改写失败且写库成功 | 热度出现「未归类」 | AC20 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-019、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-020] 现网三 Tab 不被破坏；鉴权预留

**阶段状态**：`draft`

**目标**：关系图两 Tab 与文档索引关键词/阅读器保持现网行为；问答挂了仍能读文档；鉴权中间件 pass-through；日志预留用户字段本期空。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F13 | 关键词检索与阅读器保持可用；问答服务挂了仍能读文档、关键词搜 | `PRD` |
| 需求 ID | F14 | 中间件 pass-through；日志行预留用户字段（空） | `PRD` |
| 验收 ID | AC7 | 不配 Key 或停 Qdrant：文档索引仍能打开文档 | `PRD` |
| 验收 ID | AC11 | 切回「客户端 ↔ 后台」行为与现网一致，不被问答破坏 | `PRD` |
| 验收 ID | AC12 | 文档索引顶栏关键词仍只做现有关键词检索，不强制走向量 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-003 | 第四 Tab 已接入 | 四 Tab 可切 |
| STEP-015 | 出处会切 kb | 跳转不拆阅读器 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `setView` admin/client | `existing` | `REPO_BASELINE` | SRC-H5-APP / `state.panel = "graph"` | AC11 |
| `kb.js` `search` / `MAX_RESULTS = 20` | `existing` | `REPO_BASELINE` | SRC-H5-KB / `function search` | AC12；不改成向量 |
| `#kbSearch` | `existing` | `REPO_BASELINE` | SRC-H5-HTML / `id="kbSearch"` | 关键词入口 |
| 鉴权中间件 | `planned` | `PRD` | F14；CSTR 预留 | pass-through |

**输入**：现网三 Tab 实现。  
**输出**：三 Tab 回归通过；问答挂起时 kb 仍可用；请求链有空鉴权钩子。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 降级 | 问答挂了仍能读文档、关键词搜 | `F13` / `E1` / `E2` |
| 关键词 | 仍只做现有关键词检索，不强制走向量 | `AC12` |
| 鉴权 | 本期无登录；中间件 pass-through | `F14` / `RQ-17` |
| 预留字段 | `user_id` / `owner_id` / `tenant_id` / `role` 空 | `C13` v3 |
| 禁止 | 实现登录；把问答检索接到 `#kbSearch` | `OUT-5` / `D3` |

**开发任务**：

1. 回归切「客户端 ↔ 后台」「客户端交叉」：选中、布局、打开 PRD 链接不被第四 Tab 破坏。
2. `#kbSearch` 仍走 `kb.js` 关键词；停 Qdrant/缺 Key 时仍能打开文档。
3. kb-api 预留鉴权中间件默认放行；日志用户字段空。

**不在本 STEP 范围内**：D2 把文档索引改为 brief；实现账号。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 切回「客户端 ↔ 后台」 | 与加问答前一致（节点/边/选中规则） | AC11 |
| 异常 | 停 Qdrant 或空 Key 后用文档索引打开 VIP PRD/brief | 阅读器可用 | AC7 |
| 边界 | 文档索引搜正文词 | 关键词结果，不走向量 | AC12 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区回传

**完成回传**：

> 返回 STEP-020、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

## 自检

- [x] F1–F21 均映射到 STEP（RQ-10 / D1–D3 / OUT-* 无实施 STEP）
- [x] AC1–AC24 均映射到 STEP，并写明对象比较方法
- [x] 未增加 PRD 中不存在的业务字段/错误码/状态机（日志 status 仅用 T2 枚举）
- [x] 未使用 `[自定义]` 补造端口、语言、路径前缀
- [x] 路径/符号标记了 `existing` / `planned` / `unverified`
- [x] `existing` 绑定了 source_id 与 locator
- [x] 草稿未自称已验证或可执行
- [x] 关键不确定项（路径前缀、MySQL 端口、后端语言、别名表落点）标 `PLANNED`，未写成已决定事实
- [x] 原型过程栏/chips/剧本条未进入正式 STEP 开发任务

## 阶段结果

`PASS_WITH_RISKS`

非阻断风险：

1. kb-api **语言、HTTP 路径前缀、MySQL 宿主机端口、别名表文件位置** PRD 写「实施时定」，草稿不填具体值；实施 STEP-001/002/017/009 时按已核实的项目约定确定（发现门）。
2. 无 `RUNTIME` 证据；不声称 compose 已拉起问答依赖或线上已验证。
3. AC2 / AC3 / AC17 等依赖外网模型与 Key，本草稿只能规定手工口径，不能规定秒级时延。
4. 默认 64 / 8 / 5 / 对话上限 40 不是硬验收（CSTR-008、CSTR-018）。
5. 日志保留天数未定（CSTR-020），明细页不做过期硬门槛。
6. v2 T4 拟议 `site/kb/` 不存在，后端目录 `planned`，不强制该路径。
7. 配置页抽屉 vs overlay 未指定（CSTR-025），以 AC13 字段分层为准。
8. 改写漏点名则无专路：PRD 已接受，不另开未决。
9. 仓库无 `package.json` / 测试命令；验收为本机 compose + 手工 AC。
10. AC16「日志明细里旧轮次仍在」跨 STEP-005 与 STEP-017，联测时才能完整关闭。

无产品未决（D1–D3 为延期，不阻断拆解）。

业务代码状态：`NOT_STARTED`。

本阶段停止。不得由本文宣布 `STEPS_VERIFIED`、生成里程碑计划或开始开发。

## 进度

> 路径：本文件内（项目无独立进度文档约定）  
> PRD 来源：`site/docs/design/kb-qa/PRD-知识问答-v3.md` v3  
> STEP 来源：`Hayyo-知识问答-STEP-草稿.md`  
> 当前阶段结果：`PASS_WITH_RISKS`

### 进度总览

| 完成数 | 总数 | 当前状态 |
|---|---|---|
| 0 | 20 | `NOT_STARTED` |

### STEP 明细

| STEP | 功能名称 | 需求 ID | 验收 ID | 前置 STEP | 状态 | 证据 |
|---|---|---|---|---|---|---|
| STEP-001 | 本机 Compose 增加问答依赖 | F12、G2 | AC7 | 无 | `NOT_STARTED` | — |
| STEP-002 | 密钥仅服务端与 nginx 反代 | F12、R6 | AC7、AC13 | STEP-001 | `NOT_STARTED` | — |
| STEP-003 | 第四 Tab 独立工作区入口 | F1 | AC1 | 无 | `NOT_STARTED` | — |
| STEP-004 | 正式问答壳 | F17、RQ-16 | AC21 | STEP-003 | `NOT_STARTED` | — |
| STEP-005 | 浏览器多会话 + localStorage | F16、RQ-13 | AC15、AC16 | STEP-004 | `NOT_STARTED` | — |
| STEP-006 | 生成中锁定 | F16、RQ-21 | AC23 | STEP-005 | `NOT_STARTED` | — |
| STEP-007 | 切块、两库、增量对账 | F11 | AC9、AC10 | STEP-001 | `NOT_STARTED` | — |
| STEP-008 | 启动对账与重建索引按钮 | F11、RQ-02、RQ-11 | AC9 | STEP-007、004 | `NOT_STARTED` | — |
| STEP-009 | 追问改写与换题 | F3、F4 | AC3、AC14 | STEP-002、005 | `NOT_STARTED` | — |
| STEP-010 | 单路两库混合召回 | F5 | AC2、AC10 | STEP-007、009 | `NOT_STARTED` | — |
| STEP-011 | 多意图分路检索 | F21、RQ-15 | AC17 | STEP-009、010 | `NOT_STARTED` | — |
| STEP-012 | 重排、同主题并入、保底 | F6 | AC2、AC17 | STEP-010、011 | `NOT_STARTED` | — |
| STEP-013 | 流式回答与出处折叠 | F7、F17 | AC2、AC8 | STEP-012 | `NOT_STARTED` | — |
| STEP-014 | 拒答与冲突并列 | F8、F9 | AC4、AC5 | STEP-012、013 | `NOT_STARTED` | — |
| STEP-015 | 出处跳转文档索引 | F10 | AC6、AC22 | STEP-013 | `NOT_STARTED` | — |
| STEP-016 | 本机配置页分层 | F15、RQ-12.1 | AC13 | STEP-002、004 | `NOT_STARTED` | — |
| STEP-017 | 轮次日志存法 B | F18、RQ-14、RQ-20 | AC18、AC24 | STEP-001、009～014 | `NOT_STARTED` | — |
| STEP-018 | 问答明细页 | F19、RQ-18 | AC19、AC22 | STEP-017、004 | `NOT_STARTED` | — |
| STEP-019 | 功能热度页 | F20、RQ-19 | AC20、AC22 | STEP-017、018 | `NOT_STARTED` | — |
| STEP-020 | 现网三 Tab 与鉴权预留 | F13、F14 | AC7、AC11、AC12 | STEP-003、015 | `NOT_STARTED` | — |

### 阻断与来源变化

| 日期 | STEP | 类型 | 证据或变化 | 处理结果 |
|---|---|---|---|---|
| 2026-09-17 | STEP-001/002/017 | 风险 | 路径前缀 / 端口 / 语言未定 | `PLANNED` 发现门；未改 PRD |
