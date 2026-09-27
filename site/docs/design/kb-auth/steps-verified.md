---
title: "文档工作台账号体系与管理模块 STEP 验证版"
status: "verified"
stage_result: "PASS_WITH_RISKS"
prd: "site/docs/design/kb-auth/PRD-账号体系与管理模块-v2.md"
prd_sha256: "b005262b4e8b97d5acd99d37349a0a96c246ef940ea58208c0422239dfdedd4a"
source_draft: "site/docs/design/kb-auth/steps-draft.md"
source_draft_sha256: "04084933604275c406b92fe2ae23b71f0a614904bd03ae0351505af99485aee8"
audit: "site/docs/design/kb-auth/step-audit.md"
created: "2026-09-19"
note: "step-doc-review 第一轮 review-repair 后的验证版。草稿未覆盖。含 USER_DECISION B（进管理大门独立勾选）。仍含非阻断风险；不自动开始开发。"
---

# 文档工作台账号体系与管理模块 STEP 验证版

> **现行权威**：[`PRD-账号体系与管理模块-v2.md`](PRD-账号体系与管理模块-v2.md)（status=已确认）。  
> **USER_DECISION**：2026-09-19 确认点 1 选 **B**——进管理必须单独勾「进管理模块」；AC5 前置覆盖为勾选集合 `{进管理模块, 问答明细}`。  
> **独立增量**：不替代 [`../kb-qa/PRD-知识问答-v3.md`](../kb-qa/PRD-知识问答-v3.md)、[`../kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md`](../kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md)。  
> **草稿**（未覆盖）：[`steps-draft.md`](steps-draft.md)。  
> 宿主：http://127.0.0.1:18765/feature-interaction/ 。实现状态：未实施。  
> 本文件经九维复审，仍含非阻断风险；不宣布开发已开始。

## 来源摘要

事实标签只用：`USER_DECISION`、`PRD`、`CONTRACT`、`REPO_BASELINE`、`RUNTIME`、`PLANNED`、`UNVERIFIED`。本轮无 `RUNTIME`。本轮无独立 `contract.md`；契约测试见 SRC-CONTRACT。

| source_id | 路径 | 状态 | SHA-256 | 本轮核实 |
|---|---|---|---|---|
| SRC-PRD | `site/docs/design/kb-auth/PRD-账号体系与管理模块-v2.md` | `existing` | `b005262b4e8b97d5acd99d37349a0a96c246ef940ea58208c0422239dfdedd4a` | 全文；G1–G6；F1–F14；C1–C15；RQ-01～RQ-19；AC1–AC18；E1–E10；T1–T7 |
| SRC-UD-B | 对话确认点 1 | `existing` | 不适用 | 用户回复「B」：大门独立勾选；覆盖 AC5 字面前置 |
| SRC-INDEX | `site/docs/design/kb-auth/INDEX.md` | `existing` | `234b9a15a677d6d0f2fccdba329bfc1a0adda041aaeb0c0264a7a6a677307657` | 已挂验证版、草稿与审查报告 |
| SRC-DRAFT | `site/docs/design/kb-auth/steps-draft.md` | `existing` | `04084933604275c406b92fe2ae23b71f0a614904bd03ae0351505af99485aee8` | 原文保留，本文件不覆盖 |
| SRC-API | `site/kb-api/app/main.py` | `existing` | `cb8b1fb47eff42e6bf8ff3ba1feae8ef2a316e99d97dcf9bcf7629cc5cc9124e` | `auth_passthrough` L69–72；`GET/PUT config` L104–112；`GET /rounds` L141–148；`GET /rounds/{id}` L151–156；`heatmap` L188–196；`ask` L415–426；`_ask_events` L232 从请求体取 `user_id` |
| SRC-SQL | `site/kb-api/sql/init.sql` | `existing` | `81e9fc2b8a74c7555151098444c31167d90d84a07bdbcd6d4eb3999d635a667d` | 仅 `qa_rounds` |
| SRC-LOGS | `site/kb-api/app/logs.py` | `existing` | `486de6261d4a30583a85c7ef9736f36a2edabf9ee2d53cfa567889c6168ba441` | `insert_running`；`set_feedback` 无提问人校验；`ensure_feedback_columns` L119–144 |
| SRC-HTML | `site/feature-interaction/index.html` | `existing` | `aa238fca35d117734db1ffb8b29f74b56cba9fd1310b399ac9d878851ed29982` | 四 Tab；`#qaTopActions` L38–44 健康灯+四钮 |
| SRC-QA-JS | `site/feature-interaction/qa.js` | `existing` | `30e5389e3eea73435a0c85f4d109b700ef74ff6fa608cb50e829a5d5d768d130` | `CONV_KEY` L7；`MAX_CONVS=40` L8；`CHIP_FIXED` L16–32；`user_id: null` L787–790；`refreshHeatChips` L352–376 |
| SRC-APP | `site/feature-interaction/app.js` | `existing` | `62707bc3fe79f7a0d281c9633e76a7eb32b4f512983d72085de89b2d0662d53f` | 关系图；无 `/api/kb` |
| SRC-KB-JS | `site/feature-interaction/kb.js` | `existing` | `803e4228d906b0f65a3d5f49ed5cffa91cd0a2172460d096b652fb30a0ed8efc` | 文档索引；无 kb-api 鉴权 |
| SRC-NGINX | `site/docker/nginx.conf` | `existing` | `61e81c8bfb90bfe4a2a53e6399a934340df383cda9e9d803b30b9f8141ceb1e2` | 仅 `listen 80`；`/api/kb/` 反代 |
| SRC-COMPOSE | `site/docker-compose.yml` | `existing` | `e932cada76d72f86ae61393531e9e94bd738dd6479a5d147508d480c52044ef7` | `127.0.0.1:${HAYYO_WEB_PORT:-18765}:80`；无 `0.0.0.0`；无 443 |
| SRC-CONTRACT | `site/kb-api/tests/test_site_contract.py` | `existing` | `f7983d5bca9ad078f9b19545f4e26003e988398bd7f36daf34de089aa9c369ad` | L12–14 四 Tab **有序**相等；L19–22 四钮存在；L34 无 `0.0.0.0` |
| SRC-FB-TEST | `site/kb-api/tests/test_feedback.py` | `existing` | `3e752b124f48426e8cae456a41e8b2008fe39f96e3f64c363642ce34b4d52414` | 无 Session 测 feedback |
| SRC-REQ | `site/kb-api/requirements.txt` | `existing` | `fb0c751887f3a9929de17c10ece87ac14d7de16a9ed353ef0462d3404e87fefc` | `cryptography==44.0.2` |
| SRC-ENV | `site/.env.example` | `existing` | `98436d3469db2522efa6515217c7f813070600a02fbcd3c91215b18b58f27bf6` | 无引导超管变量 |
| SRC-PYTEST | `site/kb-api/pytest.ini` | `existing` | `b160d82f7811555051f8966d8e02750a985227c1d022208c784e606946f2eada` | `testpaths = tests` |
| SRC-PIPELINE | `site/kb-api/app/pipeline.py` | `existing` | `6c48d9b9549b5a5405a57a84fc0c2152e03349af4861e49612e27f2f5e9a999f` | 本期不改 |
| SRC-INDEXER | `site/kb-api/app/indexer.py` | `existing` | `f5a7d9639f892c43c62f69691bbd7b1afdb3ef72c918c5ea074325d5c074bfd7` | 本期不改 |
| SRC-V3 | `site/docs/design/kb-qa/PRD-知识问答-v3.md` | `existing` | `2e746809407c2d72aaec69935fb1e1d2f96e9763679d9f92cf5fcaf942729144` | **不改正文** |
| SRC-FB-PRD | `site/docs/design/kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md` | `existing` | `1923bb41a8520401cd34eab9fc36f4050a194a7185d91d157b360eaae4c4fc59` | **不改正文** |

