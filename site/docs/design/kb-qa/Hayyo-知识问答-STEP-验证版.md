---
title: "Hayyo 知识问答 STEP 验证版"
status: "verified"
stage_result: "PASS_WITH_RISKS"
prd: "site/docs/design/kb-qa/PRD-知识问答-v3.md"
prd_sha256: "5788c51623f5873f7c67467e8f5d3a41cc4abab24396905ae2bc0d27adae64b6"
source_draft: "site/docs/design/kb-qa/history/Hayyo-知识问答-STEP-草稿.md"
source_draft_sha256: "ca87fefb34b8f87603a069637247ee887c210f23d250c6c6a8c1eb9c35f30711"
source_verified_r1: "site/docs/design/kb-qa/history/Hayyo-知识问答-STEP-验证版-r1.md"
source_verified_r1_sha256: "8924616f9eef59aeebe40b2b3b327b3123eb763fb8d0dd03e94ce6b4050adf88"
audit: "site/docs/design/kb-qa/history/Hayyo-知识问答-STEP-审查.md"
created: "2026-09-17"
note: "第二轮 review-repair 后的验证版。草稿与 r1 快照未覆盖。业务代码仍为 NOT_STARTED。"
---

# Hayyo 知识问答 STEP 验证版

> **现行权威**：[`PRD-知识问答-v3.md`](PRD-知识问答-v3.md)。  
> **v2 已过期**：[`history/PRD-知识问答-v2.md`](history/PRD-知识问答-v2.md) 不是实施依据（`USER_DECISION`）。v3 写「沿用 / 同 v2」的条款视为 **v3 并入**，只引用 v3，不打开 v2 当现行合同。  
> 过程稿（**不默认读**）：[`history/INDEX.md`](history/INDEX.md)。  
> 本文件经九维复审，仍含非阻断风险；不自动开始开发。

## 来源摘要

事实标签只用：`USER_DECISION`、`PRD`、`CONTRACT`、`REPO_BASELINE`、`RUNTIME`、`PLANNED`、`UNVERIFIED`。本轮无 `RUNTIME`。仓库根无 `package.json`。无 `kb-api` / Qdrant / MySQL 服务。

| source_id | 路径 | 状态 | SHA-256 | 本轮核实 |
|---|---|---|---|---|
| SRC-PRD-V3 | `site/docs/design/kb-qa/PRD-知识问答-v3.md` | `existing` | `5788c51623f5873f7c67467e8f5d3a41cc4abab24396905ae2bc0d27adae64b6` | **唯一现行权威**；已确认；未实施。并入条款以本文件为准 |
| SRC-PRD-V2 | `site/docs/design/kb-qa/history/PRD-知识问答-v2.md` | `expired` | `b3fa6bbd005490fa124698baa39c957465a5cea11402bd511d96a36493926b75` | **已过期，非实施权威**。不沿用已废止的 v2 C6、v2 C13、v2 T6「无必须日志」。本轮 STEP 不把本文件当 locator 来源 |
| SRC-H5-HTML | `site/feature-interaction/index.html` | `existing` | `86e78657d417f738b5761bbe704b57af1a15ce290debbe44e8cc651039e24a92` | 三 Tab：`admin` \| `client` \| `kb`；`#kbWorkspace` |
| SRC-H5-APP | `site/feature-interaction/app.js` | `existing` | `cbc6a79a89524509117b921e05006383163d63ccab34ed0513da11e59e485f79` | `setView`；`visibleIds`；`/` 快捷键 |
| SRC-H5-KB | `site/feature-interaction/kb.js` | `existing` | `a86a9d1721989d2344af20ff31a62cbb173646e8a95cb3680fee2c2e7e6cfb0e` | `openDocument` / `scrollToTarget` / `search`；`MAX_RESULTS=20`；`window.KB` |
| SRC-H5-MD | `site/feature-interaction/kb-md.js` | `existing` | `c39731cbba62477867d65d9cbe26aba4b702ea52b7554322a47b5cab57d09117` | `{#锚点}` → `id`；注释丢掉 |
| SRC-H5-CSS | `site/feature-interaction/style.css` | `existing` | `c6651f39c81e869709d6affddf088fd5e123161ad4839571c939761a4aec6076` | 现网样式 |
| SRC-COMPOSE | `site/docker-compose.yml` | `existing` | `f0dc5d8b02fe29c2c80ec49096f1adacfe6040eb8deb54544249a6422b6ec7e1` | 仅 `web`；`127.0.0.1:18765`；文件头启动命令 |
| SRC-NGINX | `site/docker/nginx.conf` | `existing` | `fc7558ffef014b956a35a6f89adbe6075ff154a74d809a30b5d7d831aca5d7bd` | 无 kb-api 反代 |
| SRC-PRD-INDEX | `prd/INDEX.md` | `existing` | `7a4f22efcbd51ce34243dd19c6c17543cd4683e15407798f55c3356e7585cbed` | 权威 `PRD.md` |
| SRC-BRIEF-VIP | `prd/design/vip/brief/current.md` | `existing` | `3a0c0dcdcf9eb1963f6ea7f44fbe2988f4a5e5888c5a5ceb91cb44923ac8d4c9` | `{#logic-wealth}` |
| SRC-BRIEF-ADMIN | `prd/design/admin/brief/current.md` | `existing` | `99a8846569df3aeedbc9c76c778e633ceaa7fa7b3b4e8574d37cd86efd5988aa` | `id: admin` |
| SRC-BRIEF-MARK | `prd/design/auth-login/brief/current.md` | `existing` | `12e4b663862edf3a4c26636908ccf8c810a4be8c9b173fc5db552187cf09a808` | `chunk:default` / `no` / `related-row` |
| SRC-BRIEF-UL | `prd/design/user-level/brief/current.md` | `existing` | `7f45a2ff626c9175070cf9de46c56fa21b5b636f57348d695f3fe495967a163b` | `user-level.scope` |
| SRC-BRIEF-REF | `prd/design/referral/brief/current.md` | `existing` | `94aeb0624c61970c6101999b86ca69577af7641094c656651ee56648cc14e3c4` | `referral.scope` |
| SRC-PROTO-B | `workspace/kb-qa-proto/demo-b/index.html` | `existing` | `040c60914bed77e0b2e4e99693107fe3a324411d2648a9761913bab386792d2b` | 非正式 |
| SRC-PROTO-CORE | `workspace/kb-qa-proto/shared/qa-core.js` | `existing` | `14508b9c676f446a0e1bc7a42b58aea1cac4cbb44b0bda7530875889c6948335` | 非正式 |
| SRC-PROTO-UI | `workspace/kb-qa-proto/shared/proto-ui.js` | `existing` | `92013362cc8c75b002d438b4556c1e94d32f507d05777d031028bda36875cf54` | 非正式 |

**发现门（不填具体值）：** kb-api 语言、HTTP 路径前缀、MySQL 宿主机端口、功能别名表文件位置、后端目录。实施时按已核实的项目约定确定。

**启动命令（以 compose 文件头为准，不采用与文件冲突的口头省略）：** 在 `site/` 目录 `docker compose up -d`；或仓库根 `docker compose -f site/docker-compose.yml up -d`。仓库根不再放置 `docker-compose.yml`。

## 对象比较约定

比较同一输入快照。PRD 未要求顺序时不增加顺序断言（热度「降序」除外，因 C34/F20 明示）。稳定键优先 `conv_id`、`round_id`、`chunk_id`、`path`、`feature_id`、`data-view`。

