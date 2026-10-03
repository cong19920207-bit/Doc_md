---
title: "知识问答多轮对话编排 Phase1 + 工作台管理后台 · STEP 验证版"
status: "verified"
execution_status: "CLOSED_WITH_REMAINING_ITEMS"
contract_integration: "MERGED"
updated: "2026-10-03"
stage_result: "PASS_WITH_RISKS"
source_draft: "site/docs/design/kb-qa-multdesign/history/steps-draft.md"
source_draft_sha256: "f80f6e50bf6a0e9fb9a4d3b0a7b3427888c9d528c924f6c83234583bc2883f04"
audit: "site/docs/design/kb-qa-multdesign/history/step-audit.md"
prd:
  - "site/docs/design/kb-qa-multdesign/PRD-知识问答多轮对话编排-Phase1-v1.10.md"
  - "site/docs/design/kb-qa-multdesign/PRD-Hayyo知识问答工作台管理后台-v1.1-正式确认版.md"
prd_sha256:
  - "9394c15e3303567cea45371046284581f1f5939824ba16579a32c8b9951bdfa9"
  - "93cc8a2cbb52d84d4d8bdbe7448ca8dbd945dbc044d770fdfb9f4fa643403753"
created: "2026-09-29"
note: "step-doc-review review-repair 后的验证版。草稿未覆盖。provisional 的门未过不得开发。不生成里程碑，不开始开发。source_draft_sha256 是审查当时的草稿；迁入 history 后只在文首加了不默认读说明。"
---

# 知识问答多轮对话编排 Phase1 + 工作台管理后台 · STEP 验证版

> **两份权威 PRD**：编排 [`PRD-知识问答多轮对话编排-Phase1-v1.10.md`](PRD-知识问答多轮对话编排-Phase1-v1.10.md)（下称 S01）；后台 [`PRD-Hayyo知识问答工作台管理后台-v1.1-正式确认版.md`](PRD-Hayyo知识问答工作台管理后台-v1.1-正式确认版.md)（下称 ADM）。  
> **两条线**：编排线 STEP-Q01～Q21（S01）；后台线 STEP-A01～A19（ADM）。后台线依赖编排线产出的消息、执行、版本与状态事实。  
> **当前实现状态（2026-10-03）**：用户要求按当前实现收尾，M1～M8 开发批次收口、正式契约已整合；仍有有效需求未完成，详见 [本次收尾](steps-verified.md#2026-10-03-开发收尾与正式契约整合)。下文 STEP 正文与各次记录保留当时口径，不据历史 DONE 推定全部 PRD 验收通过。\
> **不默认读**：[`history/`](history/INDEX.md) 里的 v1.9、STEP 草稿和审查报告。本文件保留复审后的 STEP 正文；后续实施授权和冻结结果见各次用户决定及进度。

## 来源摘要

事实标签只用：`USER_DECISION`、`PRD`、`CONTRACT`、`REPO_BASELINE`、`RUNTIME`、`PLANNED`、`UNVERIFIED`。本节为 2026-09-29 审查快照，当时无 `RUNTIME`。后续运行与测试证据见进度和各日期记录。

基线提交：`eff99affad02523e915748b13ae3c19098879c12`（= 两份 PRD 引用的固定提交）。工作区另有未提交改动：`site/kb-admin/admin.js`、`admin.css`、`index.html`、`contracts/kb-auth/contract.md` §6、`design/kb-admin-ui/INDEX.md`（管理站改为五个工作区）。

| source_id | 路径 | 状态 | 本轮核实（locator） |
|---|---|---|---|
| SRC-PRD-Q | `site/docs/design/kb-qa-multdesign/PRD-知识问答多轮对话编排-Phase1-v1.10.md` | `existing` | 全文；RQ-01～RQ-20 已确认；E01～E08 待确认；C01～C42、AT-01～AT-40 |
| SRC-PRD-A | `site/docs/design/kb-qa-multdesign/PRD-Hayyo知识问答工作台管理后台-v1.1-正式确认版.md` | `existing` | 全文；ADM-R01～R15、ADM-T01～T101、ADM-D01～D10、ADM-C04～C22、ADM-E01～E07 |
| SRC-API | `site/kb-api/app/main.py` | `existing` | `@app.*` 路由：`/api/kb/health`、`/auth/*`、`/conversations`、`/conversations/{conv_id}`（GET/PUT/DELETE）、`/admin/conversations`、`/admin/audits`、`/admin/feedback-summary`（`logs.list_rounds(limit=500)`）、`/admin/heatmap`、`/admin/perms`、`/admin/accounts`（GET/POST/PATCH）、`/admin/roles`、`/admin/roles/{role_id}/permissions`、`/admin/unlock`、`/admin/tls*`、`/config`（GET/PUT）、`/reindex`、`/rounds`、`/rounds/{round_id}`、`/rounds/{round_id}/feedback`、`/heatmap`、`/ask`；`_ask_events`、内部 `finish` |
| SRC-PIPE | `site/kb-api/app/pipeline.py` | `existing` | `parse_rewrite`、`block_identity`、`fill_block_content`、`apply_floor`、`numbers_ok`、`build_rewrite_user`、`retrieve`、`rerank`、`generate_messages`、`post_check_answer`、`public_c_gen` |
| SRC-CONV | `site/kb-api/app/conv_store.py` | `existing` | 模块头「上限 40」；`MAX_CONVS = 40`；满额淘汰分支 |
| SRC-LOGS | `site/kb-api/app/logs.py` | `existing` | `list_rounds(limit=…)`；`heatmap()` 内 `list_rounds(limit=5000)` |
| SRC-CFG | `site/kb-api/app/config_store.py` | `existing` | `_defaults()`；可写 `recall_k`、`rerank_n`、`history_turns`、`temperature` 及两份 Prompt |
| SRC-AUTH | `site/kb-api/app/auth_store.py` | `existing` | `PERM_CHECKBOX` 10 项：知识问答、进管理模块、配置、重建、问答明细、功能热度、对话审计、健康、操作审计、反馈汇总；超管全勾、普通用户仅知识问答 |
| SRC-IDX | `site/kb-api/app/indexer.py` | `existing` | 知识索引 hash 增量对账与重建 |
| SRC-SQL | `site/kb-api/sql/init.sql` | `existing` | 表：`qa_rounds`、`kb_roles`、`kb_role_permissions`、`kb_accounts`、`kb_sessions`、`kb_login_locks`、`kb_audit_logs`、`kb_conversations`；无逐消息表；`CREATE TABLE IF NOT EXISTS` |
| SRC-QAJS | `site/feature-interaction/qa.js` | `existing` | `saveCloud`、`clearCurrent`、`send`、`regen` |
| SRC-ADMJS | `site/kb-admin/admin.js`（含未提交改动） | `existing` | 五工作区壳（总览、问答、索引、记录、访问） |
| SRC-NGINX | `site/docker/nginx.conf` | `existing` | 整站 `auth_request /_kb_site_gate` → 未登录 302 `/login/`；`/kb-admin/` 另走 `/_kb_admin_gate`；`/api/kb/` 由 kb-api 自鉴权 |
| SRC-UI | `site/docs/design/kb-admin-ui/INDEX.md`（未跟踪） | `existing` | §2 壳、§3 工作区表、§4 以后加管理页、§5 不要做（健康仍匿名） |
| SRC-CT-AUTH | `site/docs/contracts/kb-auth/contract.md` | `existing` | §6 管理站：工作区不是新权限；页级接口只按勾选不叠加大门 |
| SRC-TEST | `site/kb-api/tests/`（`test_rules.py`、`test_feedback.py`、`test_retrieve_ops.py`、`test_site_contract.py`、`test_auth_m1..m4.py`） | `existing` | 文件存在；未运行 |

**不在仓库中的引用**（`UNVERIFIED`）：S01 §22.1 的《Hayyo-Phase1-v1.10-文档审核报告.md》、ADM §23.2 的《Hayyo管理后台-v1.1-最终审核报告.md》。不影响拆解，仅无法复核。

## 本轮用户决定

| ID | 决定 | 来源 | 影响 STEP |
|---|---|---|---|
| UD-01 | **E05 流式草稿展示选 C**：知识回答可以流式显示，但要标「草稿·核对中」；证据检查通过后转为正式回答；不通过时替换为修正稿（复查通过）或失败说明。展示与替换只在 Q10。Q19 只产出检查结论。 | `USER_DECISION`（2026-09-29） | Q10 |
| UD-02 | 后台线以**当前工作区**的五工作区结构为页面基线；新页按 `kb-admin-ui/INDEX.md` §4 归入工作区，需要新增工作区时同时改 INDEX §3 与契约 §6。ADM §3.1 的十项菜单为「信息组织建议」，不直接平铺为侧栏。 | `PRD`（ADM §3.1 自称建议）＋`CONTRACT`（SRC-UI §4）；由 AI 按现行约定处理，非新业务决定 | A03～A19 全部页面类 STEP |

## 发现门（不填值、不宣称已决定）

| 门 | 内容 | 相关 STEP | 未过门时 |
|---|---|---|---|
| G-E01 | 消息/执行/版本/任务/gap/Runtime/检查的正式 Schema、接口、错误码 | Q01、Q02、Q11、Q13、Q17、A07 | STEP 保持 `provisional`；不自造字段类型 |
| G-E01（M1 部分） | **已冻结（2026-09-29，用户确认）**：见下方「M1 门定稿」 | Q01、Q02 | — |
| G-E06（M1 部分） | **已冻结（2026-09-29，用户确认）**：Q01 重试去重、Q04 清空竞态，见下方「M1 门定稿」 | Q01、Q04 | — |
| G-E06（M2 部分） | **已冻结（2026-09-29，用户确认）**：幂等键与互斥、快照序列化、补写次数与承载，见下方「M2 门定稿」 | Q07、Q08、Q09 | — |
| G-E05（旧统计兼容） | **已冻结（2026-09-29，用户确认）**：按版本反馈与热度资格的旧记录口径，见下方「M2 门定稿」；SSE 事件与重连协议仍未冻结 | Q21 | — |
| G-E02 | 循环与测试预算、技术重试、总时长、并行、回复预留 | Q16、Q19、A09、A11 | 不启用循环/测试；空值不当无限 |
| G-E03 | 混合召回/重排/接受策略与置信度阈值 | Q11、Q15、A09 | 不预置 0.7、不信 Top 1 |
| G-E04 | Memory 索引底层选型、旧数据映射、覆盖/空洞、回填、失效传播 | Q06、Q14、A13、A14 | 不开发索引作业；覆盖状态显示「未接入」 |
| G-E05 | 旧链路/字段/统计兼容、SSE 事件与重连协议（**草稿展示已由 UD-01 决定**） | Q10、Q17、Q21 | 只做 UD-01 行为；事件名等按已核实约定定 |
| G-E06 | 幂等键、快照序列化、补写次数与承载、Runtime 单独失败、竞态、崩溃收敛 | Q04、Q07、Q08、Q09、A18 | 不承诺任意节点续跑 |
| G-E07 | 实际删除事务、清理失败、残留阻断、必要审计 | A06 | **不开放实际删除按钮** |
| G-E08 | 时区来源、相对时间、知识适用版本元信息 | Q15、Q18 | 不用服务器本地时区代替 |
| G-ADM-E01 | 管理查询 API、分页/限额、错误返回、CSRF 防护核实（**已冻结 2026-09-29，见「M3 门定稿」**） | A04 | 不写死页大小/性能目标 |
| G-ADM-E02 | Prompt 槽位注册、变量/Schema 兼容、配置包存储与原子生效 | A08、A10 | 不开放发布 |
| G-ADM-E03 | test_run 载体、隔离快照、持续执行、资源限额、删除传播 | A11 | 不开放调试发起 |
| G-ADM-E04 | 指标事件、旧热度窗口、统计缓存（**已冻结 2026-09-29，见「M4 门定稿」**） | A15 | 相应指标显示「未接入」 |
| G-E06（A18 旁路观测） | **已冻结（2026-09-29，用户确认）**：见「M4 门定稿」G-E06-6 | A18 | — |
| G-ADM-E05 | 问题记录与原文引用/删除关联 | A17 | 不开放问题创建 |
| G-ADM-E06 | 新权限正式标识与旧角色映射（**已冻结 2026-09-29，见「M3 门定稿」**） | A01 | 不上线权限拆分 |
| G-ADM-E07 | 审计事件编码、结果关联、读取审计失败观测（**已冻结 2026-09-29，见「M3 门定稿」**） | A02 | 高风险写按「审计不可用」阻断 |
| G-PATH | 测试命令：**已冻结（2026-09-29）**——在 `site/kb-api` 下执行 `.venv/bin/python -m pytest`（Python 3.9.6，`pytest.ini`：`pythonpath = .`、`testpaths = tests`）；开工前基线 52 passed（`RUNTIME`） | 全部 | 按已核实项目约定确定 |

### M1 门定稿（`USER_DECISION` 2026-09-29）

只冻结 M1 需要的部分；Q07～Q10 的互斥、快照、补写、SSE 重连仍按原门处理。

**G-E01-1 消息表 `kb_conv_messages`**：`id`（PK，`m_` 前缀）、`conv_id`、`seq`（会话内服务端顺序，`UNIQUE(conv_id, seq)`）、`round_id`（逻辑回合，`lr_` 前缀，服务端生成，≠ `qa_rounds.round_id`）、`round_seq`（本回合 User 消息的 `seq`）、`exec_id`（= `qa_rounds.round_id`）、`role`、`content`、`op_type`（`send`；Q08 加 `refresh`）、`version_no`/`is_current`（M1 固定 1/1，Q08 启用）、`completeness`（`complete`/`partial`/`error_notice`）、`client_request_id`（仅 User，`UNIQUE(conv_id, client_request_id)`）、`source`（`live`/`migrated`）、`created_at`。`seq` 由 `kb_conversations.last_seq` 用 `LAST_INSERT_ID(last_seq+1)` 原子取号。

**G-E01-2 会话表补列**：`last_seq`、`clear_seq`（默认 0）、`hidden_at`（Q03）；另建 `kb_conv_clears(id, conv_id, boundary_seq, actor_id, created_at)` 保留每次清空。

**G-E01-3 Runtime**：沿用 `qa_rounds`，一行 = 一次执行。补列 `schema_ver`、`logical_round_id`、`op_type`、`user_msg_id`、`assistant_msg_id`、`used_knowledge_rag`、`snapshot`、`error_type` 和六类状态：`biz_result`（answered/partial/insufficient/refused/clarify/not_applicable）、`exec_state`（running/completed/failed/interrupted）、`check_status`（pass/fail/error/not_run；Q19 前写 not_run）、`text_integrity`（complete/truncated/empty）、`msg_save`（saved/failed/pending/not_applicable）、`runtime_save`（insert 时 `partial`，最终 update 同句改 `saved`）。空值 = 未知。旧 `status` 照写；旧记录 `schema_ver` 为空按未知读。老库按 `INFORMATION_SCHEMA` 查缺再 `ALTER`，新库写入 `init.sql`。

**G-E01-4 接口与错误码**：`POST /ask` 新增 `client_request_id`（不传则服务端生成、不去重）；请求体 `round_id` 仍作执行 ID。SSE 新增 `accepted{conversation_id, logical_round_id, exec_id, user_msg_id, seq}`；`done` 增加 `exec_id`、`logical_round_id`、`assistant_msg_id`、`statuses`、`error_type`，保留 `status`、`log_written`。新增 `GET /conversations/{id}/messages?after_seq=&limit=`、`POST /conversations/{id}/clear`。错误 JSON 为 `{ok, code, message}`；`user_save_fail`（SSE error，不启动模型）、`duplicate_request`（带已有 id，不新建回合）、`conversation_not_found`（404，不存在/非本人/已隐藏统一）。分页默认 50、上限 200。

**G-E06-1 Q01 重试**：按 `(conv_id, client_request_id)` 唯一约束去重；首次写失败无记录，重试写一次；已成功再提交返回 `duplicate_request`。`qa.js` 每次发送生成 `client_request_id`，收到 `user_save_fail` 撤掉本地这一对消息并把原文放回输入框。

**G-E06-2 Q04 清空竞态**：清空取当时 `last_seq` 为边界，可随时清空（不因执行中拒绝）；有效范围按 `round_seq > clear_seq` 过滤，清空前开始的执行晚到结果照常落库，用户侧不可见。

**其他 M1 决定**：M1 期间 `payload.messages` 只作前端展示缓存，服务端 L1 与清空只认新消息表，前端改读 `/messages` 放在 Q03/Q05；Q05 token 用字符估算（中文 1 字 = 1 token，其他约 4 字符 = 1 token）。

**M1 闸门判定（`USER_DECISION` 2026-09-29）**：带风险通过。MySQL 实库冒烟延后到 M2 闸门前补做；Q04 AT-11「进入澄清」随 Q11（M5）验收。

### M2 门定稿（`USER_DECISION` 2026-09-29）

**G-E06-3 互斥与幂等键（Q07）**：`kb_conversations` 补 `run_exec_id`、`run_until`；带条件 UPDATE 抢占（`run_exec_id` 为空或租期已过，且无保存阻塞）。租期 300 秒，每进入新阶段续期；`finish` 按 `run_exec_id=本执行` 条件释放，崩溃靠租期到期恢复。忙碌返回 SSE error `conversation_busy`（带 `running_exec_id`），前端撤掉本地这一对消息、原文放回输入框。普通发送幂等沿用 `(conv_id, client_request_id)`；刷新也带 `client_request_id`，被接受后写入 `qa_rounds.client_request_id`（普通索引），开跑前先查，已存在返回 `duplicate_request`（带已有 `exec_id`）。顺序沿用 M1：`insert_running` 最先（被拒请求也留执行记录与 `error_type`），然后校验归属 → 查重 → 抢占 → 写 User。每个执行只写自己的行；前端丢弃 `exec_id` 与当前目标不一致的事件。

**G-E06-4 快照序列化（Q08）**：`qa_rounds.snapshot` 在 M1 字段上增加 `l1_msg_ids`（进入 L1 的 User/Assistant 消息 id 对，Assistant 为当时采用的版本）、`prev_exec_id`、`cut_seq`（本回合 User `seq`）、`time_base`（原 User `created_at`，UTC）。刷新读目标逻辑回合首次执行的快照，按 id 读回原消息组装 L1，`prev_blocks` 取 `prev_exec_id` 的 `c_gen`，`time_base` 原样写入新执行。旧快照缺 `l1_msg_ids` 时退化为当前有效范围内 `round_seq` 小于目标回合的当前版本，标 `snapshot_limited: legacy_snapshot`。现链路尚无时间解释，AT-34 在 M2 只在数据层验证。

**版本规则（Q08）**：一次执行 = 一个版本 = 一行 Assistant（按 `exec_id`），`version_no` 在逻辑回合内递增。刷新请求带 `op_type=refresh`、`logical_round_id`、`client_request_id`，问句只取库中原 User 原文。新版本先以 `is_current=0` 写入，保存成功且结果 complete（Q19 前指 success/refuse/empty）才在事务内切换为当前版本；error_notice、partial、保存失败均不替换原默认版本与其反馈。L1 只取当前版本，每轮 `exec_id` 取自该 Assistant 行。前端缓存 `versions[]` + `viewIndex`，「‹ 2/3 ›」切换查看不改默认版本；刷新失败恢复原版本并提示。未带 `logical_round_id` 的旧客户端刷新沿用 M1 行为（不写消息）。

**G-E06-5 补写次数与承载（Q09）**：请求内同步补写 2 次（共 3 次，间隔 0.5 秒、1 秒），内容不变。承载：`qa_rounds.pending_reply`（JSON）为主，进程内按 `exec_id` 缓存为备份。仍失败：`kb_conversations.save_block_exec_id` 写阻塞（写库失败时记进程内），`done` 的 `msg_save=failed`，前端显示「未保存 · 重试保存」并锁该会话输入。阻塞期间抢占返回 `save_blocked`（与 `conversation_busy` 区分）。`POST /api/kb/conversations/{id}/retry-save` 读承载写同一结果，只更新 Runtime 的 `msg_save`、`assistant_msg_id`；刷新版本按版本规则判断是否采用；成功后解除阻塞，可重复调用。承载丢失返回 `save_source_lost`，消息标「保存失败，内容无法恢复」并解除阻塞。会话详情与列表带 `saveBlockedExecId`。

**G-E05 旧统计兼容（Q21）**：反馈仍写 `POST /api/kb/rounds/{exec_id}/feedback` 与 `qa_rounds`，一版本一执行即按版本绑定。`schema_ver>=2` 的执行要求有已保存 Assistant 且结果为 success/refuse/empty，否则 409 `feedback_not_allowed`；旧记录沿用原规则。热度仍取 5000 条：新记录只统计 `used_knowledge_rag=1`；旧记录按旧口径计入不补造资格；返回增加 `legacy_rows`、`unclassified_legacy`，条目增加 `legacy_count`。

**M2 闸门判定（`USER_DECISION` 2026-09-29）**：带风险通过。AT-34 只在数据层验证（时间解释随 Q12/Q17）；进程内承载与阻塞备份在服务重启后丢失，未写入库的承载重试保存返回 `save_source_lost`。

### M3 门定稿（`USER_DECISION` 2026-09-29）

**RISK-02 基线**：以当前工作区 `site/kb-admin/*`（相对上次提交 +1274/−318 行）为后台基线，提交时间由用户安排。

**G-ADM-E06 权限标识与旧角色映射（A01）**：
- 权限码沿用中文名直存 `kb_role_permissions.perm_code`。新增 9 项：配置查看、配置编辑、Prompt查看、Prompt编辑、Prompt调试、配置发布、知识源查看、数据概览、问题处理。不新增「对话删除」。
- 超管角色启动时补全为完整新清单；鉴权仍按 `is_super` 放行。其他角色一律不自动加权限。
- 旧「配置」**停用**：库内保留，不再授予任何能力，也不出现在勾选项。持有它的角色进入迁移报告（超管接口实时计算：角色、原能力、现能力、受影响账号数），在角色页展示。
- `GET /config`：具备「配置查看」或「Prompt查看」之一即可。只有配置查看时不返回 `system_prompt`/`rewrite_prompt`；只有 Prompt查看时只返回这两项，不返回参数。
- `PUT /config`：需要「配置编辑」，含 Prompt 字段时还需「Prompt编辑」，否则整次 403。A08 前仍直接生效，在契约中登记为「待迁移」。
- 页级接口不叠加「进管理模块」大门；后台前端工作区的可见性判断改用新权限码。

**G-ADM-E07 审计编码与结果关联（A02）**：
- 现有 action 保持不变：`login_success`、`login_fail`、`password_change`、`create_account`、`enable_account`、`disable_account`、`change_role`、`create_role`、`change_role_perms`、`unlock`、`tls_upload`、`tls_enable`、`tls_disable`、`config_update`、`reindex`。
- 新登记的编码由后续 STEP 负责写入：`config_draft_save`、`config_validate`、`config_publish`、`config_publish_fail`、`config_rollback`、`config_draft_discard`（用 `object_type` 区分参数与 Prompt）、`debug_run`、`index_backfill`、`index_retry`、`conv_delete`、`issue_create`、`issue_update`、`issue_close`、`issue_reopen`、`sensitive_read`。
- `kb_audit_logs` 补列：`op_id`、`result`（accepted/success/failed/unknown）、`error_code`、`object_type`、`actor_role`、`changed_fields`、`before_ver`、`after_ver`、`relation`、`reason`。旧记录这些列为空，按「旧记录」显示，不补造。
- 高风险写流程：先插入一行 `result=accepted`，插入失败返回 503 `audit_unavailable` 且不执行；执行完同一行更新为 success/failed；更新失败时停留在 accepted，显示「待核对」，不重做。
- 高风险写范围：全部超管写（开户、启停、改角色、建角色、改角色权限、解锁、证书）、`PUT /config`、`POST /reindex`。登录、登出、改密码继续尽力记录，不阻断。
- `sensitive_read`：在对话审计详情、问答明细详情上尽力写入，失败不影响正文返回，只累加进程内失败计数（审计列表 meta 返回；重启清零，属已知风险）。
- 敏感键过滤扩大到 password、secret、token、jwt、authorization、cookie、session、api_key、key_pem、private；审计不写正文与 Prompt 正文。审计无编辑、删除、清空接口。

**G-ADM-E01 管理查询、分页、错误与 CSRF（A04）**：
- 分页：游标（主事件时间倒序 + id 倒序），游标不透明。页大小默认 50、上限 200，可配置；旧 `limit` 参数保留兼容。
- 列表响应：`items`、`next_cursor`、`has_more`、`total`（仅在确实算过时返回，否则 null）、`coverage{complete, note}`、`data_cutoff`、`time_field`、`tz`。
- 时间带时区偏移返回；显示时区可配置，默认 `Asia/Shanghai`，页面标明时区。
- 错误：保留 `{ok:false, message}`，增加 `code`（forbidden、not_found、bad_cursor、audit_unavailable、csrf_rejected 等）。
- M3 覆盖范围：审计列表、账号列表、`/rounds` 改用上述结构；总览「待处理」改为服务端筛选；前端列表统一六态（加载中、有数据、真空、无权限、出错、部分覆盖），返回列表时保留筛选与游标；统一用 `escapeHtml` 做安全渲染。
- CSRF：中间件对 `/api/kb/*` 写方法校验 Origin，没有 Origin 时校验 Referer；主机不一致返回 403 `csrf_rejected`；两者都没有时放行（curl 与测试）。`KB_TRUSTED_ORIGINS` 可追加可信来源。

**M3 闸门判定（`USER_DECISION` 2026-09-29）**：带风险通过。T85、T86 只以审计过滤规则验证，端到端随 A06、A08；审计失败计数在进程内、重启清零（A18 接入观测）；`PUT /config` 在 A08 前直接生效；执行记录按功能筛选标覆盖不完整；会话敏感读随 A05。

### M4 门定稿（`USER_DECISION` 2026-09-29）

**G-ADM-E04 指标事件、旧热度窗口、统计缓存（A15）**：
- 指标只用已记录的事实算：活跃提问账号、新逻辑回合、执行次数、主动刷新、实际调用知识库的执行、业务结果分布、执行异常率、消息保存失败率、Runtime 不完整记录数、反馈覆盖率与已评价赞占比、执行耗时。Route 分布、Memory 调用、证据检查、模型/工具用量显示「未接入」（随 M5、M6）。旧记录（`schema_ver` 为空）无法映射的项单列未知。
- 执行耗时：`qa_rounds` 补 `finished_at`（`DATETIME(3)`），执行收尾写终态时同句写入；耗时 = `finished_at − created_at`，给均值/P50/P95/样本数；没有 `finished_at` 的记录单列未知。补写与重试保存不改 `finished_at`。
- 时间范围：按执行开始时间（`created_at`，UTC 存储）筛选，默认近 7 天，最长 92 天，超出返回 400 `range_too_large`；计数用 SQL 聚合，不拿列表页推算。
- 新热度：在所选范围内按时间倒序最多扫 20000 行，超出返回 `coverage.complete=false` 与实际窗口起止；旧 `/heatmap`、`/admin/heatmap`（5000 条）不动。
- 统计缓存：不缓存，每次实时查询并返回 `data_cutoff`。
- 数据域：本期只有生产数据；测试页签显示「未接入」（随 A11）。
- 权限：概览接口用「数据概览」（从未接入列表移除）；下钻到执行/反馈明细再按「问答明细」「反馈汇总」鉴权，无权时只看聚合。

**G-E06-6 旁路观测（A18）**：
- 诊断事件写到 `DATA_DIR/diag/events.jsonl`：追加写、单文件 5 MB 轮转、保留 3 份；只记事件类型、模块、错误码、关联 id、时间，不含问句、回答、Prompt 与凭据。文件写失败时退回进程内最近 500 条并在诊断接口标「观察受限」。
- 记录点：User 保存失败、Assistant 补写失败/阻塞、Runtime 写入失败或不完整、审计写失败、知识检索异常、模型调用异常。只在已有失败分支追加一行记录，不改原有处理。
- 「标记已查看」作为追加事件（`type=ack`，带操作者与时间），不改原事件，不解除任何阻塞。
- 诊断接口用「健康」权限；打开只读快照，只做数据库与 Qdrant 的 ping，不调用模型、不写业务数据。匿名 `/health` 不变。需要用户原文时跳转到会话/执行页并按其权限再鉴权。

**A05 旧会话**：M1 之前的会话（消息表无记录）标「旧会话，消息待迁移（Q06）」，只读展示 `payload` 缓存，并标注「展示缓存，非服务端事实」。

**M4 闸门判定（`USER_DECISION` 2026-09-29）**：带风险通过。管理页面未在浏览器实跑（容器未重建）；问题记录、Memory、配置版本、测试数据域显示「未接入」（随 A17、M6、A08、A11）；概览下钻只接反馈；Router 失败未写诊断记录。

**M5 闸门判定（`USER_DECISION` 2026-09-29）**：通过，进入 M6。闸门前补做了真实模型冒烟（DeepSeek，14 项：Router 六类分路、闲聊、澄清、混合越界拆分、Rewriter v3 承接、证据检查判 fail/pass 与数字规则均符合预期；闲聊回复按 Prompt 引回业务查询）；在本机站点问答页实发一轮并点出处（运行中的接口为旧镜像）。发现并修复：旧接口没有 `/api/kb/chunk` 时点出处打不开，`checkCitation` 改为返回无业务 `code` 时按原方式打开，新接口的 `source_not_found` / `source_changed` / `source_unavailable` 仍只提示不打开。沿用的过渡：`conversation_task` 仍走知识链路（Q20）；缺较早历史如实说明暂不支持查找（Q16）；改写 Prompt 可编辑不生效（A10）；无断点补流；容器未重建。

### M6 门定稿（`USER_DECISION` 2026-09-29）

**G-E04-1 引擎**：复用 Qdrant，另建对话记忆 collection（与知识库两个 collection 分开，不共用事实源）；向量用现有 DashScope 向量模型；关键词在 MySQL 按本会话有效消息匹配；重排用现有重排模型。

**G-E04-2 粒度**：每条已保存消息一条（User 一条、每个 Assistant 版本各一条），带逻辑回合、版本、时间；超长消息切片并记字符范围；未完成、未保存的 Assistant 内容不索引。

**G-E04-3 写入与覆盖**：消息保存后服务端后台异步写索引；另建索引记录表逐条记已索引 / 失败 / 待处理；服务启动时与手动触发时补齐遗漏；覆盖状态按「本会话应索引的消息 vs 已索引的消息」逐条比对，中间有空洞标「部分」，不只看最新时间。

**G-E04-4 失效**：用户隐藏与清空不删索引，查询时按账号、可见性、清空边界过滤，回源读原文时再复核一次，对不上的命中剔除；只有管理员实际删除（A06，M7）才物理删除索引。

**G-E04-5 旧历史迁移（Q06）**：只迁移消息表里还没有记录的会话；`payload.messages` 中提问与紧随的回答配成一对，回答的执行 id 在同会话执行记录里能对上且原句一致时，按执行记录的时间迁为完整回合；对不上的也迁入，但标「来源受限、无可靠时间」，不参与精确时间查找；不补造清空边界；已隐藏会话迁入后仍隐藏；服务启动时执行，可重复执行、不重复写入。

**G-E02（M6 部分）预算**：每次执行记忆调用（搜索子项 + 读取，含重试）最多 6 次；工作流判断最多 4 步；同时并行最多 3 个；恢复的历史原文合计最多 6000 tokens；单次读取最多 3 个回合；单次记忆调用超时 15 秒、不做技术重试；总截止沿用 300 秒，剩余不足 60 秒不再派发新的记忆调用。

**G-E03 / G-E08（M6 部分）**：不设分数阈值、不信第一名；每个缺口关键词与向量各召回 20 条，融合去重后重排，最多给工作流 5 个候选，由工作流判断找到、继续或澄清；时间按 `KB_DISPLAY_TZ` 与本次提问时间换算（刷新沿用原快照时间）；明确时间只在区间内定位，命中后可补读相邻回合并标真实时间；模糊时间最多放宽一次到前后各一个同等区间并记录。

**Q16 / Q20 执行**：工作流每步只输出一个 JSON 动作（`search` / `read` / `handoff` / `clarify` / `finish`），带缺口、查询或来源、结束原因，服务端校验非法即终止；回看不调模型，原样返回已保存原文并标对话、回合、版本、时间；仅重述只把原文交给模型改写并标「重述，未重新核验」；两者都不调知识库；历史引用点击时经新只读接口按当前可见性与清空边界复核。

**M6 闸门判定（`USER_DECISION` 2026-09-29）**：通过，进入 M7。临时契约 [`M6-契约草案.md`](M6-契约草案.md)。全量 pytest 347 passed；Q06/Q14/Q15/Q16/Q20 均 `DONE`。已知过渡：重述把「文档未写」说成「文档里没写」（不确定之意还在）；运行中的接口容器未重建；问答页历史仍读展示缓存；覆盖页与物理删除随 A14、A06。

**M7 门定稿（`USER_DECISION` 2026-09-29）**：

- **G-E01（A07）**：沿用 `GET /api/kb/rounds` 与 `/rounds/{id}`。详情按七组只读展示已有 Runtime；缺字段标「旧版未记录」；展开其他会话历史正文仍要「对话审计」；页面不调模型、不改 Runtime。
- **G-E07（A06）**：用户删除仍只隐藏。另做仅超管的实际删除：二次确认，审计写不上就拒绝；先让会话不可读，再在同一次操作里删消息、版本、执行记录和记忆索引；可按操作号查询，重复点击不重做；清理失败也保持不可读，不声称备份已删。按钮等本 STEP 做完才出现。
- **G-ADM-E05（A17）**：独立表。状态为未处理、处理中、已关闭，一个处理人，不自动给原文权限；处理记录只追加；关联只存 id，不复制长对话；来源被实际删除后摘录失效并标「来源已删除」；不改赞踩、不改回答。
- **G-E04（A13、A14）**：知识来源只读，不自由新增。重建、回填、重试记成任务，范围重叠则拒绝并指向已有任务。记忆覆盖单独一页，可按会话看空洞并手动回填，与知识索引任务分开。

**M8 门（沿用已确认 PRD，2026-09-30 继续做）**：草稿不生效；发布经校验后一次切换；新接受的提问绑定当时的包，在途执行不改；回退是一次新发布，不兼容的历史包拒绝；同一操作号再点不重复生效。不自动回退。A08～A12、A19 的步骤证据已写入进度表，临时契约见 `M8-契约草案.md`。闸门尚未判定。

## 输入清单

### 有效需求

- S01：RQ-01～RQ-20（全部已确认）。未编号约束见下表 CSTR-Q*。
- ADM：ADM-R01～ADM-R15；已确认方案 ADM-D01～D10、ADM-C04～C22 作为 `USER_DECISION`（由 PRD 正式收录，下文标 `PRD`）约束写入各 STEP 业务定义。

### 有效验收

- S01：C01～C42、AT-01～AT-40（均为验收设计，未执行）。
- ADM：ADM-T01～ADM-T101（下文简写 T01…）。

### 未编号约束（CSTR）

| ID | 摘要 | 来源 |
|---|---|---|
| CSTR-Q01 | 每条实际 User/Assistant 消息一比一写入，不按 Route 筛选 | S01 §6.3 |
| CSTR-Q02 | Runtime 与消息分离；默认不进 L1；多次执行不覆盖成一条 | S01 §6.4、§20.3 |
| CSTR-Q03 | 只保留一个 Rewrite 入口；保留旧分路与保底能力 | S01 §11.3、§12.3、§17.1 |
| CSTR-Q04 | Generate 必须实际收到约束、历史回答与 c_gen 正文；不拿 excerpt 冒充全文 | S01 §11.4、§11.6 |
| CSTR-Q05 | 最终输出分别表达业务结果/执行状态/完整性/消息保存/Runtime 保存/错误 | S01 §20.6、§23 |
| CSTR-Q06 | 按分支实际依赖检查，知识索引故障不挡 ack/纯回看 | S01 §14、§21.1 |
| CSTR-A01 | 无勾选不请求接口、不渲染块；超管视为全勾 | SRC-UI §1 |
| CSTR-A02 | `GET /api/kb/health` 保持匿名，不增加敏感字段 | ADM §13.1；SRC-UI §5 |
| CSTR-A03 | 不套 admin-skin，不跟随 H5 主题；不写进 `prd/design/admin/` | ADM §18.1；SRC-UI §1 |
| CSTR-A04 | 未接入的功能显示「未接入/待配置」，不做可点但空执行的按钮 | ADM §5.4 |
| CSTR-A05 | 页面打开、刷新、保存草稿都不自动调模型、重建、发布 | ADM §19.1、T40、T69 |

### 排除项（两份 PRD 非目标，STEP 不得实现）

- S01 §3：跨 Conversation 检索、长期记忆、多 Agent、开放式工具循环、排队发送、多模型互审、自动回滚旧答案、批量/审批删除、任意步骤自动续跑。
- ADM §1.4：在线编辑 PRD、自由新增知识来源、拖拽编排、自动调优 Prompt、A/B、复杂工单/SLA、计费、多租户、复杂 ACL；管理员改用户原话/答案/赞踩、旧答案设默认、任意节点续跑、强制解除保存阻塞、批量删除/导出、备份恢复；证书不扩到自动签发与端口面板。

## 对象比较约定

记录级验收比较同一输入快照下的稳定标识或字段元组，不只比较条数。PRD 未要求顺序时，不增加顺序断言。

| 符号 | 比较什么 |
|---|---|
| `CONV_SET` | `conversation_id` 的集合 |
| `MSG_ID` | 消息稳定标识 |
| `ROUND_ID` | 逻辑回合标识，不是旧 `qa_rounds.round_id` |
| `VER_ID` | 回答版本标识 |
| `EXEC_ID` | 执行尝试标识 |
| `FEED` | (`VER_ID`, 赞/踩/未评价) |
| `FEAT` | 同一次 `EXEC_ID` 上 `feature_id` 的多重集 |
| `SRC` | 来源类型 + 稳定 id（消息/版本，或 path + chunk_id + hash） |

## STEP 总览

### 编排线（S01）

| STEP | 名称 | 需求 ID | 验收 ID | 前置 | 阶段 |
|---|---|---|---|---|---|
| Q01 | 服务端逐消息事实源（先存 User） | RQ-08（User 部分）、RQ-19（可见性字段）、CSTR-Q01 | AT-27 | 无 | provisional |
| Q02 | Runtime 记录扩展与多维状态 | CSTR-Q02、CSTR-Q05 | AT-15、AT-32 | Q01 | provisional |
| Q03 | 取消 40 上限、列表分页、用户删除改隐藏 | RQ-05、RQ-19 | AT-12、C26（列表/跨端部分） | Q01 | draft |
| Q04 | 服务端清空边界 | RQ-04 | AT-11 | Q01 | provisional |
| Q05 | 服务端组装 L1 | RQ-18 | AT-13、AT-38、C38（L1 部分） | Q01、Q04 | draft |
| Q06 | 旧云端历史迁移 | RQ-12（迁移部分） | 无独立 ID（覆盖由 Q14 验收） | Q01、Q04 | provisional |
| Q07 | 同会话互斥与请求幂等 | RQ-07 | AT-14、C39 | Q01、Q02 | provisional |
| Q08 | 主动刷新：新执行、新版本、原快照 | RQ-06 | AT-09、AT-10、AT-34、AT-37、AT-28（版本部分） | Q01、Q02、Q05、Q07 | provisional |
| Q09 | Assistant 保存失败：同文补写、保存阻塞 | RQ-08 | C40、AT-28（保存部分）、AT-40（补写部分） | Q01、Q07 | provisional |
| Q10 | 断线继续、统一终态、SSE 与草稿展示 | RQ-09、CSTR-Q05 | AT-16、AT-29、C41、AT-40（晚到部分） | Q02、Q07、Q09 | provisional |
| Q11 | Router v3 | RQ-01 | C01、C05、C09 | Q02、Q05 | provisional |
| Q12 | 非知识分支与按分支依赖 | RQ-01、RQ-16、CSTR-Q06 | C04、C06、C07、C08、C12、AT-23 | Q11 | draft |
| Q13 | 任务准备、部分交付、混合越界、跨轮承接 | RQ-02、RQ-03 | C36、C37、AT-01、AT-04、AT-08 | Q11 | provisional |
| Q14 | Conversation Memory 派生索引 | RQ-12（索引部分）、RQ-20 | C29、AT-21 | Q01、Q03、Q04 | provisional |
| Q15 | Memory Tool search/read | RQ-13、RQ-17、RQ-20 | C14、C15、C22、C24、C25、C26（索引/缓存部分）、C27（回源部分）、C28、C30、C31、C38（片段部分）、AT-19 | Q14、Q05 | provisional |
| Q16 | 追溯工作流受控循环与全局预算 | RQ-20 | C02（不调 Memory 部分）、C13、C16、C17、C18、C19、C20、C21、C42、AT-03（恢复部分）、AT-05、AT-06、AT-07、AT-20 | Q13、Q15、Q02 | provisional |
| Q17 | 唯一 Rewriter v3 与旧 Pipeline 适配 | CSTR-Q03 | C03、C33、AT-02、AT-03（交接部分）、AT-35 | Q13 | provisional |
| Q18 | Generate 实际输入交接 | RQ-11、CSTR-Q04 | C02（生成部分）、C10、C32、C34、C35、AT-17、AT-22 | Q17 | provisional |
| Q19 | Evidence check 与最多一次修正 | RQ-10 | AT-18、AT-30、AT-36、AT-39 | Q18、Q02 | provisional |
| Q20 | conversation_task：回看、旧版本、仅重述 | RQ-01、RQ-06（找回部分） | C11、C23、AT-26、AT-33 | Q08、Q13、Q15 | draft |
| Q21 | 按版本赞踩与热度资格 | RQ-14 | AT-24、AT-31 | Q08、Q02 | provisional |

### 后台线（ADM）

| STEP | 名称 | 需求 ID | 验收 ID | 前置 | 阶段 |
|---|---|---|---|---|---|
| A01 | 新动作权限注册与旧角色迁移 | ADM-R09、ADM-R15 | T74、T78、T96 | 无 | provisional |
| A02 | 管理操作审计扩展 | ADM-R10、ADM-R15 | T81～T86、T101 | 无 | provisional |
| A03 | 账号/角色/解锁页面补齐 | ADM-R09 | T75、T76、T77、T79、T80 | A01、A02 | draft |
| A04 | 通用列表与关联查询骨架 | ADM-R12 | T91、T92 | A01 | provisional |
| A05 | M01 会话列表与详情 | ADM-R01 | T01～T07、T10 | A04、Q01、Q03、Q04、Q08 | draft |
| A06 | M01 超管单会话实际删除 | ADM-R01、RQ-15 | T08、T09、AT-25、C27（管理删除部分） | A05、A02、Q14 | provisional |
| A07 | M02 执行列表与详情 | ADM-R02 | T11～T20、T73 | A04、Q02、Q16、Q19 | provisional |
| A08 | 配置包版本化、发布与兼容回退 | ADM-R11 | T24、T87～T90 | A01、A02 | provisional |
| A09 | M03 功能配置页 | ADM-R03 | T21、T22、T23、T25、T26、T27、T28 | A08 | provisional |
| A10 | M04 Prompt 槽位与版本编辑 | ADM-R04 | T29、T30、T36、T40 | A08 | provisional |
| A11 | M04 独立调试 test_run | ADM-R04、ADM-R15 | T31～T35、T37、T38、T39、T97、T98 | A10、A05、A07、Q16（T35 另需 A06） | provisional |
| A12 | 发布必测门 | ADM-R04、ADM-R11、ADM-R15 | T99 | A11、A08 | draft |
| A13 | M05 知识来源与知识索引任务 | ADM-R05、ADM-R15 | T41、T42、T43、T47、T100 | A04、A02 | provisional |
| A14 | M05 对话记忆索引覆盖与回填 | ADM-R05 | T44、T45、T46、T48 | A13、Q14 | provisional |
| A15 | M06 运行概览 | ADM-R06 | T49～T58 | A04、Q02、Q21 | provisional |
| A16 | M07 反馈列表与详情 | ADM-R07 | T59、T60 | A04、Q21 | draft |
| A17 | M07 人工问题记录 | ADM-R07 | T61～T64 | A16、A02（T64 另需 A06） | provisional |
| A18 | M08 健康、异常与证书 | ADM-R08 | T65～T72 | A04、Q02、Q09 | provisional |
| A19 | 旧接口兼容、统一登录核实与状态不虚标 | ADM-R13、ADM-R14、ADM-R15 | T93、T94、T95 | 分验收：T95 无；T93 见正文；T94 不捆绑 T95 | draft |

## 需求映射

| 需求 | STEP |
|---|---|
| RQ-01 | Q11、Q12、Q20 |
| RQ-02、RQ-03 | Q13 |
| RQ-04 | Q04 |
| RQ-05 | Q03 |
| RQ-06 | Q08、Q20 |
| RQ-07 | Q07 |
| RQ-08 | Q01（User 先存）、Q09（Assistant 补写） |
| RQ-09 | Q10 |
| RQ-10 | Q19 |
| RQ-11 | Q18 |
| RQ-12 | Q06（迁移）、Q14（索引/回填） |
| RQ-13 | Q15 |
| RQ-14 | Q21 |
| RQ-15 | A06 |
| RQ-16 | Q12 |
| RQ-17 | Q15 |
| RQ-18 | Q05 |
| RQ-19 | Q01（字段）、Q03（行为） |
| RQ-20 | Q14、Q15、Q16 |
| CSTR-Q01～Q06 | Q01、Q02、Q17、Q18、Q02/Q10、Q12 |
| ADM-R01 | A05、A06 |
| ADM-R02 | A07 |
| ADM-R03 | A09 |
| ADM-R04 | A10、A11、A12 |
| ADM-R05 | A13、A14 |
| ADM-R06 | A15 |
| ADM-R07 | A16、A17 |
| ADM-R08 | A18 |
| ADM-R09 | A01、A03 |
| ADM-R10 | A02 |
| ADM-R11 | A08、A12 |
| ADM-R12 | A04（列表/分页/安全渲染）、A09 与 A10（§5.4 离页提示与保存失败留本地） |
| ADM-R13、ADM-R14 | A19 |
| ADM-R15 | A01（T96）、A02（T101）、A11（T97、T98）、A12（T99）、A13（T100）、A19（T95） |
| G01 | A04 |
| G02、G04 | A07 |
| G03 | A08 |
| G05 | A15 |
| G06 | A01、A06 |
| G07 | A19 |
| S01 §20.2 引用点击 | Q18（知识引用）、Q20（历史引用） |
| ADM §6.3 详情不注入用户上下文 | A05 |
| ADM §8.6 话术预览 | A09 |

## 验收映射

| 验收 | STEP |
|---|---|
| C01、C05、C09 | Q11 |
| C02 | Q16（L1 足够不调 Memory）＋Q18（生成收到历史回答与不重复约束） |
| C03、C33 | Q17 |
| C04、C06、C07、C08、C12 | Q12 |
| C10、C32、C34、C35 | Q18 |
| C11、C23 | Q20 |
| C13、C16～C21、C42 | Q16 |
| C14、C15、C22、C24、C25、C28、C30、C31 | Q15 |
| C26 | Q03（列表/跨端不可见）＋Q15（索引/缓存不返回） |
| C27 | Q15（回源复核剔除）＋A06（管理删除触发清理） |
| C29 | Q14 |
| C36、C37 | Q13 |
| C38 | Q05（L1 不截半轮）＋Q15（片段标识范围） |
| C39 | Q07 |
| C40 | Q09 |
| C41 | Q10 |
| AT-01、AT-04、AT-08 | Q13 |
| AT-02、AT-35 | Q17 |
| AT-03 | Q17（交接、不把预算计数归零、不因旧执行表拒绝）＋Q16（同一 EXEC_ID 内实际恢复） |
| AT-05、AT-06、AT-07、AT-20 | Q16 |
| AT-09、AT-10、AT-34、AT-37 | Q08 |
| AT-11 | Q04 |
| AT-12 | Q03 |
| AT-13、AT-38 | Q05 |
| AT-14 | Q07 |
| AT-15、AT-32 | Q02 |
| AT-16、AT-29 | Q10 |
| AT-17、AT-22 | Q18 |
| AT-18、AT-30、AT-36、AT-39 | Q19 |
| AT-19 | Q15 |
| AT-21 | Q14 |
| AT-23 | Q12 |
| AT-24、AT-31 | Q21 |
| AT-25 | A06 |
| AT-26、AT-33 | Q20 |
| AT-27 | Q01 |
| AT-28 | Q08（旧默认版本不被替换）＋Q09（补写同一结果） |
| AT-40 | Q09（补写只更新保存状态）＋Q10（晚到结果不改终态） |
| T01～T07、T10 | A05 |
| T08、T09 | A06 |
| T11～T20、T73 | A07 |
| T21～T23、T25～T28 | A09 |
| T24、T87～T90 | A08 |
| T29、T30、T36、T40 | A10 |
| T31～T35、T37～T39、T97、T98 | A11 |
| T41～T43、T47、T100 | A13 |
| T44～T46、T48 | A14 |
| T49～T58 | A15 |
| T59、T60 | A16 |
| T61～T64 | A17 |
| T65～T72 | A18 |
| T74、T78、T96 | A01 |
| T75～T77、T79、T80 | A03 |
| T81～T86、T101 | A02 |
| T91、T92 | A04 |
| T93、T94、T95 | A19 |
| T99 | A12 |

## 通用约定（每个 STEP 适用）

**通用完成标志**：①本 STEP 验收断言全部通过；②未改变其他 STEP 的范围或来源需求；③新发现的路径、符号和契约证据已更新状态；④进度按下方「进度」区块回传；⑤对人可见的新增/优化按 `.cursor/rules/devlog.mdc` 追加开发记录。

**完成回传**：返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

**门未过**：该 STEP 停在 `provisional`；只能做不依赖该门的子项，并在回传中写清哪一项被门挡住。

**页面类 STEP（A 线）**：先读 `design/kb-admin-ui/INDEX.md`；按 §4 归入现有工作区（UD-02）；用 `.kb-card`、`.kb-btn`、`.kb-badge`、`.kb-table`；遵守 CSTR-A01～A05。开工前确认 SRC-ADMJS 的未提交改动已提交或已被确认为基线。

---

## 编排线 STEP 提示词

### [STEP-Q01] 服务端逐消息事实源（先存 User）

**阶段状态**：`provisional`（门：G-E01、G-E06）

**目标**：每条实际 User/Assistant 消息按条写入服务端 MySQL，普通发送先保存 User 再启动任何模型调用。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | RQ-08（User 部分） | 普通发送先保存 User；提问保存失败则不启动，保留草稿 | `PRD` S01 §20.4 第 2 条 |
| 需求 | RQ-19（字段部分） | 用户隐藏为账号级不可见，数据库保留 | `PRD` S01 §6.10 |
| 需求 | CSTR-Q01 | 所有 Route 的实际消息都写入 | `PRD` S01 §6.3 |
| 验收 | AT-27 | User 原文保存失败：不启动 Router/工具/模型，保留草稿；重试不重复逻辑回合 | `PRD` |

**前置依赖**：无。

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `site/kb-api/sql/init.sql` | `existing` | `REPO_BASELINE` | SRC-SQL / `kb_conversations`、`qa_rounds` | 现有会话与日志表；新增消息表的落点 |
| `site/kb-api/app/conv_store.py` | `existing` | `REPO_BASELINE` | SRC-CONV / 模块 | 现有 payload 整包存储 |
| `site/kb-api/app/main.py` `_ask_events` | `existing` | `REPO_BASELINE` | SRC-API / `_ask_events` | 在此处前置 User 保存 |
| 消息表与字段名 | `planned` | `PLANNED` | 不适用 | 按 G-E01 定稿 |
| 已有库补表方式 | `unverified` | `UNVERIFIED` | 不适用 | `CREATE TABLE IF NOT EXISTS` 不会给旧库补列，需按项目约定确定 |

**输入**：S01 §6.3 的消息语义表；§23「消息保存」行。

**输出**：服务端消息存储层（写入、按会话有序读取）；ask 入口先存 User。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 消息基线字段 | `conversation_id`、`round_id`（逻辑回合）、`role`、`content`、`created_at` | S01 §6.3 |
| 必须表达的语义 | 消息唯一标识与服务端顺序；逻辑回合/执行尝试/操作类型；Assistant 版本与当前采用版本；完整性、执行终态、保存状态；清空边界与可见性 | S01 §6.3 表 |

**开发任务**：

1. 按 G-E01 定稿的 Schema 新增消息存储，包括服务端顺序（时间相同也不串序）和版本关联字段。
2. 已有库的建表/补列按已核实的项目约定处理，不改动已有 `qa_rounds` 语义。
3. 在 `_ask_events` 中，普通发送先写 User；写失败直接返回可识别的失败，不进入 Router/检索/生成。
4. Assistant 最终消息写入走同一存储层（失败处理归 Q09）。
5. 不按 Route 筛选：ack、smalltalk、out_of_scope、unclear 的回复都写入。

**不在本 STEP 范围内**：旧数据迁移（Q06）；L1 组装（Q05）；会话列表/隐藏（Q03）；Assistant 补写（Q09）；前端 `saveCloud` 改造（Q03、Q05 适配）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 发送「谢谢」得到 ack | User、Assistant 两条都落库 | CSTR-Q01 |
| 异常 | 模拟 User 写入失败 | 不调用 Router/模型；客户端收到失败并保留草稿；重试不产生两个逻辑回合 | AT-27 |
| 边界 | 两条消息同一时间戳 | 服务端顺序稳定、可区分 | CSTR-Q01 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q02] Runtime 记录扩展与多维状态