**发现门（落地后回写；未实施项仍 `PLANNED`）：**

- 表名 / Cookie / 引导变量 / 登录路径：`existing`。表 `kb_roles`、`kb_role_permissions`、`kb_accounts`、`kb_sessions`、`kb_login_locks`、`kb_audit_logs`、`kb_conversations`；Cookie `hayyo_kb_sid`；`KB_BOOTSTRAP_USER` / `KB_BOOTSTRAP_PASSWORD`；`POST /api/kb/auth/login|logout`、`GET /api/kb/auth/me`、`POST /api/kb/auth/password`；会话 CRUD `GET/POST /api/kb/conversations`、`GET/PUT/DELETE /api/kb/conversations/{id}`。nginx 仍用现网 `location /api/kb/`。管理入口 URL `existing`：`/kb-admin/`（nginx `auth_request` → `GET /api/kb/auth/admin-gate`）。证书保存目录为 `DATA_DIR`，开关文件 `https.enabled`；compose 变量 `HAYYO_WEB_PORT` / `HAYYO_TLS_PORT`（默认 18765 / 18769）。
- 已有 MySQL 卷补新表：`existing`。`AuthStore.ensure_schema()`，模式同 `ensure_feedback_columns`。
- 密码 KDF：`existing`。`pbkdf2_sha256`（`cryptography` PBKDF2-HMAC-SHA256）。
- Cookie `SameSite=Lax` / `Path=/` / `Secure` 仅 HTTPS：`existing`。HttpOnly + 绝对 7 天 + 不用 JWT 仍成立。
- `GET /api/kb/health`：`existing`。不须登录（保留 `#qaHealth` 匿名可读）；问答登录墙在 STEP-005。
- Origin 校验、IP 限流：T3 💡，非验收项。
- 本机 HTTPS 宿主端口 `18768`、`HAYYO_TLS_PORT`：T5 💡。
- M1 已有 `RUNTIME`（宿主 18765）。compose 端口正则与变量字面量：实施 STEP-016 时以 pytest 实测为准。

启动命令（`REPO_BASELINE`）：`site/` 下 `docker compose up -d`；或仓库根 `docker compose -f site/docker-compose.yml up -d`。pytest：`site/kb-api` 按 `pytest.ini`。

## 对象比较约定

比较**同一输入快照**。PRD 未要求顺序时不增加产品顺序断言。现网契约测试对四 Tab 使用有序相等，那是 `CONTRACT` 回归，不是新的产品规则。

| 符号 | 定义 | 来源 |
|---|---|---|
| `MAIN_TABS` | 文案多重集 {「客户端 ↔ 后台」,「客户端交叉」,「文档索引」,「知识问答」} | SRC-HTML；CSTR-018 |
| `MAIN_TABS_SEQ` | 现网契约 `labels ==` 有序列表（仅 STEP-008 改测试时**保持**该断言，不升格为 PRD 顺序需求） | SRC-CONTRACT L12–14 |
| `TOP_OPS_FOUR` | `#qaTopActions` 内 `data-qa-reindex`、`data-qa-config`、`data-qa-rounds`、`data-qa-heatmap` 属性集合 | SRC-HTML L40–43；AC7 |
| `QA_HEALTH` | `#qaHealth` 元素存在 | C3；RQ-10 |
| `ACCOUNT_MENU` | 已登录时账号菜单可见文案多重集 {「退出」,「修改密码」} | RQ-18；AC17 |
| `ADMIN_ENTRY` | 顶栏「进管理模块」入口节点。有「进管理模块」权限：集合大小 1；无该权限：空集（无入口） | F9；E2；`USER_DECISION` B |
| `AUTH_COOKIE` | 登录成功响应 `Set-Cookie` 含 `HttpOnly`；响应体与环境变量无 JWT | C8 |
| `ME_ID` | 当前 Session 对应账号稳定标识（路径 `PLANNED`）。比较键：该标识字符串 | F1 |
| `SESSION_DEAD` | 同一 Cookie 再调须登录接口，HTTP 状态 ∈ {401} | C13；AC6；AC17；AC18 |
| `LOCK_RULE` | 同一用户名失败计数：第 5 次失败后锁定 15 分钟；第 6 次即使密码正确状态 ∈ {401}。比较同一 `username` 字符串，不是 IP | C14；AC13 |
| `LOCK_LEAK` | 密码错误与锁定中的可见文案不得分成「用户不存在」vs「密码错误」两套；锁定文案含「稍后重试」语义（PRD E3，不另造第三套产品句） | E3 |
| `PERM_CHECKBOX` | 知识问答、进管理模块、配置、重建、问答明细、功能热度、对话审计、健康、操作审计、反馈汇总 | §6.1 |
| `PERM_SUPER_ONLY` | 开户 / 改角色 / 改角色权限 / 证书 / 解锁登录锁定 | §6.1 |
| `ROLE_MINGXI` | 自定义角色勾选集合 **恰好** {进管理模块, 问答明细} | `USER_DECISION` B；AC5 |
| `ROLE_USER` | 预置普通用户勾选集合 **恰好** {知识问答} | C4 |
| `OPS_READ_WRITE` | 路径集合 {`PUT /api/kb/config`, `GET /api/kb/config`, `POST /api/kb/reindex`, `GET /api/kb/rounds`, `GET /api/kb/rounds/{id}`} | F8；G2；SRC-API |
| `STATUS_DENY` | HTTP 状态 ∈ {401, 403} | AC12；E1；E2 |
| `GRAPH_VIEWS` | 未登录可切换 `data-view` ∈ {admin, client, kb} 且对应工作区可见 | AC2；F4 |
| `NO_KB_API_GRAPH` | `app.js` 与 `kb.js` 源码不含 `"/api/kb"`（现网已成立，回归保持） | SRC-APP；SRC-KB-JS |
| `ASK_UNAUTH` | 无 Cookie 的 `POST /api/kb/ask` 状态 ∈ {401}；且该次响应不是成功生成的 SSE `done` | AC3 |
| `QA_LOGIN_WALL` | 未登录打开知识问答 Tab：页内存在用户名与密码输入及提交；`#qaSend` 不发出成功 `ASK_UNAUTH` 所禁的 ask | F3 |
| `ROUND_UID` | `qa_rounds.user_id` = 提问时 `ME_ID`；请求体 `user_id` 被忽略 | F6；CSTR-013 |
| `FB_OWNER` | 同一 `round_id`：提问人 `POST .../feedback` 2xx；用户 B 或仅有明细权限的管理员 → 403 | AC14 |
| `CONV_IDS(u)` | 账号 `u` 云端会话稳定 id 集合 | AC4 |
| `CONV_KEY_IDS` | `localStorage[CONV_KEY]` 中 `conversations[].id` 集合 | SRC-QA-JS L7、L90–99 |
| `CHIP_FIXED` | 4 个 `(title, query)` 元组多重集，文案见下表 | SRC-QA-JS L16–32；AC16 |
| `HEAT_TMPL(name)` | 「{name} 有哪些现行规则？」 | SRC-QA-JS L364 |
| `ITEMS4` | 同一 `GET /api/kb/heatmap` 快照中 `items` 前 `min(4, n)` 个元素的 `feature_id` 序列（沿用现网已排序数组前段，不另定排序） | F14 |
| `CHIP_HEAT` | 文案多重集 `{ HEAT_TMPL(display_name 或 feature_id) \| fid ∈ ITEMS4 }`；非 2xx 或 `n=0` 时为空集 | AC16 |
| `AUDIT_CFG` | 改配置后审计列表存在一行：动作可识别为改配置；可见字段名集合 = 本次 `writable` 的键集合；该行文本不含 API Key / 私钥 / 密码明文 | AC8；F10 |
| `AUDIT_REINDEX` | 点重建后审计列表存在一行：动作可识别为重建；主体为操作者 `ME_ID` | AC8 |
| `DOWN_IDS` | `{ round_id \| qa_rounds.feedback='down' }`（同一快照） | AC9 |
| `SUMMARY_DOWN` | 反馈汇总「被踩」列表的 `round_id` 集合；须 `SUMMARY_DOWN = DOWN_IDS`；点进详情后页上 `round_id` 等于所点项 | AC9 |
| `TLS_HTTP` | 对外仍为 HTTP，无强制跳到 HTTPS | AC10 未启用 |
| `TLS_REDIR` | 标准 80/443 下，HTTP 请求响应跳转到 HTTPS（`Location` scheme 为 https） | AC10 启用子条款 |
| `HOST_443_CLOSED` | 宿主机 443 端口连不上（连接失败/拒绝），即使后台已点启用 | AC11 |
| `CONV_KEY` | `hayyo-kb-qa-conversations-v1` | SRC-QA-JS L7 |
| `MAX_CONVS` | 40 | SRC-QA-JS L8；F5 |
| `SESSION_TTL` | 绝对 7 天 | C8；AC18 |