| 符号 | 定义 |
|---|---|
| `VIP_BRIEF` | `prd/design/vip/brief/current.md` |
| `ADMIN_BRIEF_PREFIX` | `prd/design/admin/brief/` |
| `MAIN_TABS` | 文本多重集 {「客户端 ↔ 后台」,「客户端交叉」,「文档索引」,「知识问答」}，大小 4 |
| `MAIN_TAB_NODES` | `header .tabs .tab` 按钮集合，与现网 `app.js` 的 `els.tabs = document.querySelectorAll(".tab")` 同一选择器。现网按钮 **无** `role="tab"`（仅父级 `role="tablist"`），比较键不得用 `role=tab`。主 Tab 用 `data-view`。明细 / 热度入口 ∉ 此集合 |
| `C_gen` | 本轮进生成 Top n 块的身份多重集，元素为 `(path, chunk_id, anchor, feature_id, collection)` |
| `excerpt(block)` | 进生成块写入日志的摘录；`len(excerpt) ≤ 500` |
| `status` | 仅 `running` / `success` / `refuse` / `rewrite_fail` / `gen_fail` / `empty` / `interrupted` |
| `truncate18(s)` | 首条用户问句去空白后，长度 >18 则取前 18 字（F16「约 18 字」） |
| `READONLY_FIELDS` | {embedding 型号, embedding 维度, 重排型号, 改写/回答型号, thinking=关闭, Key 状态, collection 名称, 切块口径} |
| `WRITABLE_FIELDS` | {召回 K, 重排 n, 历史轮数, temperature, 系统 Prompt, 改写 Prompt} |

## 输入清单

### 本期有效需求

F1–F21。F14 为 P1，其余 P0。F2/F3/F5 以 v3 表为准。

### 本期有效验收

AC1–AC14（v3 并入；会话=当前对话）、AC15–AC24。完整句子以 v3「沿用」为准，不打开过期 v2 当现行合同。

### 需求确认台账

RQ-01～RQ-12.1、RQ-13～RQ-21。

### 未编号约束（CSTR）

沿用草稿 CSTR-001～CSTR-035。草稿里写「v2 …」的出处，本文件一律读作 **v3 并入**（v3 写沿用 / 同 v2 的那些节）。覆盖草稿出处：

| ID | 摘要 | 来源 |
|---|---|---|
| CSTR-026 | 本期不以 `site/docs/design/h5-kb` L3 为基线 | v3 文首（独立工程 PRD）；`USER_DECISION`：v2 过期 |
| CSTR-036 | 不要把知识问答工程 PRD 写进 `prd/design/*/PRD.md` | v3 §11 |
| CSTR-037 | 健康检查语义：qdrant / 配置是否就绪 / 块数 / Key 是否已配（无明文） | v3 A5（接口沿用） |
| CSTR-038 | 向量 payload 预留 `user_id` / `owner_id` / `tenant_id` / `role`，本期空 | v3 G5、C13、F14 |

### 排除项

沿用 OUT-1～OUT-23，并新增 OUT-24。OUT-22 改引现行范围（不再引用过期 v2 排除表）：

| ID | 项 | 来源 |
|---|---|---|
| OUT-22 | 覆盖或当作旧 H5 L3 已批准实施 | 不在 v3 本期范围；`USER_DECISION`：v2 过期 |
| OUT-24 | 把 kb-qa 工程 PRD 写入 `prd/design/*/PRD.md` | v3 §11 |

延期 D1–D3。技术债同草稿，不新造 `TD-*`。

## 功能清单

同草稿本期范围。不实施 D1–D3、OUT-*。

**发送主路径（F2，不另开 STEP）：** STEP-005 发送按钮把用户问句写入当前 `conv_id` 并触发一轮；同一触发上 STEP-017 先尝试插 `running`；随后 STEP-009 改写。不得把发送编排做成无主路径。

## STEP 总览

| STEP | 标题 | 需求 | 验收 | 前置 | 优先级 |
|---|---|---|---|---|---|
| STEP-001 | 本机 Compose 增加问答依赖 | F12、G2 | —（G2 比较键） | 无 | P0 |
| STEP-002 | 密钥、反代、健康检查（Key/Qdrant/配置就绪） | F12、R6、CSTR-037 | AC7、AC13（Key） | STEP-001 | P0 |
| STEP-003 | 第四 Tab 独立工作区入口 | F1 | AC1 | 无 | P0 |
| STEP-004 | 正式问答壳 | F17、RQ-16 | AC21 | STEP-003 | P0 |
| STEP-005 | 浏览器多会话 + localStorage | F16、RQ-13、F2（发送入口） | AC15、AC16（浏览器侧） | STEP-004 | P0 |
| STEP-006 | 生成中锁定 | F16、RQ-21 | AC23 | STEP-005、STEP-013 | P0 |
| STEP-007 | 切块、两库、增量对账 | F11、G5、CSTR-038 | AC9（清单子条款） | STEP-001 | P0 |
| STEP-008 | 重建按钮、变更清单、块数健康 | F11、RQ-02、RQ-11、CSTR-037 | AC9 | STEP-007、STEP-004 | P0 |
| STEP-009 | 追问改写与换题 | F2、F3、F4 | AC3、AC14 | STEP-002、STEP-005 | P0 |
| STEP-010 | 单路两库混合召回 | F5 | AC2（召回）、AC8（检索 5xx）、AC10 | STEP-007、STEP-009 | P0 |
| STEP-011 | 多意图分路检索 | F21、RQ-15、C30 | AC17（分路） | STEP-009、STEP-010 | P0 |
| STEP-012 | 重排、并入、保底 | F6 | AC2（进生成集）、AC8（重排 5xx）、AC17（保底） | STEP-010；若 `named_feature_ids.length≥2` 则还需 STEP-011 | P0 |
| STEP-013 | 流式回答与出处折叠 | F2、F7、F17 | AC2、AC8（生成 5xx） | STEP-012 | P0 |
| STEP-014 | 拒答与冲突并列 | F8、F9 | AC4、AC5 | STEP-012；模型拒答路径还需 STEP-013 | P0 |
| STEP-015 | 出处跳转文档索引 | F10 | AC6、AC22（出处） | STEP-013 | P0 |
| STEP-016 | 本机配置页分层 | F15、RQ-12.1 | AC13 | STEP-002、STEP-004 | P0 |
| STEP-017 | 轮次日志存法 B | F18、RQ-14、RQ-20 | AC16（日志侧）、AC18、AC24 | STEP-001、STEP-009；AC18 联测 STEP-013 | P0 |
| STEP-018 | 问答明细页 | F19、RQ-18 | AC16（明细可见）、AC19、AC22 | STEP-017、STEP-004 | P0 |
| STEP-019 | 功能热度页 | F20、RQ-19 | AC20、AC22 | STEP-017、STEP-018 | P0 |
| STEP-020 | 现网三 Tab 与鉴权预留 | F13、F14 | AC7（索引仍开）、AC11、AC12 | STEP-003、STEP-015 | P0；F14=P1 |

## 需求映射