**阶段状态**：`provisional`（门：G-E01）

**目标**：每次执行有独立 Runtime 记录，并分别表达业务结果、执行状态、检查状态、文本完整性、消息保存与 Runtime 保存。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | CSTR-Q02 | Runtime 与消息分离；多次执行不覆盖成一条 | `PRD` S01 §6.4、§20.3 |
| 需求 | CSTR-Q05 | 最终输出不得用一个 success/log_written 覆盖全部 | `PRD` S01 §20.6 |
| 验收 | AT-15 | 日志插入成功、最终更新失败；消息保存独立成功/失败 → 分别记录 | `PRD` |
| 验收 | AT-32 | 校验通过但业务部分有依据或保存失败 → 状态分开 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q01 | 消息标识、逻辑回合、执行关联 | 能按消息找到其执行 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `site/kb-api/app/logs.py` | `existing` | `REPO_BASELINE` | SRC-LOGS / `list_rounds`、`update_round` 所在模块 | 复用既有执行日志 |
| `qa_rounds` | `existing` | `REPO_BASELINE` | SRC-SQL / `qa_rounds` | 旧 `round_id` 保留旧执行语义 |
| `main.py` `finish` | `existing` | `REPO_BASELINE` | SRC-API / `_ask_events.finish` | 终态写入点 |
| 新增字段/枚举 | `planned` | `PLANNED` | 不适用 | G-E01 |

**输入**：S01 §20.3 列出的 Runtime 语义；ADM §4.2 六类状态。

**输出**：Runtime 写入与读取能力；六类状态字段；执行与逻辑回合/版本的关联。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 六类状态 | 业务结果、执行状态、检查状态、文本完整性、消息保存、Runtime 保存；独立表达 | ADM §4.2；S01 §11.7.3 |
| 未知 | 未知不得默认为 0、false、pass 或成功 | ADM §4.2 |
| 旧 `round_id` | 保留旧执行日志语义，与新逻辑回合通过可验证关联适配 | S01 §0.3、§21.2 |

**开发任务**：

1. 扩展执行记录：执行尝试标识、操作类型（普通发送/主动刷新）、上下文快照关联、回答版本关联、实际 Knowledge RAG 调用标记、六类状态。
2. 初次插入与最终更新分开记录结果；最终更新失败不写成成功。
3. 旧日志读取带 schema 版本标识；旧记录缺字段显示未知。

**不在本 STEP 范围内**：步骤/调用级明细的具体内容（由 Q15、Q16、Q19 各自写入）；管理页展示（A07）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 一次正常执行 | 同一 `EXEC_ID` 上六类状态字段各自有值，不是合并成一个 success | AT-32 |
| 异常 | insert 成功、最终 update 失败 | 同一 `EXEC_ID`：Runtime 保存为失败或局部；消息保存保持该消息自己的结果 | AT-15 |
| 边界 | 检查 pass、业务部分有依据、消息保存失败 | 同一 `EXEC_ID` 上这三项分别为 pass、部分有依据、失败 | AT-32 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q03] 取消 40 上限、列表分页、用户删除改为账号级隐藏

**阶段状态**：`draft`

**目标**：会话数量不再触发淘汰；用户删除只隐藏，跨端不可见且数据保留。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | RQ-05 | 取消 40 上限与自动淘汰；分页/按需加载 | `PRD` S01 §6.18 |
| 需求 | RQ-19 | 用户隐藏后跨端不可见、不可自行恢复，数据库保留 | `PRD` S01 §6.10 |
| 验收 | AT-12 | 第 41 个会话正常创建，原会话不被删 | `PRD` |
| 验收 | C26（列表/跨端部分） | 用户删除后换设备也不可见 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q01 | 可见性字段 | 会话记录能表达「用户侧已隐藏」 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `conv_store.py` `MAX_CONVS` 及淘汰分支 | `existing` | `REPO_BASELINE` | SRC-CONV / `MAX_CONVS = 40` | 删除淘汰逻辑 |
| `DELETE /api/kb/conversations/{conv_id}` | `existing` | `REPO_BASELINE` | SRC-API / 该路由 | 改为隐藏 |
| `GET /api/kb/conversations` | `existing` | `REPO_BASELINE` | SRC-API / 该路由 | 加分页、过滤已隐藏 |
| `qa.js` 会话列表加载 | `existing` | `REPO_BASELINE` | SRC-QAJS / `saveCloud` 附近 | 适配分页 |
| `qa.js` `MAX_CONVS` | `existing` | `REPO_BASELINE` | SRC-QAJS / 第 8 行常量；第 266 行 `persist()` 仅在未登录时淘汰 | 去掉这处上限，避免与服务端并存 |
| 分页参数名、页大小 | `planned` | `PLANNED` | 不适用 | 按已核实项目约定确定 |

**输入**：Q01 可见性字段。

**输出**：无上限会话；分页列表；隐藏语义的删除接口。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 用户删除 | 账号级移除/隐藏，不物理删除 | S01 §6.10 |
| 字段名 | 不限定 `hidden_at` 等具体名 | S01 §6.10 |

**开发任务**：

1. 移除 `conv_store.py` 的 `MAX_CONVS` 限制与满额淘汰分支；更新模块头注释。
2. 去掉 `qa.js` 的 `MAX_CONVS` 以及 `persist()` 里未登录分支的淘汰。统一登录后这条路径通常走不到，但不能留第二处 40 上限。
3. 列表接口加分页并过滤已隐藏会话；前端按页加载。
4. DELETE 改为设置隐藏状态；被隐藏会话的 GET/PUT 对本人返回不可访问。
5. 更新依赖 40 上限的现有测试。

**不在本 STEP 范围内**：超管物理删除（A06）；索引/缓存失效（Q15）；清空（Q04）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 已有一组会话，其 `CONV_SET` 记为 S，再创建第 41 个 | 创建成功；S 仍是当前列表能翻到的会话 id 子集，没有 id 被删掉 | AT-12 |
| 异常 | 用户删除某个 `conversation_id` 后在另一设备登录 | 该 id 不在用户列表中，直接 GET 也不可访问 | C26 |
| 边界 | 翻到最后一页 | 各页 `CONV_SET` 的并集等于全部未隐藏会话，不因页大小截掉旧 id | AT-12 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q04] 服务端清空边界

**阶段状态**：`provisional`（门：G-E06 竞态部分）

**目标**：「清空当前」在服务端记录可验证边界，此后 L1、Memory、旧版本、承接和缓存都只使用边界之后的内容。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | RQ-04 | 清空显示并切断此前语境；保留窗口和数据库记录 | `PRD` S01 §6.15 |
| 验收 | AT-11 | 清空后问旧指代：旧语境不再用于 L1/Memory/Runtime 承接或缓存 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q01 | 服务端消息顺序 | 能按顺序定位边界 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `qa.js` `clearCurrent` | `existing` | `REPO_BASELINE` | SRC-QAJS / `clearCurrent` | 现只清前端数组，改为调用服务端 |
| 清空接口 | `planned` | `PLANNED` | 不适用 | 路径按已核实项目约定 |

**输入**：Q01 消息顺序。

**输出**：清空边界记录（支持多次清空）；读取历史的统一边界过滤。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 清空后 | 旧待澄清任务、已恢复工作集不自动续接；重提同一业务词不解除边界；知识查询权限不受影响 | S01 §6.15 |

**开发任务**：

1. 新增清空接口，记录边界（保留每次清空的分界，供 A05 展示）。
2. 提供统一的「当前有效范围」读取函数，后续 Q05、Q15、Q20 必须经它读取。
3. 前端 `clearCurrent` 改为调用服务端并刷新显示。

**不在本 STEP 范围内**：管理员查看清空前内容（A05）；与在途任务的竞态收敛（G-E06）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 讨论 VIP 后清空，再问「那退款呢」 | 不借用 VIP 语境，进入澄清 | AT-11 |
| 异常 | 另一设备打开同一会话 | 也只看到边界之后的内容 | AT-11 |
| 边界 | 清空后问一个完整业务问题 | 正常查询知识库 | AT-11 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q05] 服务端组装 L1

**阶段状态**：`draft`

**目标**：L1 由服务端从消息事实源组装，最多 10 个完整逻辑回合、最多 5000 tokens，整回合保留或淘汰；不采信客户端 history。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | RQ-18 | 10 完整回合/5000 tokens 双上限，整回合淘汰 | `PRD` S01 §6.5～§6.7 |
| 验收 | AT-13 | 客户端伪造 history/last_chunks 不被采信 | `PRD` |
| 验收 | AT-38 | 完整澄清可组成 L1 回合；中断片段不算 | `PRD` |
| 验收 | C38（L1 部分） | 单回合超预算时 L1 不截半轮 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q01 | 消息与完整性状态 | 能区分完整回复与中断片段 |
| Q04 | 有效范围读取函数 | 边界外消息不可读 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `main.py` `_ask_events` 读取请求体 `history`/`last_chunks` | `existing` | `REPO_BASELINE` | SRC-API / `_ask_events` | 改为服务端组装 |
| `qa.js` `send` 只传最近 5 条 User | `existing` | `REPO_BASELINE` | SRC-QAJS / `send` | 适配 |
| `config_store.py` `history_turns` | `existing` | `REPO_BASELINE` | SRC-CFG / `_defaults` | 不再用它扩大 L1 |
| token 计数方式 | `planned` | `PLANNED` | 不适用 | 按已核实项目约定 |