**`CHIP_FIXED` 四对（title = query，与现网数组一致）**

1. 币商用链接支付帮朋友充金币：付款人能拿 VIP 积分和拉新返利吗？收货人呢？这笔算不算收货人的首充？会不会进充值任务进度？  
2. 币商给用户转了 20000 金币。这笔会进 Billionaires 充值榜吗？算不算用户首充？会不会给用户加 VIP 财富值？  
3. 非 VIP 在语聊房 Game Center 点 Bounty Racing 会怎样？如果这个房间同时开着 Ludo，我关掉数值游戏弹窗后，休闲游戏还在吗？Lord of Olympus 有 VIP 限制吗？  
4. VIP 保级扣的是财富值还是金币？200 金币等于多少财富值？退款怎么扣？

**中间件分档（STEP-004 写死，消除与 005/007/012 的责任重叠）**

| 档 | 未登录 | 已登录无对应勾选 | 负责 STEP |
|---|---|---|---|
| 须登录 | 401 | 由下表权限 STEP 判 403 | 004 中间件 |
| `POST /api/kb/ask` | 401（004） | 无「知识问答」→ 403（005） | 004+005 |
| 会话 CRUD（路径 `PLANNED`） | 401（004） | 只能触达 `CONV_IDS(自己)`（007） | 004+007 |
| `GET /api/kb/heatmap` | 401（004） | 无「知识问答」→ 403（012 chips）；热度**页**另要「功能热度」（012） | 004+012 |
| `OPS_READ_WRITE` | `STATUS_DENY` | 无对应勾选 → 403 | 004 |
| 登录/登出/引导 | 按 F1 | — | 002 |

登录相关路径列入白名单，具体 URL `PLANNED`。

**大门 vs 接口（`USER_DECISION` B，未选「接口也要大门」）**

- 顶栏 `ADMIN_ENTRY`、管理 URL/页面：必须有「进管理模块」，否则无入口或 403。
- `GET /api/kb/rounds` 等页级接口：只按对应 `PERM_CHECKBOX`（问答明细/配置/…），**不**叠加大门。只勾「问答明细」、不勾大门：无管理 UI，curl 仍可能 200。记入非阻断风险 R-API-DOOR。

## 输入清单

### 本期有效需求

F1–F14（P0）。RQ-01～RQ-19。G1–G6。C1–C10、C12–C15。C11 废止。

### 本期有效验收

AC1–AC18。AC5 前置以 `USER_DECISION` B 覆盖原文「只勾问答明细」。

### 未编号约束（CSTR）

与草稿 CSTR-001～024 相同，不重列释义。落点见「约束映射」。

### 决策

C1–C10、C12–C15。C11 不实施按账号勾权限。  
**USER_DECISION B**：进管理大门独立勾选。

### 排除项

OUT-1～OUT-12 与草稿相同。落点见「排除映射」。

### 技术债（PRD T7）

| 项 | 处置 |
|---|---|
| v3 仍写本期不登录 / 顶栏四钮 | 接受；CSTR-011；不改 v3 |
| 反馈 PRD 仍写顶栏不动 | 接受；STEP-008 改现网 |
| 契约测试锁死四钮 | STEP-008：`TOP_OPS_FOUR` 空集 |
| 无网关 / ACME | OUT-6 |

未新造 `TD-*`。

## 功能清单

与草稿相同：账号、问答登录、会话上云、独立管理、审计、反馈汇总、证书手动 HTTPS、compose 80/443。不实施网关、自助注册、JWT、旧对话迁移、检索改口径。

## STEP 总览