| ID | 映射 STEP | 映射方式 |
|---|---|---|
| F1 | STEP-003 | 直接 |
| F2 | STEP-005、STEP-009、STEP-013 | 发送入口；改写；回答 |
| F3 | STEP-009 | 直接 |
| F4 | STEP-009、STEP-012 | 换题布尔；不并入 |
| F5 | STEP-010 | 直接 |
| F6 | STEP-012 | 直接 |
| F7 | STEP-013 | 直接 |
| F8 | STEP-014 | 直接 |
| F9 | STEP-014 | 直接 |
| F10 | STEP-015 | 直接 |
| F11 | STEP-007、STEP-008 | 对账；按钮与清单 |
| F12 | STEP-001、STEP-002 | 绑定；密钥 |
| F13 | STEP-020 | 直接 |
| F14 | STEP-020、STEP-007 | 中间件；payload 预留空字段 |
| F15 | STEP-016 | 直接 |
| F16 | STEP-005、STEP-006 | 多会话；锁定 |
| F17 | STEP-004、STEP-013 | DOM 槽位；阶段驱动+出处折叠 |
| F18 | STEP-017 | 直接 |
| F19 | STEP-018 | 直接 |
| F20 | STEP-019 | 直接 |
| F21 | STEP-011 | 直接 |
| RQ-01 | STEP-007 | embedding |
| RQ-02 | STEP-007、STEP-008 | 增量/全量条件 |
| RQ-03 | STEP-009 | 改写失败 |
| RQ-04 | STEP-013 | 生成失败列出处 |
| RQ-05 | STEP-014 | 系统拒答 |
| RQ-06 | STEP-009、STEP-012 | same_topic |
| RQ-07 | STEP-013 | stream |
| RQ-08 | STEP-007 | 超长块 |
| RQ-09 | STEP-010、STEP-012、STEP-016 | 默认可配不进 AC |
| RQ-10 | 无 | OUT-13；D1 |
| RQ-11 | STEP-008 | 清单、无全文快照 |
| RQ-12 / 12.1 | STEP-016 | 配置分层 |
| RQ-13 | STEP-005 | 多会话 |
| RQ-14 | STEP-017、018、019 | 日志+两页 |
| RQ-15 | STEP-011 | 分路 |
| RQ-16 | STEP-004 | 无过程栏/chips |
| RQ-17 | STEP-020 | 预留空 |
| RQ-18 | STEP-018、019 | 顶栏入口 |
| RQ-19 | STEP-017、019 | 摘录与热度 |
| RQ-20 | STEP-017 | 写库失败 |
| RQ-21 | STEP-006 | 锁定 |
| G1 | STEP-003、013、015 | 约束 |
| G2 | STEP-001 | 直接 |
| G3 | STEP-015 | 直接 |
| G4 | STEP-014 | 直接 |
| G5 | STEP-007、017 | payload 预留+日志上库 |
| G6 | STEP-017、018 | 直接 |
| G7 | STEP-011 | 直接 |
| C1 | STEP-010～013 | 检索+重排+回答 |
| C2、C8、C21 | STEP-013 | 回答 |
| C3 | STEP-010 | 混合召回 |
| C4 | STEP-012 | 重排型号 |
| C5 | STEP-005、009 | 多轮 |
| C6 v3 | STEP-005、017 | 两层 |
| C7、C26 | STEP-014 | 拒答/冲突 |
| C9、C10、C16、C17、C22、C28 | STEP-007 | 索引 |
| C11 | STEP-003 | Tab |
| C12 | STEP-015 | 出处 |
| C13 v3 | STEP-017、020 | 日志；不登录 |
| C14、C29 | STEP-008 | 重建 |
| C15 | STEP-001、002 | 绑定 |
| C18、C18′、C27 | STEP-012 | n 与并入 |
| C19、C24 | STEP-009 | 历史；改写失败 |
| C30 | STEP-009、011 | 点名列表；分路条件 |
| C20 | STEP-001 | 服务 |
| C23 | STEP-016 | 配置页 |
| C25 | STEP-013 | 生成失败（AC8 E4） |
| C31、C32 | STEP-004 | 正式 UI |
| C33、C35、C37 | STEP-017 | 日志 |
| C34 | STEP-019 | 热度 |
| C36 | STEP-018、019 | 入口 |
| C38 | STEP-006 | 锁定 |
| R1、R2、R10、CSTR-036、OUT-24 | 各 STEP「不做」 | 权威/文档 |
| R3 | STEP-007 | 切块 |
| R4 | STEP-011、013 | 不得补写 |
| R5 | STEP-005、017 | 两层 |
| R6 | STEP-002 | 密钥 |
| R7 | STEP-015 | 锚点 |
| R8 | STEP-016 | 分层 |
| R9 | STEP-011 | 未点名无专路 |
| R11 | STEP-006 | 锁定 |
| R12 | STEP-019 | 热度命中 |
| E1、E2 | STEP-002、020 | AC7 |
| E3 | STEP-008、010、012 | 重建失败清单；提问时 embedding/重排 5xx（AC8） |
| E4 | STEP-013 | 生成失败 |
| E5、E6 | STEP-014 | 拒答/冲突 |
| E7 | STEP-009 | 改写失败 |
| E8 | STEP-007 | 超长 |
| E9 | STEP-017 | interrupted |
| E10 | STEP-005 | 配额 |
| E11 | STEP-011 | 空路 |
| E12 | STEP-017 | 库挂 |
| CSTR-037 | STEP-002、008 | 002：qdrant / 配置是否就绪 / Key；008：块数 |
| CSTR-038 | STEP-007 | payload 预留 |
| D1–D3 | 无 | 延期 |
| OUT-1～OUT-24 | 「不做」 | 不实施 |
| T7 | 无修复 STEP | 接受 |

## 验收映射