**输入**：Q01、Q04。

**输出**：L1 组装函数，返回完整回合、实际窗口、token 用量、未载入原因；当前 User 单独传入。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| MAX_TURNS / MAX_HISTORY_TOKENS | 10 / 5000 | S01 §6.6 |
| 超长最新回合 | 整轮不进 L1，暴露「因预算未载入」，不宣称没有历史 | S01 §6.14 |
| 版本选择 | 普通请求在快照建立时确定各回合采用版本 | S01 §6.5 |

**开发任务**：

1. 实现 L1 组装：按逻辑回合，从最新向前累计，达到任一上限停止。
2. ask 入口不再把客户端 history/last_chunks 作为可信输入。
3. 当前 User 不放入「已完成历史」。
4. 返回未载入原因供 Runtime 记录（Q02）。

**不在本 STEP 范围内**：Memory 片段读取（Q15）；刷新时的原快照（Q08）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 12 个短回合 | L1 取最近 10 个完整回合 | RQ-18 |
| 异常 | 请求体伪造 history | 模型输入仍来自服务端 | AT-13 |
| 边界 | 最新回合单独超 5000 | 整轮不载入并记录原因，不截半轮 | C38 |
| 边界 | 上一轮是完整澄清 / 上一轮是中断片段 | 前者进入 L1，后者不当完整回合 | AT-38 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q06] 旧云端历史迁移

**阶段状态**：`provisional`（门：G-E04）

**目标**：把可可靠恢复、用户仍可访问的旧云端消息迁入新事实源；缺失不补造。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | RQ-12（迁移部分） | 核验旧 payload 与 qa_rounds 的对应、去重、缺失后迁移 | `PRD` S01 §6.17 |
| 验收 | 无独立 ID | 覆盖状态由 Q14 的 C29/AT-21 验收；管理侧展示由 A14 的 T45 验收 | — |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q01 | 新消息存储 | 可写入迁移消息并带来源标记 |
| Q04 | 清空边界 | 迁移不重置边界 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `kb_conversations.payload` | `existing` | `REPO_BASELINE` | SRC-SQL / `kb_conversations` | 迁移来源 |
| `qa_rounds` | `existing` | `REPO_BASELINE` | SRC-SQL / `qa_rounds` | 对照来源 |
| 迁移脚本/作业 | `planned` | `PLANNED` | 不适用 | G-E04 |

**输入**：旧 payload、旧日志。

**输出**：迁移后的消息（带迁移来源与完整性标记）；无法可靠恢复的记录清单。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 不导入 | 浏览器 localStorage 旧历史；已隐藏/已删除/无法可靠关联的内容 | S01 §6.17；ADM §18.3 |
| 不补造 | 原话、时间、回合关系、旧回答版本 | S01 §6.17 |

**开发任务**：

1. 核对 payload 与 qa_rounds 的对应关系、去重规则（按 G-E04 定稿）。
2. 写入可靠消息并标来源；不完整记录保留限制标记，不伪装成完整 L1 回合。
3. 旧 UI 仅清数组无法证明服务端边界时，按 G-E04 的限制处理，不伪造切点。

**不在本 STEP 范围内**：Memory 索引回填（Q14）；管理侧覆盖展示（A14）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 可对应的旧会话 | 迁移后可在 L1/详情中读取 | RQ-12 |
| 异常 | payload 与日志对不上 | 不合并成确定对话，标限制 | RQ-12 |
| 边界 | 已隐藏会话 | 迁移后仍对用户不可见 | RQ-12 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q07] 同会话互斥与请求幂等

**阶段状态**：`provisional`（门：G-E06 幂等键）

**目标**：同一会话同一时间只接受一个普通发送或刷新；网络重试不重复执行；旧响应不覆盖其他执行。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | RQ-07 | 同会话服务端互斥；发送/刷新共用；忙时保留草稿，不排队 | `PRD` S01 §6.12、§20.4 |
| 验收 | AT-14 | 两设备同时发送：只接受一个，另一方保留草稿，旧响应不覆盖 | `PRD` |
| 验收 | C39 | 请求重试、跨设备同时发送、旧流晚返回 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q01 | 会话/消息标识 | — |
| Q02 | 执行尝试标识 | 旧响应能按执行识别 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `main.py` `POST /api/kb/ask` | `existing` | `REPO_BASELINE` | SRC-API / `/api/kb/ask` | 加互斥与幂等 |
| `qa.js` `send`、`regen` | `existing` | `REPO_BASELINE` | SRC-QAJS / `send`、`regen` | 忙碌提示、保留草稿 |
| 互斥机制与幂等键 | `planned` | `PLANNED` | 不适用 | G-E06 |

**输入**：Q01、Q02。

**输出**：会话级执行权；幂等关联；忙碌状态响应。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 互斥范围 | 仅同一 Conversation，不锁整个账号 | S01 §6.12 |
| 忙碌 vs 保存阻塞 | 两种不同状态（保存阻塞见 Q09） | S01 §20.4 第 5 条 |

**开发任务**：

1. ask 入口取得会话执行权，执行结束释放。
2. 同一请求的网络重试沿用幂等关联，不新建执行。
3. 忙碌时返回可识别状态；前端保留输入框内容。
4. 迟到的旧响应不得写入其他执行。

**不在本 STEP 范围内**：保存阻塞（Q09）；刷新版本（Q08）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 单设备发送 | 正常执行 | RQ-07 |
| 异常 | 两设备同时发送 | 只接受一个；另一方提示忙碌且草稿保留 | AT-14 |
| 边界 | 同一请求网络重传 | 不重跑 | C39 |
| 边界 | 另一个会话同时发送 | 不受影响 | RQ-07 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q08] 主动刷新：新执行、新版本、原快照

**阶段状态**：`provisional`（门：G-E06 快照序列化）

**目标**：刷新在同一逻辑回合下新增执行和回答版本，沿用原问题快照；新版本成功保存并采用后才替换默认版本。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | RQ-06 | 新增执行与版本；默认最新成功采用版本；旧版可找回，不自动设回默认 | `PRD` S01 §6.16 |
| 验收 | AT-09 | 刷新无新 User 气泡，逻辑回合数不变 | `PRD` |
| 验收 | AT-10 | 刷新非最后一条：沿用原快照，不读之后对话 | `PRD` |
| 验收 | AT-34 | 隔日刷新含「昨天」：沿用原时间基准 | `PRD` |
| 验收 | AT-37 | 多次刷新时按具体执行/版本定位 Runtime | `PRD` |
| 验收 | AT-28（版本部分） | 新答案保存失败时旧默认答案及反馈保留 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q01 | 回答版本字段 | — |
| Q02 | 执行尝试与操作类型 | — |
| Q05 | L1 组装 | 可按指定快照组装 |
| Q07 | 互斥 | 刷新也受互斥 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `qa.js` `regen` | `existing` | `REPO_BASELINE` | SRC-QAJS / `regen` | 现为原位替换并新 round_id，需改 |
| 上下文快照 | `planned` | `PLANNED` | 不适用 | G-E06 |

**输入**：原问题的消息与快照。

**输出**：刷新执行；新版本；采用切换规则；前端版本切换查看。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 刷新配置 | 刷新使用被接受时的有效配置，但历史快照与时间解释沿用原问题 | ADM-C07；ADM §16.3 |
| 内部证据修正 | 不是刷新，不新建版本 | S01 §6.16 |

**开发任务**：

1. 刷新请求关联原 User，不写新 User。
2. 按原快照组装 L1，时间解释沿用原基准；原基准缺失时标限制。
3. 新版本保存成功且通过交付检查后才更新当前采用版本。
4. 后续消息保留其依赖的旧版本引用。

**不在本 STEP 范围内**：用户在对话中要求找回旧版本（Q20）；反馈绑定（Q21）；保存失败补写（Q09）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 刷新最后一条 | 原 `MSG_ID` 与 `ROUND_ID` 不变；不新增 User 消息；新增一个 `VER_ID` 和一个 `EXEC_ID` | AT-09 |
| 异常 | 新版本保存失败 | 当前采用的 `VER_ID` 及其 `FEED` 与刷新前相同 | AT-28 |
| 边界 | 刷新中间一条 | 新执行的历史快照消息 id 集合等于原问题当时的快照，不包含其后的 `MSG_ID` | AT-10 |
| 边界 | 隔天刷新含「昨天」的问题 | 时间解释区间与原问题快照相同，不改成刷新当天 | AT-34 |
| 边界 | 三次刷新后续接其中一次 | 读到的 Runtime 的 `EXEC_ID` 等于被指定的那次，不是该 `ROUND_ID` 的最后一条 | AT-37 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q09] Assistant 保存失败：同文补写与保存阻塞

**阶段状态**：`provisional`（门：G-E06 次数与承载）

**目标**：最终 Assistant 未保存时有限补写同一结果；补写仍失败则结束执行、会话进入保存阻塞，直到重试保存成功。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | RQ-08 | Assistant 未保存时有限补写同一结果，失败不继续生成，阻止该会话新发送/刷新 | `PRD` S01 §20.4 第 4～5 条 |
| 验收 | C40 | 回答已生成但保存失败 | `PRD` |
| 验收 | AT-28（保存部分） | 补写同一结果，成功后才切换；另一设备不能抢发 | `PRD` |
| 验收 | AT-40（补写部分） | 同一结果补写只更新保存状态，不伪造新生成 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q01 | 消息保存状态 | — |
| Q07 | 会话执行权 | 保存阻塞与忙碌可区分 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `main.py` `finish` | `existing` | `REPO_BASELINE` | SRC-API / `_ask_events.finish` | 保存与补写点 |
| `qa.js` | `existing` | `REPO_BASELINE` | SRC-QAJS / 消息渲染 | 「未保存/重试保存」提示 |
| 补写次数、承载 | `planned` | `PLANNED` | 不适用 | G-E06 |

**输入**：已形成的最终结果。

**输出**：补写逻辑；保存阻塞状态；用户侧「重试保存」入口。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 补写 | 只写同一份结果，不重新生成、不重算业务结果 | S01 §20.4；ADM §17.3 |
| 阻塞范围 | 仅该会话；其他会话可用；可查看/复制已收到内容 | S01 §20.4 第 5 条 |

**开发任务**：

1. 保存失败后按 G-E06 的次数自动补写同一内容。
2. 仍失败：执行结束，消息标「保存失败」，会话进入保存阻塞。
3. 用户侧「重试保存」成功后解除阻塞。
4. 阻塞期间拒绝该会话新发送/刷新。

**不在本 STEP 范围内**：后台强制解除阻塞（ADM 非目标）；Runtime 单独失败（Q02、G-E06）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 第一次补写成功 | 保存状态更新，执行不变 | AT-40 |
| 异常 | 补写全部失败 | 显示保存失败与重试入口，不显示生成中 | C40 |
| 边界 | 阻塞期间另一设备发送 | 被拒绝 | AT-28 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q10] 断线继续、统一终态、SSE 与草稿展示

**阶段状态**：`provisional`（门：G-E05 事件协议；草稿展示已由 UD-01 决定）

**目标**：客户端断线不终止已接受任务；重连只读原请求状态；终态输出分别表达六类状态；流式草稿按 UD-01 标注与替换。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | RQ-09 | 客户端断线不终止，在原预算内完成并保存；重连只读，不重复生成 | `PRD` S01 §20.6 |
| 需求 | CSTR-Q05 | 终态分别表达，不用一个 success | `PRD` S01 §20.6 |
| 需求 | UD-01 | 流式显示为「草稿·核对中」，通过转正式，不通过替换为修正稿或失败说明 | `USER_DECISION` |
| 验收 | AT-16 | EOF 不被当成功/中断；重连读原任务；前端按最终状态结束 pending | `PRD` |
| 验收 | AT-29 | 关闭页面后服务端正常完成；重开只读结果 | `PRD` |
| 验收 | C41 | 服务端真失败时半段不算完整回答 | `PRD` |
| 验收 | AT-40（晚到部分） | 超时结束后晚到结果不改业务终态 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q02 | 六类状态 | — |
| Q07 | 执行权与幂等 | 重连不新建执行 |
| Q09 | 保存阻塞 | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `main.py` 生成时检测客户端断开走 interrupted | `existing` | `REPO_BASELINE`（S01 §21.1 描述，本轮已定位 `_ask_events`） | SRC-API / `_ask_events` | 改为不因断线终止 |
| 查询请求状态的接口 | `planned` | `PLANNED` | 不适用 | G-E05 |
| SSE 事件名 | `planned` | `PLANNED` | 不适用 | G-E05 |

**输入**：执行关联。

**输出**：后台继续执行；状态查询；新终态事件；前端草稿标注与替换。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 草稿展示 | 知识回答流式时标「草稿·核对中」；检查通过→转正式；不通过→替换为修正稿（复查通过时）或失败说明 | UD-01 |
| 断线继续不等于 | 服务崩溃后任意节点续跑；忽略权限变化/清空/预算截止 | S01 §20.6 |

**开发任务**：

1. 去掉「客户端断开即 interrupted」，任务在原预算内继续并保存。
2. 提供按执行查询状态与最终结果的接口；前端重连后查询，不重发 ask。
3. 终态事件携带六类状态、最终文本与引用；旧前端不认识的状态有兼容处理，不永久 pending。
4. 前端：流式正文标「草稿·核对中」；收到检查结论后按 UD-01 转正式或替换。
5. 超时结束后到达的结果不改写终态。

**不在本 STEP 范围内**：检查与修正本身（Q19）；完整断点补流协议（S01 未要求）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 生成中关闭页面，稍后重开 | 看到完成且已保存的结果，未再次调用模型 | AT-29 |
| 异常 | SSE 收到 EOF 无 done | 前端查询服务端状态，不直接判成功或中断 | AT-16 |
| 异常 | 服务端生成真失败 | 半段不算完整回答，不进 L1 | C41 |
| 边界 | 超时后模型结果晚到 | 终态不变 | AT-40 |
| 边界 | 检查不通过 | 草稿被替换，不保留为正式答案 | UD-01 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q11] Router v3

**阶段状态**：`provisional`（门：G-E01 输出 Schema、G-E03 低置信度处理）

**目标**：Router 输出六类 route、requires_history、confidence、reason，服务端做结构校验；非法输出按分类执行异常处理。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | RQ-01 | 新增 conversation_task；context_dependent 不再是主 Route | `PRD` S01 §7.2 |
| 验收 | C01 | 同窗讨论过 VIP，本轮问 YallaPay → knowledge_query，requires_history=false | `PRD` |
| 验收 | C05 | 「好的，那退款怎么算？」不是 ack | `PRD` |
| 验收 | C09 | Router 不认识业务词 X，仍进知识查询 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q02 | Runtime 记录原始 route | — |
| Q05 | L1 | Router 输入含有限 L1 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| Router 模块与 Prompt | `planned` | `PLANNED` | 不适用 | 新增；Prompt 以 S01 §10 职责模板为参考 |
| 旧 `context_dependent` 日志 | `unverified` | `UNVERIFIED` | 不适用 | 旧分类保留，不批量改写（S01 §21.2） |

**输入**：当前输入、L1、服务范围、必要承接线索。

**输出**：Router 调用与校验；原始 route 写入 Runtime。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| route | knowledge_query、conversation_task、ack、smalltalk、out_of_scope、unclear | S01 §7.2 |
| reason | 仅日志，代码不解析 | S01 §9.1 |
| 非法 JSON | 分类执行异常，不是 unclear | S01 §9.2 |
| 阈值 | 不预置 0.7 | S01 §9.2；G-E03 |

**开发任务**：

1. 实现 Router 调用，输入 L1 与当前输入，输出按正式 Schema 校验。
2. 非法输出走执行异常通道。
3. 原始 route 写入 Runtime，后续恢复不改写。

**不在本 STEP 范围内**：各分支执行（Q12、Q13、Q20）；任务拆解（Q13）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | C01 输入 | knowledge_query / false | C01 |
| 正常 | 「好的，那退款怎么算？」 | 非 ack | C05 |
| 边界 | 不认识的功能名 X | 仍为 knowledge_query | C09 |
| 异常 | Router 返回非法 JSON | 执行异常，不当 unclear | RQ-01 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q12] 非知识分支与按分支实际依赖

**阶段状态**：`draft`

**目标**：ack、out_of_scope 从各自话术池取句；smalltalk 简短回应；unclear 生成一句澄清；各分支只检查自身依赖，知识索引故障不挡这些分支。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | RQ-01 | 各 route 分支执行 | `PRD` S01 §7.5～§7.9、§14 |
| 需求 | RQ-16 | 能力 A，越界不回答 | `PRD` S01 §7.7 |
| 需求 | CSTR-Q06 | 按分支实际依赖检查 | `PRD` S01 §14 |
| 验收 | C04 | ack：后台随机一句，之后不调 LLM/RAG | `PRD` |
| 验收 | C06 | smalltalk：简短、不追问、引导回 Hayyo | `PRD` |
| 验收 | C07、C08 | 领域外 / 设计新规则 → out_of_scope，不检索 | `PRD` |
| 验收 | C12 | 空历史「那个呢？」→ 具体澄清 | `PRD` |
| 验收 | AT-23 | Qdrant 不可用时 ack/纯回看仍可用 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q11 | route 输出 | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `main.py` `_ask_events` 先检查知识依赖 | `existing` | `REPO_BASELINE` | SRC-API / `_ask_events` | 改为按分支 |
| `ack_reply_pool`、`out_of_scope_reply_pool` | `planned` | `PLANNED` | 不适用 | 配置项；后台管理见 A09 |

**输入**：route、L1。

**输出**：四个分支的执行；分支级依赖检查。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 两个话术池 | 独立，不互相借用 | S01 §7.5、§7.7；ADM §8.6 |
| 澄清输出 | 合法 JSON，唯一字段 clarification | S01 §7.9 |

**开发任务**：

1. ack / out_of_scope：从对应池随机一句，不再调用 LLM/RAG。
2. smalltalk：Smalltalk LLM，1～2 句，不调用 Memory/Knowledge。
3. unclear：Clarification Generator 按 S01 §7.9 职责模板。
4. 依赖检查按分支进行。

**不在本 STEP 范围内**：混合任务拆分（Q13）；话术池的后台管理（A09）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 「好的，谢谢」 | 池内一句，无后续模型调用 | C04 |
| 正常 | 「今天好累」 | 简短回应并引导回 Hayyo | C06 |
| 正常 | 「法国首都是哪里」/「设计新保级规则」 | 越界话术，不检索 | C07、C08 |
| 边界 | 空历史「那个呢」 | 一句具体澄清 | C12 |
| 异常 | Qdrant 不可用时发 ack | 正常回复 | AT-23 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q13] 任务准备、部分交付、混合越界、跨轮承接

**阶段状态**：`provisional`（门：G-E01 任务/缺口结构）

**目标**：knowledge_query 与 conversation_task 进入执行前，由最小任务准备产出 task_goal/task_mode、子任务、排除项与依赖；独立任务可部分交付；越界项明确不执行；澄清后的补充能承接原任务。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | RQ-02 | 独立多任务可部分交付，明示未完成原因 | `PRD` S01 §8.3 |
| 需求 | RQ-03 | 可拆出的范围内任务执行，越界部分不执行 | `PRD` S01 §8.3 |
| 验收 | C36 | 只找到 A 却要 A/B 对照 → 不冒充完成 | `PRD` |
| 验收 | C37 | 多项独立任务部分完成 → 不宣称全部完成 | `PRD` |
| 验收 | AT-01 | 独立问题的表格/对照约束实际送达 Generate | `PRD` |
| 验收 | AT-04 | 缺用户从未提供的条件 → 不伪装历史缺口 | `PRD` |
| 验收 | AT-08 | 澄清回合超出 L1，用户答「第二个」→ 从承接关联恢复或明确无法恢复 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q11 | route 与 requires_history | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| 任务准备模块 | `planned` | `PLANNED` | 不适用 | 可复用模型调用，不强制新 LLM |
| 承接关联（Runtime） | `planned` | `PLANNED` | 不适用 | 复用 Q02 |

**输入**：原句、L1、route、必要承接线索。

**输出**：任务集合（目标、模式、范围、约束、依赖、排除项）；逐任务检查结果；承接信息。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 逐任务检查结果 | 可执行 / 缺历史有线索 / 需澄清 / 多候选 / 依赖未就绪 / 越界 / 知识依据不足 / 异常 | S01 §8.2 |
| 承接最小关联 | 原任务原句/回合、澄清消息、候选标识、已解决来源、未补缺口 | S01 §18.8 |

**开发任务**：

1. 实现任务准备，requires_history=false 时也产出 task_goal/task_mode 与约束。
2. 逐任务条件检查，按 S01 §8.2 分流。
3. 汇总各任务完成/未完成/不执行状态，不把部分完成写成全部完成。
4. 澄清/部分交付后本轮结束；下一轮按 §18.8 恢复承接，不重做已交付项。

**不在本 STEP 范围内**：历史恢复循环（Q16）；Rewrite（Q17）；非知识执行（Q20）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 独立对照表格请求 | 约束传到下游 | AT-01 |
| 异常 | 只恢复出 A，要 A/B 对照 | 不交付伪对照，说明缺 B | C36 |
| 边界 | 三项独立任务，一项缺语境 | 交付两项，说明第三项原因 | C37 |
| 边界 | 缺用户必须指定的条件 | 澄清，不搜历史 | AT-04 |
| 边界 | 澄清已滚出 L1，用户答「第二个」 | 恢复原任务或说明无法恢复 | AT-08 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q14] Conversation Memory 派生索引

**阶段状态**：`provisional`（门：G-E04）

**目标**：从消息事实源建立可重建的检索索引，能观测积压、失败、覆盖与空洞；隐藏/清空/删除时同步失效。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | RQ-12（索引部分） | 旧历史回填；未覆盖与正常未命中区分 | `PRD` S01 §6.17、§19.7 |
| 需求 | RQ-20 | 记忆工具化的索引基础 | `PRD` S01 §19.7 |
| 验收 | C29 | 索引只覆盖部分历史时返回覆盖不完整，不说用户从未讨论 | `PRD` |
| 验收 | AT-21 | 中间有空洞但最新进度已更新 → 覆盖不冒报完整 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q01 | 消息事实源 | — |
| Q03 | 隐藏状态 | 隐藏后索引结果不可交付 |
| Q04 | 清空边界 | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `site/kb-api/app/indexer.py` | `existing` | `REPO_BASELINE` | SRC-IDX / 模块 | 知识索引；只借鉴基础设施，不混为同一事实源 |
| Memory 索引引擎、collection | `unverified` | `UNVERIFIED` | 不适用 | G-E04 |

**输入**：已保存消息与版本。

**输出**：Memory 索引写入；覆盖状态（按会话、范围、代次）；回填与重试作业。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 不索引 | 未完成或未保存的 Assistant 内容 | S01 §19.7 |
| 覆盖状态 | 已接入/未接入、正常/部分/落后/失败/未知 | ADM §10.4 |

**开发任务**：

1. 按 G-E04 选定引擎，与知识索引分开。
2. 消息保存后异步更新索引，记录积压与失败。
3. 覆盖状态可识别中间空洞，不只看最新时间。
4. 回填作业按 Q06 迁移结果执行，不重置清空/隐藏边界。
5. 隐藏/清空/删除触发失效。

**不在本 STEP 范围内**：search/read 工具（Q15）；管理侧展示（A14）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 新消息保存后 | 索引更新，覆盖正常 | RQ-12 |
| 异常 | 部分历史未索引 | 覆盖显示不完整 | C29 |
| 边界 | 中间一段失败、最新已更新 | 仍显示有空洞 | AT-21 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q15] Memory Tool search/read

**阶段状态**：`provisional`（门：G-E03、G-E08）

**目标**：Memory Tool 只在本人当前有效 Conversation 内检索和读取原文，范围由服务端绑定；精确时间严格定位后允许必要补读；所有结果回源复核。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | RQ-13 | 目标时间严格命中后允许必要补读并标真实范围 | `PRD` S01 §19.5 |
| 需求 | RQ-17 | 只访问当前 Conversation | `PRD` S01 §19.2 |
| 需求 | RQ-20 | search/read 两个操作与返回合同 | `PRD` S01 §19.1、§19.4 |
| 验收 | C14、C15 | 已知 round_id 直接 read；Top 1 不足时补读下一回合 | `PRD` |
| 验收 | C22 | 本轮 User 不作为旧历史证据 | `PRD` |
| 验收 | C24、C25 | 更正识别；历史中的指令只当文本 | `PRD` |
| 验收 | C26（索引/缓存部分）、C27（回源部分） | 用户删除/管理员删除后残留命中不返回 | `PRD` |
| 验收 | C28 | 伪造他人 message_id/conversation_id 被拒 | `PRD` |
| 验收 | C30、C31 | 超时不伪装零命中；精确时间未命中不扩大 | `PRD` |
| 验收 | C38（片段部分） | 片段明确标范围，不伪称全文 | `PRD` |
| 验收 | AT-19 | 23:59 问、00:02 确认 → 命中后必要补读并标实际时间 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q14 | Memory 索引 | 可检索 |
| Q05 | L1 与当前 User 分离 | 当前 User 不在历史集 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| Memory Tool 模块 | `planned` | `PLANNED` | 不适用 | 新增 |
| 时区来源 | `unverified` | `UNVERIFIED` | 不适用 | G-E08 |

**输入**：模型提出的 operation、gap_id、查询/时间线索/来源标识；服务端绑定的账号、会话、清空边界、快照、预算。

**输出**：逐 gap/调用的状态、候选、回源原文、实际范围、覆盖、完整性、续读入口、用量。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 不能放宽 | 账号/权限/可见性、当前 conversation_id、本轮快照 | S01 §19.2 |
| 模糊时间 | 可按规则有限扩大并记录 | S01 §19.2 |
| 重排分数 | 不称为「就是用户所指的概率」 | S01 §19.4 |

**开发任务**：

1. search：服务端过滤 → 关键词+语义召回 → 融合去重 → 重排 → 回源读取。
2. read：校验来源标识后直接读取，支持相邻回合补读。
3. 回源时复核可见性、清空边界、删除状态；失效命中剔除并触发清理。
4. 精确时间：定位严格；补读区间单独标出。
5. 返回逐项状态，批量部分失败不被顶层 success 抹平。

**不在本 STEP 范围内**：循环控制与预算（Q16）；工具调用 Knowledge（禁止）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 已知准确 round_id | 直接 read | C14 |
| 正常 | Top 1 只有问题 | 补读下一回合 | C15 |
| 异常 | 伪造他人会话 ID | 拒绝 | C28 |
| 异常 | Memory 超时 | 返回服务异常，不当零命中 | C30 |
| 异常 | 会话已隐藏/已被删除但索引残留 | 不返回内容 | C26、C27 |
| 边界 | 精确日期未命中 | 不扩到其他日期 | C31 |
| 边界 | 跨午夜确认 | 补读并标真实时间 | AT-19 |
| 边界 | 当前 User 已落库 | 不进入证据集 | C22 |
| 边界 | 用户先说 A 后更正为 B | 识别更正关系 | C24 |
| 边界 | 历史中含「忽略权限」指令 | 当文本，不执行 | C25 |
| 边界 | 超长回合 | 片段标范围 | C38 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q16] 追溯工作流受控循环与全局预算

**阶段状态**：`provisional`（门：G-E02）

**目标**：按缺口受控调用 Memory Tool，独立缺口可并行、依赖串行，所有调用共享本轮预算并在派发前预占；足够、无进展、歧义、异常或超限时停止。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | RQ-20 | L1 不足时按缺口恢复，共享预算，足够或无进展停止 | `PRD` S01 §18 |
| 验收 | C02（不调 Memory 部分） | L1 足够时不调用 Memory | `PRD` |
| 验收 | C13 | L1 没有但 MySQL 有 → 追溯而非 unclear | `PRD` |
| 验收 | C16～C21 | 一次找齐即停；只补缺失项；独立并行；依赖串行；无进展停止；歧义澄清 | `PRD` |
| 验收 | C42 | Memory/Rewrite/Knowledge 多次往返共用同一预算 | `PRD` |
| 验收 | AT-05 | 循环 LLM 返回非法动作 → 校验后终结 | `PRD` |
| 验收 | AT-06 | 批量 G1 成功 G2 超时 → 逐项保留 | `PRD` |
| 验收 | AT-07 | A 被更正后重新核验依赖 A 的 B | `PRD` |
| 验收 | AT-20 | 剩一次额度时两个并行查询 → 派发前限制 | `PRD` |
| 验收 | AT-03（恢复部分） | 接到 needs_context 缺口后，在同一执行、同一预算内进入恢复 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q13 | 任务与缺口 | — |
| Q15 | Memory Tool | — |
| Q02 | Runtime 记录调用与预算 | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| 工作流与 Orchestrator | `planned` | `PLANNED` | 不适用 | Prompt 以 S01 §18.7 职责模板为参考 |
| 预算数值 | `unverified` | `UNVERIFIED` | 不适用 | G-E02；未配置不启用循环 |

**输入**：任务、gap、L1、Memory 返回。

**输出**：逐步控制动作；工作集；stop_reason；预算用量。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 出口 | ready、need_more、needs_clarification、not_found、no_progress、budget_exceeded、tool_error、access_changed | S01 §18.6 |
| 预算 | 派发前预占，返回后结算；模型无权修改 | S01§18.4、§20.5 |

**开发任务**：

1. 实现逐步控制：模型给动作，代码校验（未知动作、空查询、无效来源、动作与终态矛盾都不执行）。
2. 独立 gap 批量/并行，依赖 gap 串行。
3. 派发前预占预算；不重跑 Router、不新建轮次逃避上限。
4. 更正上游定位时复核依赖项。
5. 预算未配置时循环不启用，只用 L1。

**不在本 STEP 范围内**：needs_context 由谁产生（Q17）；最终生成（Q18）。本 STEP 负责接到缺口之后的恢复。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | L1 足够 | 不调用 Memory | C02 |
| 正常 | 历史在 MySQL 不在 L1 | 进入追溯 | C13 |
| 正常 | 一次找齐 A、B | 结束 | C16 |
| 边界 | 只找到 A | 只补 B | C17 |
| 边界 | A、B 独立 / B 依赖 A | 并行 / 串行 | C18、C19 |
| 异常 | 连续无新信息 | no_progress 停止 | C20 |
| 异常 | 两个合理候选 | 澄清 | C21 |
| 异常 | 非法动作 | 终结，不盲调 | AT-05 |
| 异常 | G1 成功 G2 超时 | 同一 `EXEC_ID` 上 G1、G2 两个 gap id 的状态分别为成功与超时 | AT-06 |
| 边界 | A 被更正 | B 重新核验 | AT-07 |
| 边界 | 剩一次额度 | 同一 `EXEC_ID` 上只派发一个调用，另一个不启动 | AT-20 |
| 边界 | 多次往返 | 同一 `EXEC_ID` 的预算计数连续累计，不归零、不新建执行 | C42 |
| 边界 | 夹具注入 needs_context 缺口，且该执行预算计数已大于 0 | 同一 `EXEC_ID` 上出现恢复调用；预算计数不归零。联调时缺口来自 Q17，本步不依赖 Q17 才能单测 | AT-03 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q17] 唯一 Rewriter v3 与旧 Pipeline 适配

**阶段状态**：`provisional`（门：G-E01、G-E05 字段映射）