| STEP | 标题 | 需求 | 验收 | 前置 |
|---|---|---|---|---|
| STEP-001 | 账号角色会话表与空库引导超管 | F7（引导） | —（AC1 前置） | 无 |
| STEP-002 | 登录登出、7 天 Cookie、失败锁定 | F1、F10（登录成败打点） | AC1（登录/登出接口）、AC13（锁）、AC18 | STEP-001 |
| STEP-003 | 自己改密并作废 Session | F2 | AC17（改密） | STEP-002 |
| STEP-004 | 运维 API 鉴权与中间件分档 | F8（接口）、G2 | AC12 | STEP-001、STEP-002 |
| STEP-005 | 问答登录墙；图/索引匿名 | F3、F4 | AC1（登出后不可问）、AC2、AC3 | STEP-002、STEP-004 |
| STEP-006 | 提问与赞踩身份取 Session | F6 | AC14 | STEP-002、STEP-005 |
| STEP-007 | 云端对话隔离 | F5 | AC4 | STEP-002、STEP-004 |
| STEP-008 | 顶栏去四钮、账号菜单、契约测试 | F2（菜单）、F9 | AC7、AC17（菜单） | STEP-002、STEP-003 |
| STEP-009 | 独立管理模块按角色展示 | F8（UI）、F5（审计全部） | AC5 | STEP-004、STEP-008 |
| STEP-010 | 开户角色、最后超管、禁用踢会话 | F7 | AC6、AC15 | STEP-001、STEP-009 |
| STEP-011 | 超管解锁登录锁定 | F7 | AC13（解锁） | STEP-002、STEP-010 |
| STEP-012 | 热度分层 | F14 | AC16 | STEP-004、STEP-005、STEP-009 |
| STEP-013 | 操作审计列表 | F10 | AC8 | STEP-002、STEP-004、STEP-009 |
| STEP-014 | 反馈汇总 | F11 | AC9 | STEP-006、STEP-009 |
| STEP-015 | 证书保存与启用/关闭 | F12 | AC10（未启用/关闭/坏证书/非标准不跳转） | STEP-010 |
| STEP-016 | compose 80/443 | F13 | AC10（标准端口跳转）、AC11 | STEP-015 |

## 需求映射

| ID | STEP |
|---|---|
| F1 | 002 |
| F2 | 003、008 |
| F3 | 005 |
| F4 | 005 |
| F5 | 007、009 |
| F6 | 006 |
| F7 | 001、010、011 |
| F8 | 004、009 |
| F9 | 008 |
| F10 | 002（打点）、003（打点）、010（打点）、011（打点）、013（列表）、015（打点） |
| F11 | 014 |
| F12 | 015 |
| F13 | 016 |
| F14 | 012 |
| G1 | 005、006 |
| G2 | 004、009 |
| G3 | 007、009 |
| G4 | 016 |
| G5 | CSTR-001（全 STEP 不改 pipeline/indexer/图） |
| G6 | 002、011 |
| RQ-01 | 016 |
| RQ-02 | 005 |
| RQ-03 | 008、009 |
| RQ-04 | 003、010 |
| RQ-05 | 007 |
| RQ-06 | 013、014 |
| RQ-07 | 009 |
| RQ-08 | 002 |
| RQ-09 | 015、016 |
| RQ-10 | 008 |
| RQ-11 | 012 |
| RQ-12 | 010 |
| RQ-13 | 015 |
| RQ-14 | 003、010 |
| RQ-15 | 002 |
| RQ-16 | 002、011 |
| RQ-17 | 010 |
| RQ-18 | 008 |
| RQ-19 | 006 |
| C1 | 016 |
| C2 | 005 |
| C3 | 008、009 |
| C4 | 001、009、010 |
| C5 | 007、009 |
| C6 | 009、013、014 |
| C7 | 009 |
| C8 | 002 |
| C9 | 015、016 |
| C10 | 010 |
| C11 废止 | 010 不在账号上逐项勾选 |
| C12 | 012 |
| C13 | 003、010 |
| C14 | 002、011 |
| C15 | 006 |

## 验收映射

| AC | STEP | 比较键 |
|---|---|---|
| AC1 | 002（登录/登出）、005（登出后不可问） | `AUTH_COOKIE`；`SESSION_DEAD`；`ASK_UNAUTH` / `QA_LOGIN_WALL` |
| AC2 | 005 | `GRAPH_VIEWS`；`NO_KB_API_GRAPH` |
| AC3 | 005 | `ASK_UNAUTH`；`QA_LOGIN_WALL` |
| AC4 | 007 | `CONV_IDS(u)` 两浏览器相等；`CONV_KEY_IDS ∩ CONV_IDS(u) = ∅` |
| AC5 | 009 | `ROLE_MINGXI`；明细 `round_id` 可见；配置/重建无入口且接口 403 |
| AC6 | 010 | 初始密码登录 `ME_ID`；禁用后 `SESSION_DEAD` |
| AC7 | 008 | `TOP_OPS_FOUR = ∅`；`QA_HEALTH` |
| AC8 | 013 | `AUDIT_CFG`；`AUDIT_REINDEX` |
| AC9 | 014 | `SUMMARY_DOWN = DOWN_IDS`；点进 `round_id` 相等 |
| AC10 | 015、016 | `TLS_HTTP` / 关闭 / 坏证书；`TLS_REDIR` 在 016 |
| AC11 | 016 | `HOST_443_CLOSED` |
| AC12 | 004 | `OPS_READ_WRITE` ×（未登录或 `ROLE_USER`）→ `STATUS_DENY` |
| AC13 | 002、011 | `LOCK_RULE`；解锁后正确密码登录 `ME_ID` |
| AC14 | 006 | `FB_OWNER` 同一 `round_id` |
| AC15 | 010 | 最后一名启用超管禁用/改角色 → 拒绝（不编造文案） |
| AC16 | 012 | `CHIP_FIXED`；`CHIP_HEAT`；热度页无入口 |
| AC17 | 003、008 | `ACCOUNT_MENU`；改密后 `SESSION_DEAD` |
| AC18 | 002 | 满 7 天 `SESSION_DEAD` |

E1→004/005；E2→004/009；E3→002；E4→010；E5/E8→015；E6→016；E7→CSTR-023；E9→006；E10→010。

## 约束映射

| CSTR | STEP / 处置 |
|---|---|
| 001 | 全 STEP 不改 pipeline/indexer/图逻辑 |
| 002 | 009 不套 admin-skin；不写 `prd/design/admin` |
| 003 | 001 无自助注册 |
| 004 | 001 `tenant_id` 可空 |
| 005 | 002 无 JWT |
| 006 | 015/016 无网关/ACME/后台改端口 |
| 007 | 007 不导入 `CONV_KEY` |
| 008 | 005 `GRAPH_VIEWS` |
| 009 | 006 不改 feedback 列 |
| 010 | 010 不强制首次改密 |
| 011 | 008 不改 v3/反馈 PRD 文件 |
| 012 | 007 删会话后 `qa_rounds.round_id` 集合仍含旧轮 |
| 013 | 006 `ROUND_UID` |
| 014 | 013 审计表 ≠ `qa_rounds` |
| 015 | 014 只用 `feedback` 列 |
| 016 | 015 不编体积上限 |
| 017 | 015 非标准端口不强制 `TLS_REDIR` |
| 018 | 008 `MAIN_TABS` |
| 019 | 007 `MAX_CONVS` |
| 020 | 016 compose 无 `0.0.0.0` |
| 021 | 010 超管角色锁死 |
| 022 | 001 引导不重复重置 |
| 023 | 006 写库失败仍可答（不改主路径） |
| 024 | 012 `CHIP_FIXED` |