| AC | 映射 STEP | 比较键（同一快照） |
|---|---|---|
| AC1 | STEP-003 | `MAIN_TAB_NODES` 从左到右文本序列最后一项=「知识问答」，其左侧相邻=「文档索引」。问答工作区根节点 `id ≠ kbWorkspace`。进入后该工作区可见，`#kbWorkspace` 不是问答 DOM 的父节点 |
| AC2 | STEP-010、012、013 | 问句=「保级扣的是财富值还是金币」。010：召回块 `path` 集合含 `VIP_BRIEF`。012：`C_gen` 的 `path` 集合含 `VIP_BRIEF`。013：流式结束后出处 `(path, chunk_id)` 多重集 = `C_gen` 的 `(path, chunk_id)` 多重集；存在成功回答气泡 |
| AC3 | STEP-009 | 上一轮改写成功且问保级。本轮原句=「那退款呢」。本轮 `same_topic=true`；`C_gen`（本轮，在 012 之后联测）的 `path` 集合含 `VIP_BRIEF`。009 单独可测：改写输出 `same_topic=true` 且独立问句非空、未发明功能 ID |
| AC4 | STEP-014 | 问 brief 未写的具体数字表。系统拒答或声明文档未写。回答中出现的数字集合 ⊆ 本轮 `C_gen` 块正文数字集合；`C_gen` 为空则回答数字集合为空 |
| AC5 | STEP-014 | 当 `C_gen` 含互斥两块 A、B：回答同时引用 A、B 的 `(path, chunk_id)`，且不把其中一条标为唯一现行 |
| AC6 | STEP-015 | 点击出处 i 后 `KB.getCurrentPath()` = 出处 i 的 `path`。有锚点则视口元素 `id` = 锚点；否则 `headingText` 命中标题。切回问答后 `conv_id` = 点击前 `conv_id` |
| AC7 | STEP-002、020 | 002：空 Key 或停 Qdrant 后提问，失败说明非空且可区分（缺 Key / 索引未就绪）。020：随后打开已知文档 P，`KB.getCurrentPath()` = P |
| AC8 | STEP-010、012、013 | **提问路径**。010：检索/query embedding 5xx → 成功回答气泡集合为空；不编造候选。012：重排 5xx → 成功回答气泡集合为空；不编造 `C_gen`。013：生成 5xx/断流 → 成功回答气泡集合为空（无半段当成功）。若已有 `C_gen`：可见出处 `(path, chunk_id)` 多重集 = `C_gen` 的 `(path, chunk_id)`，且出处列表不是回答气泡 |
| AC9 | STEP-007、008 | 对块 B=`(path, chunk_id)` 改正文后重建：清单含 `(path, chunk_id, action=改)`。删除 B 后重建：清单含 `(path, chunk_id, action=删)`；此后召回 `chunk_id` 集合不含 B。008「再问」：回答所用 `C_gen` 的 content 反映新文（与 B 新 hash 对应） |
| AC10 | STEP-010 | 问纯后台字段。至少一条出处 `path` 以 `ADMIN_BRIEF_PREFIX` 为前缀 |
| AC11 | STEP-020 | 点击「客户端 ↔ 后台」后：该按钮 `data-view=admin` 且 `active`；`.app` 不含 `kb-active`（问答工作区不可见）；`#kbWorkspace` `hidden`。图仍由现网 `setView('admin')` 路径渲染（不要求改 `visibleIds` 算法） |
| AC12 | STEP-020 | `#kbSearch` 一次查询：结果条数 ≤ 20；打开文档 path ∈ 现网 scan_roots/关键词索引，不是向量 `chunk_id`。该次操作请求 URL 集合不含 kb-api 反代前缀 |
| AC13 | STEP-016、002 | 配置页只读控件名集合 = `READONLY_FIELDS`，均可读不可改。可改控件名集合 = `WRITABLE_FIELDS`。Key 状态 ∈ {已配置, 未配置}，任何响应/DOM 文本不含 Key 明文。保存 K 后下一轮检索参数 `K` = 保存值（本轮进行中不变） |
| AC14 | STEP-009 | 改写失败：本轮出处列表为空；成功回答气泡为空。`conv_id` 不变。上一轮 messages 的 `(role, text)` 多重集与失败前相等。可再发送 |
| AC15 | STEP-005 | 新建 A、B。A 首条用户问句 Ta，B 为 Tb（写入用户气泡即可，**不要求生成成功**）。`title(A)=truncate18(Ta)`，`title(B)=truncate18(Tb)`。`messages(A)` 与 `messages(B)` 的 `(role, text)` 多重集不相交。刷新后 `conv_id` 集合仍含 {A,B} |
| AC16 | STEP-005、017、018 | 005：删除 X 后，列表 `conv_id` 集合与 localStorage 中 id 集合均不含 X。017/018：删除前已写入成功的 `round_id` 多重集，明细页仍全部存在 |
| AC17 | STEP-011、012 | 问句=「用户等级 2、VIP5，在拉新页能获得什么 / 能做什么」。011：本轮检索调用的 `filter.feature_id` 集合 ⊇ {`user-level`,`vip`,`referral`}（各至少一次）。012：每个非空分路的 `feature_id` 在 `C_gen` 中至少 1 块。出处 `feature_id` 能带到有块功能。回答不得把单一功能写成覆盖全部三个 |
| AC18 | STEP-017 | 生成未结束刷新且写库成功：该 `round_id` 的 `status=interrupted`。UI 成功回答气泡不含本轮半段正文 |
| AC19 | STEP-018 | 写库成功 round R：详情投影 (原句, 改写句, `named_feature_ids`, 每路 `(feature_id, count, empty)`, `C_gen` 各块元数据与 `excerpt`, 回答全文或错误态, `status`) = R 写入快照同一组字段 |
| AC20 | STEP-019 | 对已写入成功行按 C34 聚合得到多重集 H=`(feature_id, count)`。热度页行集合（不含未归类）= H。空路 `feature_id` ∉ 本轮 +1 集合。另：无 `C_gen` 且写库成功的轮次使「未归类」行存在 |
| AC21 | STEP-004 | 正式空会话：chip 按钮个数=0（无 `[data-suggest]` / `.qa-chip`）。过程栏节点个数=0（无 `#qaProcess` 及等价右侧过程栏）。`MAIN_TABS` 大小=4 |
| AC22 | STEP-018、019、015 | 点「问答明细」「功能热度」后 `MAIN_TAB_NODES` 文本多重集仍 = `MAIN_TABS`（大小仍为 4；明细/热度按钮 ∉ `MAIN_TAB_NODES`）。独立工作区可关；关后 `conv_id` 不变。015：明细出处跳转后 `getCurrentPath()` = 出处 path，再回问答 `conv_id` 不变 |
| AC23 | STEP-006 | 生成未结束：输入 `disabled`；点击其它对话后 `conv_id` 仍为本轮对话；本轮 `round` 未中断。切文档索引：`data-view=kb` 可达。结束后切换到 Y：`conv_id=Y` 且 messages 不串 |
| AC24 | STEP-017 | 停库或本轮写失败：主路径仍按既有成败作答（回答对错不因写日志失败而改变）。出现「本轮日志未写入」类非空提示。明细 `round_id` 集合与热度所用 round 集合均不含本轮 |

## STEP 模板字段约定

每个 STEP 均适用（与提示词模板对齐，禁止另造字段）：

- **输入**：该 STEP 前置依赖表中的「所需产物」加上来源映射条款。
- **输出**：验收映射表中由该 STEP 负责的比较键全部成立。
- **业务定义**：上文「对象比较约定」中的符号，加上该 STEP 正文已列定义。
- **不在本 STEP 范围内**：其它 STEP 已映射的 ID、OUT-*、D1–D3。

正文较短的 STEP 不重复粘贴上述四块，以免与映射表漂移。

---

## 完整 STEP 提示词

### [STEP-001] 本机 Compose 增加问答依赖

**阶段状态**：`verified`

**目标**：在现有 nginx 之外增加 Qdrant、kb-api、MySQL；只绑 127.0.0.1；避开 3306/3307。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F12 / G2 | 起容器；静态站+问答依赖+日志库；仅 127.0.0.1 | `PRD` |

**前置依赖**：无。

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `site/docker-compose.yml` | `existing` | `REPO_BASELINE` | SRC-COMPOSE / `services.web`；文件头第 3–4 行命令 | 保留 web；按文件头启动 |
| qdrant / kb-api / mysql | `planned` | `PLANNED` | 不适用 | 名称/镜像/端口实施时定 |

**输入**：现网仅 nginx。  
**输出**：三依赖可随 compose 拉起；无 0.0.0.0 映射。

**业务定义**：绑定仅 127.0.0.1（C15）；MySQL 只存轮次日志（C13 v3）；端口避开 3306/3307，具体数字不填（CSTR-017）。

**开发任务**：

1. 增加 Qdrant、kb-api、MySQL；语言/镜像/服务名/路径前缀按项目约定确定。
2. 宿主机绑定 127.0.0.1；Qdrant 不对公网。
3. 用 SRC-COMPOSE 文件头两条命令之一启动后，18765 静态站仍可达。

**不在本 STEP 范围内**：反代与 Key（002）；切块（007）；把本 STEP 当成 AC7。

**测试与验收**：

| 场景 | 输入/前提 | 比较键与预期 | 对应验收 ID |
|---|---|---|---|
| 正常 | 按文件头命令 up | `127.0.0.1:18765/feature-interaction/` 可达；compose `services` 键集合除 `web` 外含问答三依赖（名称 planned 但进程可列） | G2 |
| 异常 | 检查 ports | 每条 ports 宿主机地址=127.0.0.1；映射集合不含 3306、3307 | G2 / CSTR-003 |
| 边界 | 无 0.0.0.0 | compose 与运行中 publish 均无 0.0.0.0 | CSTR-003 |

**完成标志**：

- [ ] 上表比较键全部通过
- [ ] 未映射 AC7、未改其它 STEP 范围
- [ ] 新服务名已回写来源摘要（仍标 planned 直至文件存在）
- [ ] 进度已回传

**完成回传**：返回 STEP-001 状态与证据。不得自动启动下一 STEP。

---

### [STEP-002] 密钥、反代、健康检查（Key/Qdrant/配置就绪）

**阶段状态**：`verified`

**目标**：浏览器只打 kb-api；两 Key 仅环境变量；健康检查能报 Key / Qdrant / 配置是否就绪且无明文。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F12、R6、CSTR-037 | Key 仅服务端；健康检查含 Key 是否已配、qdrant、配置是否就绪 | `PRD`（v3 R6 / A5） |
| 验收 ID | AC7 | 不配 Key 或停 Qdrant：失败说明可读 | `PRD` |
| 验收 ID | AC13 | 看不到 Key 明文 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | 服务可起 | compose 含 kb-api/qdrant |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `site/docker/nginx.conf` | `existing` | `REPO_BASELINE` | SRC-NGINX | 增加反代；前缀 planned |
| `DASHSCOPE_API_KEY`、`DEEPSEEK_API_KEY` | `existing`（名称） | `PRD` | SRC-PRD-V3 / R6（两 Key；名称经 v3「R6 同 v2」并入，不引用过期 v2 文件） | 不进 git |