**目标**：Knowledge RAG 内只有一个 Rewrite 入口，输出 ready/needs_context、standalone_query、response_constraint、missing_context，并适配旧 Pipeline 所需的分路字段。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | CSTR-Q03 | 唯一 Rewrite；保留 named_feature_ids、same_topic 语义与保底 | `PRD` S01 §11.3、§12.3 |
| 验收 | C03 | 恢复指代后只查该场景，不拼入无关主题 | `PRD` |
| 验收 | C33 | needs_context 或空 Query 不检索空串 | `PRD` |
| 验收 | AT-02 | 新 JSON 接入旧 Pipeline，多功能分路与保底不丢 | `PRD` |
| 验收 | AT-03（交接部分） | 发现历史指代时返回 needs_context；不把预算计数归零；不因旧执行表拒绝。不在本步调用 Memory | `PRD` |
| 验收 | AT-35 | Rewriter 未检索就说知识库无规则 → 不采信 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q13 | 任务目标与约束 | — |

本 STEP 只把缺口交回编排器，并保持同一 `EXEC_ID` 的预算计数。实际恢复由 Q16 完成。Q16 未接入时，该缺口按澄清或「历史恢复未接入」结束，不得假装已经恢复。

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `pipeline.py` `parse_rewrite`、`build_rewrite_user` | `existing` | `REPO_BASELINE` | SRC-PIPE / 两函数 | 旧解析与输入 |
| `pipeline.py` `retrieve`、`rerank`、`apply_floor` | `existing` | `REPO_BASELINE` | SRC-PIPE / 三函数 | 消费 `rewrite_query`、`same_topic`、`named_feature_ids` |
| `settings.py` `REWRITE_PROMPT` | `unverified` | `UNVERIFIED` | 不适用 | 旧 Prompt 位置需按实际核实 |

**输入**：上下文包（S01 §11.4）。

**输出**：新 Rewrite 输出与旧字段映射；needs_context 返回编排器。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| same_topic ≠ requires_history | 两者不能互换 | S01 §11.3 |
| 旧配置 Prompt | 不能在启动时覆盖新合同 | S01 §21.2；ADM §18.3 |

**开发任务**：

1. 新 Rewrite 输出按正式 Schema；映射到 `rewrite_query`、`same_topic`、`named_feature_ids`。
2. needs_context：空 Query 不检索，带缺口回到编排器。
3. 更新 `parse_rewrite` 相关测试。
4. Prompt 与解析器成套生效。

**不在本 STEP 范围内**：实际 Memory 恢复（Q16）；Generate（Q18）；后台 Prompt 版本管理（A10）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 多功能问题 | 分路与保底不丢 | AT-02 |
| 正常 | L1 明确 YallaPay，问「那退款呢」 | 只查该场景 | C03 |
| 异常 | needs_context | 不检索空串 | C33 |
| 边界 | requires_history=false，Rewrite 发现历史指代 | 返回 needs_context 与缺口；同一 `EXEC_ID` 的预算计数不归零；不因旧表拒绝；本步无 Memory 调用记录 | AT-03 |
| 边界 | Rewriter 声称无规则 | 不作为知识结论 | AT-35 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q18] Generate 实际输入交接

**阶段状态**：`provisional`（门：G-E08 知识版本元信息）

**目标**：Generate 真正收到原句、任务、独立 Query、回答约束、c_gen 正文，以及相关时的历史回答/核验目标；业务结果按实际知识读取分类。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | RQ-11 | 统一知识授权；不等于管理权限 | `PRD` S01 §4 |
| 需求 | CSTR-Q04 | 约束、历史回答、c_gen 正文实际到达；不拿 excerpt 冒充全文 | `PRD` S01 §11.6 |
| 验收 | C02（生成部分） | 生成时获得相关历史回答与不重复约束 | `PRD` |
| 验收 | C10 | 「刚才的退款说法有依据吗」→ 定位目标回答并按知识来源核验 | `PRD` |
| 验收 | C32 | 「去年生效规则」不用聊天时间替代规则版本 | `PRD` |
| 验收 | C34 | 收到「别重复」但历史回答未传 → 合同校验失败 | `PRD` |
| 验收 | C35 | 新证据推翻历史结论 → 更正 | `PRD` |
| 验收 | AT-17 | 知识为空/局部/冲突 → 分别产出正确业务结果 | `PRD` |
| 验收 | AT-22 | 块身份有效但正文版本变了/回源失败 → 不拿 excerpt 冒充 | `PRD` |
| 约束 | S01 §20.2 | 点击知识引用时按当前可读性复核；不可读就不返回正文，不用新正文配旧 hash | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q17 | Rewrite 输出 | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `pipeline.py` `generate_messages` | `existing` | `REPO_BASELINE` | SRC-PIPE / `generate_messages` | 补输入 |
| `pipeline.py` `fill_block_content`、`block_identity` | `existing` | `REPO_BASELINE` | SRC-PIPE / 两函数 | 正文回退 excerpt 的位置 |
| `pipeline.py` `public_c_gen` | `existing` | `REPO_BASELINE` | SRC-PIPE / `public_c_gen` | 公开卡片无 content，不能当证据 |

**输入**：上下文包、c_gen。

**输出**：Generate 输入合同校验；业务结果分类。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 业务结果 | 已回答、部分有证据、依据不足、证据冲突、缺上下文、服务失败 | S01 §11.5 |
| 证据身份 | path＋chunk_id、content、content_hash；hash 必须对应本次正文 | S01 §11.6 |

**开发任务**：

1. 扩展 `generate_messages` 输入。
2. 合同校验：有「不重复」「核验旧回答」约束时，必须带上对应历史原文。
3. 正文只能是可读全文或明确标为片段；不把 excerpt 填入 content。
4. 输出业务结果分类；冲突并列展示，不裁决。
5. 知识引用点击时复核当前可读性。来源已变或不可回源时拒绝正文，不把新 content 配到旧 hash 上。

**不在本 STEP 范围内**：Evidence check（Q19）；历史回看（Q20）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 「还有么」 | 生成收到之前的回答和不重复约束 | C02 |
| 正常 | 核验上一条退款说法 | 带目标回答并对照知识 | C10 |
| 异常 | 「别重复」但缺历史回答 | 校验失败，不当正常通过 | C34 |
| 异常 | 正文回源失败 | 标限制，不用 excerpt | AT-22 |
| 边界 | 新证据推翻旧结论 | 明确更正 | C35 |
| 边界 | 零命中 / 局部 / 冲突 | 业务结果各自正确 | AT-17 |
| 边界 | 问「去年规则」 | 说明知识版本限制 | C32 |
| 边界 | 点击一条知识引用，其 `SRC` 当前不可读 | 返回缺失/拒绝，响应里没有该 hash 对应的新正文 | S01 §20.2 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q19] Evidence check 与最多一次修正

**阶段状态**：`provisional`（门：G-E02 修正剩余预算判断）

**目标**：知识答案草稿用同一份 c_gen 做语义检查；失败且预算允许时最多修正一次再复查；检查异常不放行。检查结论供 Q10 替换草稿，本步不实现前端标注。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | RQ-10 | 本轮原文校验；最多修正 1 次；仍失败停止该项；不重新检索 | `PRD` S01 §11.7 |
| 验收 | AT-18 | 数字都在证据中但业务关系错 → 不能判有依据 | `PRD` |
| 验收 | AT-30 | 草稿含不支持的承诺 → 最多修正一次，失败/异常不放行 | `PRD` |
| 验收 | AT-36 | 汇总改写已通过检查的正文 → 旧 check 不适用 | `PRD` |
| 验收 | AT-39 | 找「第一次回答」时不返回内部被否决的草稿 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q18 | 草稿与 c_gen | — |
| Q02 | 检查状态与 repair_count 写入 | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `pipeline.py` `post_check_answer`、`numbers_ok`、`remainder_without_unwritten` | `existing` | `REPO_BASELINE` | SRC-PIPE / 三函数 | 旧数字/文案检查，需替换语义 |
| `tests/test_rules.py` | `existing` | `REPO_BASELINE` | SRC-TEST / 文件 | 含与新规则冲突的旧用例（S01 §21.1），需更新预期 |

**输入**：current_query、任务、standalone_query、约束、answer_draft、c_gen、必要核验目标。

**输出**：check_status/issues；修正草稿；复查结果；草稿与正式版本的区分。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 四类问题 | 无依据结论；对象/条件/例外错误或遗漏；引用不支持说法；实质偏离任务 | S01 §11.7.2 |
| repair_count | 后端维护，初值 0，最多 1，不因子任务重置 | S01 §11.7.1 |
| 异常 | 超时、空响应、非法 JSON、字段矛盾 → 执行异常，不当 pass | S01 §11.7.2 |

**开发任务**：

1. 实现检查调用与结构校验（来源 ID 必须属于本轮 c_gen）。
2. 失败且未修正、预算足够 → 派发一次修正 → 复查新草稿。
3. 复查失败或异常 → 该项停止交付；其他独立任务照常交付。
4. 被否决草稿不成为正式回答版本。
5. 处理旧 `post_check_answer` 中「保留无依据数字并附提示」与新规则的冲突；更新 `test_rules.py` 对应用例。

**不在本 STEP 范围内**：前端草稿标注（Q10）；后台展示检查详情（A07）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 草稿含「当天到账」但证据不支持 | fail → 修正 → 复查 | AT-30 |
| 异常 | 检查超时 | 不放行 | AT-30 |
| 边界 | 数字都在证据中但关系错误 | fail | AT-18 |
| 边界 | 汇总重写了业务正文 | 旧检查不适用 | AT-36 |
| 边界 | 事后找「第一次回答」 | 返回正式版本，不返回被否决草稿 | AT-39 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q20] conversation_task：回看、旧版本找回、仅重述

**阶段状态**：`draft`

**目标**：conversation_task 返回已保存原文或只做表达变换；已知标识直接读取；不调用 Knowledge RAG，不对旧答案做新背书。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | RQ-01 | conversation_task 承接历史回看/仅重述 | `PRD` S01 §7.4 |
| 需求 | RQ-06（找回部分） | 旧版可按对话找回，不自动设回默认 | `PRD` S01 §6.16 |
| 验收 | C11 | 「简单一点」→ 仅重述，保留前提与不确定性 | `PRD` |
| 验收 | C23 | 「我之前问的是哪种方式」→ 不调 Knowledge | `PRD` |
| 验收 | AT-26 | 找回第一版答案：读真实原文与时间，不重新生成，不设默认 | `PRD` |
| 验收 | AT-33 | Memory 取回原文后任务仅为回看/重述 → 不调 Knowledge | `PRD` |
| 约束 | S01 §20.2 | 点击历史引用时按当前可见性复核 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q08 | 回答版本 | — |
| Q13 | 任务准备 | — |
| Q15 | Memory read | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| 回看/重述执行模块 | `planned` | `PLANNED` | 不适用 | 新增；重述用 LLM，回看不用 |

**输入**：目标原文、版本、范围、表达要求。

**输出**：回看回复（带历史出处）；重述回复（标未核验）。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 回看引用 | 标明此前对话、逻辑回合/消息、版本、时间、范围 | S01 §20.2 |
| 仅重述 | 保留意义、范围、不确定性、出处；不声称重新核验 | S01 §20.2 |

**开发任务**：

1. 回看：定位目标原文（已知 ID 直接 read），原样返回并标出处。
2. 找回旧版本：只读，不改默认版本。
3. 仅重述：保留原文前提与不确定性。
4. 两种执行都不调用 Knowledge RAG。
5. 回复中的历史引用在点击时复核当前可见性、清空边界和删除状态。

**不在本 STEP 范围内**：「哪个版本符合现行规则」（走 Q18 知识核验）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 「把上个版本找出来」 | 读真实旧版原文与时间 | AT-26 |
| 正常 | 「我之前问的是哪种方式」 | 回看原文，不查知识 | C23 |
| 边界 | 「简单一点」 | 重述，不新增事实 | C11 |
| 边界 | Memory 取回后仅需回看 | 不调 Knowledge | AT-33 |
| 边界 | 引用指向的 `MSG_ID` 随后被清空或隐藏，再点击该引用 | 不返回该消息正文；链接里的 id 仍是原来的 `MSG_ID` | S01 §20.2 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-Q21] 按版本赞踩与热度资格

**阶段状态**：`provisional`（门：G-E05 旧统计兼容）

**目标**：所有正常完成的 Assistant 回复都可赞踩，并绑定到回答版本；功能热度只统计实际调用 Knowledge RAG 的执行。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | RQ-14 | 全回复赞踩按版本绑定；热度仅统计实际知识调用 | `PRD` S01 §20.7 |
| 验收 | AT-24 | ack/澄清可赞踩；只有实际调用 Knowledge 才计热度 | `PRD` |
| 验收 | AT-31 | 刷新前后分别赞踩，新版不继承旧版 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| Q08 | 回答版本 | — |
| Q02 | 实际 Knowledge 调用标记 | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `POST /api/kb/rounds/{round_id}/feedback` | `existing` | `REPO_BASELINE` | SRC-API / 该路由 | 现按旧 round_id，需改为按版本 |
| `logs.py` `heatmap()` | `existing` | `REPO_BASELINE` | SRC-LOGS / `heatmap`（`limit=5000`） | 加资格过滤；不扩大窗口承诺 |
| `contracts/kb-qa-feedback/contract.md` | `existing` | `CONTRACT` | 契约目录 | 旧反馈合同，需同步 |

**输入**：版本、执行调用标记。

**输出**：按版本的反馈；带资格过滤的热度。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 不开放赞踩 | 纯技术错误、未完成生成稿 | S01 §20.7 |
| 热度计数 | 符合资格的执行中 c_gen 的 feature_id 去重，每个 +1；无功能计未归类 | S01 §20.7 |
| 旧日志 | 无调用标记的保留旧口径，不补造资格 | S01 §20.7 |

**开发任务**：

1. 反馈接口改为绑定回答版本；前端按版本显示。
2. heatmap 加「实际调用 Knowledge RAG」过滤。
3. 旧记录标旧口径。
4. 更新 `test_feedback.py`、`test_retrieve_ops.py` 中的热度用例。

**不在本 STEP 范围内**：后台反馈页（A16）；运行概览（A15）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | ack 回复 | 该 `VER_ID` 可写入 `FEED`；其 `EXEC_ID` 不进入热度，`FEAT` 不因此增加「未归类」 | AT-24 |
| 边界 | 刷新前踩、刷新后赞 | 两个 `VER_ID` 的 `FEED` 分别为踩和赞，互不覆盖 | AT-31 |
| 异常 | 纯技术错误回复 | 无赞踩按钮 | RQ-14 |

**完成标志**：通用完成标志①～⑤。

---

## 后台线 STEP 提示词

### [STEP-A01] 新动作权限注册与旧角色迁移

**阶段状态**：`provisional`（门：G-ADM-E06）

**目标**：新增配置查看、配置编辑、Prompt 查看、Prompt 编辑、Prompt 调试、配置发布、知识源查看、数据概览、问题处理等动作权限；已有角色不自动扩权；旧 `/config` 按新查看权限过滤。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | ADM-R09 | 账号角色、动作权限和旧授权兼容 | `PRD` ADM §14.3～§14.5 |
| 需求 | ADM-R15（C17、C18、C08） | 查看与编辑分离；旧接口同步鉴权；不自动扩权 | `PRD` |
| 验收 | T74 | 有页级权限无管理 UI 大门 → 保持 UI/API 区分 | `PRD` |
| 验收 | T78 | 旧配置角色迁移：展示权限变化，不自动扩新权；旧写接口不能绕过发布 | `PRD` |
| 验收 | T96 | 只有配置查看或只有 Prompt 查看 → 只读获权内容；旧 `/config` 同样过滤 | `PRD` |

**前置依赖**：无。

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `auth_store.py` `PERM_CHECKBOX` | `existing` | `REPO_BASELINE` | SRC-AUTH / `PERM_CHECKBOX` | 追加新权限 |
| `GET/PUT /api/kb/config` | `existing` | `REPO_BASELINE` | SRC-API / `/api/kb/config` | 按新权限过滤；PUT 迁移为草稿写入（依赖 A08） |
| `contracts/kb-auth/contract.md` §6 | `existing` | `CONTRACT` | SRC-CT-AUTH / §6 | 页级接口不叠加大门 |
| 新权限正式标识 | `planned` | `PLANNED` | 不适用 | G-ADM-E06 |

**输入**：ADM §14.3 权限矩阵。

**输出**：新权限注册；角色映射报告（受影响旧角色清单）；`/config` 过滤。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 不新增 | 可分配的「对话删除」权限 | ADM §14.3 |
| 超管 | 内置全权限，不可修改权限清单 | ADM §14.1 |

**开发任务**：

1. 追加新权限；超管自动拥有；其他角色默认不加。
2. 迁移时输出受影响旧角色清单，供超管分配。
3. `GET /config`：没有 Prompt 查看权限就不返回 Prompt 正文。
4. `PUT /config`：在 A08 就绪前维持旧行为并登记为待迁移；A08 就绪后改为草稿写入，不保留绕过例外。
5. 更新 `test_auth_m*.py` 与契约 §5/§6。

**不在本 STEP 范围内**：账号/角色页面（A03）；发布流程（A08）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 只有配置查看的角色调 `GET /config` | 无 Prompt 正文 | T96 |
| 异常 | 旧「配置」角色迁移后 | 没有新权限，迁移报告列出 | T78 |
| 边界 | 只勾问答明细、不勾大门 | 无管理 UI；页级 API 仍按勾选 | T74 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-A02] 管理操作审计扩展

**阶段状态**：`provisional`（门：G-ADM-E07）

**目标**：审计覆盖账号/角色、配置/Prompt、调试、索引、删除、问题、证书和敏感阅读事件，记录结果与前后版本；高风险写在审计明确不可用时阻断；敏感读取审计失败不阻断已授权读取。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | ADM-R10 | 审计和高风险写留痕 | `PRD` ADM §15 |
| 需求 | ADM-R15（C15、C22） | 高风险写审计不可用阻断；读取审计尽力 | `PRD` |
| 验收 | T81～T86 | 记录字段；旧字段名不补造；审计不可用阻断；写已执行审计失败不重做；删除后最小留痕；仅审计权限点原文重新鉴权 | `PRD` |
| 验收 | T101 | 读取审计失败时正文仍返回 | `PRD` |

**前置依赖**：无。

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `kb_audit_logs` | `existing` | `REPO_BASELINE` | SRC-SQL / `kb_audit_logs` | 扩展字段 |
| `GET /api/kb/admin/audits` | `existing` | `REPO_BASELINE` | SRC-API / 该路由 | 列表扩展（分页由 A04） |
| 事件编码 | `planned` | `PLANNED` | 不适用 | G-ADM-E07 |

**输入**：ADM §15.2 事件表、§15.3 字段。

**输出**：审计写入 API（受理、结果两段）；高风险写前置检查；读取审计的尽力写入。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 不写入 | 密码、Session、API Key、Authorization、私钥、被查看正文 | ADM §15.3 |
| 高风险写 | 发布、回退、实际删除、角色/账号高风险修改、证书变更、索引写任务 | ADM §15.5 |

**开发任务**：

1. 扩展审计字段：操作标识、结果、安全错误码、前后版本标识、关联。
2. 提供「高风险写前置检查」，审计不可用就拒绝操作。
3. 敏感读取审计失败只记异常，不影响返回。
4. 写已执行但结果审计失败：按同一操作查询实际状态，不重做。

**不在本 STEP 范围内**：审计列表页的筛选 UI（A04 骨架＋本 STEP 字段，页面在「记录」工作区）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 修改角色 | 有操作者、对象、前后值、结果；无秘密 | T81 |
| 异常 | 审计不可用时发布 | 拒绝 | T83 |
| 异常 | 写成功但结果审计失败 | 不重复执行 | T84 |
| 边界 | 旧审计只有字段名 | 不补造前值 | T82 |
| 边界 | 删除后查看审计 | 无被删原文 | T85 |
| 边界 | 仅审计权限点 Prompt 版本 | 重新鉴权，拒绝 | T86 |
| 边界 | 读取审计写入失败 | 正文照常返回 | T101 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-A03] 账号、角色与解锁页面补齐

**阶段状态**：`draft`

**目标**：在「访问」工作区补齐修改账号角色、编辑自定义角色权限（显示前后差异，二次确认）、登录解锁；服务端保护最后一名启用中的超管。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | ADM-R09 | 页面补齐 | `PRD` ADM §14.2 |
| 验收 | T75 | 修改账号角色或自定义角色权限有真实页面 | `PRD` |
| 验收 | T76 | 禁用/降级最后一名启用超管被拒 | `PRD` |
| 验收 | T77 | 禁用/改密/撤权后旧页面不能继续敏感操作 | `PRD` |
| 验收 | T79 | 登录解锁不影响问答执行/保存状态 | `PRD` |
| 验收 | T80 | 非超管尝试证书/开户/角色/物理删除 → 服务端拒绝 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| A01 | 新权限列表 | 角色编辑页能勾新权限 |
| A02 | 审计写入 | 修改有审计 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `PATCH /api/kb/admin/accounts/{account_id}` | `existing` | `REPO_BASELINE` | SRC-API / 该路由 | 改角色 |
| `PUT /api/kb/admin/roles/{role_id}/permissions` | `existing` | `REPO_BASELINE` | SRC-API / 该路由 | 编辑权限 |
| `POST /api/kb/admin/unlock` | `existing` | `REPO_BASELINE` | SRC-API / 该路由 | 解锁 |
| `admin.js` 「访问」工作区 | `existing` | `REPO_BASELINE` | SRC-ADMJS / 访问 | 补页面 |

**输入**：现有接口。

**输出**：三处页面补齐；最后超管保护的并发校验。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 不新增 | 删除账号、后台重置密码、强制首次改密 | ADM §14.1 |

**开发任务**：

1. 账号详情：修改角色、启停。
2. 自定义角色：编辑权限，展示差异与影响，二次确认。
3. 解锁：按用户名查看锁定状态并解锁。
4. 服务端核实最后超管保护在并发下也生效。

**不在本 STEP 范围内**：新权限注册（A01）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 超管改某账号角色 | 成功并留审计 | T75 |
| 异常 | 降级最后一名超管 | 拒绝 | T76 |
| 异常 | 权限撤销后用旧页面操作 | 服务端拒绝 | T77 |
| 边界 | 解锁 | 只解登录锁 | T79 |
| 异常 | 非超管 curl 开户/证书 | 403 | T80 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-A04] 通用列表与关联查询骨架

**阶段状态**：`provisional`（门：G-ADM-E01）

**目标**：后台列表统一做服务端真筛选与分页、稳定排序、覆盖说明；报错和真实空结果分开；跨模块链接只传稳定标识，进入目标页再鉴权；正文安全渲染。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | ADM-R12 | 关联查询和错误/分页一致性 | `PRD` ADM §5、§17.4 |
| 验收 | T91 | 列表报错/分页截断/加载中与零记录区分，返回保留筛选 | `PRD` |
| 验收 | T92 | 正文含 HTML/指令/伪权限字段 → 安全渲染，不执行 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| A01 | 权限 | 页面按权限请求 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `GET /api/kb/rounds`（`limit ≤ 500`） | `existing` | `REPO_BASELINE` | SRC-API / `/api/kb/rounds` | 现有分页形态参考 |
| `admin.js` 左列表右详情 | `existing` | `REPO_BASELINE` | SRC-ADMJS / 问答工作区 | 复用布局 |
| `admin.js` 总览 `/rounds?limit=200` | `existing` | `REPO_BASELINE` | SRC-ADMJS / 约第 260 行 | 去掉「先取 200 再过滤」 |
| 分页游标、页大小 | `planned` | `PLANNED` | 不适用 | G-ADM-E01 |
| CSRF 防护现状 | `unverified` | `UNVERIFIED` | 不适用 | G-ADM-E01 核实 |

**输入**：ADM §5.1～§5.3。

**输出**：列表响应约定（items、续页信息、覆盖/截断说明、数据截止、错误）；前端通用列表组件；安全渲染函数。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 时间字段 | 必须标明是创建、执行开始、反馈发生还是任务时间 | ADM §5.1 |
| URL | 不放原文、Prompt、密码、token | ADM §3.3 |

**开发任务**：

1. 定义列表响应约定并在后端实现公共部分。
2. 去掉总览里写死的 `/rounds?limit=200`。筛选在服务端做，不能先取 200 行再在页面里过滤并当成查完。
3. 前端列表：加载中/正常/真空/无权/异常/部分覆盖六态。
4. 跨模块链接与目标页再鉴权；目标被删除、无权、无数据分别提示。
5. 统一安全渲染（文本或受约束 Markdown）。

**不在本 STEP 范围内**：各模块的具体字段（A05～A18）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 异常 | 列表接口 500 | 显示错误，不显示「暂无记录」 | T91 |
| 边界 | 从详情返回列表 | 筛选与页码保留 | T91 |
| 边界 | 正文含 `<script>` | 显示为文本 | T92 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-A05] M01 会话列表与详情

**阶段状态**：`draft`

**目标**：有「对话审计」权限者可按账号、会话、关键词、时间、可见性、清空、交互状态查询会话；详情按服务端顺序展示消息、清空分界、隐藏标识、回答版本与关联执行，全部只读。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | ADM-R01 | 会话/消息/版本真实查阅 | `PRD` ADM §6.1～§6.4、§6.6 |
| 验收 | T01 | 按账号/会话/关键词找旧回复，真实匹配集分页 | `PRD` |
| 验收 | T02 | 用户已隐藏会话：管理员可查阅，无恢复入口 | `PRD` |
| 验收 | T03 | 多次清空显示真实分界 | `PRD` |
| 验收 | T04 | 刷新多次：一条 User、多版本、反馈分开 | `PRD` |
| 验收 | T05 | 被否决初稿不出现在版本列表 | `PRD` |
| 验收 | T06 | 新版本保存失败时旧默认版本不替换 | `PRD` |
| 验收 | T07 | 忙碌与保存阻塞分别显示，无强制解锁 | `PRD` |
| 验收 | T10 | 第 41 个会话及翻页：不淘汰，分页不等于上限 | `PRD` |
| 约束 | ADM §6.3 | 打开详情不把原文送入该用户的 L1、Memory 或调试 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| A04 | 列表骨架 | — |
| Q01 | 消息事实源 | — |
| Q03 | 可见性 | — |
| Q04 | 清空边界 | — |
| Q08 | 回答版本 | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `GET /api/kb/admin/conversations` | `existing` | `REPO_BASELINE` | SRC-API / 该路由 | 现仅返回元信息，扩展 |
| `admin.js` 问答工作区「按会话」分段 | `existing` | `REPO_BASELINE` | SRC-ADMJS / 问答 | 放置位置（UD-02） |
| 会话详情接口 | `planned` | `PLANNED` | 不适用 | 路径按 G-ADM-E01 |

**输入**：消息、版本、状态。

**输出**：会话列表与详情页；关键词检索（实际文本）。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 禁止操作 | 改原话、覆盖答案、代赞踩、设旧版为默认、恢复用户访问、强制解除阻塞、插入伪消息 | ADM §6.6 |
| 权限 | 「对话审计」看会话全文；「问答明细」不自动获得全文 | ADM §6.1 |

**开发任务**：

1. 扩展管理会话接口：筛选、分页、关键词定位到消息/版本。
2. 详情：消息顺序、清空分界提示、隐藏标识、版本列表、关联执行跳转。
3. 当前交互状态：可继续/执行忙碌/保存阻塞/不可访问/未知。
4. 页面不提供任何写操作（删除入口属 A06）。
5. 打开详情只读。不得因此写入该用户的 L1、Memory 或 test_run。

**不在本 STEP 范围内**：实际删除（A06）；带入调试（A11）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 关键词搜旧回复 | 定位到对应消息/版本 | T01 |
| 正常 | 隐藏会话 | 可查阅，无恢复按钮 | T02 |
| 正常 | 多次清空 | 分界可见 | T03 |
| 边界 | 刷新三次 | 同一个 `MSG_ID`、同一个 `ROUND_ID`；三个不同 `VER_ID`；各自 `FEED` 不合并 | T04 |
| 边界 | 有被否决初稿 | 该草稿 id 不在版本列表的 `VER_ID` 集合里 | T05 |
| 异常 | 新版本保存失败 | 当前采用的 `VER_ID` 与失败前相同 | T06 |
| 边界 | 忙碌与保存阻塞 | 分开显示，无解锁按钮 | T07 |
| 边界 | 41 个以上会话 | 各页 `CONV_SET` 的并集包含全部未隐藏 id，不因翻页丢掉旧 id | T10 |
| 边界 | 打开某会话详情 | 该用户打开前后的 L1 消息 id 集合、Memory 可检索 id 集合、test_run id 集合都不变 | ADM §6.3 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-A06] M01 超管单会话实际删除

**阶段状态**：`provisional`（门：G-E07；**门未过不开放删除按钮**）

**目标**：仅超管可对单个会话执行实际删除：二次确认、服务端复核、阻断读取与晚到写回、清理事实数据和派生数据，如实展示结果。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | ADM-R01 | 单会话超管删除 | `PRD` ADM §6.5 |
| 需求 | RQ-15 | 仅超管实际删除所选 Conversation，不新增可分配删除权限 | `PRD` S01 §6.11 |
| 验收 | T08 | 普通管理员直接调用删除 → 服务端拒绝 | `PRD` |
| 验收 | T09 | 清理延迟、旧结果晚到 → 不返回原文，不复活 | `PRD` |
| 验收 | AT-25 | 有对话审计权但非超管 → 拒绝；删除后残留不返回 | `PRD` |
| 验收 | C27（管理删除部分） | 删除后触发派生清理 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| A05 | 会话详情入口 | — |
| A02 | 高风险写审计 | 审计不可用时拒绝 |
| Q14 | Memory 索引失效接口 | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `DELETE /api/kb/conversations/{conv_id}` | `existing` | `REPO_BASELINE` | SRC-API / 该路由 | **不得**直接复用为物理删除（Q03 已改为隐藏） |
| 删除接口与操作状态 | `planned` | `PLANNED` | 不适用 | G-E07 |

**输入**：目标会话。

**输出**：删除操作（含操作标识与状态查询）；受管副本清单的清理；M08 清理异常；M10 最小审计。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 删除状态 | 尚未执行、已受理/处理中、事实数据结果、派生清理结果、失败或未知 | ADM §6.5 |
| 受管副本 | 消息、回答版本、Runtime、索引、引用缓存、工作集、问题中受管内容、真实源测试快照 | ADM §17.5 |
| 不承诺 | 备份与外部副本删除；恢复/撤销 | ADM §6.5 |

**开发任务**：

1. 确认页列出影响范围；二次确认。
2. 服务端复核超管身份与目标状态，审计前置检查。
3. 先阻断读取与晚到写回，再处理事实数据与派生清理。
4. 状态可按同一操作标识查询；重复点击不重复执行。
5. 清理失败时内容仍不可访问，异常推给 M08。

**不在本 STEP 范围内**：测试快照清理的具体实现（A11 按本 STEP 的失效接口接入）；问题记录中的内容清理（A17）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 超管删除 | 事实数据删除，派生清理状态如实 | C27 |
| 异常 | 对话审计角色 curl 删除 | 403 | T08、AT-25 |
| 边界 | 清理延迟中旧结果晚到 | 不复活，不返回原文 | T09 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-A07] M02 执行列表与详情

**阶段状态**：`provisional`（门：G-E01）