## 排除映射

| ID | 处置 |
|---|---|
| OUT-1 | 不改 `prd/design/auth-login`；无 STEP 实施 App 登录 |
| OUT-2 | STEP-009 不套 admin-skin；不写入 `prd/design/admin/` |
| OUT-3 | STEP-001 无自助注册 |
| OUT-4 | STEP-001 `tenant_id` 可空；无多租户产品 |
| OUT-5 | STEP-002 无 JWT |
| OUT-6 | STEP-015/016 无网关/ACME/后台改端口 |
| OUT-7 | STEP-007 不导入 `CONV_KEY` |
| OUT-8 | 全 STEP 不改 pipeline/indexer/默认 Prompt |
| OUT-9 | STEP-005 图/索引不强制登录 |
| OUT-10 | STEP-006 不改 feedback 表结构、不按人计票 |
| OUT-11 | STEP-010 不强制首次改密 |
| OUT-12 | STEP-008 不改反馈 PRD / v3 正文 |

---

## 完整 STEP 提示词

### [STEP-001] 账号角色会话表与空库引导超管

**阶段状态**：`verified`

**目标**：空库引导出启用中超管；预置 `ROLE_USER`；无自助注册。

**来源映射**：F7（引导）、RQ-04、C4、CSTR-003/022。

**前置依赖**：无。

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `init.sql` `qa_rounds` | `existing` | `REPO_BASELINE` | SRC-SQL | 不删表 |
| `ensure_feedback_columns` | `existing` | `REPO_BASELINE` | SRC-LOGS L119–144 | 已有卷补表模式 |
| 新表名 / 引导变量名 | `existing` | `RUNTIME` | `kb_*` 表；`KB_BOOTSTRAP_USER` / `KB_BOOTSTRAP_PASSWORD` | T2 落地 |
| `cryptography` | `existing` | `REPO_BASELINE` | SRC-REQ L5 | 哈希 |

**输入**：空 MySQL 卷或已有仅 `qa_rounds` 的卷。  
**输出**：存在启用超管；`ROLE_USER` = {知识问答}；再次启动不重置引导密码。

**业务定义**：超管内置全权限、不可删、不可改权限清单（C4）；一账号一角色；无自助注册；引导仅空库一次。

**开发任务**：

1. `CREATE IF NOT EXISTS` 账号体系表；已有卷启动补表。
2. 空库创建超管与 `ROLE_USER`；密码不明文。
3. 无自助注册路由。

**不在范围内**：Cookie（002）；开户 UI（010）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 空库启动 | 存在启用超管；`ROLE_USER` 勾选集合恰好 {知识问答} | AC1 前置 |
| 异常 | 账号表非空后改引导口令重启 | 超管密码哈希不变 | CSTR-022 |
| 边界 | 自助注册路径 | 不存在或 `STATUS_DENY` | CSTR-003 |

**完成标志**：

- [ ] 空库可登录的超管存在（供 002）
- [ ] `qa_rounds` 表仍在
- [ ] 无自助注册
- [ ] 新表名落地后回传 `existing`

**完成回传**：返回 STEP ID、完成/阻断、证据、变更文件、来源变化、下一 STEP。不得自动启动下一 STEP。

---

### [STEP-002] 登录登出、7 天 Cookie、失败锁定

**阶段状态**：`verified`

**目标**：Session + HttpOnly Cookie；绝对 7 天；`LOCK_RULE`；登录成败写入审计存储（列表在 013）。

**来源映射**：F1、RQ-08/15/16、AC1（接口）、AC13（锁）、AC18、F10（登录成败打点）。

**前置依赖**：STEP-001（引导超管可登录）。

**参考路径**：`auth_passthrough` 已由 004 替换；`POST /api/kb/auth/login|logout`、`GET /api/kb/auth/me` `existing`。

**输入**：STEP-001 超管。  
**输出**：`AUTH_COOKIE`；登出 `SESSION_DEAD`；锁定与 7 天过期。

**业务定义**：C8、C14、E3。不用 JWT。

**开发任务**：

1. 登录发 Cookie，登出作废；无 JWT。
2. 按用户名 `LOCK_RULE`；`LOCK_LEAK`。
3. 提供 me 查询（路径 `PLANNED`）→ `ME_ID`。
4. 登录成功/失败各写一条审计（字段谁/何时/动作/IP；无密码）。
5. AC18 用测试时钟，不改产品 TTL。

**不在范围内**：解锁 UI（011）；问答墙 UI（005）；中间件替换（004）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 引导账号正确密码 | `AUTH_COOKIE`；me 返回该 `ME_ID`；登出后须登录接口 `SESSION_DEAD` | AC1 |
| 异常 | 同一用户名 5 次错密后第 6 次正确 | `LOCK_RULE`；`LOCK_LEAK` | AC13；E3 |
| 边界 | 登录满 7 天 | `SESSION_DEAD` | AC18 |

**完成标志**：

- [ ] `AUTH_COOKIE`、无 JWT
- [ ] `LOCK_RULE` 与 `LOCK_LEAK` 成立
- [ ] AC18 `SESSION_DEAD`
- [ ] 登录成败审计行可被 013 读到（不要求本 STEP 做列表 UI）

**完成回传**：同上。

---

### [STEP-003] 自己改密并立即作废 Session

**阶段状态**：`verified`

**目标**：旧密+新密成功后该账号全部 Session `SESSION_DEAD`。不强制首次改密。

**来源映射**：F2、RQ-14、AC17（改密）、C13、F10（改密打点）。

**前置依赖**：STEP-002。

**参考路径**：`POST /api/kb/auth/password` `existing`。

**开发任务**：校验旧密、写新哈希、作废该 `ME_ID` 全部 Session；写审计（无密码明文）；不强制首次改密。

**不在范围内**：菜单 UI（008）；禁用踢会话（010）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 旧密正确改密 | 两路 Cookie 均 `SESSION_DEAD` | AC17 |
| 异常 | 旧密错误 | 哈希不变；原 Session 仍可用 | F2 |
| 边界 | 同账号两个 Session，其一改密 | 两个均 `SESSION_DEAD` | C13 |

**完成标志**：改密成功 → `SESSION_DEAD`；无强制首次改密；审计无密码。

**完成回传**：同上。

---

### [STEP-004] 运维 API 鉴权与中间件分档

**阶段状态**：`verified`