**输入**：STEP-001 已可列出问答三依赖。  
**输出**：反代后浏览器请求只到本机 kb-api；健康检查含 qdrant 就绪、配置是否就绪、Key 已配/未配且无明文。  
**业务定义**：Key 名称 `DASHSCOPE_API_KEY`、`DEEPSEEK_API_KEY`（v3 R6 并入）；健康检查语义见 CSTR-037（块数属 008）。

**开发任务**：

1. nginx 反代 kb-api；前缀实施时定。
2. 空 Key 不调外网模型；失败说明可区分缺哪类 Key。
3. 健康检查返回 qdrant 是否就绪、配置是否就绪、Key 是否已配置（布尔/枚举），不含明文。

**不在本 STEP 范围内**：配置页字段分层（016）；块数（008）；打开文档（020）。

**测试与验收**：

| 场景 | 输入/前提 | 比较键与预期 | 对应验收 ID |
|---|---|---|---|
| 正常 | Key 已配 | 前端响应/DOM 文本不含 Key 明文；请求只到本机反代 | AC13 |
| 异常 | 环境变量空后提问 | 失败说明非空；类型=缺 Key；不调用外网 | AC7 |
| 边界 | 停 Qdrant 后提问 | 失败说明类型=索引未就绪 | AC7 |
| 健康 | 调健康检查 | 字段含 qdrant 就绪、配置是否就绪、Key 已配/未配；无明文 | CSTR-037 |

**完成标志**：

- [ ] 上表比较键全部通过
- [ ] 未改 016 的只读清单
- [ ] 反代前缀已记录为 planned 或回写 locator
- [ ] 进度已回传

**完成回传**：返回 STEP-002 状态与证据。不得自动启动下一 STEP。

---

### [STEP-003] 第四 Tab 独立工作区入口

**阶段状态**：`verified`

**目标**：在「文档索引」右侧增加「知识问答」Tab，进入独立工作区。

**来源映射**：F1、AC1、C11、CSTR-022、CSTR-035。

**前置依赖**：无。

**参考路径与符号**：SRC-H5-HTML `.tabs` 内 `.tab` 第 17–19 行（现网按钮无 `role="tab"`）；SRC-H5-APP `els.tabs` / `setView`；`#kbWorkspace`；`ev.key === "/"` 约第 482 行。

**输入**：现网三 Tab（admin/client/kb）与 `setView`。  
**输出**：AC1 比较键全部成立。  
**业务定义**：`MAIN_TABS`、`MAIN_TAB_NODES` 见对象比较约定。不得用 `role=tab` 当选择器。

**开发任务**：插入第四 Tab 与独立工作区；扩展 `setView`；问答输入聚焦时 `/` 不抢搜索框。

**不在本 STEP 范围内**：多会话数据（005）；过程栏禁止的完整空状态（004）。

**测试与验收**：

| 场景 | 输入/前提 | 比较键与预期 | 对应验收 ID |
|---|---|---|---|
| 正常 | 打开 H5 点「知识问答」 | 见验收映射 AC1 | AC1 |
| 边界 | 切回文档索引 | `#kbWorkspace` 仍是阅读器，问答根节点不是其子节点 | AC1 |

**完成标志**：AC1 比较键通过；进度已回传。不得自动启动下一 STEP。

---

### [STEP-004] 正式问答壳

**阶段状态**：`verified`

**目标**：左列表+中对话；无过程栏；无 chips；预留阶段文案槽位（驱动在 013）。

**来源映射**：F17（槽位）、RQ-16、AC21、C31、C32。

**前置依赖**：STEP-003。

**参考路径**：SRC-PROTO-B 只借鉴左+中；`#qaProcess`、`.qa-chip` 正式禁止。

**输入**：STEP-003 的第四 Tab 与独立工作区。  
**输出**：AC21 比较键全部成立。  
**业务定义**：正式页无 `#qaProcess`、无 chips（C31/C32）；阶段槽位存在，驱动属 013。

**不在本 STEP 范围内**：阶段文案切换（013）；多会话（005）。

**开发任务**：落地双栏；确认无右侧过程栏、无 chips、无剧本条；阶段槽位存在。阶段文案真正切换属 013。

**测试与验收**：

| 场景 | 输入/前提 | 比较键与预期 | 对应验收 ID |
|---|---|---|---|
| 正常 | 正式空会话 | 见 AC21 | AC21 |

**完成标志**：AC21 比较键通过。不得自动启动下一 STEP。

---

### [STEP-005] 浏览器多会话 + localStorage

**阶段状态**：`verified`

**目标**：新建/切换/删除/清空当前；标题 `truncate18`；刷新恢复；发送用户问句并触发一轮。

**来源映射**：F16、F2（发送入口）、RQ-13、AC15、AC16（浏览器侧）、E10。

**前置依赖**：STEP-004。不前置 013（避免环）。AC15 不要求生成成功。

**参考路径**：SRC-PROTO-CORE `MAX_CONVS=40`、`titleFromText` 仅参考；正式键名 planned。

**输入**：STEP-004 的正式问答壳。  
**输出**：AC15、AC16 浏览器侧比较键全部成立；发送触发 017+009。  
**业务定义**：两层会话 C6；上限默认 40 非硬验收；配额 E10。

**开发任务**：

1. CRUD 与隔离；localStorage 恢复。
2. 发送：写入用户问句到当前 `conv_id` 并触发 017+009。
3. 超限淘汰最旧非当前；写失败提示「对话未保存」。

**不在本 STEP 范围内**：生成中锁定（006）；日志仍在（017/018）。

**测试与验收**：

| 场景 | 输入/前提 | 比较键与预期 | 对应验收 ID |
|---|---|---|---|
| 正常 | 新建 A/B 各写一条用户问句 | 见 AC15 | AC15 |
| 异常 | localStorage 写失败 | 出现「对话未保存」；当前 `conv_id` 仍在内存 | E10 |
| 边界 | 删除 X | 列表与 localStorage 的 id 集合均不含 X | AC16 浏览器侧 |

**完成标志**：AC15 与 AC16 浏览器侧比较键通过。不得自动启动下一 STEP。

---

### [STEP-006] 生成中锁定本轮对话操作

**阶段状态**：`verified`

**目标**：生成未结束禁止再发送/新建/切换/删除/清空；可切其它 Tab 与开配置/明细/热度。

**来源映射**：F16、RQ-21、C38、R11、AC23。

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-005 | 至少两条对话 | conv id 集合大小 ≥2 |
| STEP-013 | 能进入生成中 | 存在 busy/stream 未结束的一轮 |

**输入**：STEP-005 至少两条对话；STEP-013 可进入生成中。  
**输出**：AC23 比较键全部成立。  
**业务定义**：锁定范围见 C38；切 kb/admin/client 与配置/明细/热度不中断本轮。

**不在本 STEP 范围内**：发送入口（005）；流式正文（013）。

**开发任务**：生成中禁用输入并拦截列表操作且不中断本轮；允许切 kb/admin/client 与开配置/明细/热度；结束后切换不串。

**测试与验收**：见 AC23 比较键。

**完成标志**：AC23 通过。不得自动启动下一 STEP。

---

### [STEP-007] 切块、两库、增量对账

**阶段状态**：`verified`

**目标**：只切 `chunk:default`；两 collection；hash 增量；超长失败上报；payload 预留账号字段为空。

**来源映射**：F11、F14、G5、CSTR-038、AC9（清单子条款）。**不映射 AC10。**

**前置依赖**：STEP-001。

**参考路径**：SRC-BRIEF-*；C22 默认 `hayyo-client` / `hayyo-admin`；C17 `text-embedding-v4` 1024。