**目标**：按执行查询并只读展示七组信息（输入与上下文、路由与任务、历史恢复、改写与知识、生成/检查/修正、预算与异常、交付与保存）和六类状态；缺失标「旧版未记录」。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | ADM-R02 | 单次执行与步骤/证据追踪，只读 | `PRD` ADM §7 |
| 验收 | T11～T20 | 发起方式计次；L1 未载入原因；无 Memory 为正常路径；并行逐项；needs_context 不改原分类；候选与 c_gen 区分；检查与修正对应；多维状态；当次/当前来源；旧执行缺字段 | `PRD` |
| 验收 | T73 | 只有问答明细 → 不能通过新快照字段读全站历史原文 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| A04 | 列表骨架 | — |
| Q02 | Runtime 与状态 | — |
| Q16 | 调用/gap 记录 | — |
| Q19 | 检查/修正记录 | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `GET /api/kb/rounds`、`/rounds/{round_id}` | `existing` | `REPO_BASELINE` | SRC-API / 两路由 | 旧执行日志；保留旧语义 |
| `admin.js` 问答工作区「全部轮次」 | `existing` | `REPO_BASELINE` | SRC-ADMJS / 问答 | 放置位置（UD-02） |

**输入**：Runtime 与步骤记录。

**输出**：执行列表（固定主列＋可选列）；步骤详情；证据当次/当前两个入口。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 不展示 | 模型私有 reasoning/thinking 长推理 | ADM §7.4 |
| 禁止操作 | 改 Runtime、强行通过、续跑、再生成覆盖、删执行 | ADM §7.7 |
| 历史正文 | 展开其他历史消息正文还需对话审计 | ADM §14.3 |

**开发任务**：

1. 执行列表字段与筛选（ADM §7.2）。
2. 详情七组信息；循环组与并行组可展开。
3. 证据：当次快照与当前来源分开，标 hash 是否相同。
4. 历史正文按对话审计再鉴权。
5. 页面不调用模型、不自动回放。

**不在本 STEP 范围内**：带入调试（A11）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 发送+刷新+重传+内部重试 | 执行与调用关联各自正确 | T11 |
| 边界 | L1 超预算 | 显示未载入原因 | T12 |
| 边界 | requires_history=true 但 L1 足够 | 不告警缺步骤 | T13 |
| 异常 | 并行 gap 一成一败 | 逐项显示 | T14 |
| 边界 | needs_context 后恢复 | 原 Router 分类不变 | T15 |
| 边界 | 候选与 c_gen 不同 | 分别标识 | T16 |
| 边界 | 初稿失败→修正→复查 | 草稿对应正确 | T17 |
| 边界 | pass 但部分依据且保存失败 | 状态分开 | T18 |
| 边界 | 知识源已变 | 当前来源另列 | T19 |
| 边界 | 旧执行 | 标旧版未记录 | T20 |
| 异常 | 仅问答明细看历史正文 | 拒绝 | T73 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-A08] 配置包版本化、发布与兼容回退

**阶段状态**：`provisional`（门：G-ADM-E02）

**目标**：配置与 Prompt 共用版本化配置包：草稿不生效；发布经服务端校验后原子切换；新接受执行绑定当时有效包；回退是一次新发布；并发发布只有一个成功。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | ADM-R11 | 发布、回退与精确配置包 | `PRD` ADM §16 |
| 需求 | ADM-D02、ADM-C06 | 草稿→测试→发布，兼容回退 | `PRD` |
| 验收 | T24 | 保存草稿后正式配置与在途执行不变 | `PRD` |
| 验收 | T87 | 两人同时发布：一个成功，另一个冲突 | `PRD` |
| 验收 | T88 | 在途执行沿用旧包，新执行用新包 | `PRD` |
| 验收 | T89 | 回退到旧 Schema/40 淘汰配置 → 拒绝 | `PRD` |
| 验收 | T90 | 发布失败/未知/重复点击 → 不半切换，不重复生效 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| A01 | 配置编辑/发布权限 | — |
| A02 | 高风险写审计 | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `config_store.py` | `existing` | `REPO_BASELINE` | SRC-CFG / 模块 | 现为「当前配置」单份，改为版本化 |
| `ConfigStore.load` 的 LEGACY 覆盖 | `existing` | `REPO_BASELINE` | SRC-CFG / 约第 70–79 行 | 启动时不得覆盖已发布合同 |
| `PUT /api/kb/config` | `existing` | `REPO_BASELINE` | SRC-API / 该路由 | 迁移为草稿写入 |
| 配置包存储 | `planned` | `PLANNED` | 不适用 | G-ADM-E02 |

**输入**：当前有效配置。

**输出**：草稿/修订/已发布/历史版本；发布与回退操作；执行绑定配置包版本。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 发布阻断项 | 缺注册职责/变量；Schema 不兼容；违反固定规则；预算非法；关键必测未过；前置服务未接入；权限失效；并发冲突；审计不可用 | ADM §16.4 |
| 不做 | 自动回退、灰度、多人审批、定时发布 | ADM §16.5 |

**开发任务**：

1. 版本化存储：草稿修订号、已发布版本、历史版本。
2. 发布：再次校验兼容性/修订/权限 → 原子切换 → 记录结果。
3. ask 入口在接受执行时绑定当时的有效包。
4. 回退：选兼容历史版本作新发布；不兼容拒绝。
5. 同一操作结果未知时查询，不重复发布。
6. 旧 `PUT /config` 改写草稿（与 A01 衔接）。
7. 去掉 `ConfigStore.load` 在命中 `LEGACY_SYSTEM_PROMPTS` / `LEGACY_REWRITE_PROMPTS` 时把配置卷 Prompt 写回 `settings` 默认值的行为（`config_store.py` 约第 70–79 行）。已发布合同不能在启动时被这段迁移覆盖。

**不在本 STEP 范围内**：配置页（A09）；Prompt 页（A10）；必测门（A12）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 保存草稿 | 有效配置不变 | T24 |
| 异常 | 两人并发发布 | 一个成功，一个冲突 | T87 |
| 边界 | 发布时有在途执行 | 在途用旧包 | T88 |
| 异常 | 回退到不兼容版本 | 拒绝 | T89 |
| 异常 | 发布结果未知后重复点击 | 查询同一操作，不重复生效 | T90 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-A09] M03 功能配置页

**阶段状态**：`provisional`（门：G-E02、G-E03 数值与范围）

**目标**：展示当前有效配置、草稿、版本、话术池；固定规则只读；已接入参数带单位与组合校验；未冻结参数只读显示「待定/未接入」；模型/环境信息只读。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | ADM-R03 | 固定规则只读、合法配置与独立话术池 | `PRD` ADM §8 |
| 需求 | ADM-D01 | 固定规则只读；其他已接入且有合法范围的参数可配置 | `PRD` |
| 验收 | T21 | 试图改 L1/修正次数/跨会话范围 → 不开放，服务端拒绝 | `PRD` |
| 验收 | T22 | 循环预算空白 → 不能启用 | `PRD` |
| 验收 | T23 | 组合非法 → 指出具体问题 | `PRD` |
| 验收 | T25 | 同一草稿并发修改 → 修订冲突 | `PRD` |
| 验收 | T26 | 停用最后一条话术 → 阻止发布，两池不互借 | `PRD` |
| 验收 | T27 | 历史恢复停用 → 后续任务明确受限，不绕过 | `PRD` |
| 验收 | T28 | Key 已配置但无连接证据 → 不标可用 | `PRD` |
| 约束 | ADM §5.4 | 配置草稿未保存时离页要提示；保存失败保留本地编辑并标明未保存 | `PRD` |
| 约束 | ADM §8.6 | 话术提供预览 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| A08 | 配置包与草稿 | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `admin.js` 索引工作区「配置」卡 | `existing` | `REPO_BASELINE` | SRC-ADMJS / 索引 | 现有配置 UI；放置位置按 UD-02 |
| `config_store.py` 只读项（模型、collection、Key 状态） | `existing` | `REPO_BASELINE` | SRC-CFG / 模块 | 只读展示 |

**输入**：配置包。

**输出**：配置页（固定规则区、可配置区、话术池、模型只读区）。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 固定只读 | L1 10 回合/5000 tokens、修正 1 次、历史范围、工作流职责、消息事实源与保留、交付与并发、反馈/热度资格、删除权限 | ADM §8.2 |
| 不做 | 录入 API Key、添加提供方、在线换 Embedding/模型 | ADM §8.4 |

**开发任务**：

1. 固定规则区只读展示；服务端拒绝越界写入。
2. 可配置项：单位、范围、组合校验；未接入项显示「未接入」。
3. 话术池：新增/修改/启停/移除；空池阻止发布；每条话术可预览将发出的原文。
4. 历史恢复开关（停用只影响后续执行）。
5. 草稿修订冲突提示与差异显示。
6. 编辑未保存时离页提示。保存失败时编辑区内容仍在，并标明未保存。

**不在本 STEP 范围内**：Prompt 正文（A10）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 异常 | curl 修改 L1 上限 | 拒绝 | T21 |
| 异常 | 预算空白 | 不能启用循环 | T22 |
| 异常 | 组合非法 | 指出具体项 | T23 |
| 异常 | 并发修改草稿 | 冲突提示 | T25 |
| 边界 | 停用最后一条 ack 话术 | 阻止发布 | T26 |
| 边界 | 停用历史恢复 | 新执行明确受限，L1 可用 | T27 |
| 边界 | Key 已配置 | 只显示「已配置」 | T28 |
| 边界 | 改了配置草稿未保存就离开 | 有离开提示；确认留下后编辑区内容与离开前一致 | ADM §5.4 |
| 异常 | 保存配置草稿失败 | 编辑区仍是刚提交的内容，页面标明未保存 | ADM §5.4 |
| 正常 | 打开一条话术的预览 | 预览文本等于该条话术原文，不另调模型 | ADM §8.6 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-A10] M04 Prompt 职责槽位与版本编辑

**阶段状态**：`provisional`（门：G-ADM-E02）

**目标**：Prompt 按代码注册的职责槽位管理；编辑已发布版本时新建草稿；保存时做变量、Schema、固定边界的静态校验；草稿改动后旧测试标为「针对旧修订」。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | ADM-R04 | 职责 Prompt、精确版本 | `PRD` ADM §9.1～§9.3 |
| 验收 | T29 | Router 模板加工具字段 → 注册合同校验拒绝 | `PRD` |
| 验收 | T30 | 缺变量/Schema 不兼容 → 静态校验失败 | `PRD` |
| 验收 | T36 | 修改已测试通过的草稿 → 旧测试不能背书 | `PRD` |
| 验收 | T40 | 点击详情或保存草稿 → 不调用模型 | `PRD` |
| 约束 | ADM §5.4 | Prompt 草稿未保存时离页要提示；保存失败保留本地编辑并标明未保存 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| A08 | 配置包 | Prompt 修订进入同一包 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `config_store.py` 两份 Prompt | `existing` | `REPO_BASELINE` | SRC-CFG / 模块 | 旧 Prompt 迁入槽位 |
| 槽位注册表 | `planned` | `PLANNED` | 不适用 | 槽位清单见 ADM §9.2 |

**输入**：ADM §9.2 槽位清单；Q11～Q20 实际注册的职责。

**输出**：槽位列表；编辑页（正文、只读职责边界、变量清单、Schema 说明、差异）；静态校验。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 槽位 | Router、任务准备/追溯、唯一 Rewriter、Generate、Evidence check、单次修正、Smalltalk、Clarification、仅重述 | ADM §9.2 |
| 不做 | 后台新增节点；在 Prompt 中改账号/权限/预算 | ADM §9.1、§9.3 |

**开发任务**：

1. 实现槽位注册，只列代码已接入的槽位；未接入标「未接入」。
2. 编辑与草稿；已发布版本不可原地修改。
3. 静态校验：未知变量、缺必需变量、不支持的 Schema、空文本、渲染错误、长度。
4. 草稿修订变更后，关联测试标为旧修订。
5. 编辑未保存时离页提示。保存失败时正文编辑区内容仍在，并标明未保存。

**不在本 STEP 范围内**：调试（A11）；必测门（A12）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 异常 | Router 模板加工具字段 | 拒绝 | T29 |
| 异常 | 缺必需变量 | 校验失败 | T30 |
| 边界 | 测试通过后又改草稿 | 旧测试失效 | T36 |
| 边界 | 保存草稿 | 无模型调用 | T40 |
| 边界 | 改了 Prompt 草稿未保存就离开 | 有离开提示；确认留下后正文与离开前一致 | ADM §5.4 |
| 异常 | 保存 Prompt 草稿失败 | 编辑区仍是刚提交的正文，页面标明未保存 | ADM §5.4 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-A11] M04 独立调试 test_run

**阶段状态**：`provisional`（门：G-ADM-E03、G-E02）

**目标**：提供单职责调试和整链路测试，都写入独立 test_run，不污染生产数据；已授权的真实对话可带入隔离副本；已受理的测试在离页或断线后继续执行。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | ADM-R04 | 独立调试 | `PRD` ADM §9.4～§9.7、§9.9 |
| 需求 | ADM-R15（C09、C10、C20） | 两种模式；真实对话带入隔离副本；断线继续 | `PRD` |
| 验收 | T31 | 模拟工具返回清楚标注 | `PRD` |
| 验收 | T32 | 整链路测试不写生产消息/版本/反馈/热度 | `PRD` |
| 验收 | T33、T97 | 他人真实对话带入：不冒用身份、不写回、不读生产记忆索引 | `PRD` |
| 验收 | T34 | 带入后会话被隐藏/清空 → 旧 test_run 不能绕过 | `PRD` |
| 验收 | T35 | 生产会话删除后关联测试快照失效清理 | `PRD` |
| 验收 | T37 | 两版本对比时知识源已变 → 展示来源差异 | `PRD` |
| 验收 | T38 | 调用完成、Schema、检查、人工结论分开 | `PRD` |
| 验收 | T39 | 预算未配置或权限不全 → 不发起 | `PRD` |
| 验收 | T98 | 已受理测试离页/断网后继续，按同一 test_run 查询 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| A10 | Prompt 精确修订 | — |
| A05、A07 | 真实对话/执行的选择入口 | — |
| Q16 | 整链路编排器 | 可在测试域运行 |
| A06（仅 T35） | 删除失效接口 | T35 在 A06 完成后验证 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| test_run 存储与隔离副本 | `planned` | `PLANNED` | 不适用 | G-ADM-E03 |
| 测试预算 | `unverified` | `UNVERIFIED` | 不适用 | G-E02 |

**输入**：精确 Prompt/配置修订、测试输入（合成或已授权快照）、预算。

**输出**：test_run 记录（输入、修订、模式、来源版本、输出、校验、步骤、用量、错误）；对比视图。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 带入调试的权限 | 同时具备 Prompt 调试、对应会话/消息查看、所需数据权限 | ADM §9.5 |
| 隔离副本 | 只含本次带入范围；缺失的更早历史按缺语境处理 | ADM §9.5 |
| 不保存 | 模型私有长推理 | ADM §7.4 |

**开发任务**：

1. 单职责模式：合成输入或受控原文，可标注模拟工具返回。
2. 整链路模式：调用同版编排器，写入测试域。
3. 带入真实对话：建隔离副本，记忆检索只查副本。
4. 服务端受理后与页面连接解耦，按 test_run 查询。
5. 权限、预算前置校验；缺哪项明确提示。
6. 对比视图显示来源差异；失败一侧也保留。
7. 接入 A06 的删除失效。

**不在本 STEP 范围内**：发布必测（A12）；大规模自动评分（非目标）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 单职责＋模拟工具 | 标注模拟 | T31 |
| 正常 | 整链路 | 生产数据无变化 | T32 |
| 正常 | 带入他人对话 | 隔离副本，不读生产记忆索引 | T33、T97 |
| 异常 | 带入后被隐藏/清空 | 旧快照不能绕过 | T34 |
| 异常 | 生产会话被删除 | 测试副本失效 | T35 |
| 边界 | 对比时来源已变 | 显示来源差异 | T37 |
| 边界 | Schema 通过但业务未解决 | 各结论分开 | T38 |
| 异常 | 预算未配置 | 不发起 | T39 |
| 边界 | 受理后关页 | 继续执行，重进查同一 test_run | T98 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-A12] 发布必测门

**阶段状态**：`draft`

**目标**：发布前必须对将发布的精确修订跑完受影响职责的关键必测用例并全部达到预期；非关键未覆盖项展示风险；测试用例可保存和逐项运行。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | ADM-R04、ADM-R11 | 发布前验证 | `PRD` ADM §9.7～§9.8、§16.4 |
| 需求 | ADM-C19 | 受影响关键必测必须达到预期才允许发布 | `PRD` |
| 验收 | T99 | 关键必测未达预期 → 阻止发布；非关键未覆盖只提示 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| A11 | test_run | — |
| A08 | 发布流程 | 发布接口调用本门 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| 测试用例存储、关键标记 | `planned` | `PLANNED` | 不适用 | 字段见 ADM §9.7 |

**输入**：测试用例、test_run 结果、待发布修订。

**输出**：用例管理；发布前覆盖与未测项视图；发布阻断判定。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 负向断言 | 预期为拒绝/越界拦截时，实际符合即视为通过 | ADM §9.8 |
| 用例字段 | 名称、目的、输入、预期 Route/断言、来源类型、创建人、版本 | ADM §9.7 |
| 不宣称 | S01 C/AT 已跑通过；必测通过等于零幻觉 | ADM §9.7、§16.4 |

**开发任务**：

1. 用例增删改；标记关键/非关键与所属职责。
2. 发布时找出受影响职责的关键用例，要求针对精确修订的 test_run 全部达预期。
3. 展示非关键未测项与风险；发布人填发布说明。

**不在本 STEP 范围内**：自动评分系统（非目标）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 关键用例全过 | 允许发布 | T99 |
| 异常 | 一条关键用例未过 | 阻止发布 | T99 |
| 边界 | 测试针对旧修订 | 不算数 | T99 |
| 边界 | 非关键未覆盖 | 只提示 | T99 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-A13] M05 知识来源与知识索引任务

**阶段状态**：`provisional`（门：G-E04 一致性部分）

**目标**：知识来源只读查询（受控来源登记）；知识重建留任务记录与变更明细；部分失败如实展示；范围重叠的进行中任务不重复受理。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | ADM-R05 | 来源、索引与作业 | `PRD` ADM §10.1～§10.3、§10.5 |
| 需求 | ADM-C21 | 重叠任务不重复受理 | `PRD` |
| 验收 | T41 | chunk:default 标切片范围，不宣称整份 PRD；hash 不当生效日期 | `PRD` |
| 验收 | T42 | 任意服务器路径/外部 URL → 拒绝 | `PRD` |
| 验收 | T43 | 部分块失败 → 真实展示，不自动截正文 | `PRD` |
| 验收 | T47 | 重试/重复提交可追溯，不重复派发 | `PRD` |
| 验收 | T100 | 已有进行中任务覆盖新范围 → 不受理并跳转 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| A04 | 列表骨架 | — |
| A02 | 索引写任务审计 | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `indexer.py` | `existing` | `REPO_BASELINE` | SRC-IDX / 模块 | hash 增量对账、超长块失败处理 |
| `POST /api/kb/reindex` | `existing` | `REPO_BASELINE` | SRC-API / 该路由 | 保留能力，补任务留痕 |
| 任务记录存储 | `planned` | `PLANNED` | 不适用 | 字段见 ADM §10.3 |

**输入**：受控来源扫描结果。

**输出**：来源列表与详情；任务记录与变更明细；重叠检测。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 任务字段 | 标识、操作者、时间、类型/范围、来源版本、起止、扫描/变更/失败量、错误、目标代次、结果完整性 | ADM §10.3 |
| 不做 | 在线编辑 PRD、上传资料、排队系统 | ADM §10.1、§10.5 |

**开发任务**：

1. 来源列表字段与筛选（ADM §10.2）；只读。
2. 重建前显示范围与影响；打开页面不自动重建。
3. 任务记录与变更明细；部分失败如实标注。
4. 重叠检测：有进行中的重叠任务时不受理并返回已有任务。
5. 重试保留父任务与前次结果。

**不在本 STEP 范围内**：对话记忆索引（A14）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 查看 chunk:default 来源 | 标切片范围 | T41 |
| 异常 | 输入任意路径 | 拒绝 | T42 |
| 异常 | 部分块失败 | 真实展示，不截正文 | T43 |
| 边界 | 重复提交 | 不重复派发 | T47 |
| 边界 | 重叠范围 | 不受理并跳转已有任务 | T100 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-A14] M05 对话记忆索引覆盖与回填

**阶段状态**：`provisional`（门：G-E04）

**目标**：展示 Conversation Memory 索引的接入状态、覆盖范围、缺口、积压、来源质量与失效传播；在后端能力内发起受控回填、重建、重试。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | ADM-R05 | 两类索引分开及覆盖/作业 | `PRD` ADM §10.4～§10.5 |
| 验收 | T44 | 最新进度已更新但中间有空洞 → 覆盖不完整 | `PRD` |
| 验收 | T45 | 旧历史缺失时间/版本/原文 → 保留限制，不导入 localStorage | `PRD` |
| 验收 | T46 | 回填遇到隐藏/清空历史 → 不恢复用户可检索性 | `PRD` |
| 验收 | T48 | 残留命中但源已失效 → 不返回摘要；不可手改为完整 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| A13 | 任务记录模式 | 复用 |
| Q14 | Memory 索引与覆盖状态 | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| Memory 索引覆盖接口 | `planned` | `PLANNED` | 不适用 | 由 Q14 提供 |

**输入**：Q14 覆盖状态。

**输出**：对话记忆索引子页；回填/重试操作。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 仅任务元信息权限 | 不展示消息正文或账号敏感信息；看正文仍要对话审计 | ADM §10.4 |
| 禁止 | 手工把覆盖改成完整；在线编辑向量/原文 | ADM §10.5 |

**开发任务**：

1. 覆盖视图：按账号/会话、边界、范围、代次；显示空洞与未知区间。
2. 积压：无可靠计数时不填 0。
3. 回填/重建/重试按 A13 的任务模式；重叠不受理。
4. 失效传播状态与残留处理异常。

**不在本 STEP 范围内**：索引本身的实现（Q14）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 异常 | 中间有空洞 | 显示不完整 | T44 |
| 边界 | 旧历史缺字段 | 标限制 | T45 |
| 边界 | 回填隐藏/清空历史 | 用户侧仍不可检索 | T46 |
| 异常 | 残留命中 | 不返回摘要，无「设为完整」操作 | T48 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-A15] M06 运行概览

**阶段状态**：`provisional`（门：G-ADM-E04）

**目标**：提供轻量运行概览，每个指标都标明来源、时间范围与时区、事件时间字段、单位、分子/分母、截止时间、旧数据支持与覆盖限制；未知单列；生产与测试数据分开；下钻保持同一口径并再鉴权。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | ADM-R06 | 可靠统计、资格/分母与未知口径 | `PRD` ADM §11 |
| 需求 | ADM-D05 | 轻量概览，不扩成 BI | `PRD` |
| 验收 | T49～T58 | 回合/执行计数；未实际调用不计热度；同功能只 +1；ack/回看/澄清不计；旧记录未知单列；有限窗口标覆盖；反馈时间口径；分母为 0 显示不适用；运行中/待补写/观测不足单列；无明细权限不泄露 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| A04 | 列表与下钻骨架 | — |
| Q02 | 执行与状态 | — |
| Q21 | 热度资格与版本反馈 | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `GET /api/kb/admin/heatmap` | `existing` | `REPO_BASELINE` | SRC-API / 该路由 | 保留入口 |
| `admin.js` 总览工作区 | `existing` | `REPO_BASELINE` | SRC-ADMJS / 总览 | 放置位置（UD-02） |
| 概览聚合接口 | `planned` | `PLANNED` | 不适用 | G-ADM-E04 |

**输入**：ADM §11.3 指标字典、§11.4 反馈口径、§11.5 热度规则。

**输出**：概览页；聚合接口；下钻链接。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 不新增 | 模型正确率、综合质量分、用户价值评分、金额估算 | ADM §11.1、§11.3 |
| 评价覆盖率 | 有赞或踩的版本数 ÷ 可评价版本数 | ADM §11.4 |
| 已评价赞占比 | 赞 ÷（赞＋踩）；分母 0 显示不适用 | ADM §11.4 |

**开发任务**：

1. 按 §11.3 实现各指标服务端聚合；不拿一页数据推算全量。
2. 每个统计区显示口径声明。
3. 生产为默认域，测试数据在独立页签。
4. 下钻到相同数据域和时间语义的明细；无权时只看聚合。
5. 新热度显示实际窗口、截止、资格未知记录；旧口径分开显示。

**不在本 STEP 范围内**：普通用户热度 chips（保持原路径）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 一轮新提问、刷新两次、一次重传，四次请求各自有 id | 计入的 `ROUND_ID` 只有提问那一个；计入的 `EXEC_ID` 是提问和两次刷新；重传那次请求 id 不在执行集合里 | T49 |
| 边界 | 某 `EXEC_ID` 的 route 是 knowledge_query，但没有知识工具调用记录 | 该 `EXEC_ID` 不进入热度，`FEAT` 不增加「未归类」 | T50 |
| 边界 | 同一次执行多个子任务检索同一 `feature_id` | 该 `EXEC_ID` 的 `FEAT` 里这个 id 只出现一次 | T51 |
| 边界 | 纯 ack/回看/澄清 | 这些 `EXEC_ID` 不进入热度，`FEAT` 不增加「未归类」 | T52 |
| 边界 | 旧记录缺标记 | 单列未知 | T53 |
| 边界 | 查整月但只返回有限窗口 | 标覆盖不足 | T54 |
| 边界 | 反馈与生成跨月 | 时间口径明确 | T55 |
| 边界 | 无已评价回复 | 显示不适用 | T56 |
| 边界 | 运行中/待补写 | 单列 | T57 |
| 异常 | 无明细权限点数字 | 不泄露 | T58 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-A16] M07 反馈列表与详情

**阶段状态**：`draft`

**目标**：按回答版本展示用户反馈（默认被踩），支持筛选与真实分页；详情指向实际被评价的版本；管理员只读，不能改赞踩。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | ADM-R07 | 按版本反馈 | `PRD` ADM §12.1～§12.2 |
| 验收 | T59 | 旧版被踩后刷新成功 → 被踩详情仍指向旧版 | `PRD` |
| 验收 | T60 | 管理员试图改赞踩 → 无入口，服务端拒绝 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| A04 | 列表骨架 | — |
| Q21 | 按版本反馈 | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `GET /api/kb/admin/feedback-summary`（最近 500 条） | `existing` | `REPO_BASELINE` | SRC-API / 该路由 | 替换为真实筛选分页；旧接口处理见 A19 |
| `admin.js` 问答工作区「被踩」分段 | `existing` | `REPO_BASELINE` | SRC-ADMJS / 问答 | 放置位置（UD-02） |

**输入**：版本反馈。

**输出**：反馈列表与详情。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 旧轮次反馈 | 显示「旧版轮次反馈，无法可靠关联回答版本」 | ADM §12.1 |
| 未评价 | 可在回复队列中查看，但不是一条反馈事件 | ADM §12.1 |

**开发任务**：

1. 列表字段与筛选（ADM §12.1），时间字段明确。
2. 详情展示被评价版本与对应执行；刷新后标「此反馈属于旧版」。
3. 服务端拒绝管理员写赞踩。

**不在本 STEP 范围内**：问题记录（A17）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 旧版被踩后刷新 | 详情指向旧版 | T59 |
| 异常 | 管理员 curl 写反馈 | 拒绝 | T60 |
| 边界 | 超过 500 条反馈 | 分页能查到全部 | ADM-R07 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-A17] M07 轻量人工问题记录

**阶段状态**：`provisional`（门：G-ADM-E05）

**目标**：可从反馈、执行、索引任务、异常创建或关联问题；单一处理人；状态为未处理、处理中、已关闭，可重开；处理记录只追加；关闭结论要有依据。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | ADM-R07 | 轻量问题处理 | `PRD` ADM §12.3～§12.5 |
| 需求 | ADM-D06 | 串联反馈、执行、调试、发布和结论，不自动改答案或关闭问题 | `PRD` |
| 验收 | T61 | 分配给缺原文权限的人 → 不自动扩权 | `PRD` |
| 验收 | T62 | 发布完成不自动关闭；未复测不能标已验证修复 | `PRD` |
| 验收 | T63 | 关闭后可重开，保留追加记录 | `PRD` |
| 验收 | T64 | 来源被删除 → 受管原文/敏感摘要失效，只留允许元信息 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| A16 | 反馈入口 | — |
| A02 | 审计 | — |
| A06（仅 T64） | 删除失效接口 | T64 在 A06 完成后验证 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| 问题记录存储 | `planned` | `PLANNED` | 不适用 | G-ADM-E05 |

**输入**：来源对象的稳定标识。

**输出**：问题列表、详情、处理记录；与测试/发布的关联。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 人工分类 | 路由、语境、检索、来源、生成/检查、保存、权限、体验、其他/未确定 | ADM §12.3 |
| 关闭结论 | 已验证修复、复核非缺陷、资料待补/外部处理、无法复现 | ADM §12.3 |
| 不做 | 多级工单、SLA、审批、附件上传、自动发给用户 | ADM §12.3～§12.5 |

**开发任务**：

1. 问题的增改、分配、状态流转、追加记录。
2. 关联：反馈、版本、执行、索引任务、异常、测试、发布。
3. 看底层原文仍按原权限。
4. 接入 A06 删除失效。

**不在本 STEP 范围内**：客服回复（非目标）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 边界 | 处理人无原文权限 | 只见管理信息 | T61 |
| 边界 | 发布成功 | 问题不自动关闭 | T62 |
| 正常 | 关闭后重开 | 历史记录保留 | T63 |
| 异常 | 来源被删除 | 受管内容失效 | T64 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-A18] M08 健康、异常与证书

**阶段状态**：`provisional`（门：G-E06 旁路观测）

**目标**：新增受「健康」权限保护的诊断与异常观测，只观察、定位、跳转；匿名 `/health` 不扩字段；按实际依赖显示影响；保存异常分类展示；证书能力保留。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | ADM-R08 | 真实依赖/保存/索引异常及证书 | `PRD` ADM §13 |
| 需求 | ADM-D08 | 只观察定位；不加保存重试/强制解锁/中途恢复 | `PRD` |
| 验收 | T65～T72 | 知识索引故障不笼统判全部不可用；ping 成功不覆盖写失败；Runtime 库失败时标观察受限；确认已查看不解除阻塞；打开健康页无写动作；未授权拒绝、匿名不扩；证书启用失败如实显示；非标准端口如实说明 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| A04 | 列表骨架 | — |
| Q02 | Runtime 保存状态 | — |
| Q09 | 保存异常 | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `GET /api/kb/health`（匿名） | `existing` | `REPO_BASELINE` | SRC-API / 该路由 | 保持不变（CSTR-A02） |
| `/api/kb/admin/tls*` | `existing` | `REPO_BASELINE` | SRC-API / 四个路由 | 证书保留 |
| `admin.js` 顶栏健康点、访问工作区证书页签 | `existing` | `REPO_BASELINE` | SRC-ADMJS / 顶栏、访问 | 放置位置（UD-02） |
| 授权诊断接口、异常存储 | `planned` | `PLANNED` | 不适用 | — |

**输入**：各依赖的真实检查结果与异常记录。

**输出**：诊断页、异常列表与详情；「标记已查看/关联问题」。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 观察项 | 消息事实源、Runtime 存储、Knowledge 检索、Memory、模型连接、运行配置、服务异常 | ADM §13.1 |
| 不做 | 任意 URL 探测、SQL 执行、手改状态、无限重试、外部通知 | ADM §13.1、§13.5 |

**开发任务**：