**目标**：替换 `auth_passthrough`；按上文「中间件分档」；`OPS_READ_WRITE` 对未登录与 `ROLE_USER` 为 `STATUS_DENY`。

**来源映射**：F8、G2、AC12、E1、E2。

**前置依赖**：STEP-001、STEP-002。

**参考路径**：SRC-API 上列现网路由全部 `existing`。

**开发任务**：

1. 去掉一律放行；实现分档。白名单仅登录/登出/me（URL `PLANNED`）。
2. `OPS_READ_WRITE`：登录 + 对应勾选（配置/重建/问答明细）。`GET` 与 `PUT` config 都要「配置」；`GET rounds` 与 `GET rounds/{id}` 都要「问答明细」。
3. 未登录打 ask/heatmap/会话 CRUD → 401（本 STEP）；角色 403 由 005/012/007。
4. 因鉴权变红的测试改为带 Session，不得恢复裸奔。

**不在范围内**：页内登录墙（005）；管理 UI（009）；chips 分层细节（012）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 超管调 `OPS_READ_WRITE` | 2xx（语义与现网成功时一致，权限已过） | AC12 对照 |
| 异常 | 未登录调每一条 `OPS_READ_WRITE` | `STATUS_DENY` | AC12；E1 |
| 边界 | `ROLE_USER` 已登录调每一条 `OPS_READ_WRITE` | 403 | AC12；E2 |
| 边界 | 未登录 `POST /api/kb/ask`、`GET /api/kb/heatmap` | 401 | 分档；供 005/012 |

**完成标志**：

- [ ] `OPS_READ_WRITE` × 未登录/`ROLE_USER` → `STATUS_DENY`
- [ ] 未登录 ask、heatmap → 401
- [ ] `pipeline`/`indexer` 未改

**完成回传**：同上。

---

### [STEP-005] 问答登录墙；图/索引匿名

**阶段状态**：`verified`

**目标**：未登录不能完成提问；图/索引匿名可读。承担 AC1「登出后问答不可问」。

**来源映射**：F3、F4、AC1（问答子条款）、AC2、AC3、C2。

**前置依赖**：STEP-002、STEP-004（未登录 ask 已 401）。

**参考路径**：`POST /api/kb/ask` existing；`send` SRC-QA-JS L781–791；`GRAPH_VIEWS` SRC-HTML；`NO_KB_API_GRAPH`。

**开发任务**：

1. 已登录无「知识问答」→ ask 403。
2. 问答 Tab `QA_LOGIN_WALL`。
3. 不给关系图/文档索引加登录。

**不在范围内**：`ROUND_UID`（006）；云端列表（007）；去四钮（008）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 未登录切 admin/client/kb | `GRAPH_VIEWS`；`NO_KB_API_GRAPH` 仍成立 | AC2 |
| 异常 | 未登录 ask 或点发送 | `ASK_UNAUTH`；`QA_LOGIN_WALL` | AC3；E1 |
| 边界 | 已登录后登出再打开问答 | `QA_LOGIN_WALL`；ask `ASK_UNAUTH` | AC1 |

**完成标志**：`GRAPH_VIEWS`；`ASK_UNAUTH`；`QA_LOGIN_WALL`；`MAIN_TABS` 不变。

**完成回传**：同上。

---

### [STEP-006] 提问与赞踩身份取 Session

**阶段状态**：`verified`

**目标**：`ROUND_UID`；`FB_OWNER`；不改 feedback 列。

**来源映射**：F6、RQ-19、AC14、C15、CSTR-013。

**前置依赖**：STEP-002、STEP-005。

**参考路径**：`_ask_events` L232；`set_feedback` L146–166；`test_feedback.py`。

**开发任务**：ask 身份只来自 Session；feedback 校验 `qa_rounds.user_id`；更新 SRC-FB-TEST；写库失败仍可答（CSTR-023）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | A 提问 | 该轮 `ROUND_UID` = A 的 `ME_ID`；A 可赞/踩/取消 | F6 |
| 异常 | 同一 `round_id`，B 或管理员 `POST feedback` | 403 | AC14；E9 |
| 边界 | 请求体伪造他人 `user_id` | 落库仍为 Session `ME_ID` | CSTR-013 |

**完成标志**：`ROUND_UID`；`FB_OWNER`；feedback 列结构未改。

**完成回传**：同上。

---

### [STEP-007] 云端对话隔离，不迁 localStorage

**阶段状态**：`verified`

**目标**：`CONV_IDS(u)` 跨浏览器相等；不导入 `CONV_KEY`；上限 40；删会话不删 `qa_rounds`。

**来源映射**：F5、RQ-05、AC4、CSTR-007/012/019。

**前置依赖**：STEP-002、STEP-004（会话 CRUD 未登录 401）。

**参考路径**：`CONV_KEY`/`MAX_CONVS` existing；CRUD 路径 `planned`。

**开发任务**：按 `ME_ID` 隔离 CRUD；登录后列表权威为云端；不把 `CONV_KEY_IDS` 写入云端。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 普通用户两浏览器各登录 | `CONV_IDS(u)` 相等 | AC4 |
| 异常 | 浏览器有旧 `CONV_KEY` | `CONV_KEY_IDS ∩ CONV_IDS(u) = ∅` | AC4 |
| 边界 | 删一条云端会话 | 该 id ∉ `CONV_IDS(u)`；其下 `qa_rounds.round_id` 仍在库 | CSTR-012 |
| 边界 | 会话数 | ≤ `MAX_CONVS` | CSTR-019 |

**完成标志**：AC4 两集合断言；未导入 `CONV_KEY`。

**完成回传**：同上。

---

### [STEP-008] 问答顶栏去四钮、账号菜单、契约测试

**阶段状态**：`verified`

**目标**：`TOP_OPS_FOUR = ∅`；`QA_HEALTH`；`ACCOUNT_MENU`；有大门权限才有 `ADMIN_ENTRY`。

**来源映射**：F9、F2（菜单）、RQ-10/18、AC7、AC17（菜单）、CSTR-011/018。

**前置依赖**：STEP-002、STEP-003。

**参考路径**：SRC-HTML L38–44；SRC-CONTRACT L19–22；管理 URL `planned`。

**开发任务**：

1. 去掉四钮，保留 `#qaHealth`。
2. 菜单文案多重集 = `ACCOUNT_MENU`。
3. `ADMIN_ENTRY`：有「进管理模块」为 1，否则空集。
4. 契约：四钮不存在；保持 `MAIN_TABS_SEQ`（现网有序，不升格为产品顺序）。
5. 不改 v3 / 反馈 PRD 文件。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 任意访客问答顶栏 | `TOP_OPS_FOUR = ∅`；`QA_HEALTH` | AC7 |
| 正常 | 已登录点/悬停账号 | `ACCOUNT_MENU` | AC17 |
| 边界 | `ROLE_USER` | `ADMIN_ENTRY = ∅` | F9；B |
| 边界 | `ROLE_MINGXI` | `ADMIN_ENTRY` 大小 1 | B |
| 回归 | pytest 契约 | 无四钮；`MAIN_TABS_SEQ` 仍过 | AC7；CSTR-018 |