**输入**：STEP-001 的 Qdrant 可达。  
**输出**：AC9 清单子条款与 CSTR-038 预留字段为空。  
**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| payload | path、feature_id、chunk_id、section、heading、anchor、content_hash、collection，以及 `user_id`/`owner_id`/`tenant_id`/`role` 本期空 | v3 §6.2 索引 + G5；CSTR-038 |
| 路由 | `feature_id===admin` → admin 库，其余 client | CSTR-028 |
| 超长 | 超过 embedding 上限（8192 token）不入库、不二次切 | C28 |

**开发任务**：解析 default 块；hash 对账 upsert/删除陈旧点；超限进失败清单。

**测试与验收**：

| 场景 | 输入/前提 | 比较键与预期 | 对应验收 ID |
|---|---|---|---|
| 正常 | 改块 B 后增量对账 | 清单含 `(path(B), chunk_id(B), action=改)` | AC9 子条款 |
| 异常 | 超长 default | 失败清单含该 `(path, chunk_id)`；该 id 不在库点集合 | E8 |
| 边界 | 预留字段 | 抽查点 payload 的四账号字段均为空 | CSTR-038 |
| 幂等 | 同 hash 再增量 | 不重复 embed（v3 A5 接口沿用） | AC9 子条款 |

**完成标志**：上表通过；未映射 AC10。不得自动启动下一 STEP。

---

### [STEP-008] 重建按钮、变更清单、块数健康

**阶段状态**：`verified`

**目标**：启动自动增量；顶栏「重建索引」同一路径；返回结构化清单；健康检查含块数。

**来源映射**：F11、RQ-02、RQ-11、C14、C29、CSTR-037、AC9。

**前置依赖**：STEP-007、STEP-004。

**输入**：STEP-007 切块对账；STEP-004 顶栏可挂按钮。  
**输出**：AC9 全条款比较键成立；健康检查含非负块数。  
**业务定义**：清单字段 path、chunk_id、旧/新 hash、增/改/删、失败项；不存全文快照（RQ-11）。

**不在本 STEP 范围内**：Key / Qdrant / 配置是否就绪（002）；召回（010）。

**开发任务**：启动与按钮走同一增量；清单字段 path、chunk_id、旧/新 hash、增/改/删、失败项；不存全文快照；健康检查返回块数。

**测试与验收**：见 AC9 全条款（含再问反映新文，联测 010/013）。健康检查块数字段存在且为非负整数。

**完成标志**：AC9 比较键通过。不得自动启动下一 STEP。

---

### [STEP-009] 追问改写与换题

**阶段状态**：`verified`

**目标**：改写产出独立问句 + `same_topic` + `named_feature_ids`（仅已有 ID）；失败整轮停。

**来源映射**：F2、F3、F4、C24、C30、AC3、AC14。

**前置依赖**：STEP-002、STEP-005。

**输入**：STEP-002 的模型 Key；STEP-005 当前 `conv_id` 用户问句。  
**输出**：AC3 改写侧与 AC14 比较键成立。  
**业务定义**：改写模型 `deepseek-flash`、`thinking: disabled`；`named_feature_ids` 仅已有功能 ID（C30）。

**不在本 STEP 范围内**：检索（010/011）；生成（013）。

**开发任务**：调用 `deepseek-flash`、`thinking: disabled`；过滤已有功能 ID；失败不检索不生成。与 017 同一发送触发，009 在 running 尝试之后改写。

**测试与验收**：见 AC3（009 可单独测 same_topic；`C_gen` 含 VIP_BRIEF 与 012 联测）、AC14。

**完成标志**：AC3 改写侧与 AC14 通过。不得自动启动下一 STEP。

---

### [STEP-010] 单路两库混合召回

**阶段状态**：`verified`

**目标**：点名 0 或 1 时两库 BM25+向量混合召回。

**来源映射**：F5、AC2（召回）、AC8（检索/query embedding 5xx）、AC10。**不映射 007。**

**前置依赖**：STEP-007、STEP-009。

**输入**：STEP-007 两库点；STEP-009 独立问句与点名列表（0 或 1）。  
**输出**：AC2 召回段、AC8 检索 5xx 段、AC10 比较键成立。  
**业务定义**：两库 BM25+向量混合召回（C3）；`ADMIN_BRIEF_PREFIX` 见对象比较约定。

**不在本 STEP 范围内**：切块（007）；分路（011）；重排（012）。

**测试与验收**：

| 场景 | 输入/前提 | 比较键与预期 | 对应验收 ID |
|---|---|---|---|
| 正常 | AC2 问句、点名 0/1 | 召回 `path` 集合含 `VIP_BRIEF` | AC2 |
| 边界 | 问纯后台字段 | 至少一条出处/候选 `path` 以 `ADMIN_BRIEF_PREFIX` 为前缀 | AC10 |
| 异常 | 停 Qdrant | 不编造候选；失败类型=索引未就绪 | E2 |
| 异常 | 提问时检索/query embedding 5xx | 成功回答气泡集合为空；不编造候选 | AC8（E3） |

**完成标志**：AC2 召回段、AC8 检索 5xx 段与 AC10 通过。不得自动启动下一 STEP。

---

### [STEP-011] 多意图分路检索

**阶段状态**：`verified`

**目标**：`named_feature_ids.length≥2` 时每 ID 一路，合并去重；空路不整轮失败。

**来源映射**：F21、RQ-15、C30、R9、E11、AC17（分路）。

**前置依赖**：STEP-009、STEP-010。

**输入**：STEP-009 的 `named_feature_ids.length≥2`；STEP-010 单路能力可复用。  
**输出**：AC17 分路段比较键成立。  
**业务定义**：每已有 ID 一路；空路 count=0 且 empty=true，整轮继续（E11）。

**不在本 STEP 范围内**：保底进生成（012）；回答（013）。

**测试与验收**：见 AC17 的 011 段（`filter.feature_id` 集合）。空路：该 `feature_id` 的 count=0 且 empty=true，整轮继续。

**完成标志**：AC17 分路段通过。不得自动启动下一 STEP。

---

### [STEP-012] 重排、同主题并入、多意图保底

**阶段状态**：`verified`

**目标**：`qwen3.7-text-rerank`；同主题可并入上轮 Top；换题不并入；C18′ 保底。

**来源映射**：F6、C18′、C27、AC2（进生成集）、AC8（重排 5xx）、AC17（保底）。

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-010 | 单路候选 | 有合并列表或空 |
| STEP-011 | 仅当 `named_feature_ids.length≥2` | 分路合并结果存在 |

点名 0 或 1 **不得**等待 011。

**输入**：STEP-010 候选；若 `named_feature_ids.length≥2` 则还需 STEP-011 分路结果。  
**输出**：AC2 进生成集段、AC8 重排 5xx 段、AC17 保底段比较键成立。  
**业务定义**：`C_gen` 见对象比较约定；换题不并入（C27）；点名数 > n 时 `n'`=点名功能数（C18′）。

**不在本 STEP 范围内**：流式回答（013）。

**测试与验收**：`C_gen` 的 path 含 `VIP_BRIEF`（AC2）；每个非空分路 feature_id 在 `C_gen` 至少 1 块（AC17）。点名数 > n 时 `n' = 点名功能数`。重排 5xx：成功回答气泡集合为空；不编造 `C_gen`（AC8 E3）。

**完成标志**：AC2 进生成集段、AC8 重排 5xx 段、AC17 保底段通过。不得自动启动下一 STEP。

---

### [STEP-013] 流式回答与出处折叠

**阶段状态**：`verified`

**目标**：有块则 stream；结束后出处折叠；失败丢半段并列 `C_gen` 出处。

**来源映射**：F2、F7、F17、RQ-04、RQ-07、AC2、AC8（生成 5xx / E4）、R4。

**前置依赖**：STEP-012。

**输入**：STEP-012 的 `C_gen`。  
**输出**：AC2 出处段、AC8 生成失败段比较键成立；F17 阶段文案被驱动。  
**业务定义**：出处 `(path, chunk_id)` 多重集 = `C_gen` 的 `(path, chunk_id)`；空路声明「文档未写」。