1. 授权诊断接口（「健康」权限）。
2. 异常列表与详情；需要原文时按 M01/M02 权限再鉴权。
3. 保存异常分三类：User 保存失败、Assistant 待补写/失败、Runtime 不完整。
4. 证书页维持现状；启用失败如实显示。
5. 打开或刷新页面不触发付费调用或写动作。

**不在本 STEP 范围内**：修复操作（非目标）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 边界 | 知识索引不可用 | 不标所有路径不可用 | T65 |
| 异常 | DB 可 ping 但消息写失败 | 分开显示 | T66 |
| 异常 | Runtime 库失败无旁路 | 标观察受限 | T67 |
| 边界 | 确认已查看 | 不解除阻塞 | T68 |
| 边界 | 打开健康页 | 无写动作 | T69 |
| 异常 | 未授权访问诊断 | 拒绝；匿名接口不变 | T70 |
| 异常 | 证书上传成功、启用失败 | 如实显示 | T71 |
| 边界 | 非标准端口 | 显示限制 | T72 |

**完成标志**：通用完成标志①～⑤。

---

### [STEP-A19] 旧接口兼容、统一登录核实与状态不虚标

**阶段状态**：`draft`

**目标**：核对旧接口与新规则并存时的映射，旧未知保持未知，旧写入口不能绕过新规则；核实统一登录门禁；未接入的能力在后台标「未接入/待配置」。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 | ADM-R13 | 旧数据/旧写接口及源权限兼容 | `PRD` ADM §18.2～§18.3 |
| 需求 | ADM-R14 | 文档状态与实施前置不伪造 | `PRD` ADM §0、§22～§23 |
| 需求 | ADM-R15（C04） | 工作台统一登录 | `PRD` |
| 验收 | T93 | 旧消息/状态/Prompt/反馈接口与新版并存：可靠映射，旧 PUT/config 与 payload 写不能绕过 | `PRD` |
| 验收 | T94 | E/ADM-E 未冻结 → 对应能力标未接入，不虚报 | `PRD` |
| 验收 | T95 | 未登录打开工作台页面 → 统一登录门禁生效；登录不等于管理授权 | `PRD` |

**前置依赖**（按验收分开，不把 T95 绑在其他验收后面）：

| 验收 | STEP | 所需产物 | 验证方式 |
|---|---|---|---|
| T95 | 无 | `nginx.conf` 已有整站门禁 | 未登录打开页面即被转到登录；登录后问答仍按自己的权限 |
| T93 消息/payload | Q01 | 服务端消息事实源 | 旧 PUT payload 不覆盖已写入的 `MSG_ID` |
| T93 配置/Prompt | A01、A08 | 新查看权限与草稿写入 | 旧 PUT `/config` 不直接改有效配置 |
| T93 反馈 | A16 | 按版本的反馈接口 | 旧反馈写入不能改到别的 `VER_ID` |
| T94 | 无 | 当时已经做出的后台块 | 门未过的块显示未接入；不要求 A05、A08、A16 都完成 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `nginx.conf` `/_kb_site_gate`、`/_kb_admin_gate` | `existing` | `REPO_BASELINE` | SRC-NGINX / 两个 gate | T95 已有实现，做回归 |
| `ConfigStore.load` 的 LEGACY 覆盖 | `existing` | `REPO_BASELINE` | SRC-CFG / 约第 70–79 行 | 确认 A08 已去掉启动覆盖 |
| ADM §18.2 旧入口表所列接口 | `existing` | `REPO_BASELINE` | SRC-API / 对应路由 | 逐项核对 |
| `PUT /api/kb/conversations/{conv_id}`（payload 整包写） | `existing` | `REPO_BASELINE` | SRC-API / 该路由 | 不能覆盖新消息事实源 |
| `contracts/kb-auth/contract.md` | `existing` | `CONTRACT` | SRC-CT-AUTH | 登记统一登录与旧匿名阅读的差异 |

**输入**：ADM §18.2 表。

**输出**：旧接口兼容清单与处理结果；「未接入」标识核对；契约差异登记。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 统一登录 | 工作台页面先过登录门禁；知识问答等能力再分别鉴权 | ADM §14.1 |
| 历史差异 | 旧账号文档的匿名阅读要求作为已确认目标差异登记，不写成从未存在 | ADM §14.1、§18.1 |

**开发任务**：

1. 逐项核对 ADM §18.2 的旧入口：保留、迁移或拒绝绕过。
2. 旧 payload 整包写不再覆盖服务端消息事实源。
3. 核对每个后台块在门未过时显示「未接入/待配置」。T94 只检查已经存在的块。
4. 回归统一登录。T95 不依赖 A01、A05、A08、A16。契约登记差异。
5. 确认启动时不再执行 `ConfigStore.load` 的 LEGACY Prompt 覆盖。

**不在本 STEP 范围内**：各模块功能本身。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 异常 | 旧客户端 PUT payload | 已有 `MSG_ID` 的正文不变 | T93 |
| 异常 | 旧 PUT /config | 有效配置包的版本 id 不变，写入进了草稿 | T93 |
| 边界 | 某 E 项未冻结 | 对应已有块显示未接入；不要求无关页面已完成 | T94 |
| 正常 | 未登录打开 `/feature-interaction/`，且 A05/A08/A16 可以尚未完成 | 跳转登录；登录后问答仍按「知识问答」权限，不因此获得管理权限 | T95 |

**完成标志**：通用完成标志①～⑤。

---

## 自检

- [x] 所有需求和验收均映射到 STEP（RQ-01～RQ-20、CSTR-Q01～Q06、ADM-R01～R15；C01～C42、AT-01～AT-40、ADM-T01～T101，无遗漏）。
- [x] 每个 STEP 的需求 ID、验收 ID、依赖和范围明确；跨 STEP 分拆的验收（C02、C26、C27、C38、AT-03、AT-28、AT-40）已写明各自承担的子条款。
- [x] 未增加 PRD 中不存在的业务语义；唯一新增业务决定为 UD-01（用户确认）。
- [x] 未使用 `[自定义]`；预算、阈值、页大小、权限标识、时区、保留期均未填值。
- [x] 所有路径和符号标记 `existing`、`planned` 或 `unverified`。
- [x] `existing` 引用均绑定 source_id 与定位符。
- [x] 关键 `unverified` 所在 STEP 保持 `provisional`，并写明门。
- [x] 本文件是复审通过的验证版，仍不授权开工；`provisional` 门未过不得开发该子项。
- [x] 阶段结果：`PASS_WITH_RISKS`。

## 风险列表（非阻断）

| ID | 风险 | 处理 |
|---|---|---|
| RISK-01 | E01～E08、ADM-E01～E07 未冻结，涉及 31 个 `provisional` STEP | 各 STEP 写明门；门未过不开发该子项 |
| RISK-02 | 管理站未提交改动不在 PRD 基线提交中 | A 线开工前先提交或确认基线（通用约定） |
| RISK-03 | ADM §3.1 的十项菜单与现行五工作区规则不一致 | UD-02：按 INDEX §4 归入工作区 |
| RISK-04 | `test_rules.py` 旧用例与新检查规则冲突 | Q19 负责更新预期 |
| RISK-05 | 两份审核报告不在仓库 | 不影响拆解；复审时如需请提供 |
| RISK-06 | Memory 索引底层未选，Q14/Q15/Q16/A14 工作量不确定 | G-E04 先定 |
| RISK-07 | 两线跨依赖多（A05 依赖 Q01/Q03/Q04/Q08 等） | 里程碑编排时按依赖排序，不按编号 |
| RISK-08 | `qa.js` 的 40 上限只在未登录 `persist()` 生效 | Q03 仍要求去掉，避免两套上限 |

## 进度

> 路径：保留在本文件中（本专题尚无独立进度文档约定）。  
> PRD 来源：SRC-PRD-Q、SRC-PRD-A。  
> STEP 来源：`steps-verified.md`。草稿在 `history/`，不默认读。  
> 当前阶段结果：`PASS_WITH_RISKS`

### 进度总览

| 完成数 | 总数 | 当前状态 |
|---|---|---|
| 40（历史开发记录） | 40 | 开发批次 `CLOSED_WITH_REMAINING_ITEMS`，契约 `MERGED`（2026-10-03 用户要求先收尾）。原 M1～M6 判定保留；M7/M8 不补造全量验收通过，未完成条款及本次验证见文末收尾。 |

### STEP 明细

以下 DONE 是各次实施记录，已知差距由文末剩余事项统一承接；不改写原 STEP 的验收要求。