**完成标志**：`TOP_OPS_FOUR = ∅`；`ACCOUNT_MENU`；v3 与反馈 PRD 未改。

**完成回传**：同上。

---

### [STEP-009] 独立管理模块按角色展示

**阶段状态**：`verified`

**目标**：大门 = 「进管理模块」。`ROLE_MINGXI` 能进并看明细，不能改配置/重建。不套 admin-skin。对话审计页要「对话审计」勾选。

**来源映射**：F8、F5、RQ-07、AC5、C7、`USER_DECISION` B。

**前置依赖**：STEP-004、STEP-008。

**参考路径**：qa.js overlay；nginx 无管理 location → `planned`。

**业务定义**：独立入口；按勾选展示内页；证书/解锁仅超管；B：无大门则无入口或管理 URL 403。

**开发任务**：

1. nginx 管理 location（路径 `PLANNED`）；自做页面。
2. 无「进管理模块」：`ADMIN_ENTRY = ∅`；管理 URL 403。
3. 迁出 overlay 的配置/重建/明细/热度，不改默认 Prompt 语义。
4. 「对话审计」可看全部云端会话 id 集合；无该勾选不能得到他人 `CONV_IDS`。

**不在范围内**：开户 CRUD 验收（010）；审计列表数据（013）；汇总算法（014）；证书（015）。可留入口位。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | `ROLE_MINGXI` 进管理 | 明细页 `round_id` 集合含已知样本；无配置/重建入口；`PUT config` 与 `POST reindex` → 403 | AC5 |
| 异常 | 无「进管理模块」（含只勾问答明细）打开管理 URL | 403；`ADMIN_ENTRY = ∅` | E2；B |
| 边界 | 有「对话审计」 | 可见的会话 id 集合为全站云端 id；`ROLE_USER` 不能 | F5 |

**完成标志**：`ROLE_MINGXI` 满足 AC5 比较；未引用 admin-skin。

**完成回传**：同上。

---

### [STEP-010] 超管开户角色、最后一名超管、禁用踢会话

**阶段状态**：`verified`

**目标**：仅超管开户/改角色/改角色权限；可多名超管；不能去掉最后一名启用超管；禁用 → `SESSION_DEAD`。不在账号上逐项勾权限（C11 废止）。

**来源映射**：F7、RQ-12/17、AC6、AC15、C4、C10、C13、CSTR-010/021、F10（开户/改角色打点）。

**前置依赖**：STEP-001、STEP-009。

**开发任务**：超管指定初始密码；一账号一角色；禁用作废 Session；拦截最后一名启用超管；角色勾选只用 `PERM_CHECKBOX`。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 开户指定初始密码赋 `ROLE_USER` | 该密码登录得 `ME_ID`；不必先改密 | AC6；CSTR-010 |
| 异常 | 禁用时其 Cookie 仍在 | `SESSION_DEAD` | AC6；E4 |
| 边界 | 仅一名启用超管，禁用或去掉超管角色 | 拒绝；启用超管人数仍 ≥ 1 | AC15；E10 |

**完成标志**：AC6 `ME_ID` + `SESSION_DEAD`；AC15 人数不变；无按账号勾权限。

**完成回传**：同上。

---

### [STEP-011] 超管后台解锁登录锁定

**阶段状态**：`verified`

**目标**：超管清失败次数；解锁后立即可以登录。

**来源映射**：F7、RQ-16、AC13（解锁）、C14、F10（解锁打点）。

**前置依赖**：STEP-002、STEP-010。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 某 `username` 已锁定，超管解锁 | 正确密码 → `ME_ID` | AC13 |
| 异常 | `ROLE_USER` 调解锁 | 403 | E2 |
| 边界 | 超管 A 被锁，超管 B 解锁 | A 可登录 | RQ-12 |

**完成标志**：解锁后同一 `username` 登录成功；非超管 403。

**完成回传**：同上。

---

### [STEP-012] 热度分层：chips 与管理页

**阶段状态**：`verified`

**目标**：登录且有知识问答可读 heatmap 作 chips；热度页要「功能热度」。未登录不展示 `CHIP_HEAT`。

**来源映射**：F14、RQ-11、AC16、C12、CSTR-024。

**前置依赖**：STEP-004、STEP-005、STEP-009。

**参考路径**：`GET heatmap`；`CHIP_FIXED`；`refreshHeatChips`；不改 `logs.heatmap` 公式。

**开发任务**：chips 用登录+知识问答；管理页要「功能热度」；未登录不请求或 `CHIP_HEAT=∅`；不改公式与 `CHIP_FIXED` 文案。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | `ROLE_USER` 已登录空状态 | 空状态 chips 含 `CHIP_FIXED` 四对；另加 `CHIP_HEAT`（最多 4） | AC16 |
| 异常 | 该用户进热度管理页 | 无入口或 403 | AC16 |
| 边界 | 未登录 | `CHIP_HEAT=∅`；不能靠热度 chip 发出成功 ask | F14 |

**完成标志**：`CHIP_FIXED` 四对相等；`CHIP_HEAT` 按 `ITEMS4`；公式未改。

**完成回传**：同上。

---

### [STEP-013] 操作审计列表

**阶段状态**：`verified`

**目标**：独立审计存储可筛列表。AC8 用 `AUDIT_CFG` / `AUDIT_REINDEX`。与 `qa_rounds` 分家。

**来源映射**：F10、RQ-06、AC8、CSTR-014。

**前置依赖**：STEP-002（登录成败已打点）、STEP-004（配置/重建接口）、STEP-009（审计页）。

**开发任务**：独立表（名 `PLANNED`）；列表要「操作审计」勾选；配置只展示字段名。登录/改密/开户/解锁/证书行由各 STEP 打点，本 STEP 能列出。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 超管改配置 | `AUDIT_CFG` | AC8 |
| 正常 | 超管重建 | `AUDIT_REINDEX` | AC8 |
| 异常 | 无「操作审计」 | 无入口、403 | F8 |
| 边界 | 读改密/解锁行 | 无密码明文 | F10 |

**完成标志**：`AUDIT_CFG` 与 `AUDIT_REINDEX`；审计存储 ≠ `qa_rounds`。

**完成回传**：同上。

---

### [STEP-014] 反馈汇总

**阶段状态**：`verified`

**目标**：`SUMMARY_DOWN = DOWN_IDS`；无新采集口。

**来源映射**：F11、AC9、CSTR-015。

**前置依赖**：STEP-006、STEP-009。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 库内有 up/down | 被踩列表 `SUMMARY_DOWN = DOWN_IDS`；点进详情 `round_id` 相等 | AC9 |
| 异常 | 无「反馈汇总」 | 无入口、403 | F8 |
| 边界 | 页面 | 无新的赞踩采集控件 | AC9 |