**不在本 STEP 范围内**：系统 0 块拒答（014）；出处跳转（015）。

**开发任务**：stream；出处 `(path, chunk_id)` = `C_gen`；阶段文案按改写中→检索中→重排中→生成中驱动；复制回答；空路声明未写。

**测试与验收**：见 AC2 013 段、AC8 013 段（生成 5xx/断流）。阶段文案在对应阶段出现（F17）。

**完成标志**：AC2、AC8 生成失败段、F17 阶段驱动通过。不得自动启动下一 STEP。

---

### [STEP-014] 拒答与冲突并列

**阶段状态**：`verified`

**目标**：0 块系统拒答；有块模型可声明未写；冲突并列。

**来源映射**：F8、F9、C26、AC4、AC5。

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-012 | 重排结果 | 可知 `C_gen` 是否空 |
| STEP-013 | 仅模型拒答路径 | 有块仍走生成 |

0 块路径 **不得**等待 013。

**输入**：STEP-012 可知 `C_gen` 是否空；模型拒答路径还需 STEP-013。  
**输出**：AC4、AC5 比较键成立。  
**业务定义**：0 块系统拒答（C26）；有块时回答数字 ⊆ `C_gen` 正文数字。

**不在本 STEP 范围内**：流式主路径成功回答（013）。

**测试与验收**：见 AC4、AC5。

**完成标志**：AC4、AC5 通过。不得自动启动下一 STEP。

---

### [STEP-015] 出处跳转文档索引

**阶段状态**：`verified`

**目标**：点出处打开 brief 对应节；`conv_id` 不变。

**来源映射**：F10、R7、AC6、AC22（出处）。

**前置依赖**：STEP-013。

**参考路径**：`openDocument` 第 356–393 行 `hash` / `headingText`；`scrollToTarget` 第 278 行；`setView('kb')`。

**输入**：STEP-013 的可见出处。  
**输出**：AC6、AC22 出处段比较键成立。  
**业务定义**：跳转走现网 `setView('kb')` + `KB.openDocument`（hash / headingText）。

**不在本 STEP 范围内**：改 `kb-md.js` 注释 id；关系图行为（020）。

**开发任务**：`setView('kb')` + `KB.openDocument`；不为 chunk 注释 id 改 `kb-md.js`。

**测试与验收**：见 AC6、AC22 出处段。

**完成标志**：AC6 与 AC22 出处段通过。不得自动启动下一 STEP。

---

### [STEP-016] 本机配置页分层

**阶段状态**：`verified`

**目标**：只读/可改集合与 PRD 清单相等；Key 无明文；只对后续轮生效。

**来源映射**：F15、RQ-12.1、C23、AC13。

**前置依赖**：STEP-002、STEP-004。

**输入**：STEP-002 的 Key 状态接口；STEP-004 顶栏可挂入口。  
**输出**：AC13 比较键成立。  
**业务定义**：`READONLY_FIELDS` / `WRITABLE_FIELDS` 见对象比较约定；形态抽屉或 overlay 均可（CSTR-025）。

**不在本 STEP 范围内**：反代与健康检查实现（002）。

**测试与验收**：见 AC13。形态抽屉或 overlay 均可（CSTR-025）。

**完成标志**：AC13 字段集合比较通过。不得自动启动下一 STEP。

---

### [STEP-017] 轮次日志存法 B 与写失败降级

**阶段状态**：`verified`

**目标**：发送先插 `running`；存法 B；写失败不阻断、不落本地副本。

**来源映射**：F18、RQ-14、RQ-20、C33、C35、C37、AC16（日志侧）、AC18、AC24。

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | MySQL 服务 | compose 含日志库 |
| STEP-009 | 同一发送触发 | 能区分改写失败/成功 |

017 与 009 同一发送：017 先尝试 `running`，再 009。不要求 010–014 全部完成才开始写 running。终态更新发生在一轮结束时，终态路径依赖 009–014 的结果。AC18（生成未结束刷新）须在 STEP-013 可进入生成中之后联测，013 未完成不得将 AC18 标为 `DONE`。

**输入**：STEP-001 的 MySQL；与 STEP-009 同一发送触发。AC18 联测还需 STEP-013。  
**输出**：AC16 日志侧、AC18、AC24 比较键成立。  
**业务定义**：存法 B 见 C33；status 枚举见对象比较约定；预留用户字段空。

**不在本 STEP 范围内**：改写语义（009）；明细页（018）；热度（019）。

**测试与验收**：见 AC18、AC24、AC16 日志侧。

**完成标志**：AC16 日志侧、AC18、AC24 通过。不得自动启动下一 STEP。

---

### [STEP-018] 问答明细页

**阶段状态**：`verified`

**目标**：顶栏「问答明细」独立工作区；详情字段等于写入快照。

**来源映射**：F19、RQ-18、C36、AC16（明细可见）、AC19、AC22。

**前置依赖**：STEP-017、STEP-004。

**输入**：STEP-017 已写入成功的 round；STEP-004 顶栏。  
**输出**：AC19、AC16 明细、AC22 入口段比较键成立。  
**业务定义**：详情投影字段见 AC19；禁止写入 `prd/design/admin/`（CSTR-005、OUT-24）。

**不在本 STEP 范围内**：热度聚合（019）；写库（017）。

**测试与验收**：见 AC19、AC16 明细、AC22（`MAIN_TAB_NODES` 仍 = `MAIN_TABS`、可回、conv_id 不变）。禁止写入 `prd/design/admin/`（CSTR-005、OUT-24）。

**完成标志**：AC19、AC16 明细、AC22 入口段通过。不得自动启动下一 STEP。

---

### [STEP-019] 功能热度页

**阶段状态**：`verified`

**目标**：按 C34 聚合已写入行；降序；未归类单独一行。

**来源映射**：F20、RQ-19、C34、R12、AC20、AC22。

**前置依赖**：STEP-017、STEP-018。

**输入**：STEP-017 已写入成功行；STEP-018 入口形态可复用。  
**输出**：AC20、AC22 热度入口比较键成立。  
**业务定义**：按 C34 聚合 `(feature_id, count)`；空路不计；无 `C_gen` 计入未归类。

**不在本 STEP 范围内**：明细字段投影（018）。

**测试与验收**：见 AC20（含降序：count 非增）；AC22 热度入口。空路不计。

**完成标志**：AC20、AC22 热度入口通过。不得自动启动下一 STEP。

---

### [STEP-020] 现网三 Tab 不被破坏；鉴权预留

**阶段状态**：`verified`

**目标**：关系图与文档索引保持现网行为；问答挂了仍能打开文档；鉴权 pass-through。

**来源映射**：F13、F14、AC7（索引仍开）、AC11、AC12。

**前置依赖**：STEP-003、STEP-015。

**参考路径**：`setView` admin/client；`kb.js` `search`；`#kbSearch`。

**输入**：STEP-003 第四 Tab 已存在；STEP-015 出处跳转可回文档索引。  
**输出**：AC7 打开文档段、AC11、AC12 比较键成立。  
**业务定义**：现网 `setView('admin'|'client'|'kb')` 与 `#kbSearch` 关键词路径保持；中间件 pass-through。

**不在本 STEP 范围内**：问答检索（010）；配置页（016）。

**开发任务**：回归三 Tab；`#kbSearch` 仍走关键词；停 Qdrant/空 Key 时 `openDocument` 仍成功；中间件 pass-through；日志用户字段空。

**测试与验收**：见 AC11、AC12、AC7 的 020 段。

**完成标志**：AC7 打开文档、AC11、AC12 通过。不得自动启动下一 STEP。

---

## 自检