| STEP | 功能名称 | 需求 ID | 验收 ID | 前置 STEP | 状态 | 证据 |
|---|---|---|---|---|---|---|
| Q01 | 服务端逐消息事实源 | RQ-08、RQ-19、CSTR-Q01 | AT-27 | 无 | `DONE` | `tests/test_m1_conv_facts.py` 的 `test_q01_*` 7 项通过（ack 两条落库、拒答也落库、User 写失败不调模型且重试只一个逻辑回合、同时间戳 seq 稳定、非本人会话拒绝、刷新不伪造 User）；全量 59 passed。改动：`app/msg_store.py`（新）、`conv_store.py` 补列、`init.sql`、`main.py` `_ask_events`、`qa.js` 发送/刷新 |
| Q02 | Runtime 与多维状态 | CSTR-Q02、CSTR-Q05 | AT-15、AT-32 | Q01 | `DONE` | `test_q02_*` 5 项通过（正常执行六类状态各自有值；最终 update 失败 → runtime_save=partial 而 msg_save=saved；insert 失败 → failed；消息保存失败与已回答分开；存储层 pass/partial/failed 互不覆盖、旧记录读为未知）；全量 64 passed。AT-32 中「检查 pass、业务部分有依据」的真实产出分别由 Q19、Q13 接入，本 STEP 验证的是独立表达与存储。改动：`logs.py`（新列、`sanitize_runtime_fields`、`runtime_statuses`、`ensure_runtime_columns`、带新列更新失败时保住旧字段）、`init.sql`、`main.py` `finish` |
| Q03 | 取消 40 上限与用户隐藏 | RQ-05、RQ-19 | AT-12、C26 | Q01 | `DONE` | `test_q03_*` 4 项通过（第 41 个会话后原 40 个全在；5 条/页翻 23 个并集无缺无重；页大小钳制 50/200；删除后另一设备列表/GET/PUT/DELETE/ask 均不可访问，库内会话与消息保留、后台仍可见）；全量 68 passed。改动：`conv_store.py`（去 `MAX_CONVS` 与淘汰、`list_page`、`_owned_row`、删除改 `hidden_at`）、`main.py` 列表接口 `offset/limit/next_offset`、`qa.js`（去前端 40 上限、「加载更多」）、`qa.css` |
| Q04 | 清空边界 | RQ-04 | AT-11 | Q01 | `DONE` | `test_q04_*` 4 项 + `test_q05_clear_cuts_l1_context` 通过（另一设备只见边界后；清空后完整问题照常检索；清空前开始的回合晚到回复落库但不可见；多次清空各留边界；分页读取）；全量 78 passed。**偏差待闸门判定**：AT-11「那退款呢 → 进入澄清」中「不借用清空前语境」已验证（L1 与复用块均为空），「进入澄清」需 Q11 的 unclear 分路，M1 现有链路仍走知识检索。改动：`msg_store.py` `effective_messages`/`clear`、`main.py` `GET …/messages`、`POST …/clear`、会话 404 带 `code`、`qa.js` `clearCurrent` 先调服务端 |
| Q05 | 服务端 L1 | RQ-18 | AT-13、AT-38、C38 | Q01、Q04 | `DONE` | `test_q05_*` 6 项通过（12 回合取最近 10、旧→新、当前 User 不进历史；伪造 history/last_chunks 不采信，复用块取服务端上一轮 c_gen；最新回合超 5000 整轮不载入并记 over_budget；完整澄清算回合、partial/error_notice 不算；字符估算与整轮预算边界；清空后 L1 为空）；全量 78 passed。改动：`app/l1.py`（新）、`main.py` 接入并把 L1 摘要写 Runtime `snapshot`。过渡：旧 `Pipeline.rewrite` 仍按 `history_turns` 截取末尾若干条（只收窄不扩大），Q17 重做；刷新在 Q08 前用当前有效范围的 L1，不是原快照 |
| Q06 | 旧历史迁移 | RQ-12 | — | Q01、Q04 | `DONE` | `test_q06_*` 8 项通过（执行 id 与原句都对上 → 按执行记录时间迁为完整回合并进 L1、报告不含原文；对不上/无回答 → 标 `migrated_ltd`、不关联执行、不进 L1；已隐藏会话迁入后对用户仍 404；重复执行不重复写入，消息表已有记录的会话不迁旧缓存；无提问可挂的回答丢弃并列清单，旧失败提示迁为 `error_notice`；不补造、不重置清空边界；单个会话写入失败不影响其他、失败会话不留半截；服务启动时迁移且只有可靠回合进入新提问的 L1）；全量 294 passed。实库冒烟 12/12（复制本机 10 个旧会话与 70 条执行记录到临时库，按启动流程迁移：19 个回合全部对上、38 条消息均为 `migrated`，用户消息时间 = 执行记录时间，未造清空边界，seq 不超 `last_seq`，重跑不重复，L1 只取可靠回合；结束删库）。改动：`app/migrate.py`（新）、`msg_store.py`（`insert_many` 单事务、`has_messages`、`next_seq`、`insert_migrated`）、`l1.py`（来源受限回合不算完整回合）、`main.py`（启动时迁移）。**过渡**：迁移报告写 `DATA_DIR/migrate/q06-report.json`，后台展示随 A14；来源受限消息的 `created_at` 是会话创建时间占位，精确时间查找须按 `source` 排除（Q15）；问答页仍读 `payload` 展示缓存，不读消息表 |
| Q07 | 同会话互斥 | RQ-07 | AT-14、C39 | Q01、Q02 | `DONE` | `tests/test_m2_exec_versions.py` 的 `test_q07_*` 5 项通过（执行期间同会话抢占返回忙碌、其他会话不受影响；另一设备占用时发送得 `conversation_busy` 且不写 User、不调模型，释放后同请求号可再发；已受理请求重传即便会话被占也先判 `duplicate_request` 不重跑；刷新重传判重；租期过期可再抢、只释放本执行）。实库冒烟：12 路并发抢占只有 1 个成功。改动：`conv_store.py`（`run_exec_id`/`run_until`、`acquire_run`/`renew_run`/`release_run`）、`logs.py`（`client_request_id`、`find_by_request`、索引）、`main.py`（`_ask_events` 外层释放、查重→抢占顺序、各阶段续期）、`qa.js`（忙碌撤回并放回草稿、按 `exec_id` 过滤事件） |
| Q08 | 刷新与版本 | RQ-06 | AT-09、AT-10、AT-28、AT-34、AT-37 | Q01、Q02、Q05、Q07 | `DONE` | `test_q08_*` 7 项通过（刷新最后一条：原 MSG/ROUND 不变、无新 User、新增 1 执行 1 版本并采用，下一问 L1 读新版本；新版本生成失败不替换默认版本及其反馈；刷新中间一条 `l1_msg_ids` 等于原快照、不含之后消息；隔日刷新 `time_base` 等于原问题；三次刷新第三次失败时后续接读到被采用那次的 `EXEC_ID` 与 `c_gen`；清空前回合 `round_not_found`；旧快照标 `legacy_snapshot`）。**偏差**：AT-34 只在数据层验证，现链路尚无时间解释，Q12/Q17 接入。改动：`msg_store.py`（版本写入、`visible_round`、`get_by_ids`、`adopt_version`）、`l1.py`（`l1_msg_ids`、`assemble_from_ids`）、`main.py`（刷新分支、`_refresh_l1`、`_write_reply`）、`qa.js`（`versions`/`viewIndex`、「‹ n/m ›」、失败恢复） |
| Q09 | 保存失败补写 | RQ-08 | C40、AT-28、AT-40 | Q01、Q07 | `DONE` | `test_q09_*` 6 项通过（第一次补写成功只更新保存状态；三次全失败 → `msg_save=failed`、承载写入、会话阻塞，另一设备发送得 `save_blocked`、其他会话可用，重试保存仍失败保持阻塞、成功后同文落库并解除、再次调用幂等；刷新版本保存失败时旧默认版本保留、重试保存后采用；承载丢失返回 `save_source_lost` 并解除且不重新生成；阻塞写库失败时进程内仍阻塞）。改动：`conv_store.py`（`save_block_exec_id`、进程内备份）、`logs.py`（`pending_reply`）、`main.py`（`save_reply` 补写、`POST …/retry-save`）、`qa.js`（「未保存 · 重试保存」、锁输入、跨设备阻塞提示）、`qa.css` |
| Q10 | 断线继续与草稿展示 | RQ-09、CSTR-Q05 | AT-16、AT-29、C41、AT-40 | Q02、Q07、Q09 | `DONE` | `test_q10_*` 5 项通过（AT-29 生成中关闭订阅 → 后台照常完成并保存，状态接口运行中报 `terminal=false`、完成后给出正文、六类状态与公开引用，重开读取不再调用模型、生成只 1 次；状态接口只给本人执行，非本人/不存在 404、未登录 401、不需要「问答明细」，本进程未在跑且租期不属于它的 running 执行按中断报告且不写库；C41 服务端生成中途真失败时半段不落库、不进下一问的历史；AT-40 超过总截止 → `exec_timeout` 执行失败并落超时说明，之后晚到的模型结果不改写终态，执行权已释放可继续提问；前端流式标「草稿·核对中」、收到 `check` 转正式或替换、EOF/断线未收到终态时轮询状态接口，`main.py` 不再有「断开即中断」）；全量 286 passed。实库冒烟 M5 11/11（旧库补 `rewrite`/`call_usage`/`evidence_check` 列并读回、修正后只存修正稿、`conflict`/`missing_context` 落库、状态接口读库、遗留执行按中断报告不改库、非本人 404）。改动：`main.py`（`_ask_events` 改后台任务 + 订阅队列、`_close_timed_out`、`GET /api/kb/rounds/{exec_id}/status`、去掉断开即中断）、`qa.js`（草稿标注、`check` 事件、`settleFromServer` 轮询、新阶段文案）。**过渡**：没有断点补流，重连后只拿最终结果、不回放中间 token；服务重启遗留的执行只在读取时按中断报告，库里仍是 running（会话执行权租期到期后自然可用）；前端页面未在浏览器实跑 |
| Q11 | Router v3 | RQ-01 | C01、C05、C09 | Q02、Q05 | `DONE` | `tests/test_m5_orchestration.py` 的 `test_q11_*` 33 项通过（四字段 Schema 合法输出与多余字段只记名；非 JSON、缺字段、`"true"`/0/1、confidence 超范围/布尔/字符串/NaN、未知 route 含 `context_dependent`、空 reason 均为 `router_invalid`，空响应与调用失败为 `router_fail` 且不重试；非法输出不检索不生成、不记 clarify、`error_notice` 落库、执行权释放；C01 Runtime 记 knowledge_query/false 且 Router 输入含 L1、当前原句不在 L1；C05、C09 进入知识链路；低置信度只记录不改分支；route 每执行只写一次；刷新按原快照 L1 单独分类）；全量 153 passed。真实模型冒烟（DeepSeek，脚本不入库）：C01 knowledge_query/false，C05（有/无 L1）knowledge_query，C09 knowledge_query；参考 C04 ack、C07 out_of_scope、C12 unclear、C11 conversation_task。改动：`app/router.py`（新）、`settings.py` `ROUTER_PROMPT`、`logs.py`（`route`/`requires_history`/`router` 三列与校验）、`init.sql`、`main.py` `_ask_flow` 接入、`qa.js` 阶段文案、`tests/conftest.py` 默认替身 Router。**过渡**：Q11 后六类 route 仍走现有知识链路，分支执行自 Q12 起 |
| Q12 | 非知识分支 | RQ-01、RQ-16、CSTR-Q06 | C04、C06、C07、C08、C12、AT-23 | Q11 | `DONE` | `test_q12_*` 17 项通过（C04 ack 取 ack 池一句、Router 后无模型调用与检索、回复落库、`biz_result=not_applicable`；两个话术池不相交、空池报 `reply_pool_empty`；C06 smalltalk 用 Smalltalk Prompt、只收 L1 与当前输入、不检索；C07/C08 越界取越界池、`refused`、不检索；C12 空历史「那个呢？」走 Clarification Generator、输入含空 L1/停止原因/当前原句、`clarify`；澄清输出只认唯一 `clarification` 非空字符串；闲聊/澄清模型失败或输出非法为执行异常、提示不写成反问、`error_notice` 落库、诊断记 `model_error`、执行权释放；AT-23 Qdrant 不可用时 ack 正常且不 ping 知识索引，知识查询仍报 `index_not_ready`；时间基准未知时如实说明；前端阶段文案）；全量 200 passed。改动：`app/branches.py`（新）、`settings.py`（两个话术池、`SMALLTALK_PROMPT`、`CLARIFY_PROMPT`）、`main.py`（`_ask_flow` 按 route 分路；知识依赖检查移到知识分支；分支失败写诊断）、`qa.js` 阶段文案。**过渡**：未跑真实模型冒烟；AT-23「纯回看」随 `conversation_task`（Q13/M6）；话术池为 PRD 示例值，后台管理随 A09 | 
| Q13 | 任务准备与承接 | RQ-02、RQ-03 | C36、C37、AT-01、AT-04、AT-08 | Q11 | `DONE` | `test_q13_*` 31 项通过（Schema：合法任务集与多余字段只记名、非 JSON/缺字段/空任务/非法 mode/check（含准备阶段不得给的 knowledge_insufficient）/重复或非法 id/未知依赖/依赖成环/未知缺口/缺口指向未知任务/缺口类型非法/超 6 个任务均为 `task_prep_invalid`，空响应 `task_prep_fail`；C36 对照任务依赖的一方缺失 → `blocked_by_dependency`，说明写「依赖的…尚未完成」并要求不得写成已完成、不得把未知一方写成没有规则；AT-01 requires_history=false 也做任务准备，表格/对照约束与回答约束送达 Rewrite 与 Generate，真实 `Pipeline` 组装的消息确含此说明、无任务说明时不变；C37 三项一项缺较早历史 → 交付两项、第三项标「需要更早的对话内容，当前暂不支持查找」、`biz_result=partial`；RQ-03 混合越界只执行整理、设计部分标不执行、`partial`；AT-04 缺用户条件 → Clarification Generator 收到待补信息点、不检索、`clarify`；只剩缺历史 → 如实说明未完成、不调模型、`insufficient`；全部越界 → 越界话术 `refused`；AT-08 澄清已滚出 L1 时从消息与 Runtime 恢复原任务原句、澄清消息与候选，交给 Router 与任务准备，`task_prep.carry` 指向上一轮执行；上一轮正常回答不承接、清空后不承接、Router unclear 的澄清也可承接；任务准备失败/非法为执行异常、不降级不检索不重试、`error_notice` 落库、诊断记 `model_error`；澄清出口在 Qdrant 不可用时照常）；全量 231 passed。实库冒烟 12/12（旧库补 `task_prep` 列、JSON 读回、MySQL 消息与 Runtime 恢复承接、部分完成后承接列已交付项、清空后不承接）；M2/A05/A16/A15 冒烟回归 20/13/11/15（脚本补了替身任务准备）。改动：`app/tasks.py`（新）、`settings.py` `TASK_PREP_PROMPT`、`branches.py`（澄清可带待补信息点与承接线索，默认不变）、`pipeline.py`（`_task_brief` 进 Rewrite/Generate 消息）、`logs.py`（`task_prep` 列）、`init.sql`、`main.py`（Router 前取承接、知识分支先任务准备再分四个出口、有未完成项记 `partial`）、`qa.js` 阶段文案、`tests/conftest.py` 默认替身任务准备。**过渡**：任务说明经请求内 `cfg["_task_brief"]` 交给现有 Rewrite/Generate，Q17/Q18 改为正式交接；`conversation_task` 做完任务准备后仍走知识链路（分支执行随 Q20）；未跑真实模型冒烟；逐任务 `knowledge_insufficient` 未单独标记，整轮 0 块仍走原拒答 |
| Q14 | Memory 索引 | RQ-12、RQ-20 | C29、AT-21 | Q01、Q03、Q04 | `DONE` | `test_q14_*` 11 项通过（新消息保存后后台写入、覆盖正常，点带会话/账号/回合/角色/版本；部分回答与失败提示不索引也不算应索引；C29 迁移消息未索引时覆盖为「部分」、回填后恢复正常；AT-21 中间一条向量失败而最新已写入 → 仍为「部分」并列出空洞、失败记录错误码与次数，回填重试后正常；末尾几条还没写完为「落后」不是空洞；无 Key / 向量库不可用 → 「未接入」且消息照常保存；超长消息切 600 字一片并记字符范围，重写不产生重复点；隐藏与清空不删索引、管理员删除清掉点与记录；刷新版本各自一条带版本号；索引通知出错不影响提问与回答保存；保存时先记待处理）；全量 305 passed。实环境冒烟 13/13（临时 MySQL 库 + 本机 Qdrant 临时 collection + 真实 DashScope 向量：本机 10 个会话迁移后回填 38 条消息、52 个切片点，全部「正常」；重跑全部跳过、不新增点；按会话过滤检索、首条命中探测原文；注入中间失败显示空洞；管理员删除只清该会话；知识库 collection 未动；结束删库删 collection）。改动：`app/memory_index.py`（新：记录表、Qdrant 专用 collection、切片、异步写入、回填、覆盖判定、管理员删除清理）、`msg_store.py`（`on_saved` 保存后通知）、`settings.py`（`COLLECTION_MEMORY`）、`main.py`（`mem_index`、启动时建记录表，知识索引启动后接入并回填）、`sql/init.sql`（`kb_mem_index`）、`tests/conftest.py`（启动时不连真实记忆库）。**过渡**：手动触发回填与覆盖展示随 A14；管理员删除调用随 A06；隐藏/清空的过滤与回源复核在 Q15；索引写入是本进程后台任务，重启时未写完的由启动回填补齐 |
| Q15 | Memory Tool | RQ-13、RQ-17、RQ-20 | C14、C15、C22、C24～C28、C30、C31、C38、AT-19 | Q14、Q05 | `DONE` | `test_q15_*` 15 项通过（C14 已知回合直接 read、不调向量与重排；C15 命中回合只有问题时读下一回合；C22 本轮 User 与之后的消息不进证据集；C24 先说后更正的两个回合按真实顺序带出；C25 历史里的「忽略权限」只当文本、范围仍只本会话；C26 清空前回合即使索引还在也不返回、会话隐藏后 search/read 都报 `access_changed`；C27 已删除消息的残留命中不返回；C28 伪造他人消息/回合 id 被拒、错账号 `access_changed`；C30 超时报 `timeout` 不当零命中；C31 明确「昨天」没命中不扩日期、「好像昨天」只放宽一次并标注、认不出的时间报 `time_unresolved`；AT-19 23:59 问、次日 00:02 确认 → 按「昨天」只命中前一回合，补读下一回合标真实时间与「不在区间内」；C38 超长消息返回命中附近 1500 字片段并标范围与总长；向量不可用时关键词照常、如实报通道与覆盖；来源受限的迁移消息不参与按时间定位、标时间不可靠；相对时间按服务端给的提问时间换算）；全量 320 passed。实环境冒烟 11/11（临时库 + 临时 collection + 真实向量与重排：关键词与向量两路都通、已重排、≤5 候选、覆盖正常、只返回本会话、快照之后不返回、直接读、伪造他会话 id 被拒、错账号拒绝；结束删库删 collection）。改动：`app/memory_tool.py`（新：`MemoryScope` 服务端绑定范围、时间线索换算与放宽、MySQL 关键词 + 向量召回、RRF 融合、重排、回源复核、回合恢复与片段、read 相邻回合）。**过渡**：更正关系只按顺序带出，由工作流判断（Q16）；重排不可用时退回融合顺序并标 `fused_rerank_unavailable`；尚未接入问答链路（Q16） |
| Q16 | 受控循环与预算 | RQ-20 | C02、C13、C16～C21、C42、AT-03、AT-05～AT-07、AT-20 | Q13、Q15、Q02 | `DONE` | `test_q16_*` 16 项通过（AT-05 未知动作/空查询/无来源 read/交接未读过的回合/缺原因结束/非 JSON 都终结且不调工具；C16 一次找齐即停、C18 两个独立缺口同一步派发；C17 只补缺失项，再查已解决项判非法；C19 依赖未解决的缺口不派发；C20 连续无新信息 → no_progress；C21 两个候选 → 澄清、不替用户选；AT-06 同批 G1 成功 G2 超时逐项保留；AT-07 A 换了回合后依赖 A 的 B 重新打开；AT-20 只剩一次额度只派发一个、另一个记 `not_dispatched_budget`、再派发报 `budget_exceeded`；C42 同一执行两次追溯共用预算连续累计、临近截止不派发、次数为 0 不启用；链路：C02 任务就绪时不进入追溯、计数为 0；C13 历史在 L1 之外 → 追溯找回，改写与生成都收到原文、Runtime `recall` 只记来源 id 不存原文；未找到时说明「本次范围内没有找到」不说「从未」、不检索；追溯歧义走澄清并带候选；AT-03 改写缺历史对象 → 同一执行恢复后再改写一次再检索，改写计数 2、预算步数 3；预算未配置时保持「暂不支持查找」）；全量 336 passed。真实模型冒烟 9/9（临时库 + 临时 collection；真实任务准备在 L1 缺历史时给出 `needs_history`；DeepSeek 驱动工作流 2 步 1 次调用找回 L1 窗口外的第一回合原文；问从未讨论的内容如实停止、不编来源；结束删库删 collection）。改动：`app/recall.py`（新：`RecallBudget` 预占与截止预留、动作校验、依赖串行、去重、无进展、更正复核、逐项状态、`recall_gaps`/`apply_recall`/原因文案）、`settings.py`（预算数值与 `RECALL_PROMPT`）、`tasks.py`（`needs_history` 原因优先用追溯结果）、`main.py`（任务准备后追溯、needs_context 恢复后再改写、恢复原文交改写与生成、`call_usage` 增 `recall`/`memory`、`_memory_tool`）、`logs.py` 与 `sql/init.sql`（Runtime `recall` 列）、`qa.js`（「查找此前对话中…」）、`tests/conftest.py`（旧用例默认不启用追溯）、`test_m5_orchestration.py`（计数多两项）。**过渡**：检索子项在一次调用内顺序执行，并行上限按派发数控制；追溯后歧义的澄清文案仍由澄清生成器按候选生成；`conversation_task` 的回看/重述执行随 Q20 |
| Q17 | 唯一 Rewriter | CSTR-Q03 | C03、C33、AT-02、AT-03（交接）、AT-35 | Q13 | `DONE` | `test_q17_*` 20 项通过（v3 七字段 Schema：`standalone_query` 映射 `rewrite_query`、`named_feature_ids` 经原过滤去掉未知 ID、`same_topic` 保留；空响应/非 JSON/旧格式缺 status/非法 status/ready 空 Query/confidence 越界或布尔/same_topic 非布尔/named 非数组/ready 带缺口/needs_context 无缺口/缺口类型非法/缺口指向非本轮任务均为改写失败；AT-35 Rewriter 附带的「知识库没有该规则」只记字段名不采信；唯一入口用代码内 v3 Prompt，`/config` 旧 `rewrite_prompt` 不再生效，L1 与任务说明进入输入；C03 独立问句只含本场景并交给旧 Pipeline；AT-02 映射后多功能分路按功能各召回一路；C33/AT-03 requires_history=false 时 Rewriter 返回 needs_context → 不检索、不重跑 Router、不再次改写、无 Memory 调用，`biz_result=missing_context`，`call_usage` 计数写入 Runtime；缺用户条件时走澄清；非法输出记 `rewrite.valid=false` 与诊断）；全量 251 passed。改动：`pipeline.py`（`parse_rewrite_v3`、`RewriteInvalid`，`rewrite` 改用 v3，旧 `parse_rewrite` 保留）、`settings.py` `REWRITE_V3_PROMPT`、`logs.py`（`rewrite`、`call_usage`、`evidence_check` 三列，`biz_result` 增 `conflict`、`missing_context`）、`init.sql`、`main.py`（改写记录、needs_context 两个出口、各模型调用计数）。**过渡**：后台配置页的「改写 Prompt」仍可编辑但不再生效（A10 接管）；needs_context 缺历史时如实说明暂不支持查找（Q16 接入恢复） |
| Q18 | Generate 交接 | RQ-11、CSTR-Q04 | C02、C10、C32、C34、C35、AT-17、AT-22 | Q17 | `DONE` | `test_q18_*` 9 项通过（C02「还有么」时 Generate 实际收到 L1 里的此前回答与「不重复」约束；C10 核验任务带上一条回答原文作核验目标；C35 交接规则要求新证据推翻历史结论时先更正；C34 要求不重复或核验却没有可用的此前回答 → `generate_contract_fail`、不检索不生成；AT-22 回源失败只剩片段时标「片段（非全文）」且清空 hash，回源成功时 hash 换成本次正文的 hash、公开卡片不含正文；C32 生成输入带按显示时区换算的提问时间与「只有当前版 brief、不含历史版本」说明；AT-17 点名多功能只命中一部分 → `partial`，零命中 → `insufficient`，`biz_result` 已含 `conflict`/`missing_context`；引用复核接口 hash 一致给正文、不一致 409 `source_changed` 且不含新正文、读不到 404、缺参数 400、未登录 401，前端点引用先复核）；全量 259 passed。改动：`pipeline.py`（`fill_block_content` 换 hash 与 `content_scope`、`block_identity`、`generate_messages` 交接段）、`branches.py`（`local_time_text`，`time_context` 改按显示时区）、`settings.py`（`KNOWLEDGE_VERSION_NOTE`、`GENERATE_HANDOFF_RULES`）、`main.py`（`_generate_handoff` 与合同校验、多功能部分命中记 `partial`、`GET /api/kb/chunk`、状态接口放行规则）、`qa.js`（`checkCitation`）。**过渡**：证据冲突的判定随 Q19 检查输出；历史回答只取 L1 内的回合（较早历史随 Q16）；核验目标固定取 L1 最近一条回答；引用复核读的是进程内入库元数据，重建索引前后以当时内存为准 |
| Q19 | Evidence check | RQ-10 | AT-18、AT-30、AT-36、AT-39 | Q18、Q02 | `DONE` | `test_q19_*` 22 项通过（检查输出 Schema：pass⇔issues 为空、来源 ID 必须属于本轮 E 编号、answer_span 必须摘自草稿、conflict 为布尔，空响应为 `check_fail`，其余非法为 `check_invalid`；AT-30 草稿含「当天到账」→ fail → 修正一次 → 复查新草稿通过，正式保存修正稿，`check` 事件 `replaced=true`，检查与修正用同一份 c_gen；复查仍失败不修第二次、该项不交付，只存失败说明，被否决草稿不进任何消息（AT-39）；刷新结果未通过检查不替换原有效版本；首检/复查超时或修正失败为执行异常、不放行、只落 `error_notice`；剩余时间不足 120 秒不派发修正；AT-18 数字都在证据中但关系错，语义 fail 生效；块外数字即使模型判 pass 也并入 fail；原文互相冲突记 `biz_result=conflict`；AT-36 保存正文的 hash 等于通过检查那份草稿的 hash，`post_check_answer` 不再改正文；ack 等非知识分支不做检查、记 `not_run`）；`test_rules.py` 旧用例「块外数字附提示后照常交付」改为只标 `numbers_ok=False`；`test_m1` 六类状态用例 `check_status` 预期改为 `pass`；全量 281 passed。改动：`app/evidence.py`（新）、`settings.py`（`CHECK_PROMPT`、`REPAIR_PROMPT`）、`pipeline.py` `post_check_answer`、`main.py`（执行总截止、检查—修正—复查、`evidence_check` 记录、`finish` 支持 `check_status`/`delivered`、新 `check` 事件与 `check`/`repair` 阶段）、`tests/conftest.py` 默认替身检查。**过渡**：检查与修正不做技术重试；多任务集中在一份草稿里检查，未按任务拆分交付；前端草稿标注与替换随 Q10 |
| Q20 | conversation_task | RQ-01、RQ-06 | C11、C23、AT-26、AT-33 | Q08、Q13、Q15 | `DONE` | `test_q20_*` 11 项通过（C11「简单一点」只有一轮时直接重述、标未重新核验、不调知识库、出处指向原回答、交给模型的原文不含「[原文」编号；多轮「第一个回答说得简单一点」重述被指认的第一条、不猜最后一轮、不检索；一条原文不加编号、多条用分隔线；C23 回看从 L1 回合指认、原样返回、不调 Memory 与知识库；AT-26 找回第一版只读原文与时间、不改当前采用版本、不重新生成；版本选择规则；AT-33 追溯取回后只回看不调知识库；夹杂核验仍走知识链路；历史引用点击复核：清空、隐藏、他会话 id、未登录均不返回正文；重述失败为执行异常）；全量 347 passed。端到端冒烟（临时库旧表结构 + 真实 Router/任务准备/工作流/重述）：回看路由为 `conversation_task`、不调知识库、原样返回保存原文并带历史引用；「你第一个回答说得简单一点」重述第一条代充回答（转账与 YallaPay），正文无「[原文」标记、不调知识库；不确定性写成「文档里没写」（保留文档没写这层意思，不是原文「文档未写」四字）；引用清空前可读、清空后 404；旧表自动补 `recall`/`history_refs` 列、建 `kb_mem_index`。改动：`app/conv_task.py`（新；重述去掉「[原文 N]」）、`memory_tool.py`（`round_views`、`versions`）、`recall.py`（`seed` 已读回合）、`main.py`（Q20 分支：多轮重述从 L1 指认，只有一轮时直接重述；`GET /conversations/{id}/messages/{msg_id}`）、`settings.py`（`RESTATE_PROMPT` 禁止输出编号与「原文」字样）、`logs.py` 与 `sql/init.sql`（`history_refs` 列）、`qa.js`/`qa.css`（历史引用渲染与点击复核） |
| Q21 | 版本反馈与热度 | RQ-14 | AT-24、AT-31 | Q08、Q02 | `DONE` | `test_q21_*` 4 项 + `test_feedback.py`、`test_retrieve_ops.py` 新增断言通过（刷新前踩、刷新后赞两版本各自保存；技术错误与未保存回复 409 `feedback_not_allowed`；未实际调用 Knowledge 的执行不进热度也不加未归类，旧记录按旧口径计入并单列 `legacy_count`/`legacy_rows`，结果与原算法一致）。实库冒烟：被拒请求不计入热度。改动：`main.py`（反馈资格、热度字段透传）、`logs.py`（`aggregate_heat`）、`qa.js`（按查看版本发送、409 回滚提示、未保存不显示赞踩） |
| A01 | 权限注册与迁移 | ADM-R09、ADM-R15 | T74、T78、T96 | 无 | `DONE` | `tests/test_m3_admin_base.py` 的 `test_a01_*` 5 项通过（9 个新权限注册、超管清单补全；只有配置查看时 `/config` 不含 Prompt、只有 Prompt查看时只含 Prompt；旧「配置」角色读写 `/config` 均 403 且进迁移报告、账号数正确；`PUT /config` 需配置编辑，含 Prompt 字段另需 Prompt编辑+Prompt查看、否则整次拒绝；页级权限不叠加管理入口）；全量 120 passed。实库冒烟：旧角色被拒、迁移报告、超管补全。改动：`auth_store.py`（`PERM_CHECKBOX`、`RETIRED_PERMS`、`PENDING_PERMS`、`sync_super_perms`、`perm_migration_report`）、`main.py`（`_ops_perm` 支持任一权限、`/config` 过滤与字段鉴权、`GET /admin/perm-migration`）、`admin.js`（`canSeeConfig`、只读字段不提交）。**过渡**：`PUT /config` A08 前仍直接生效 |
| A02 | 审计扩展 | ADM-R10、ADM-R15 | T81～T86、T101 | 无 | `DONE` | `test_a02_*` 5 项通过（改角色审计含前后值与 `changed_fields`；审计写不进时高风险写 503 `audit_unavailable` 且未执行；结果更新失败时操作不重做、行停 accepted；旧记录标 `legacy` 不补造字段，detail 不含密码/Prompt/正文；读取审计失败仍返回正文并计数）；全量 120 passed。实库冒烟：启动补齐 10 列、accepted→success 同一行更新、被拒操作记 failed、JSON 列解码。**偏差**：T85（删除后最小留痕）与 T86（仅审计权限读版本）只以过滤规则验证，端到端随 A06、A08。改动：`auth_store.py`（补列、`begin_audit`/`finish_audit`/`record_sensitive_read`、`page_audits`、`audit_health`）、`main.py`（11 类高风险写接入、`GET /rounds/{id}` 敏感读）、`init.sql` |
| A03 | 账号/角色/解锁页 | ADM-R09 | T75～T77、T79、T80 | A01、A02 | `DONE` | `test_a03_*` 5 项通过（角色权限修改前后差异入审计；并发降级两名超管只成功一个、写后复核回滚；撤权后旧页面请求 403；解锁只清登录锁定、不影响会话执行/保存状态；非超管即使勾满也不能进超管接口）；全量 120 passed。实库冒烟：最后超管降级被拒、锁定状态查询与解锁。改动：`auth_store.py`（`_SUPER_GUARD`、`_ensure_super_left`、`lock_status`）、`main.py`（`GET /admin/login-lock`）、`admin.js`（改角色确认、角色编辑预览差异后二次确认、迁移报告卡、「未接入」「停用」标记、解锁查状态）、`admin.css` |
| A04 | 列表骨架 | ADM-R12 | T91、T92 | A01 | `DONE` | `test_a04_*` 4 项 + `test_a01_t74_*` 通过（查询失败 503 `list_unavailable` 不显示成空；审计游标翻页无缺无重、稳定倒序；执行记录服务端按关键词/待处理/反馈筛选、账号分页带 total；跨站 Origin 写请求 403 `csrf_rejected`、同源与无来源放行；前端列表用 `esc` 渲染的静态检查）；全量 120 passed。实库冒烟：120 条审计 3 页、12 条同一时间执行记录分页无缺无重、`pending` 与关键词服务端筛选、旧 `limit` 兼容、CSRF 拒绝。**过渡**：带 `feature_id` 的执行查询沿旧路径并标 `coverage.complete=false`。改动：`listing.py`（新）、`settings.py`、`logs.py` `page_rounds`、`main.py`（CSRF 中间件、错误 `code`、三类列表接口）、`admin.js`（列表六态、加载更多、审计筛选、时区说明） |
| A05 | M01 会话 | ADM-R01 | T01～T07、T10 | A04、Q01、Q03、Q04、Q08 | `DONE` | `tests/test_m4_admin_observe.py` 的 `test_a05_*` 10 项通过（关键词在消息正文中服务端筛选，命中非当前旧版本并给出消息/版本定位，不在第一页也能找到；已隐藏会话可查阅、标「用户侧已移除」、页面无恢复入口；两次清空分界 2/4、回合分三段；刷新三次一条 User 一个逻辑回合四个版本、反馈各自保留；未保存且承载丢失的新版本不进版本列表、当前版本不变；忙碌与保存阻塞分开显示与筛选、页面本节无写请求；45 个会话 10 条一页并集完整；打开详情前后用户有效消息、消息总数、执行记录、清空边界不变，只留 `sensitive_read`；旧会话只读展示缓存并标明；无权 403、未找到 404、筛选值与游标非法 400、查询失败 503）；全量 163 passed。实库冒烟 13/13（正文 LIKE 含 `%` `_` 字面量、游标分页、GROUP BY 统计、各筛选、详情分界与版本、审计写入）。改动：`conv_store.py`（`admin_page`、`admin_get`、`interaction`、`note_clear`）、`msg_store.py`（`search`/`stats`/`list_clears`、`admin_search`/`admin_messages`/`excerpt`）、`main.py`（`GET /admin/conversations` 扩展、`GET /admin/conversations/{id}`、清空后同步边界）、`admin.js`（按会话分段：服务端检索与筛选、加载更多、详情分段/版本切换/执行跳转）、`admin.css`。**过渡**：时间筛选用会话 `updated_at`（最近更新），列表另显示真实最近消息时间；页面未在浏览器实跑 |
| A06 | 超管实际删除 | ADM-R01、RQ-15 | T08、T09、AT-25、C27 | A05、A02、Q14 | `DONE` | `test_m7_purge.py` 7 项通过（对话审计直接删 403，原文仍在；确认号不对不删；超管删除后详情 404、消息与执行记录清空、记忆索引导出一次，重复提交同一个操作号；晚到写回不再落原文；审计写不进则 503 且未删；用户删除只隐藏；派生清理失败仍不可读且事实已删）。全量 377 passed。改动：`app/purge.py`（新）、`conv_store.py`（`purged_at`，后台不再返回已删会话）、`msg_store.py`、`logs.py`、`main.py`（`POST /admin/conversations/{id}/purge`、`GET /admin/purge-ops/{id}`，晚到收尾不再写回）、`admin.js`（超管二次确认）、`init.sql`。**过渡**：不声称备份已删；测试快照清理由 A11 接；运行中的接口容器未重建 |
| A07 | M02 执行 | ADM-R02 | T11～T20、T73 | A04、Q02、Q16、Q19 | `DONE` | `test_m7_exec.py` 10 项通过（T12 未载入原因不写成没有历史；T13 未调用记忆是正常路径；T14 缺口逐项；T15 原始 Route 不被追溯改写；T16 候选与送入生成分开；T17 初稿与修正稿分列；T18 检查/业务/保存分开；T19 当次 hash 不充当当前来源；T20 旧执行标旧版未记录；T11 发送与刷新分列，列表把发起方式与 Route 交给服务端；T73 只有问答明细读不到历史正文，对话审计可以，快照外的 id 404）。全量 357 passed。`admin.js` 语法检查通过。改动：`app/exec_view.py`（新）、`main.py`（详情附 `view`、`GET /rounds/{id}/context/{msg_id}` 要对话审计）、`logs.py`（列表增加发起方式、Route、业务结果、执行状态、检查、保存、是否要历史、是否调用知识库）、`admin.js`（七组详情、发起方式与 Route 筛选、失败不显示成绿色成功）。**过渡**：页面只露出发起方式与 Route，其余筛选已在接口；时间范围、账号与可选列未做；运行中的接口容器未重建，页面要等重建才看得到 `view` |
| A08 | 配置包与发布 | ADM-R11 | T24、T87～T90 | A01、A02 | `DONE` | `test_m8_config.py` 6 项通过（草稿不改生效包；同一修订第二次发布 409；并发只有一次成功；已接受的配置拷贝在发布后不变；含 40 条上限的历史包回退被拒；同一操作号再点不重复切换）。旧 Prompt 文件启动时不再被覆盖成代码默认值。全量 383 passed。改动：`config_store.py`（草稿、发布、回退、接受时拷贝）、`main.py`（`PUT /config` 改写草稿，`POST /config/publish`、`POST /config/rollback`，提问接受时绑定当时的包）、`admin.js`（保存草稿 / 发布草稿）、`auth_store.py`（「配置发布」移出未接入）。**过渡**：配置页还不是 A09 的完整参数页；必测门随 A12；不自动回退 |
| A09 | M03 配置页 | ADM-R03 | T21～T23、T25～T28 | A08 | `DONE` | `test_m8_rest.py` 的 `test_a09_*` 8 项通过（改 L1/修正次数/跨会话被拒且不进可写项；循环预算空白不能发布；并行大于调用次数时点名这两个字段；同一修订再保存 409 且先保存的值还在；停用最后一条确认话术不能发布，范围池不能顶上；历史恢复关掉后新包的追溯预算不启用，L1 仍能组装完整回合；密钥只显示已配置或未配置）。页面有离页提示、保存失败标「未保存」、话术预览不调用模型。`admin.js` 语法检查通过。全量 408 passed。改动：`config_store.py`、`recall.py` `budget_for`、`main.py`（话术按生效包取、提问时按包建预算）、`admin.js`。**过渡**：故障重试、分类兜底、在线换模型仍标未接入；页面未在浏览器实跑，接口容器未重建 |
| A10 | M04 Prompt 编辑 | ADM-R04 | T29、T30、T36、T40 | A08 | `DONE` | `test_a10_*` 4 项通过（Router 正文带 tool_call 被拒；缺必需内容或写入未接入的 Generate 被拒；测试通过后再改草稿，旧测试标「针对旧修订」；保存和读取都不调用模型）。改动：`app/prompts.py`（新）、`config_store.py`、`router.py`（已发布的 Router 正文优先于代码默认）、`admin.js`（槽位编辑）。**过渡**：除 Router 外，其余槽位正文存在配置包里，生产链路仍用代码里的模板 |
| A11 | M04 test_run | ADM-R04、ADM-R15 | T31～T35、T37～T39、T97、T98 | A10、A05、A07、Q16；T35 另需 A06 | `DONE` | `test_a11_*` 9 项通过（模拟工具标「模拟工具返回」；整链路不写消息、不写执行记录；带入他人会话只复制原文，操作者不是原主人，不查生产记忆索引；隐藏或实际删除后旧测试不再返回原文；两次带入内容不同会标出来源已变化；Schema 通过和业务未解决分列；预算空白或没有调试权限都不开始；同一测试编号离开后再查得到）。改动：`app/test_runs.py`（新）、`main.py`（`/admin/test-runs`、删除后作废快照）、`admin.js`（调试页）。**过渡**：整链路没有在测试域调用正式编排器；测试在同一次请求里做完，没有单独的后台任务；重启后测试记录不保留 |
| A12 | 发布必测门 | ADM-R04、ADM-R11、ADM-R15 | T99 | A11、A08 | `DONE` | `test_a12_t99_*` 通过（关键用例未过不能发布；针对旧修订的通过不算；非关键未覆盖只在结果里警告；预期是拒绝时，实际拒绝才算通过）。改动：`test_runs.py` `gate`、`config_store.publish`、`POST /admin/test-cases`。**过渡**：用例只能新增，还不能改和删；发布说明还没做输入框。不宣称这些用例等于零幻觉 |
| A13 | 知识来源与索引任务 | ADM-R05、ADM-R15 | T41～T43、T47、T100 | A04、A02 | `DONE` | `test_m7_index.py` 的 `test_a13_*` 4 项通过（来源标切片、哈希不当生效日期；任意路径与新增来源拒绝；部分块失败原样保留且任务标部分；进行中的重建不再派发，重试另起一条并保留父任务）。改动：`app/index_tasks.py`（新）、`main.py`（`GET/POST /admin/knowledge-sources`、任务查询与重试、`POST /reindex` 记任务）、`admin.js`（知识来源只读表）、`auth_store.py`（「知识源查看」移出未接入）、`init.sql`。**过渡**：来源列表来自现有 brief 扫描，不新开上传；打开页面不自动重建 |
| A14 | 记忆索引覆盖 | ADM-R05 | T44～T46、T48 | A13、Q14 | `DONE` | `test_m7_index.py` 的 `test_a14_*` 4 项通过（中间空洞为部分覆盖且响应不含正文；缺时间标受限；回填隐藏会话不恢复可见，未接入时积压为未知而不是 0；残留只给 id，没有「设为完整」）。改动：`main.py`（`GET /admin/memory-coverage`、`POST /admin/memory-backfill`）、`admin.js`（对话记忆覆盖，与知识重建分开）。**过渡**：回填沿用 Q14，不另写一套索引 |
| A15 | M06 概览 | ADM-R06 | T49～T58 | A04、Q02、Q21 | `DONE` | `test_a15_*` 6 项通过（一轮提问、两次刷新、一次重传 → 新逻辑回合 1、执行 3、刷新 2、被拒 1，执行写入 `finished_at` 并有耗时样本；route 为 knowledge_query 但未实际调用、ack 不进热度也不加未归类，同执行同功能只 +1，资格未知与生成集未采集、旧口径分别单列；超过扫描上限标覆盖不完整并给实际窗口；无已评价回复赞占比「不适用」、覆盖率 0%，运行中/终态未知不进异常率分母、待补写/保存中不进保存失败率，Memory/证据检查/用量标未接入，每个指标带来源、时间字段、单位、口径；反馈概览按生成时间、反馈列表按反馈时间分开标注，概览不含账号/会话/正文，无权 403，超 92 天 400，测试域未接入，「数据概览」移出未接入）；全量 183 passed。实库冒烟 15/15（旧库补 `finished_at`、SUM/COUNT DISTINCT/GROUP BY/TIMESTAMPDIFF 聚合、热度扫描、真实 ping）。改动：`app/overview.py`（新）、`logs.py`（`finished_at` 列、`overview_counts`、`heat_rows`）、`main.py`（`GET /admin/overview`、执行收尾写 `finished_at`）、`auth_store.py`（`PENDING_PERMS` 去掉数据概览）、`init.sql`、`admin.js`（总览「运行概览」，反馈指标有权时下钻到反馈列表）、`admin.css`。**过渡**：下钻只接反馈（其余明细列表尚不支持相同时间范围筛选，不提供不同口径的下钻）；耗时只算计算终态，消息最终保存耗时未单列；Route 分布在 Q12 前各分支仍走知识链路；页面未在浏览器实跑 |
| A16 | M07 反馈 | ADM-R07 | T59、T60 | A04、Q21 | `DONE` | `test_a16_*` 4 项通过（旧版被踩后刷新成功：列表与详情仍指向 v1、标「此反馈属于旧版」，详情不含新版正文，留 `sensitive_read`；管理员与超管写用户赞踩 403、原值不变，页面反馈分段无写入口；520 条反馈 200 条一页 3 页查全；反馈值/账号/执行筛选，旧轮次反馈标「无法可靠关联回答版本」且不挂版本，非法值 400、处理记录筛选 `not_supported`、无反馈 404、无权 403、查询失败 503）；全量 167 passed。实库冒烟 11/11（动态筛选、反馈时间游标倒序、时间范围、旧轮次行、管理员写被拒）。改动：`logs.py` `page_feedback`、`main.py`（`GET /admin/feedback`、`GET /admin/feedback/{exec_id}`）、`admin.js`（「被踩」分段改为「反馈」：踩/赞/全部、账号检索、加载更多、只读详情与执行/会话跳转）。**过渡**：关联问题状态与「是否已有处理记录」筛选随 A17，接入前显示「未接入」；总览「待处理」卡片与旧 `/admin/feedback-summary` 不动（A19）；页面未在浏览器实跑 |
| A17 | M07 问题记录 | ADM-R07 | T61～T64 | A16、A02；T64 另需 A06 | `DONE` | `test_m7_issues.py` 5 项通过（分配处理人不扩大原文权限；发布钩子不关闭问题，未复测不能标已验证修复；关闭后重开保留追加记录；来源实际删除后摘录清空并标来源已删除；无「问题处理」403）。改动：`app/issues.py`（新）、`main.py`、`admin.js`（问题页；反馈与异常可记为问题，不复制对话）、`auth_store.py`（「问题处理」移出未接入）、`init.sql`。**过渡**：反馈列表的「是否已有处理记录」筛选仍返回 `not_supported` |
| A18 | M08 健康与异常 | ADM-R08 | T65～T72 | A04、Q02、Q09 | `DONE` | `test_a18_*` 10 项通过（Qdrant 不可用只标知识检索并说明不依赖知识的分支照常、消息事实源仍正常；数据库可 ping 但 Assistant 补写失败时消息事实源标有异常，User/Assistant/Runtime 三类保存异常分开计数，事件文件不含问句与回答；诊断文件写不进时 Runtime 标「观察受限」、列表覆盖不完整，不补造执行记录；标记已查看后会话仍阻塞、未重新生成，详情显示当前阻塞与补写次数；两次打开诊断前后消息、执行记录、审计、模型调用、诊断文件均不变且不重建索引；无「健康」403、匿名 `/health` 字段集合不变；坏证书上传后启用失败 → 仍 HTTP、标待启用与失败原因、不回显私钥，端口限制说明；文件 5 MB 轮转保留 3 份；页面本节无修复/解锁/重试保存）；全量 177 passed。改动：`app/diag.py`（新）、`main.py`（诊断快照、异常列表/详情/已查看接口，在 User/Assistant/Runtime/审计/检索/模型已有失败分支追加记录）、`tls_store.py`（`pending`、`last_enable_error`、`port_note`）、`admin.js`（索引工作区「健康与异常」、证书页状态）、`admin.css`。**过渡**：Memory 显示「未接入」（M6），运行配置版本「未接入」（A08），关联问题「未接入」（A17）；「是否仍在发生」筛选未提供；Router 调用失败（Q11，M5 线）未接入诊断记录；页面未在浏览器实跑 |
| A19 | 旧接口兼容与登录核实 | ADM-R13、ADM-R14、ADM-R15 | T93～T95 | 分验收：T95 无前置 | `DONE` | `test_a19_*` 3 项通过（旧 PUT 配置不改生效包编号；消息表已有原文时，旧 PUT 带上的 messages 不覆盖；反馈带了别的回答编号则 409，不改写；故障重试、分类兜底、在线换模型仍是未接入，没有新造页面；站点门禁仍挡未登录的知识问答页，登录页单独放开，管理站另有管理门，没有「知识问答」不能提问）。改动：`main.py`（有消息事实时忽略 payload 里的 messages；反馈目标不一致则拒绝）、`auth_store.py`（「Prompt调试」移出未接入）。**过渡**：问答页仍读 payload 展示缓存；正式契约未并入 |

### 阻断与来源变化

| 日期 | STEP | 类型 | 证据或变化 | 处理结果 |
|---|---|---|---|---|
| 2026-09-29 | Q10、Q19 | 用户决定 | E05 流式草稿展示选 C（UD-01） | 展示与替换在 Q10；Q19 只产出检查结论 |
| 2026-09-29 | 见审查 Diff | 复审修正 | 验收比较键、AT-03 拆分、Q19 去掉对 Q10 的前置、补 §5.4/§8.6/§6.3/§20.2 | 写入本验证版 |
| 2026-09-29 | 全部 | 门冻结 | G-PATH 核实：`site/kb-api/.venv/bin/python -m pytest` 可用，基线 52 passed | 用户同意写入；G-E01、G-E06（M1 部分）仍待定稿，M1 未开工 |
| 2026-09-29 | Q01、Q02、Q04 | 门冻结 | 用户确认按推荐方案冻结 G-E01、G-E06 的 M1 部分（见「M1 门定稿」） | M1 开工 |
| 2026-09-29 | Q04 | 偏差 | AT-11「进入澄清」依赖 Q11 unclear 分路 | 边界部分已验证；交 M1 闸门判定 |
| 2026-09-29 | M1 | 未验证 | 无 MySQL/Docker 环境：`Mysql*Repo`、补列 `ALTER`、`LAST_INSERT_ID` 取号未实库运行；旧会话只有 payload、没有消息表记录，Q06 迁移前 L1 为空 | 无 `RUNTIME` 证据；交 M1 闸门判定 |
| 2026-09-29 | M1 | 用户决定 | M1 带风险通过：MySQL 冒烟延后到 M2 闸门前；AT-11「进入澄清」随 Q11 验收 | M2 开工 |
| 2026-09-29 | Q07、Q08、Q09、Q21 | 门冻结 | 用户确认按推荐方案冻结 G-E06（M2 部分）与 G-E05 旧统计兼容（见「M2 门定稿」） | M2 开工 |
| 2026-09-29 | M1、M2 | 实库冒烟 | 本机 Docker MySQL 8.4 临时库 `hayyo_kb_m2smoke`：先建 git HEAD（M1 前）旧表，应用启动补列补索引；发送、重传、12 路并发抢占、忙碌、刷新版本、刷新重传、补写失败阻塞与承载、重试保存、按版本反馈、热度资格、清空后刷新拒绝、清空后消息为空，20/20 通过，结束删库 | M1「无 `RUNTIME`」风险解除（取号、补列、唯一约束、清空事务已实库运行）；脚本不入库 |
| 2026-09-29 | Q08 | 偏差 | AT-34 仅数据层验证（`time_base` 沿用），时间解释链路在 Q12/Q17 | 交 M2 闸门判定 |
| 2026-09-29 | M2 | 用户决定 | M2 带风险通过：AT-34 数据层；重启后未入库承载丢失 → `save_source_lost` | M3 开工 |
| 2026-09-29 | A01～A04 | 门冻结 | 用户确认按推荐方案冻结 G-ADM-E06、G-ADM-E07、G-ADM-E01，RISK-02 以当前工作区为基线（见「M3 门定稿」） | M3 开工 |
| 2026-09-29 | A01～A04 | 实库冒烟 | 本机 Docker MySQL 临时库 `hayyo_kb_m3smoke`：先建 git HEAD 旧表，应用启动补齐审计 10 列、补全超管权限；旧配置角色拒绝与迁移报告、改角色两段审计、最后超管保护、审计/执行记录游标分页、服务端筛选、旧 `limit`、锁定状态与解锁、CSRF，20/20 通过，结束删库 | 脚本不入库 |
| 2026-09-29 | A02 | 偏差 | T85、T86 只以审计过滤规则验证；实际删除（A06）与版本详情（A08）落地后端到端验收 | 交 M3 闸门判定 |
| 2026-09-29 | A02、A04 | 过渡 | 审计失败计数在进程内、重启清零（A18 接入观测）；`PUT /config` A08 前直接生效；执行记录按功能筛选仍取回后过滤、标覆盖不完整；会话敏感读随 A05 | 交 M3 闸门判定 |
| 2026-09-29 | M3 | 用户决定 | M3 带风险通过：T85/T86 端到端随 A06/A08；审计失败计数进程内；`PUT /config` A08 前直接生效；按功能筛选覆盖不完整、会话敏感读随 A05 | M4 门定稿 |
| 2026-09-29 | Q11 | 门冻结 | 用户确认按推荐方案冻结 G-E01（Router 部分）与 G-E03（Q11 部分）：输出只认 `route`（六类）、`requires_history`（JSON 布尔）、`confidence`（0～1 数值）、`reason`（非空字符串），多余字段忽略只记名；沿用 `parse_rewrite` 容错取第一个对象；任一字段非法为 `router_invalid`，调用失败/空响应为 `router_fail`，均为执行异常、不当 unclear、不重试；低置信度兜底 M5 不启用、不设阈值，只校验与记录；Runtime 补 `route`、`requires_history`、`router`(JSON) 三列，只写一次；新增 `stage=route` | Q11 开工 |
| 2026-09-29 | A05、A15、A16、A18 | 门冻结 | 用户确认按推荐方案冻结 G-ADM-E04、G-E06 旁路观测、A05 旧会话展示（见「M4 门定稿」） | M4 开工 |
| 2026-09-29 | A05、Q12 | 会话中断 | 上一会话因用量耗尽中断：A05 仅写入 `conv_store.py` 后台查询层，Q12 已写入 `branches.py` 与 `main.py`/`settings.py` 接入，两者均未测试、未记进度。恢复时备份全部未提交改动到 `~/Desktop/lxm-tm/_backup/`（仓库外） | A05 在本会话续做完成；Q12 仍未验收 |
| 2026-09-29 | A05 | 过渡 | 时间筛选按会话 `updated_at`（最近更新，含标题等变更），不是严格的「最近消息时间」；列表与详情另列真实最近消息时间。内存仓库下清空边界原先不同步到会话行，「是否清空」筛选失效（MySQL 同表写入不受影响），已由 `note_clear` 同步 | 交 M4 闸门判定 |
| 2026-09-29 | A05 | 未验证 | 管理页面未在浏览器实跑：运行中的容器为旧代码，未重建以免影响本机环境；前端只做了语法检查与静态断言 | 交 M4 闸门判定 |
| 2026-09-29 | A16、A18、A15 | 过渡 | A16 问题状态与处理记录筛选随 A17；A18 Memory/配置版本/关联问题未接入、Router 失败（M5 线）未写诊断、无「是否仍在发生」筛选；A15 下钻只接反馈、测试数据域未接入 | 交 M4 闸门判定 |
| 2026-09-29 | M4 | 实库冒烟 | 闸门前重跑：M2 20/20（冒烟脚本补了替身 Router，因 Q11 后 ask 先经 Router）、A05 13/13、A16 11/11、A15 15/15，均为临时库、结束删库；全量 pytest 183 passed | `GATE_EVIDENCE_READY` |
| 2026-09-29 | M4 | 用户决定 | M4 带风险通过：页面未在浏览器实跑；问题记录/Memory/配置版本/测试域未接入；概览下钻只接反馈；Router 失败未写诊断 | M5 续做（Q12 起） |
| 2026-09-29 | M5 | 实库冒烟 | 闸门前：M5 11/11、Q13 12/12；回归 M2 20/20、A05 13/13、A16 11/11、A15 15/15（脚本补了替身任务准备与替身检查），均为临时库、结束删库；全量 pytest 286 passed；`qa.js` 语法检查通过 | `GATE_EVIDENCE_READY` |
| 2026-09-29 | M5 | 未验证 | 未跑真实模型冒烟（读取 `.env` 中 Key 被自动审查拦下）：Router 之后的分支话术、任务拆解、Rewriter v3、证据检查与修正的实际质量只由 Prompt 与替身测试保证；问答页与管理页均未在浏览器实跑（容器未重建） | 交 M5 闸门判定 |
| 2026-09-29 | M5 | 真实模型冒烟 | DeepSeek 14 项全部符合预期（只调模型与解析器，不连库、不碰向量库）；问答页在本机站点实发一轮、点出处；出处点击在旧接口下打不开，已修 `qa.js` `checkCitation` 兼容，`test_q18_citation_recheck_endpoint` 通过 | 补齐原「未验证」项 |
| 2026-09-29 | M5 | 用户决定 | M5 通过，进入 M6 | M6 门定稿 |
| 2026-09-29 | Q06、Q14、Q15、Q16、Q20 | 门冻结 | 用户确认按推荐方案冻结 G-E04、G-E02（M6 部分）、G-E03/G-E08（M6 部分）与 Q16/Q20 执行方式（见「M6 门定稿」） | Q06 开工 |
| 2026-09-29 | Q20 | 修复 | 用户确认：多轮重述不再猜最后一轮，从 L1 指认；去掉「[原文 N]」。全量 347 passed；端到端冒烟重述第一条代充回答且无内部编号。不确定性被说成「文档里没写」 | M6 契约草案与闸门 |
| 2026-09-29 | M6 | 用户决定 | M6 通过，进入 M7。临时契约 `M6-契约草案.md`。过渡：重述用词「文档里没写」；容器未重建；问答页仍读展示缓存；覆盖页与物理删除随 A14、A06 | M7 门冻结 |
| 2026-09-29 | A07、A06、A17、A13、A14 | 门冻结 | 用户确认：执行详情沿用现有轮次接口；实际删除为仅超管的同次操作（未做完不放按钮）；问题记录独立表；知识索引与记忆覆盖分开（见「M7 门定稿」） | A07 开工 |
| 2026-09-30 | A06、A17、A13、A14 | 证据 | 超管单会话实际删除、问题记录、知识来源任务与记忆覆盖已落地。全量 pytest 383 passed。临时契约 `M7-契约草案.md`。容器未重建 | 交 M7 闸门；用户已要求继续后面的里程碑 |
| 2026-09-30 | A08 | 证据 | 配置改为草稿后发布。保存不改生效包；并发发布只有一次成功；回退不兼容版本拒绝；同一操作号不重复切换。提问在接受时拷贝当时的包 | A09 尚未做 |
| 2026-09-29 | Q12～Q10 | 过渡 | 任务说明与交接字段经请求内 `cfg`（`_task_brief`、`_task_ids`、`_handoff`）传给现有 Pipeline；`conversation_task` 做完任务准备后仍走知识链路（Q20）；缺较早历史一律如实说明暂不支持查找（Q16）；后台「改写 Prompt」可编辑但已不生效（A10）；检查/修正不做技术重试；无断点补流；服务重启遗留执行只在读取时报中断 | 交 M5 闸门判定 |
| 2026-09-29 | Q13 | 门冻结 | 用户确认按推荐方案冻结 G-E01（任务/缺口部分）：①任务准备为一次独立模型调用，只在 knowledge_query / conversation_task 执行，输出 JSON 由服务端校验；②Runtime 新增 JSON 列 `task_prep`，含 `tasks[{task_id, goal, mode, scope, constraints, depends_on, check, gap_ids}]`、`excluded[{text, reason}]`、`information_gaps[{gap_id, task_ids, type, required, status, candidates, clue}]`、`response_constraint`，`check` 为 §8.2 八类检查结果的英文枚举；③就绪的范围内任务合并跑一次现有知识链路，未就绪/越界/缺条件的任务连同原因交给 Generate 明确说明；④需要较早历史但不在 L1 的任务，M5 标未完成、原因「需要更早的对话内容，当前暂不支持查找」，其他独立任务照常交付，M6 接入后改为查找；⑤跨轮承接只看清空边界之后最近一个逻辑回合的当前版本执行，且其结果为澄清或部分完成，从其 `task_prep` 恢复原任务原句、澄清消息、候选与未补缺口交给 Router 与任务准备，找不到可靠关联就澄清；⑥任务准备调用失败/输出非法为执行异常 `task_prep_fail` / `task_prep_invalid`，不检索、不生成、不重试，`error_notice` 落库 | Q13 开工 |
| 2026-09-29 | Q17、Q18、Q19、Q10 | 门冻结 | 用户确认按推荐方案冻结 M5 剩余门：**Q17（G-E01 Rewrite 部分、G-E05 字段映射）**输出 `status`(ready/needs_context)、`standalone_query`、`response_constraint`、`missing_context[{task_id, type, clue}]`、`confidence`(0～1)、`named_feature_ids`、`same_topic`；`standalone_query` 映射旧 `rewrite_query`，`named_feature_ids` 仍经原过滤与分路保底，`same_topic` 仍只用于复用上轮知识块；ready 时 Query 为空或字段非法为 `rewrite_fail`；Rewriter v3 Prompt 写在代码里与解析器成套生效，`/config` 旧 `rewrite_prompt` 照存不用，后台编辑随 A10；needs_context 时本轮不检索，缺用户条件→澄清、缺较早历史→如实说明暂不支持查找，不重跑 Router、不再次改写，本执行调用计数写入 Runtime、不归零。**Q18（G-E08）**时区用 `KB_DISPLAY_TZ`（默认 Asia/Shanghai）把提问时间换成本地日期交给模型；知识只有当前版 brief、不含历史版本，生成时明确告知，问历史规则时如实说明、不用聊天时间替代；`biz_result` 增加 `conflict`、`missing_context`，冲突由 Q19 检查顺带输出（按来源并列、不裁决），needs_context 收口记 `missing_context`；新增只读接口按 path+chunk_id+content_hash 取正文，hash 不符或读不到返回 409 `source_changed` / 404，不返回新正文，前端点引用先经此接口。**Q19（G-E02 修正预算）**执行总截止沿用执行权 300 秒；首次检查明确 fail、尚未修正、剩余 ≥120 秒才派发 1 次修正并复查；检查超时/空/非法 JSON 为异常，不放行不重试；复查仍失败该项不交付；去掉旧「无依据数字附提示后照常交付」，数字不在证据中作为一条检查问题并入 fail，重排 0 块拒答保留，更新 `test_rules.py`。**Q10（G-E05 SSE 与重连）**执行改为服务端后台任务，SSE 只是订阅；新增 `GET /api/kb/rounds/{exec_id}/status`（六类状态、最终文本、引用、是否终态），断线或 EOF 未收到 done 时前端轮询、不重发；新增 `check` 事件，流式正文标「草稿·核对中」，通过转正式、不通过替换为修正稿或失败说明；不做断点补流；服务重启后运行中的执行按租期到期标中断 | Q17 开工 |

STEP工作项状态只使用 `NOT_STARTED`、`IN_PROGRESS`、`DONE`、`BLOCKED`。只有完成标志全部有验证证据时才能标为 `DONE`。

## 2026-10-03 管理后台复查修正与样式优化

本轮状态：`DONE`（只覆盖本节授权范围）。用户先要求核对近期开发与文档、确认问题后再修正，随后确认由本会话处理并优化后台样式；另明确授权更新本机接口容器及既有启动迁移/索引更新。原有未提交改动保留，未提交 Git、未改正式需求或替用户判定 M7/M8 闸门；进度总览的 `IN_PROGRESS` 仍有效。

| 范围 | 实际修正 |
|---|---|
| 调试真实性与隔离 | 单职责复用实际模型调用和解析器，整链路复用 `_ask_flow`，按服务端结果判断结构/业务/断言，不再信客户端 `passed`。消息、Runtime、Memory 使用本次副本；Knowledge 合成材料明确标记。有限预算、202 异步受理、持久结果、重启中断、回查与对比落地 |
| 读取权限与失效 | 调试要 Prompt调试+Prompt查看+配置查看；会话快照要对话审计与明确选定消息。精确执行导入仅给该执行提问/回答，按问答明细授权；不能绕过历史权限。读取/列表/对比复查来源权限；隐藏、清空、实际删除撤销来源副本。冲突响应按查看权限过滤 Prompt |
| 配置/发布一致性 | 原子落盘失败回退内存、草稿、历史和操作记录。精确修订审阅、说明、操作号绑定修订/类型，重试跨重启保留；修订单调连续，发布/丢弃后仍可继续保存。发布者独立于编辑者但须读取整包；历史整包恢复为新草稿再测试发布 |
| Prompt 与上下文 | 修正 TaskPrep 默认校验字段；所有已接入职责读取接受时配置包正文。现有回答系统 Prompt 保留，完整 Generate 职责仍标未接入。Rewriter 不再用旧 history_turns 截断已经按完整回合/token 组装的 L1 |
| 发布门禁 | 没有关键用例不能发布；关键用例须精确配置修订、同用例版本、来源有效且实际达到预期。变更需覆盖实际受影响职责；两话术池分别要求经过对应分支。停用追溯允许整链路验证，不要求执行已停用 Recall。未完成测试预算不能发布 |
| 实际删除与问题 | 来源关联由服务端验证并绑定真实会话。清理问题的标题、现象、关闭依据与追加记录正文，同时清理测试副本；删除屏障用于派生记录读取。操作先记 running，阻断失败不继续删正文；副本清理失败不能记成功，未知结果明确报告 |
| 索引/分页/观测 | 重叠检查查全部运行中任务，MySQL 命名锁串行受理；来源、任务、问题分页，来源正文/hash/索引一致性详情与任务重试落地。反馈处理状态在 SQL 分页前筛选。Memory/配置版本读真实状态，测试概览独立；实库发现并修正调用聚合的 `check` SQL 别名转义 |
| 页面 | 保留深色/青色主题，重新整理导航、卡片、间距、表单和详情；Prompt 折叠、独立版本侧栏、审阅差异与说明、调试记录/对比、问题追加记录、来源/任务详情补齐；390px 手机端无整页横向溢出 |

### 本轮验证

- 本机 Python 3.9 全量 pytest：425 passed。最终 Python 3.12 Docker 镜像内全量 pytest：425 passed（网络关闭、仓库只读、临时数据）。镜像内仍有 `datetime.utcnow()` 弃用告警，不算真实模型验证。
- `admin.js` Node 语法检查通过；本轮 API/UI 范围 `git diff --check` 通过。仓库其他既有差异未改动。
- Chrome 使用实际页面/接口、临时仓库与合成模型返回：保存默认表单 200、异步调试 done、恢复记录；桌面 1440px 与手机 390px，页面脚本无异常，手机整页无横向溢出。
- 四种角色：Prompt 编辑者、独立发布者、合成调试者、带问答明细的执行调试者均通过浏览器权限/入口检查，未发出失败或越权 API 请求。独立发布者无保存按钮但有审阅按钮，填写发布说明→取消→重新审阅不误标为未保存配置；无对话审计时不提供整段会话选择。
- 临时环境完整操作：建立并运行关键整链路用例→审阅发布 200→发布后继续保存 200→丢弃后继续保存 200→历史整包恢复草稿 200。未执行真实业务配置发布。
- 独立临时 MySQL 库实测 8 项：最近100条之外的运行任务仍阻断重叠、两个独立 Book 的并发受理只成功一次、232条任务分页无缺无重、问题全部文本副本清理、230条问题分页、反馈 handled 筛选先于 LIMIT、概览 SQL 聚合、删除操作状态持久化。测试库和临时账号已删除。

### 本机运行环境

- 用户确认后备份数据库与 `/data` 到 `/private/tmp/kb-review-rollbacks-01a0ff73/`，旧接口镜像保留为 `hayyo-docs-kb-api:before-admin-review-01a0ff73`；备份目录仅本机当前用户可访问。
- 只构建并重建 `site/docker-compose.yml` 的 `kb-api`，其他项目服务未重建。最终镜像：`sha256:29ae8eaf236534f550c7cf8764fa898a5a03595dbd8dca50c54af973806f6dd3`。
- 最终接口已启动；真实现有数据库只读概览/任务/问题查询通过。生效包仍 `pkg-base`、修订0，本轮未发布业务配置。
- `/api/kb/health`：Qdrant/config/index 就绪，346个知识切片，`startup_error` 为空。启动 Memory 回填：13会话、indexed=0、failed=0、skipped=68。匿名后台入口302到登录门，鉴权仍有效。
- 页面由 Nginx 挂载当前仓库，前后端已同步。打开本机 `/kb-admin/` 可查看新样式；浏览器操作验收仍以临时数据证据为准，未另建业务账号或更改真实问题/测试记录。

### 记录与后续边界

- 具体接口增量同步到 `M7-契约草案.md`、`M8-契约草案.md`，页面规则同步 `../kb-admin-ui/INDEX.md`；保留 DRAFT 与原闸门待判定状态。
- 效果截图（合成数据）：`/Users/umark/.codex/visualizations/2026/10/03/01a0ff73-8533-7320-9349-6513f4788983/admin-review/`。临时验收脚本/日志在 `/private/tmp/kb-review-preview/`，不纳入业务代码。
- 本轮未验证真实模型输出质量/计费 token；未完成完整 Generate 职责整合、全部诊断筛选/下钻、问答页 payload 展示缓存迁移、M7/M8 正式契约合并。发布测试采取整修订保守失效，未实现按无关字段复用旧测试。本节不将这些历史延期项宣称完成。

### 2026-10-03 总览生产/测试文字排版修复

状态：`DONE`。用户明确要求修复总览「生产」「测试」两页的文字结构；本次仅改 `site/kb-admin/admin.js`、`admin.css` 中的总览呈现，并追加本记录。

- 复现：统计分区标题距卡片边缘仅 1px，长统计口径与数值相互挤占；测试状态拼成一行。桌面总览沿用固定高度，内容超出卡片时底部统计受到遮挡。
- 修复：正文统一内边距；统计范围、时间口径、截止时间、查询方式独立排布；指标标题/单位、数值、补充状态、统计口径分层。桌面指标两列，手机单列；状态分布、模型调用、耗时与热度覆盖逐项对齐，比例保留分子/分母，未知值独立显示。总览改为主区滚动，问答原固定分栏保留。
- 新验证：Chrome 合成数据布局检查先复现贴边失败，修复后普通/长数值与完整分布/空数据 × 生产/测试 × 1440、1024、980、768、390、320px，共 36 组通过；核对原统计口径与单位、比例/耗时数值保留、时间筛选与数据域切换，无整页横向溢出、卡片内容越界、相邻块重叠或页面脚本异常。另使用临时接口实际返回，确认桌面可滚动至末尾统计与热度、问答布局仍正常，并逐图检查两个 tab 的桌面/手机效果。
- Node 语法检查与本次 JS/CSS 范围 `git diff --check` 通过。本次未改 API/数据口径，未重跑上节后端全量测试，也未执行真实数据写入、迁移或模型调用。
- 本机 `hayyo-docs-web` 内 JS/CSS 的 SHA-256 与当前源码一致；沿用静态挂载及 `no-cache`，刷新即可加载。截图为临时合成数据，保存于 `/Users/umark/.codex/visualizations/2026/10/03/01a0ff73-8533-7320-9349-6513f4788983/admin-overview/`；脚本在 `/private/tmp/kb-review-preview/overview_layout_check.cjs`、`overview_live_check.cjs`。

### 2026-10-03 工作区拆分、访问与记录结构调整

状态：`DONE`（仅本节范围）。用户确认按已提出方案调整：优化访问和记录，将原索引页拆为配置、知识与记忆、运行状态，并梳理总览到问答的入口。本次修改 `site/kb-admin/admin.js`、`admin.css`，同步 `../kb-admin-ui/INDEX.md` 和本记录；既有 API、权限勾选及发布规则沿用，未更改后端。

- **访问管理**：账号列表成为主内容，新建、角色修改与启停放入详情抽屉；新建账号必须主动选择角色。角色改为左列表、右侧按用途分组的权限面板，保留变更预览、确认和超管只读限制，新增未保存离开提示。登录解锁与系统证书保留独立页签。
- **操作记录**：独立筛选区，常用条件与对象/操作号条件分层；摘要表保留五列，点击动作打开详情抽屉，附加字段逐项呈现，原始字段折叠。沿用服务端筛选和游标分页；手机端列表转为逐条卡片。
- **工作区拆分**：配置包含运行参数、Prompt 与话术、版本与发布三个页签，共用一个草稿表单，切换保留输入，保存仍提交完整授权字段。知识与记忆包含来源、对话记忆、索引任务，仅加载当前页签；运行状态单独承载诊断和异常。各入口按原权限独立显示，打开页面不触发重建、回填或模型调用。
- **总览与问答**：原「待处理」改称「需关注」，准确说明既有条件为非成功执行或被踩，并区分关联问题的处理状态。单条进入对应详情，查看全部进入同条件列表；保留反馈统计下钻全部反馈。返回总览恢复原滚动位置。
- **切页与表单复核**：防止旧配置/证书/问答读取，以及配置或角色保存完成后覆盖新页面；取消发布审阅后，隐藏的发布说明不再阻止保存草稿，确认发布仍校验非空说明。

本次新增验证证据（与上节后端测试区分）：

- 本机 Chrome + 临时 API/合成数据：九个导航入口、总览单条/全部跳转、返回总览、配置跨页签保留输入、离开取消、保存草稿 200、打开/取消审阅后继续保存 200；审计详情及对象类型筛选；临时账号创建/禁用、临时角色创建/修改、权限预览及未保存离开提示通过。页面脚本无异常。
- 十一类权限角色通过入口与请求检查：Prompt 编辑者、独立发布者、调试者、带执行读取的调试者、知识查看者、仅重建、仅健康、仅审计、仅问答明细、仅反馈汇总、仅数据概览。无失败接口请求；反馈角色不请求轮次详情，无反馈权限的角色不请求反馈列表。
- 十二组页面/页签 × 1440、1024、390、320px，共 48 组布局及 8 组抽屉检查通过，无整页或主区横向溢出、无页面脚本异常；逐图核对桌面角色权限、配置及手机记录卡片、开户抽屉。
- 延迟响应验证覆盖配置读取、证书读取、问答列表读取、角色保存和配置保存离页；均保持新页面。审计、账号、问答各以模拟接口的 50+3 条两页验证追加与筛选保留，问答继续发送 `pending=1`；嵌套审计字段可读。1440px/390px 总览反馈下钻及原滚动位置恢复通过。分页数据为模拟返回，本次未重跑数据库筛选实现。
- Node 语法检查、本次 JS/CSS 范围 `git diff --check` 通过。未重跑后端全量测试，未执行真实业务数据写入、配置发布、容器重建、迁移或模型调用。
- 本机 `hayyo-docs-web` 中 JS/CSS 的 SHA-256 与源码一致，沿用静态挂载及 `no-cache`，刷新页面即可加载。浏览器操作验收使用临时账号/数据，不代表已用真实业务账号完成同样写操作。

截图（临时数据）：`/Users/umark/.codex/visualizations/2026/10/03/01a0ff73-8533-7320-9349-6513f4788983/admin-structure/`。临时验收脚本与本次修改前的前端副本保存在 `/private/tmp/kb-structure-review/`；不纳入业务代码。本节不改变 M7/M8 原闸门状态及上节列出的历史延期事项。

## 2026-10-03 开发收尾与正式契约整合

**本次任务状态：DONE；开发批次：CLOSED_WITH_REMAINING_ITEMS；契约整合：MERGED。**

`USER_DECISION`：用户要求“先收尾吧，然后因为今天又做了大量调整，你根据实际代码，整合相关的契约文档吧，然后验证下”。本次据此收口当前开发批次、以当前代码整合正式契约并执行回归。原 M1～M6 判定及已确认取舍保留；M7/M8 的开发收尾不等于所有原验收条款通过，未完成项继续列账。本次没有修改两份 PRD 或 STEP 验收正文来适配实现。

### 范围与实际改动

- 正式契约沿用现有三个主落点：[kb-qa](../../contracts/kb-qa/contract.md)、[kb-auth](../../contracts/kb-auth/contract.md)、[kb-qa-feedback](../../contracts/kb-qa-feedback/contract.md)。补齐多轮编排 M1～M8 的实际实现，并核对今天已授权的工作台、管理站九工作区、回答过程与版本恢复。H5站点登录边界同步 [h5-kb](../../contracts/h5-kb/contract.md)；已有暖夜主题规则核对后沿用。
- 修正旧契约中的40条会话上限、旧“配置”单权限、匿名文档访问、五工作区、客户端刷新快照和仅payload恢复等过期描述；明确消息保存、Runtime保存、业务结果、执行状态、证据检查分别表达。
- M1～M8草案保留历史正文，并加正式落点说明；本计划、专题索引、契约入口、旧执行记录和根 `llm-manifest.json` 指向当前实现及本节，不新增平行的正式合同。
- 首轮回归发现两条过期静态断言：账号改版后不再使用 `data-set-role` 和原只读提示句，固定规则也改为只读名称/值面板。只调整对应静态断言，后端权限、审计和固定字段拒写断言保留；新增 `site/kb-admin/tests/admin-contract.test.cjs` 的5项行为回归接续覆盖。未修改生产功能源码。
- 保留工作区原有未提交改动，未提交Git、未发布配置、未重建容器、未改业务数据库。本次不把源码/文档更新说成运行环境重新部署。

### M1～M8 实现增量落点

下表覆盖 Q01～Q21、A01～A19 共40个 STEP，每项一个主落点；其他契约仅交叉引用。映射证明文档覆盖，不证明原验收点全部完成。源码模块均在 `site/kb-api/app/`，测试均在 `site/kb-api/tests/`；前端另见 `site/feature-interaction/qa.js` 和 `site/kb-admin/admin.js`。

| 里程碑 | STEP | 正式主落点 | 实现及回归依据 |
|---|---|---|---|
| M1 | Q01、Q02、Q03、Q04、Q05 | kb-qa §9.1～9.3：逐消息、状态、取消上限、清空、L1 | msg_store / conv_store / logs / l1 / main；test_m1_conv_facts |
| M2 | Q07、Q08、Q09 | kb-qa §9.3：幂等互斥、刷新版本、保存补写 | main / msg_store / qa.js；test_m2_exec_versions |
| M2 | Q21 | kb-qa-feedback §3～4：反馈绑定执行版本 | main.set_round_feedback / qa.js；test_m2_exec_versions |
| M3 | A01、A02、A04 | kb-auth §3、§10.1、§13.1：权限、分页、审计、错误与CSRF | auth_store / listing / main；test_m3_admin_base |
| M3 | A03 | kb-auth §3、§4、§6：账号角色、预览确认、超管保护 | auth_store / admin.js；test_m3_admin_base；admin-contract.test.cjs |
| M4 | A05 | kb-auth §10.1：对话审计 | conv_store / msg_store / main；test_m4_admin_observe |
| M4 | A16 | kb-qa-feedback §9：反馈列表、被评价版本与筛选 | logs / main；test_m4_admin_observe、test_admin_review_regressions |
| M4 | A18、A15 | kb-auth §13.2～13.3：诊断异常、概览与热度 | diag / overview / logs / main；test_m4_admin_observe |
| M5 | Q11、Q12、Q13、Q17、Q18、Q19 | kb-qa §10：Router、分支、任务、Rewriter、生成与检查 | router / branches / tasks / pipeline / evidence / main；test_m5_orchestration |
| M5 | Q10 | kb-qa §4、§9.3：草稿替换、断流查状态、截止时间 | main / qa.js；test_m5_orchestration |
| M6 | Q06 | kb-qa §9.4：旧历史迁移 | migrate；test_m6_memory |
| M6 | Q14、Q15、Q16、Q20 | kb-qa §11：Memory索引、受限检索、追溯与回看 | memory_index / memory_tool / recall / conv_task；test_m6_memory |
| M7 | A07、A06 | kb-auth §10：执行详情、超管实际删除 | exec_view / purge / main；test_m7_exec、test_m7_purge、test_admin_review_regressions |
| M7 | A17、A13、A14 | kb-auth §12：问题、知识来源、Memory覆盖与索引任务 | issues / index_tasks / memory_index / main；test_m7_issues、test_m7_index、test_admin_review_regressions |
| M8 | A08、A09、A10、A11、A12 | kb-auth §11：配置包、固定规则、Prompt、隔离测试、发布门禁 | config_store / prompts / admin_test_runtime / test_runs / main；test_m8_config、test_m8_rest、test_admin_review_regressions |
| M8 | A19 | kb-auth §3～5、§11.1：旧入口兼容；消息与反馈引用各自主契约 | nginx.conf / main / qa.js；test_m8_rest、test_site_contract |

当日额外增量：回答过程的事件/持久化/answer-history归 kb-qa §4，交互归 kb-qa-feedback §6.1（`answer_process.py`、`test_answer_process.py`、`qa-process.test.cjs`）；回答Markdown归反馈§6（`kb-md.test.cjs`）；九工作区、表单与详情抽屉归 kb-auth §6/§11.2 并引用 `kb-admin-ui/INDEX.md`；独立登录页归 kb-auth §5.1，暖夜主题沿用 h5-theme 契约；四Tab与图谱/文档布局沿用 h5-kb 契约。本次未另改主题或布局源码。

### 本轮新验证（2026-10-03）

| 验证 | 方法与隔离范围 | 实际结果 |
|---|---|---|
| 后端全量 | `cd site/kb-api`；临时 DATA_DIR、KB_AUTH_MEMORY=1、模型Key置空；`.venv/bin/python -m pytest -q`，Python3.9.6 | 首次430通过/2失败；修正过期页面断言并补行为覆盖后 **432 passed**，1条urllib3/LibreSSL环境告警，无失败 |
| 前端全量 | 原生Node：`node --test site/feature-interaction/tests/*.test.cjs site/login/tests/*.test.cjs site/kb-admin/tests/*.test.cjs` | **28 passed**（原23项+后台5项），无失败 |
| 新增后台行为 | 执行实际admin.js handler，替身DOM/网络 | 超管权限只读；角色修改取消不写/确认只写选定角色；开户主动选角色；权限预览后修改使预览失效，须再次预览及确认；固定规则可见且无编辑控件，均通过 |
| Chrome问答检查 | 实际页面/脚本，全部网络拦截为合成响应；1440/390/320px，reduced-motion；无业务服务连接 | 3种视口均通过：键盘展开/收起、版本与过程恢复；旧版无过程不补造；无页面/过程横向溢出，无脚本异常。这是桌面浏览器视口模拟，不是手机设备验收 |
| 契约核对 | 对照实际路由、权限分支、注册槽位、状态和源码模块；检查本次文档链接/锚点、manifest引用及40项映射 | 286处文档链接/锚点无缺失；36项manifest文档及引用有效；40个STEP无遗漏/重复；正式契约中62处完整API路径均匹配当前路由；本次增量空白检查通过 |

原始日志与本次修改前副本：`/private/tmp/kb-contract-close-20261003/`（pytest-initial.log、pytest-final.log、node-final.log、browser.log、before、baseline.json）；临时目录不保证长期保留，以上结果与命令是仓库内持久记录。浏览器最初在沙箱内启动被系统中止，授权后的隔离启动通过；无测试失败被忽略。

### 历史证据与复用边界

前文“管理后台复查修正”“工作区拆分、访问与记录结构调整”中的真实临时MySQL、Docker Python3.12、十一类权限、48组布局及抽屉检查仍是**历史证据**；本次生产源码未改，保留其原结论。此次新增的本机全量pytest、Node和Chrome问答检查单独列在上表。没有重跑真实模型调用、容器镜像测试、数据库迁移、TLS特权端口或所有历史人工验收，不能用本次替身测试替代这些结果。

### 仍未完成或受限的范围

| 范围 | 当前事实与影响 | 后续恢复依据 |
|---|---|---|
| Generate完整职责 | `prompts.generate` 未接入；现有system_prompt生效，任务交接仍靠请求cfg内部字段 | Q18、A10；kb-qa §10.3、kb-auth §11.2 |
| Prompt完整静态检查 | 仅登记/接入、非空、关键词与Router禁词；未完成变量、Schema、渲染与长度检查 | A10；kb-auth §14；不能宣称保存即验证通过 |
| 关键用例维护 | 当前只有建立/列表，无编辑/删除；发布按整修订保守失效，未实现无关字段复用 | A12；kb-auth §11.3 |
| 诊断与筛选 | “是否仍在发生”等完整筛选/下钻和执行页部分筛选未全部实现；Router失败无旁路model_error，仅Runtime保留 | A07、A18；kb-auth §13～14 |
| 多任务与核验 | 尚未完整按任务表达knowledge_insufficient并逐任务检查/交付；集中检查一份草稿；核验目标仍为L1最近回答 | Q13、Q18、Q19；kb-qa §12 |
| 运行边界 | 无断点补流；重启遗留执行读取时报告中断；进程内补存承载/诊断计数重启丢失；Memory子查询串行 | Q09、Q10、Q15、Q16；kb-qa §9/§11/§12 |
| 展示缓存 | answer-history已在登录加载/切换会话恢复服务端版本；旧payload兼容缓存尚未完全删除 | A19；kb-qa §9.2，旧“前端只读payload”结论已失效 |
| 验收边界 | 本轮没有真实模型质量/计费tokens、真实移动设备及全部生产故障验收；原反馈AC7人工未验证结论保留 | 使用原验收条件按需验证，不能把合成/自动化结果改称真实验收 |

这些条款没有因收尾而删除或弱化，也不擅自补判 M7/M8 全量闸门PASS。**恢复位置**：先读本节及对应正式契约的限制，再按原STEP验收条件处理选定剩余项；不重新启动M1、不默认重跑前提未变的历史结果、不自动部署或发布。当前授权的“收尾、按代码整合、回归验证”完成后无待用户重复确认事项。