**完成标志**：集合等式；`feedback` 列未改结构。

**完成回传**：同上。

---

### [STEP-015] 证书保存与手动启用/关闭 HTTPS

**阶段状态**：`verified`

**目标**：仅超管上传/挂载；上传不启用；坏证书不切换协议；可关闭回 HTTP。非标准端口不强制跳转。标准 80/443 跳转在 016。

**来源映射**：F12、RQ-13、AC10（未启用/关闭/坏证书/非标准）、E5、E8、CSTR-016/017、F10（证书打点）。

**前置依赖**：STEP-010。

**参考路径**：nginx `listen 80` existing；证书 API/卷 `planned`。

**开发任务**：PEM 保存、私钥不回显；启用前校验；关闭回 HTTP；不实现 ACME/后台改端口；不编体积上限。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 上传不启用 | `TLS_HTTP` | AC10 |
| 正常 | 启用后再关闭 | 回到 `TLS_HTTP` | AC10 |
| 异常 | 坏证书点启用 | 协议不变；失败原因可见（不编造固定句） | E5 |
| 边界 | 本机非 80/443 点启用 | 不强制 `TLS_REDIR` | CSTR-017 |
| 边界 | 非超管 | 403 | RQ-13 |

**完成标志**：`TLS_HTTP` 三态（未启用/关闭/坏证书维持）；无私钥回显。

**完成回传**：同上。

---

### [STEP-016] compose 80/443 与后台改不了端口

**阶段状态**：`verified`

**目标**：`.env`/compose 可映射 80 与 443；正文无 `0.0.0.0`；后台改不了端口。承担 AC10 `TLS_REDIR` 与 AC11。

**来源映射**：F13、RQ-01/09、AC10（标准跳转）、AC11、CSTR-020、E6。

**前置依赖**：STEP-015（启用开关已存在）。

**参考路径**：SRC-COMPOSE ports；SRC-CONTRACT L29–41；SRC-ENV。TLS 变量名 `planned`。

**开发任务**：变量映射 80/443；默认本机 loopback 不丢；后台无端口面板；契约继续禁止 `0.0.0.0`；端口正则按实测修正。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 本机默认 compose | `127.0.0.1:18765` HTTP 仍可登录问答 | F13；C1 |
| 正常 | 已映射 80/443 且 015 已启用 | `TLS_REDIR` | AC10 |
| 异常 | 未映射宿主机 443，仅后台启用 | `HOST_443_CLOSED` | AC11 |
| 边界 | compose 正文 | 不含 `0.0.0.0`；MySQL/Qdrant 仍 127.0.0.1 | CSTR-020 |

**完成标志**：`TLS_REDIR`（标准端口环境）；`HOST_443_CLOSED`（未映射环境）；无 `0.0.0.0`。

**完成回传**：同上。

---

## 进度区块

> 路径：本验证版内。  
> PRD：`PRD-账号体系与管理模块-v2.md`  
> STEP 来源：`steps-verified.md`  
> 阶段结果：`PASS_WITH_RISKS`  
> 执行记录：`execution/账号体系与管理模块开发执行记录.md`

| 完成数 | 总数 | 当前状态 |
|---|---|---|
| 16 | 16 | M1–M4 已验收；正式契约 `site/docs/contracts/kb-auth/` |

| STEP | 状态 | 证据 |
|---|---|---|
| STEP-001 | `VERIFIED` | 空库/已有卷引导超管；`ROLE_USER`={知识问答}；重启不重置哈希；无自助注册；`qa_rounds` 仍在 |
| STEP-002 | `VERIFIED` | `hayyo_kb_sid` HttpOnly 无 JWT；5 次失败后第 6 次锁定；测试时钟 7 天 `SESSION_DEAD`；登录成败审计无密码 |
| STEP-003 | `VERIFIED` | 改密后两路 Session 401；错误旧密哈希不变；无强制首次改密 |
| STEP-004 | `VERIFIED` | 未登录 OPS 401；`ROLE_USER` 403；未登录 ask/heatmap 401；未改 pipeline/indexer |
| STEP-005 | `VERIFIED` | 登录墙；图/索引匿名；无知识问答 ask 403 |
| STEP-006 | `VERIFIED` | `ROUND_UID` 取 Session；赞踩仅提问人 |
| STEP-007 | `VERIFIED` | 云端会话按账号隔离；不导入 CONV_KEY |
| STEP-008 | `VERIFIED` | 顶栏无四钮；账号菜单退出/改密；契约 `MAIN_TABS_SEQ` |
| STEP-009 | `VERIFIED` | `/kb-admin/`；无大门 403；`ROLE_MINGXI` 明细可看、配置/重建 403 |
| STEP-010 | `VERIFIED` | 开户初始密码得 `ME_ID`；禁用 `SESSION_DEAD`；最后超管不可去 |
| STEP-011 | `VERIFIED` | 超管解锁后可登录；`ROLE_USER` 403 |
| STEP-012 | `VERIFIED` | `CHIP_FIXED` 四对；未登录不请求热度；热度页要「功能热度」 |
| STEP-013 | `VERIFIED` | `AUDIT_CFG`/`AUDIT_REINDEX`；`kb_audit_logs` ≠ `qa_rounds` |
| STEP-014 | `VERIFIED` | 被踩列表 = down 的 round_id；无新采集口 |
| STEP-015 | `VERIFIED` | 上传不启用；坏证书不切协议；关闭回 HTTP；非超管 403 |
| STEP-016 | `VERIFIED` | compose 变量映射 80/443；默认 18765 HTTP；宿主机 443 未映射连不上 |

## 自检

- [x] F/RQ/G/C/CSTR/OUT/AC 均有落点
- [x] AC5 前置为 `USER_DECISION` B，未 silently 改 PRD 文件
- [x] 比较键已写（集合/多重集/状态码集合）
- [x] 未新造 `TD-*` / 业务字段
- [x] `existing` 绑定 source_id 与 locator
- [x] 未自称无风险或已开始开发

## 非阻断风险

1. 契约测试现网仍断言四钮；008 必须改。
2. 已有 MySQL 卷不重跑 `init.sql`。
3. compose 端口正则可能不匹配变量写法；无 RUNTIME。
4. `test_feedback.py` 无 Session。
5. T 节路径/表名/Cookie 名 💡。
6. v3 / 反馈 PRD 旧口径残留，不改文件。
7. 非标准端口不强制跳转。
8. **R-API-DOOR**：B 不叠加「大门」到 `GET /rounds` 等页级接口；只勾明细、不勾大门时 curl 可能 200。
9. `GET /health` 鉴权 `PLANNED`。
10. SRC-INDEX SHA 在 INDEX 再改后会过期，实施不依赖该哈希。