- [x] F1–F21 均映射；F2 发送主路径写清
- [x] AC1–AC24 均有比较键；AC7/AC10/AC16 只挂直接验证的 STEP；AC8 按 E3/E4 拆到 010/012/013
- [x] AC1/AC22 用 `MAIN_TAB_NODES`（`.tab`），不用 `role=tab`
- [x] v2 标 `expired`；现行 locator 只指向 v3 / 仓库基线
- [x] CSTR-037「配置是否就绪」在 002；块数在 008
- [x] 未新造业务状态；日志 status 仅 T2 枚举
- [x] 未填端口/语言/路径前缀具体值
- [x] `existing` 均有 SHA 与 locator（brief 抽查已补 SHA）
- [x] 012/014/006 依赖按前置条件唯一修正；005 不前置 013（无环）
- [x] payload 预留空字段、健康检查、§11 文档禁写已入 CSTR/OUT
- [x] 各 STEP 均有输入/输出/业务定义；草稿与 r1 快照未覆盖

## 阶段结果

`PASS_WITH_RISKS`

非阻断风险：

1. 语言、反代前缀、MySQL 端口、别名表路径 `PLANNED`。
2. 无 `RUNTIME`；无自动化测试命令。
3. 默认 64/8/5/40 不是硬验收。
4. 日志保留天数未定。
5. 配置抽屉 vs overlay 未指定。
6. 改写漏点名无专路：PRD 已接受。
7. AC4/AC5 在无互斥块/无数字时，比较键为条件句（有则比较身份，无则不编造）。
8. AC3 的「退款相关」用 `same_topic=true` + `VIP_BRIEF` ∈ `C_gen.path`，不编造具体 chunk_id。
9. 服务名/镜像未定，001 比较「三依赖进程可列」而非写死镜像名。
10. `truncate18` 按「约 18 字」取前 18 字；原型省略号不写入硬验收。
11. v3 未抄录沿用 AC/C/E 全文（并入指针在 v3）；实施以 v3 为准，不打开过期 v2 当合同。
12. Key 环境变量名经 v3 R6 并入；v3 正文只写「两 Key」。

无产品语义阻断。业务代码 `NOT_STARTED`。

## 进度

> 路径：本文件内  
> PRD：v3  
> STEP 来源：`Hayyo-知识问答-STEP-验证版.md`  
> 实施计划：`Hayyo-知识问答-实施计划.md`（M1–M4；`IMPLEMENTATION_PLAN_READY`）  
> 当前阶段结果：`PASS_WITH_RISKS`

### 进度总览

| 完成数 | 总数 | 当前状态 |
|---|---|---|
| 6 | 20 | `IN_PROGRESS`（001–005、020 `VERIFIED`；其余 `IMPLEMENTED`；M1 `GATE_EVIDENCE_READY`） |

> 完成数只计 `VERIFIED`。详细证据见 `execution/知识问答开发执行记录.md`。执行器不判定里程碑通过。

### STEP 明细

| STEP | 功能名称 | 需求 ID | 验收 ID | 前置 STEP | 状态 | 证据 |
|---|---|---|---|---|---|---|
| STEP-001 | Compose 问答依赖 | F12、G2 | — | 无 | `VERIFIED` | compose 四服务 Up；ports 仅 127.0.0.1:18765/18766/18767；H5 200 |
| STEP-002 | 密钥/反代/健康检查 | F12、R6 | AC7、AC13 | 001 | `VERIFIED` | health 含 qdrant/config/Key 枚举无明文；空 Key ask=`missing_key`；停 Qdrant 时 `qdrant_ready:false` |
| STEP-003 | 第四 Tab | F1 | AC1 | 无 | `VERIFIED` | `MAIN_TAB_NODES` 末项「知识问答」；`#qaWorkspace` 独立 |
| STEP-004 | 正式问答壳 | F17、RQ-16 | AC21 | 003 | `VERIFIED` | 无 chip / `#qaProcess`；主 Tab=4 |
| STEP-005 | 多会话 | F16、F2 | AC15、AC16 | 004 | `VERIFIED` | `hayyo-kb-qa-conversations-v1`；`truncate18`；删后 id 不在列表 |
| STEP-006 | 生成中锁定 | F16、RQ-21 | AC23 | 005、013 | `IMPLEMENTED` | `lockGuard` 已写；真实流式未结束缺 Key |
| STEP-007 | 切块对账 | F11、G5 | AC9 子条款 | 001 | `IMPLEMENTED` | 单元：`chunk:default`、CSTR-038 空字段；rebuild 缺 DashScope |
| STEP-008 | 重建与清单 | F11 | AC9 | 007、004 | `IMPLEMENTED` | `POST /reindex` 空 Key=`missing_key`；再问待 M3 |
| STEP-009 | 改写 | F3、F4、F2 | AC3、AC14 | 002、005 | `IMPLEMENTED` | 代码+单元 parse；RUNTIME 缺 DeepSeek |
| STEP-010 | 单路召回 | F5 | AC2、AC8、AC10 | 007、009 | `IMPLEMENTED` | hybrid 两库已写；无索引点 |
| STEP-011 | 分路 | F21、C30 | AC17 | 009、010 | `IMPLEMENTED` | `named≥2` 分路代码已写；未 RUNTIME |
| STEP-012 | 重排 | F6 | AC2、AC8、AC17 | 010；（≥2 时）011 | `IMPLEMENTED` | `apply_floor` 单元通过；重排缺 Key |
| STEP-013 | 流式回答 | F7、F17、F2 | AC2、AC8 | 012 | `IMPLEMENTED` | SSE token/citations；未生成成功气泡 |
| STEP-014 | 拒答/冲突 | F8、F9 | AC4、AC5 | 012；（模型拒答）013 | `IMPLEMENTED` | `post_check_answer`；未 RUNTIME |
| STEP-015 | 出处跳转 | F10 | AC6、AC22 | 013 | `IMPLEMENTED` | `openCitation`→`KB.openDocument`；成功出处待 Key |
| STEP-016 | 配置页 | F15 | AC13 | 002、004 | `IMPLEMENTED` | 只读/可改集合相等；K=32 已持久化；检索 K 未 RUNTIME |
| STEP-017 | 轮次日志 | F18 | AC16、AC18、AC24 | 001、009；（AC18 联测）013 | `IMPLEMENTED` | 空 Key 轮次 `gen_fail` 已入表；interrupted/停库未 RUNTIME |
| STEP-018 | 明细页 | F19 | AC16、AC19、AC22 | 017、004 | `IMPLEMENTED` | overlay 非第五 Tab；成功投影待有 `c_gen` 的轮次 |
| STEP-019 | 热度页 | F20 | AC20、AC22 | 017、018 | `IMPLEMENTED` | `unclassified=3`；有块热度待成功轮次 |
| STEP-020 | 三 Tab/鉴权 | F13、F14 | AC7、AC11、AC12 | 003、015 | `VERIFIED` | admin Tab；`#kbSearch≤20` 不打 `/api/kb`；可打开 VIP brief |

### 阻断与来源变化

| 日期 | STEP | 类型 | 证据或变化 | 处理结果 |
|---|---|---|---|---|
| 2026-09-17 | 多处 | 第一轮审查修复 | 见审查报告 Diff（草稿→r1） | 写入验证版 r1；草稿未覆盖 |
| 2026-09-17 | 002/003/010/012/018 等 | 第二轮审查修复 | v2 过期；`MAIN_TAB_NODES`；AC8 E3；CSTR-037 配置就绪 | 写入本文件；r1 快照未覆盖 |
| 2026-09-17 | — | 实施计划 | M1–M4 已确认落盘 `Hayyo-知识问答-实施计划.md` | `IMPLEMENTATION_PLAN_READY`；代码仍 `NOT_STARTED` |
| 2026-09-17 | 001–020 | 实施 | 用户授权按实施计划落地业务代码 | 发现门已填实（见执行记录）；M1 `GATE_EVIDENCE_READY` |
| 2026-09-17 | 007–019 | 阻塞 | 未配置 `DASHSCOPE_API_KEY` / `DEEPSEEK_API_KEY` | 模型链路与重建无 RUNTIME；不标对应 STEP `VERIFIED` |
