---
title: "文档工作台账号体系与管理模块 STEP 草稿"
status: "draft"
stage_result: "PASS_WITH_RISKS"
prd: "site/docs/design/kb-auth/PRD-账号体系与管理模块-v2.md"
prd_sha256: "b005262b4e8b97d5acd99d37349a0a96c246ef940ea58208c0422239dfdedd4a"
created: "2026-09-19"
note: "本文件是草稿，未经 step-doc-review 完整复审前不得当作已验证或可执行计划。不宣布 STEPS_VERIFIED，不生成里程碑，不开始开发。"
---

# 文档工作台账号体系与管理模块 STEP 草稿

> **现行权威**：[`PRD-账号体系与管理模块-v2.md`](PRD-账号体系与管理模块-v2.md)（status=已确认）。  
> **独立增量**：不替代 [`../kb-qa/PRD-知识问答-v3.md`](../kb-qa/PRD-知识问答-v3.md)、[`../kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md`](../kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md)。检索 / 重排 / 生成 / 关系图 / 文档索引阅读口径不因本专题改写。  
> **v1 不读**：`history/PRD-账号体系与管理模块-v1.md` 不是实施依据。  
> 宿主：http://127.0.0.1:18765/feature-interaction/ 。实现状态：未实施。  
> 本文件 **draft**。不得当作 `steps-verified.md`。

## 来源摘要

事实标签只用：`USER_DECISION`、`PRD`、`CONTRACT`、`REPO_BASELINE`、`RUNTIME`、`PLANNED`、`UNVERIFIED`。本轮无 `RUNTIME`。本轮无独立 `contract.md`；契约测试见 SRC-CONTRACT。

| source_id | 路径 | 状态 | SHA-256 | 本轮核实 |
|---|---|---|---|---|
| SRC-PRD | `site/docs/design/kb-auth/PRD-账号体系与管理模块-v2.md` | `existing` | `b005262b4e8b97d5acd99d37349a0a96c246ef940ea58208c0422239dfdedd4a` | 全文；G1–G6；F1–F14；C1–C15；RQ-01～RQ-19；AC1–AC18；E1–E10；T1–T7；无阻塞待确认 |
| SRC-INDEX | `site/docs/design/kb-auth/INDEX.md` | `existing` | `0cc21e38a378cd8e144096af545e4a5f3cb5fde96fdca5126b97841032eac663` | 本夹唯一现行 PRD；拆解时尚无 steps 文件 |
| SRC-API | `site/kb-api/app/main.py` | `existing` | `cb8b1fb47eff42e6bf8ff3ba1feae8ef2a316e99d97dcf9bcf7629cc5cc9124e` | `auth_passthrough` L69–72 一律放行；路由 health/config/reindex/rounds/feedback/heatmap/ask；`_ask_events` L232 从请求体取 `user_id` |
| SRC-SQL | `site/kb-api/sql/init.sql` | `existing` | `81e9fc2b8a74c7555151098444c31167d90d84a07bdbcd6d4eb3999d635a667d` | 仅 `qa_rounds`；`user_id`/`owner_id`/`tenant_id`/`role` 可空；`feedback`/`feedback_at` 已有；无账号表 |
| SRC-LOGS | `site/kb-api/app/logs.py` | `existing` | `486de6261d4a30583a85c7ef9736f36a2edabf9ee2d53cfa567889c6168ba441` | `insert_running` 写入四身份字段；`set_feedback` 无提问人校验；`ensure_feedback_columns` 给已有卷补列 |
| SRC-HTML | `site/feature-interaction/index.html` | `existing` | `aa238fca35d117734db1ffb8b29f74b56cba9fd1310b399ac9d878851ed29982` | 四 Tab；`#qaTopActions` 含健康灯 + `data-qa-reindex/config/rounds/heatmap` |
| SRC-QA-JS | `site/feature-interaction/qa.js` | `existing` | `30e5389e3eea73435a0c85f4d109b700ef74ff6fa608cb50e829a5d5d768d130` | `CONV_KEY`；`MAX_CONVS=40`；ask 固定 `user_id: null`；overlay 打开配置/重建/明细/热度；`GET /heatmap` 做 chips |
| SRC-APP | `site/feature-interaction/app.js` | `existing` | `62707bc3fe79f7a0d281c9633e76a7eb32b4f512983d72085de89b2d0662d53f` | 关系图；无 `/api/kb` |
| SRC-KB-JS | `site/feature-interaction/kb.js` | `existing` | `803e4228d906b0f65a3d5f49ed5cffa91cd0a2172460d096b652fb30a0ed8efc` | 文档索引读静态文档；无 kb-api 鉴权依赖 |
| SRC-NGINX | `site/docker/nginx.conf` | `existing` | `61e81c8bfb90bfe4a2a53e6399a934340df383cda9e9d803b30b9f8141ceb1e2` | 仅 `listen 80`；`location /api/kb/` 反代；无管理入口 location、无 TLS |
| SRC-COMPOSE | `site/docker-compose.yml` | `existing` | `e932cada76d72f86ae61393531e9e94bd738dd6479a5d147508d480c52044ef7` | `127.0.0.1:${HAYYO_WEB_PORT:-18765}:80`；MySQL/Qdrant 同绑 127.0.0.1；正文无 `0.0.0.0`；无 443 |
| SRC-CONTRACT | `site/kb-api/tests/test_site_contract.py` | `existing` | `f7983d5bca9ad078f9b19545f4e26003e988398bd7f36daf34de089aa9c369ad` | 断言顶栏四钮仍在；compose 正文不含 `0.0.0.0`；端口抽取正则 `127.0.0.1:\d+:\d+` |
| SRC-FB-TEST | `site/kb-api/tests/test_feedback.py` | `existing` | `3e752b124f48426e8cae456a41e8b2008fe39f96e3f64c363642ce34b4d52414` | 无 Session 测 `POST .../feedback` |
| SRC-REQ | `site/kb-api/requirements.txt` | `existing` | `fb0c751887f3a9929de17c10ece87ac14d7de16a9ed353ef0462d3404e87fefc` | 已有 `cryptography==44.0.2` |
| SRC-ENV | `site/.env.example` | `existing` | `98436d3469db2522efa6515217c7f813070600a02fbcd3c91215b18b58f27bf6` | 无引导超管变量；有 `HAYYO_WEB_PORT` 等 |
| SRC-PYTEST | `site/kb-api/pytest.ini` | `existing` | `b160d82f7811555051f8966d8e02750a985227c1d022208c784e606946f2eada` | `testpaths = tests` |
| SRC-PIPELINE | `site/kb-api/app/pipeline.py` | `existing` | `6c48d9b9549b5a5405a57a84fc0c2152e03349af4861e49612e27f2f5e9a999f` | 本轮只读；本期不改 |
| SRC-INDEXER | `site/kb-api/app/indexer.py` | `existing` | `f5a7d9639f892c43c62f69691bbd7b1afdb3ef72c918c5ea074325d5c074bfd7` | 本轮只读；本期不改 |
| SRC-V3 | `site/docs/design/kb-qa/PRD-知识问答-v3.md` | `existing` | `2e746809407c2d72aaec69935fb1e1d2f96e9763679d9f92cf5fcaf942729144` | **不改正文**。RQ-17/D3「本期不登录」、C36 顶栏四钮、C6 localStorage 由本专题覆盖现网行为 |
| SRC-FB-PRD | `site/docs/design/kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md` | `existing` | `1923bb41a8520401cd34eab9fc36f4050a194a7185d91d157b360eaae4c4fc59` | **不改正文**。顶栏四钮以本专题 C3 覆盖 |

**发现门（不填具体值、不宣称已决定）：**

- 新表名、Cookie 名、引导环境变量名、管理入口 URL、新 API 路径：PRD T 节标 💡，不是用户批准的产品名词。实施按已核实项目约定确定（`PLANNED`）。T3 拟议 `POST /api/kb/auth/login` 等仅作候选。
- 已有 MySQL 卷补新表：现网只有 `ensure_feedback_columns`（SRC-LOGS）。挂在 lifespan 或其它启动点按项目约定确定，不得假定重跑 `init.sql`。
- 密码哈希算法：T2 写「现有依赖 `cryptography` + 标准 KDF」（SRC-REQ 已有该包）。具体 KDF 名称 `PLANNED`。
- Cookie `SameSite` / `Path` / `Secure`：T2 💡；已确认的只有 HttpOnly + 绝对 7 天 + 不用 JWT（C8）。
- `GET /api/kb/health` 是否须登录：C3 保留健康灯；T3 写「问答登录后健康灯可用」为 💡。保留灯；接口鉴权按项目约定，不得取消灯。
- 写操作 Origin 校验、按 IP 短期限流：T3 💡，非验收项，不单开 STEP。
- 本机 HTTPS 宿主端口 `18768`、compose 变量名 `HAYYO_TLS_PORT`：T5 💡。
- 本轮未跑 pytest / 未起 Docker：无 `RUNTIME`。SRC-CONTRACT 端口正则与现网 `${HAYYO_WEB_PORT:-18765}` 字面量是否仍匹配，实施时以实测为准。

启动命令（`REPO_BASELINE`，compose 文件头）：在 `site/` 执行 `docker compose up -d`；或仓库根 `docker compose -f site/docker-compose.yml up -d`。pytest：`site/kb-api` 下按 `pytest.ini`。

## 对象比较约定

| 符号 | 定义 | 来源 |
|---|---|---|
| `MAIN_TABS` | 文本多重集 {「客户端 ↔ 后台」,「客户端交叉」,「文档索引」,「知识问答」}，大小 4 | SRC-HTML；SRC-CONTRACT |
| `TOP_OPS_FOUR` | 顶栏 `data-qa-reindex`、`data-qa-config`、`data-qa-rounds`、`data-qa-heatmap` 四钮 | SRC-HTML L40–43；C3；AC7 |
| `CONV_KEY` | `hayyo-kb-qa-conversations-v1` | SRC-QA-JS L7 |
| `MAX_CONVS` | 40 | SRC-QA-JS L8；F5「上限沿用现网 40」 |
| `PERM_CHECKBOX` | 角色上可勾：知识问答、进管理模块、配置、重建、问答明细、功能热度、对话审计、健康、操作审计、反馈汇总 | PRD §6.1 |
| `PERM_SUPER_ONLY` | 写死仅超管、不做勾选项：开户 / 改角色 / 改角色权限 / 证书 / 解锁登录锁定 | PRD §6.1 |
| `CHIP_FIXED` | 空状态常驻 4 条，文案沿用现网 `CHIP_FIXED` | SRC-QA-JS L16–32；F14；反馈 C14 |
| `SESSION_TTL` | 登录绝对 7 天 | C8；RQ-15；AC18 |
| `LOCK_RULE` | 同一用户名连续 5 次失败锁定 15 分钟；锁定期内密码正确也不可登录 | C14；AC13 |

## 输入清单

### 本期有效需求

功能需求 **F1–F14**（PRD §6.1，全部 P0）。确认台账 **RQ-01～RQ-19** 已写入 C/F，另表映射，不改造成新的 `F-*`。

### 本期有效验收

**AC1–AC18**（PRD §8）。

### 未编号约束（CSTR）

| ID | 摘要 | 来源 |
|---|---|---|
| CSTR-001 | 不改检索公式、切块、生成 Prompt 默认值；不改 `pipeline.py` / `indexer.py` / 关系图逻辑 | §4.2；T4 |
| CSTR-002 | 不改 Hayyo App 登录；不写入 `prd/design/admin/`；不套 admin-skin | §4.2；C7 |
| CSTR-003 | 无自助注册；账号只能超管角色生成 | C10；C4 |
| CSTR-004 | 不做多租户产品化；`tenant_id` 可继续空 | §4.2 |
| CSTR-005 | 不用 JWT；JWT 不进环境变量 | C8 |
| CSTR-006 | 不做独立网关 / ACME / 后台改端口、绑定、域名面板 | C9 |
| CSTR-007 | 不迁移旧 `localStorage`；登录后云端空列表 | C5；AC4 |
| CSTR-008 | 关系图 / 文档索引保持匿名可读 | C2；AC2 |
| CSTR-009 | 不改 feedback 表结构；不按人计赞踩；仍一轮一个值 | C15；RQ-19 |
| CSTR-010 | 不强制首次改密 | RQ-17 |
| CSTR-011 | 不改写反馈 PRD、不改写 kb-qa v3 正文；顶栏/登录以本文覆盖 | RQ-10；T7 |
| CSTR-012 | 删云端对话不删 `qa_rounds` | §6.3；kb-qa C6 |
| CSTR-013 | 写接口身份以服务端 Session 为准，不信任请求体 `user_id` / `role` | §6.3 |
| CSTR-014 | 操作审计与问答明细不是同一份数据 | §6.3 |
| CSTR-015 | 反馈汇总不新增采集字段，只用现有 `feedback` | C6；F11 |
| CSTR-016 | 证书体积上限用户未给出，不编造成验收数字 | §2.3 |
| CSTR-017 | 本机非标准端口不强制 HTTP→HTTPS 跳转 | §6.3（PRD 标 💡） |
| CSTR-018 | 四个主 Tab 文案与数量不变 | SRC-HTML；SRC-CONTRACT |
| CSTR-019 | 会话上限沿用现网 40 | F5；`MAX_CONVS` |
| CSTR-020 | compose 正文不含 `0.0.0.0`；公网绑定用 `.env` / compose 变量 | C9；SRC-CONTRACT |
| CSTR-021 | 超管角色不可删、不可改权限清单；`PERM_SUPER_ONLY` 不做勾选项 | C4；§6.1 |
| CSTR-022 | 引导密码不在每次启动重置；仅账号表为空时创建一次 | T5 |
| CSTR-023 | MySQL 写轮次失败沿用 kb-qa C37：主路径仍可答 | E7 |
| CSTR-024 | 空状态固定 4 chips 沿用现网 `CHIP_FIXED` | F14 |

### 决策（已确认，不新造）

C1–C10、C12–C15。C11 已废止，不实施「按账号勾权限」。

### 排除项 / 本期不做

| ID | 项 | 来源 |
|---|---|---|
| OUT-1 | Hayyo App 登录注册 | §4.2 |
| OUT-2 | 写入产品运营后台 PRD / 套 admin-skin | C7 |
| OUT-3 | 自助注册 | C10 |
| OUT-4 | 多租户产品化 | §4.2 |
| OUT-5 | JWT | C8 |
| OUT-6 | 独立网关 / Let’s Encrypt / 后台改端口绑定 | C9 |
| OUT-7 | 旧本机对话导入 | C5 |
| OUT-8 | 改检索/切块/生成默认链路 | §4.2 |
| OUT-9 | 关系图 / 文档索引强制登录 | C2 |
| OUT-10 | 按人计赞踩 / 改 feedback 表结构 | C15 |
| OUT-11 | 强制首次改密 | RQ-17 |
| OUT-12 | 改写反馈 PRD / kb-qa v3 正文 | RQ-10；T7 |

### 技术债（PRD T7）

| 项 | 处置 |
|---|---|
| v3 仍写「本期不登录 / 顶栏运维入口」 | 接受；CSTR-011；不另开 STEP |
| 反馈 PRD 仍写「顶栏结构不动」 | 接受；C3 覆盖四钮；STEP-008 改现网 |
| 契约测试锁死顶栏四钮与 compose 无 `0.0.0.0` | STEP-008 改四钮断言；STEP-016 保持无 `0.0.0.0` |
| 无网关、无 ACME | 接受；OUT-6 |

## 功能清单

本期只实施：工作台账号（超管开户、Session Cookie、锁定）、问答必须登录、会话上云按人隔离、独立管理模块与 RBAC、操作审计、反馈汇总、证书手动启用 HTTPS、compose 可映射 80/443。不实施网关产品、自助注册、JWT、旧对话迁移、检索链路改口径。

## STEP 总览

| STEP | 标题 | 需求 | 验收 | 前置 | 优先级 |
|---|---|---|---|---|---|
| STEP-001 | 账号角色会话表与空库引导超管 | F7（引导子条款） | —（为 AC1 供输入） | 无 | P0 |
| STEP-002 | 登录登出、7 天 Cookie、失败锁定 | F1 | AC1、AC13（锁定）、AC18 | STEP-001 | P0 |
| STEP-003 | 自己改密并立即作废 Session | F2 | AC17（改密） | STEP-002 | P0 |
| STEP-004 | 现有运维 API 按 Session 与角色拒绝 | F8（接口） | AC12 | STEP-001、STEP-002 | P0 |
| STEP-005 | 问答登录墙；图/索引匿名 | F3、F4 | AC2、AC3 | STEP-002 | P0 |
| STEP-006 | 提问与赞踩身份取 Session | F6 | AC14 | STEP-002、STEP-005 | P0 |
| STEP-007 | 云端对话隔离，不迁 localStorage | F5 | AC4 | STEP-002 | P0 |
| STEP-008 | 问答顶栏去四钮、账号菜单、契约测试 | F9 | AC7、AC17（菜单） | STEP-002、STEP-003 | P0 |
| STEP-009 | 独立管理模块按角色展示 | F8（UI）、F5（审计全部） | AC5 | STEP-004、STEP-008 | P0 |
| STEP-010 | 超管开户角色、最后一名超管、禁用踢会话 | F7 | AC6、AC15 | STEP-001、STEP-009 | P0 |
| STEP-011 | 超管后台解锁登录锁定 | F7（解锁） | AC13（解锁） | STEP-002、STEP-010 | P0 |
| STEP-012 | 热度分层：chips 与管理页 | F14 | AC16 | STEP-005、STEP-009 | P0 |
| STEP-013 | 操作审计列表 | F10 | AC8 | STEP-009、STEP-010 | P0 |
| STEP-014 | 反馈汇总 | F11 | AC9 | STEP-006、STEP-009 | P0 |
| STEP-015 | 证书保存与手动启用/关闭 HTTPS | F12 | AC10 | STEP-010 | P0 |
| STEP-016 | compose 80/443 与后台改不了端口 | F13 | AC11 | STEP-015 | P0 |

## 需求映射

| 需求 ID | STEP | 说明 |
|---|---|---|
| F1 | STEP-002 | 登录/登出/7 天/锁定 |
| F2 | STEP-003 | 自己改密；菜单入口在 STEP-008 |
| F3 | STEP-005 | 问答登录墙 |
| F4 | STEP-005 | 匿名只读 |
| F5 | STEP-007、STEP-009 | 自己的云端会话；有权限者管理端看全部 |
| F6 | STEP-006 | ask 写 `user_id`；赞踩仅提问人 |
| F7 | STEP-001、STEP-010、STEP-011 | 引导；开户角色与最后超管；解锁 |
| F8 | STEP-004、STEP-009 | 接口 401/403；独立管理页 |
| F9 | STEP-008 | 顶栏 |
| F10 | STEP-013 | 操作审计 |
| F11 | STEP-014 | 反馈汇总 |
| F12 | STEP-015 | 证书 |
| F13 | STEP-016 | 服务器 Docker |
| F14 | STEP-012 | 热度分层 |
| RQ-01 | STEP-016 | 本机可测、后续公网 Docker |
| RQ-02 | STEP-005 | 问答须登录；图/索引匿名 |
| RQ-03 | STEP-008、STEP-009 | 独立管理入口；顶栏去四钮 |
| RQ-04 | STEP-003、STEP-010 | RBAC；超管开户；自己改密 |
| RQ-05 | STEP-007 | 会话上云；不迁移 |
| RQ-06 | STEP-013、STEP-014 | 审计与反馈汇总 |
| RQ-07 | STEP-009 | 自做管理页 |
| RQ-08 | STEP-002 | Session Cookie |
| RQ-09 | STEP-015、STEP-016 | 只做证书；手动 HTTPS |
| RQ-10 | STEP-008 | 顶栏覆盖反馈 PRD |
| RQ-11 | STEP-012 | 热度分层 |
| RQ-12 | STEP-010 | 多名超管；至少一名启用超管 |
| RQ-13 | STEP-015 | 证书仅超管 |
| RQ-14 | STEP-003、STEP-010 | 禁用或改密作废 Session |
| RQ-15 | STEP-002 | 绝对 7 天 |
| RQ-16 | STEP-002、STEP-011 | 5 次/15 分钟；超管解锁 |
| RQ-17 | STEP-010 | 开户指定初始密码 |
| RQ-18 | STEP-008 | 右侧账号菜单 |
| RQ-19 | STEP-006 | 赞踩仅提问人 |

## 验收映射

| 验收 ID | STEP | 说明 |
|---|---|---|
| AC1 | STEP-002 | 引导账号登录/登出；前置 STEP-001 |
| AC2 | STEP-005 | 未登录可读图/索引 |
| AC3 | STEP-005 | 未登录不能提问 |
| AC4 | STEP-007 | 只见自己的云端会话；旧 localStorage 不出现 |
| AC5 | STEP-009 | 只勾明细的角色不能改配置/重建 |
| AC6 | STEP-010 | 开户初始密码；禁用后会话立即失效 |
| AC7 | STEP-008 | 顶栏无四钮 |
| AC8 | STEP-013 | 改配置/重建出现在操作审计 |
| AC9 | STEP-014 | 反馈汇总统计并进原明细 |
| AC10 | STEP-015 | 上传不启用仍 HTTP；启用后标准端口跳转；可关闭 |
| AC11 | STEP-016 | 未映射 443 时后台启用打不开宿主机 443 |
| AC12 | STEP-004 | 未登录或普通用户调 config/reindex/rounds → 401 或 403 |
| AC13 | STEP-002、STEP-011 | 锁定；超管解锁 |
| AC14 | STEP-006 | 非提问人 feedback → 403 |
| AC15 | STEP-010 | 不能去掉最后一名启用超管 |
| AC16 | STEP-012 | 普通用户 chips；进不去热度管理页 |
| AC17 | STEP-003、STEP-008 | 改密须重登；菜单含退出/改密 |
| AC18 | STEP-002 | 满 7 天再调需登录接口 → 401 |

E1→STEP-004/005；E2→STEP-004/009；E3→STEP-002；E4→STEP-010；E5/E8→STEP-015；E6→STEP-016；E7→CSTR-023（不改主路径）；E9→STEP-006；E10→STEP-010。

## 完整 STEP 提示词

### [STEP-001] 账号角色会话表与空库引导超管

**阶段状态**：`draft`

**目标**：空库能引导出启用中的超级管理员；角色/账号/会话等持久化表可被后续 STEP 使用；不提供自助注册。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F7 | 仅超管角色开户；无自助注册；空库才能登录依赖引导 | `PRD` |
| 需求 ID | RQ-04 | 角色 RBAC；超管开户 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| 无 | — | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `site/kb-api/sql/init.sql` `qa_rounds` | `existing` | `REPO_BASELINE` | SRC-SQL / 全文仅此表 | 不删、不重建轮次表 |
| `LogStore.ensure_feedback_columns` | `existing` | `REPO_BASELINE` | SRC-LOGS / L119–144 | 已有卷补对象的现网模式 |
| `lifespan` 调 `ensure_feedback_columns` | `existing` | `REPO_BASELINE` | SRC-API / L58–63 | 启动补齐挂载点参考 |
| 账号/角色/会话/失败计数等新表名 | `planned` | `PLANNED` | 不适用 | T2 💡，不填具体名 |
| 引导环境变量名 | `planned` | `PLANNED` | 不适用 | T2 拟 `KB_BOOTSTRAP_*` 仅候选 |
| `cryptography` | `existing` | `REPO_BASELINE` | SRC-REQ / L5 | 密码不明文；KDF 名 `PLANNED` |

**输入**：现网 MySQL 卷与 `init.sql`；PRD：超管内置全权限、不可删、不可改权限清单；预置「普通用户」（默认仅知识问答）；`PERM_CHECKBOX` / `PERM_SUPER_ONLY`。

**输出**：空库启动后存在一名启用超管，可用引导口令登录的前置数据；账号表非空后再次启动不重置引导密码。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 超管角色 | 系统内置、全权限、不可删、不可改权限清单 | C4 |
| 预置普通用户 | 默认仅知识问答 | C4；§6.1 |
| 一账号一角色 | 每个账号只关联一个角色 | C4 |
| 无自助注册 | 账号只能超管角色生成 | C10 |
| 引导仅空库一次 | 仅账号表为空时创建一次；不每次启动重置 | T5；CSTR-022 |

**开发任务**：

1. 在不删除 `qa_rounds` 的前提下增加账号体系所需表（`CREATE IF NOT EXISTS`）；已有卷按现网补列模式补表，挂载点 `PLANNED`。
2. 空库创建超管与预置普通用户角色；密码哈希用现有 `cryptography` + 标准 KDF（名称 `PLANNED`）。
3. 不暴露自助注册接口。

**不在本 STEP 范围内**：登录 Cookie 行为（STEP-002）；开户 UI（STEP-010）；管理页（STEP-009）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 空库启动 | 存在启用中超管；预置普通用户角色仅知识问答 | —（AC1 前置） |
| 异常 | 账号表已有数据后改引导口令并重启 | 不重置已有超管密码 | CSTR-022 |
| 边界 | 调用任何自助注册入口（若被误加） | 不存在或拒绝 | CSTR-003 |

**完成标志**：

- [ ] 空库引导可被后续登录 STEP 使用
- [ ] `qa_rounds` 未删除、未重建
- [ ] 未实现自助注册
- [ ] 新表名/变量名若落地，回传为 `existing` 并注明原为 `PLANNED`

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

### [STEP-002] 登录登出、7 天 Cookie、失败锁定

**阶段状态**：`draft`

**目标**：用服务端 Session + HttpOnly Cookie 完成登录/登出；绝对 7 天过期；同一用户名连续 5 次失败锁定 15 分钟；不用 JWT。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F1 | 用户名+密码；登出；校验锁定；Session Cookie 绝对 7 天 | `PRD` |
| 验收 ID | AC1 | 引导账号登录进入已登录态；登出后问答不可问 | `PRD` |
| 验收 ID | AC13 | 连续 5 次失败后第 6 次即使密码正确，15 分钟内不可登录 | `PRD` |
| 验收 ID | AC18 | 登录满 7 天再调需登录接口 → 401 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | 空库已有启用超管 | 能用引导口令做登录请求 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `auth_passthrough` | `existing` | `REPO_BASELINE` | SRC-API / L69–72 | 本 STEP 建立 Session 后，中间件替换在 STEP-004 完成；本 STEP 至少提供登录/登出/me |
| 登录/登出/me 路径 | `planned` | `PLANNED` | 不适用 | T3 💡 候选，不选定 |
| Cookie 名 / SameSite / Path / Secure | `planned` | `PLANNED` | 不适用 | 已确认仅 HttpOnly + 7 天 |

**输入**：STEP-001 超管；C8、C14、E3。

**输出**：可登录、可登出、绝对 7 天、锁定 15 分钟；失败提示不暴露用户是否存在。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 凭证 | 服务端 Session + HttpOnly Cookie；不用 JWT | C8 |
| 过期 | 绝对 7 天 | RQ-15；AC18 |
| 锁定 | 同一用户名连续 5 次失败锁定 15 分钟；锁定期内密码正确也不可登录 | C14 |
| 失败提示 | 不暴露用户是否存在；锁定中提示稍后重试，不暗示过细 | E3 |

**开发任务**：

1. 实现登录成功发 Cookie、登出销毁 Session；禁用 JWT。
2. 按用户名计失败次数与 15 分钟锁定。
3. 提供「当前是否已登录」查询，供后续登录墙使用。
4. AC18 可用测试时钟拨到 7 天后或等价手段，不得把 TTL 改成「方便测试的别的天数」当作产品规则。

**不在本 STEP 范围内**：超管后台解锁（STEP-011）；改密踢会话（STEP-003）；运维 API 全面改鉴权（STEP-004）。AC1「登出后问答不可问」的完整 UI 墙在 STEP-005；本 STEP 须使登出后需登录的接口返回 401。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 空库引导账号正确密码 | 已登录；Cookie HttpOnly；登出后需登录接口 401 | AC1 |
| 异常 | 连续 5 次错误密码后第 6 次正确密码 | 15 分钟内不可登录；提示不暴露账号是否存在 | AC13；E3 |
| 边界 | 登录满 7 天 | 需登录接口 401 | AC18 |

**完成标志**：

- [ ] AC1（接口层登录/登出）、AC13 锁定子条款、AC18 通过
- [ ] 无 JWT、无 JWT 环境变量
- [ ] 未做后台解锁 UI
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

### [STEP-003] 自己改密并立即作废 Session

**阶段状态**：`draft`

**目标**：登录用户用旧密+新密改密；成功后该账号全部 Session 立即作废，须重新登录。不强制首次改密。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F2 | 顶栏账号菜单；旧密+新密；更新哈希；作废全部 Session | `PRD` |
| 验收 ID | AC17 | 改密后需重新登录 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-002 | 有效 Session | 带 Cookie 调改密 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| 改密路径 | `planned` | `PLANNED` | 不适用 | T3 💡 候选 |
| 顶栏菜单 UI | `planned` | `PLANNED` | 不适用 | 入口在 STEP-008；本 STEP 先完成接口 |

**输入**：已登录 Session；C10、C13。

**输出**：改密接口；成功后该账号所有 Session 失效。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 改密 | 登录后用户自己改密；开户不强制首次改密 | C10；RQ-17 |
| 作废 | 该账号改密成功后已有 Session 全部立即作废 | C13；RQ-14 |

**开发任务**：

1. 校验旧密、写入新哈希、作废该账号全部 Session。
2. 不实现「首次登录强制改密」。

**不在本 STEP 范围内**：顶栏菜单外观（STEP-008）；禁用账号踢会话（STEP-010）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 已登录，旧密正确，提交新密 | 须重新登录才能调需登录接口 | AC17 |
| 异常 | 旧密错误 | 不改密、原 Session 仍有效 | F2 |
| 边界 | 同一账号两个 Session，其一改密 | 两个 Session 均立即失效 | C13 |

**完成标志**：

- [ ] AC17 改密子条款通过
- [ ] 无强制首次改密
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

### [STEP-004] 现有运维 API 按 Session 与角色拒绝

**阶段状态**：`draft`

**目标**：替换 `auth_passthrough`；未登录或无权限不能调配置/重建/明细等运维接口。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F8 | 无权限 403；管理能力按角色 | `PRD` |
| 验收 ID | AC12 | 未登录或普通用户 `PUT config`、`POST reindex`、`GET rounds` → 401 或 403 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | 普通用户角色仅知识问答 | 用该角色账号登录 |
| STEP-002 | Session | 带/不带 Cookie 调现网路径 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `auth_passthrough` | `existing` | `REPO_BASELINE` | SRC-API / L69–72 | 替换为按 Session 校验 |
| `PUT /api/kb/config` | `existing` | `REPO_BASELINE` | SRC-API / L109–112 | AC12 |
| `POST /api/kb/reindex` | `existing` | `REPO_BASELINE` | SRC-API / L115–138 | AC12 |
| `GET /api/kb/rounds` | `existing` | `REPO_BASELINE` | SRC-API / L141–148 | AC12 |
| `GET /api/kb/heatmap` | `existing` | `REPO_BASELINE` | SRC-API / L188–196 | 本 STEP 至少不再裸奔；chips 分层在 STEP-012 |
| `GET /api/kb/health` | `existing` | `REPO_BASELINE` | SRC-API / L99–101 | 鉴权细节 `PLANNED`；不得取消健康灯数据源 |

**输入**：现网上述路由；`PERM_CHECKBOX`；普通用户默认仅知识问答。

**输出**：AC12 三条路径对未登录/普通用户为 401 或 403；有对应权限的角色可调用。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 配置/重建/问答明细 | 角色勾选后才可调对应写/读接口 | F8；C4 |
| 身份来源 | 以服务端 Session 为准 | CSTR-013 |

**开发任务**：

1. 去掉一律放行；白名单仅登录相关路径（具体集合 `PLANNED`）。
2. `PUT config` / `POST reindex` / `GET rounds` 要求登录 + 对应权限。
3. 同步会因鉴权变红的测试（发现门：SRC-FB-TEST 等），不得为保绿而恢复裸奔。

**不在本 STEP 范围内**：问答 `ask` 登录墙（STEP-005）；管理 UI（STEP-009）；热度 chips 分层（STEP-012）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 超管 Session 调三条路径 | 与现网成功语义一致（仍可读写） | AC12 对照 |
| 异常 | 未登录调三条路径 | 401 或 403 | AC12；E1 |
| 边界 | 普通用户（仅知识问答）已登录调三条路径 | 403 | AC12；E2 |

**完成标志**：

- [ ] AC12 通过
- [ ] `pipeline` / `indexer` 未改
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

### [STEP-005] 问答登录墙；图/索引匿名

**阶段状态**：`draft`

**目标**：未登录不能完成知识问答提问；关系图与文档索引仍可匿名阅读。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F3 | 未登录打开知识问答或调用提问接口：不能提问；页内登录 | `PRD` |
| 需求 ID | F4 | 未登录打开关系图/文档索引：与现网只读行为一致 | `PRD` |
| 验收 ID | AC2 | 未登录打开关系图、文档索引可阅读 | `PRD` |
| 验收 ID | AC3 | 未登录打开知识问答或 `POST /api/kb/ask` 不能完成提问 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-002 | 登录接口与 Session | 登录后可提问（提问身份在 STEP-006） |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `POST /api/kb/ask` | `existing` | `REPO_BASELINE` | SRC-API / L415–426 | 未登录须拒绝 |
| `qa.js` `send` | `existing` | `REPO_BASELINE` | SRC-QA-JS / L781–791 | 页内登录墙 |
| 四 Tab / `app.js` / `kb.js` | `existing` | `REPO_BASELINE` | SRC-HTML；SRC-APP；SRC-KB-JS | 匿名只读不得改口径 |

**输入**：STEP-002 Session；C2。

**输出**：问答 Tab 未登录为登录墙；`POST /api/kb/ask` 未登录不能完成提问；前三个 Tab 匿名可读。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 登录范围 | 图/索引匿名；知识问答必须登录 | C2 |
| 页内登录 | 未登录打开知识问答：不能提问；页内登录 | F3 |

**开发任务**：

1. `POST /api/kb/ask` 未登录拒绝（401）；须有知识问答权限（预置普通用户具备）。
2. 问答页未登录展示登录墙，不发问。
3. 不给关系图/文档索引加登录。

**不在本 STEP 范围内**：`user_id` 写入（STEP-006）；云端会话列表（STEP-007）；顶栏去钮（STEP-008）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 未登录打开关系图、文档索引 | 可阅读，行为与现网只读一致 | AC2 |
| 异常 | 未登录 `POST /api/kb/ask` 或在问答页发送 | 不能完成提问；401 或登录墙 | AC3；E1 |
| 边界 | 登录后打开问答 | 可进入问答（完整提问身份 STEP-006） | AC1 衔接 |

**完成标志**：

- [ ] AC2、AC3 通过
- [ ] `MAIN_TABS` 不变
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

### [STEP-006] 提问与赞踩身份取 Session

**阶段状态**：`draft`

**目标**：登录后 ask 把 `qa_rounds.user_id` 写成 Session 账号；不信任请求体身份字段；仅该轮提问人可改赞踩；他人或管理员 403。仍一轮一个值，不改 feedback 表结构。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F6 | 身份取 Session；赞踩仅提问人；`qa_rounds.user_id` 有值；他人 403 | `PRD` |
| 验收 ID | AC14 | 用户 A 的一轮，用户 B 或管理员调 feedback → 403；仅 A 可改 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-002 | Session 账号 id | 登录后 ask |
| STEP-005 | ask 必须已登录 | 未登录已不能问 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `_ask_events` `body.get("user_id")` | `existing` | `REPO_BASELINE` | SRC-API / L227–236 | 改为 Session |
| `qa.js` `user_id: null` | `existing` | `REPO_BASELINE` | SRC-QA-JS / L787–790、L834–837 | 前端不得再充当身份权威 |
| `set_feedback` | `existing` | `REPO_BASELINE` | SRC-LOGS / L146–166 | 无提问人校验，须加 |
| `POST /api/kb/rounds/{round_id}/feedback` | `existing` | `REPO_BASELINE` | SRC-API / L159–185 | AC14 |
| `test_feedback.py` | `existing` | `REPO_BASELINE` | SRC-FB-TEST | 须改为带 Session |

**输入**：`qa_rounds.user_id` 可空列（不重建表）；C15；CSTR-013。

**输出**：新轮次 `user_id` 为 Session 账号；非提问人改反馈 403；一轮仍一个值。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 一轮一值 | 仍一轮一个值；不按人计票 | C15 |
| 提问人可改 | 仅该轮提问人可赞/踩/取消 | C15 |
| 管理员只读 | 有明细权限的管理员不能改别人的评价 | C15 |
| 身份 | 以 Session 为准，不信任请求体 `user_id`/`role` | §6.3 |

**开发任务**：

1. ask 写入身份只来自 Session；忽略或拒绝请求体伪造。
2. feedback 校验 `qa_rounds.user_id` 对应当前账号。
3. 不改 `feedback` 列语义（空 / `up` / `down`）。
4. 更新 `test_feedback.py`。

**不在本 STEP 范围内**：反馈汇总页（STEP-014）；明细搬家（STEP-009）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 用户 A 登录提问 | 该轮 `user_id` 为 A；A 可赞/踩/取消 | F6 |
| 异常 | 用户 B 或管理员对该轮 `POST feedback` | 403 | AC14；E9 |
| 边界 | 请求体带他人 `user_id` 提问 | 落库仍为 Session 账号，不以请求体为准 | CSTR-013 |

**完成标志**：

- [ ] AC14 通过
- [ ] feedback 表结构未改
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

### [STEP-007] 云端对话隔离，不迁 localStorage

**阶段状态**：`draft`

**目标**：登录用户的新建/切换/删除/清空按账号在服务端持久化；换浏览器只见自己的列表；不导入 `CONV_KEY`；上限 40；删对话不删 `qa_rounds`。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F5 | 登录用户新建/切换/删除/清空；按账号隔离；上限沿用现网 40 | `PRD` |
| 验收 ID | AC4 | 普通用户问答、换浏览器再打开：只见自己的云端会话；旧 localStorage 不出现 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-002 | 登录态 | 两个浏览器同一账号 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `CONV_KEY` / `MAX_CONVS` | `existing` | `REPO_BASELINE` | SRC-QA-JS / L7–8、L90–104、L140–164 | 登录后不再作为权威；不导入 |
| 会话 CRUD 路径 | `planned` | `PLANNED` | 不适用 | T3 💡 |
| 云端对话表 | `planned` | `PLANNED` | 不适用 | T2 💡 |

**输入**：C5；CSTR-007；CSTR-012；CSTR-019。

**输出**：登录用户云端会话列表；跨浏览器一致；旧本地列表不出现。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 上云 | 登录后会话上云；用户只看自己的 | C5 |
| 不迁移 | 登录后云端空列表；不导入旧本机对话 | C5 |
| 上限 | 沿用现网 40 | F5 |
| 删对话 | 不删 `qa_rounds` | §6.3 |

**开发任务**：

1. 会话 CRUD 按 Session 账号隔离。
2. 登录后问答列表以云端为准，不把 `CONV_KEY` 灌进云端。
3. 上限 40；删除/清空不删轮次日志。

**不在本 STEP 范围内**：管理端看全部（STEP-009 对话审计页）；未登录本地草稿（未登录不能问，不保留为权威）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 普通用户登录后新建对话，换浏览器再登录 | 只见自己的云端列表 | AC4 |
| 异常 | 浏览器里仍有旧 `CONV_KEY` | 登录后列表不出现那些旧对话 | AC4 |
| 边界 | 超过 40 条 | 不超过现网上限策略；删列表项后明细里旧轮次仍在 | CSTR-019；CSTR-012 |

**完成标志**：

- [ ] AC4 通过
- [ ] 未导入 `CONV_KEY`
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

### [STEP-008] 问答顶栏去四钮、账号菜单、契约测试

**阶段状态**：`draft`

**目标**：问答顶栏去掉重建/配置/明细/热度；保留健康灯；右侧账号菜单（退出、修改密码）；有「进管理模块」权限者另给管理入口；契约测试改为断言四钮不应存在。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F9 | 无运维四按钮；有健康灯；右侧账号菜单；有权限者有管理入口 | `PRD` |
| 验收 ID | AC7 | 任意访客看问答顶栏：无重建/配置/明细/热度四按钮 | `PRD` |
| 验收 ID | AC17 | 顶栏右侧账号，点击或悬停：菜单含退出、修改密码 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-002 | 登录/登出 | 菜单退出 |
| STEP-003 | 改密接口 | 菜单改密 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `#qaTopActions` 四钮 | `existing` | `REPO_BASELINE` | SRC-HTML / L38–44 | 删除四钮，保留 `#qaHealth` |
| `openConfig` 等 overlay | `existing` | `REPO_BASELINE` | SRC-QA-JS / `openConfig` 等、L1099–1102 | 顶栏不再打开；页面搬家 STEP-009 |
| `test_fourth_tab_and_no_chips_or_process` | `existing` | `CONTRACT` | SRC-CONTRACT / L19–22 | 四钮断言改为不应存在 |
| 管理入口 URL | `planned` | `PLANNED` | 不适用 | T1 拟 `/kb-admin/` 仅候选 |

**输入**：C3；RQ-10；RQ-18。

**输出**：顶栏无 `TOP_OPS_FOUR`；有健康灯与账号菜单；契约测试与之一致。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 四钮 | 去掉重建索引 / 配置 / 问答明细 / 功能热度 | C3 |
| 健康灯 | 可留 | RQ-10；C3 |
| 账号菜单 | 点击或悬停：退出、修改密码 | RQ-18 |
| 管理入口 | 有「进管理模块」权限者另给 | C3 |

**开发任务**：

1. 从 `index.html` 去掉四钮；保留健康灯。
2. 右侧账号：已登录显示当前账号；菜单退出、改密。
3. 有权限者展示管理入口（目标地址 `PLANNED`）。
4. 改 SRC-CONTRACT：四钮不应存在；四 Tab 仍断言 `MAIN_TABS`。
5. 不改反馈 PRD / v3 正文。

**不在本 STEP 范围内**：管理页内容（STEP-009）；热度 chips（STEP-012）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 任意访客打开问答顶栏 | 无四钮；健康灯仍在 | AC7 |
| 正常 | 已登录，点击或悬停右侧账号 | 菜单含退出、修改密码 | AC17 |
| 边界 | 无「进管理模块」的普通用户 | 无管理入口 | F9 |
| 异常 | 契约测试 | 四钮断言为不存在；四 Tab 仍过 | AC7 |

**完成标志**：

- [ ] AC7、AC17 菜单子条款通过
- [ ] v3 与反馈 PRD 文件未改
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

### [STEP-009] 独立管理模块按角色展示

**阶段状态**：`draft`

**目标**：已登录且角色允许「进管理模块」的人使用独立入口；按勾选展示健康、配置、重建、明细、热度页、对话审计、操作审计、反馈汇总等页；无权限无入口且接口 403；本站自做，不套 admin-skin。自定义角色只勾「问答明细」时能看明细、不能改配置、不能重建。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F8 | 独立入口；按角色展示；无权限 403 | `PRD` |
| 需求 ID | F5 | 有权限者在管理端看全部对话 | `PRD` |
| 验收 ID | AC5 | 自定义角色只勾「问答明细」：能看明细；不能改配置、不能重建 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-004 | 运维 API 已按权限拒绝 | 无权限调配置/重建 403 |
| STEP-008 | 顶栏管理入口 | 有权限者能点进独立入口 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `qa.js` overlay 配置/重建/明细/热度 | `existing` | `REPO_BASELINE` | SRC-QA-JS / `openConfig` 等 | 迁出问答顶栏，行为搬到管理页 |
| `nginx.conf` location | `existing` | `REPO_BASELINE` | SRC-NGINX / 无管理 location | 增加独立静态入口，路径 `PLANNED` |
| admin-skin | `existing`（禁止使用） | `PRD` | SRC-PRD / C7 | 不套 |

**输入**：C7；`PERM_CHECKBOX`；证书与解锁仅超管可见（页在 STEP-010/011/015 接上）。

**输出**：独立管理静态站 + 按角色显隐；AC5 成立；对话审计页能看全部云端会话（需「对话审计」权限）。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 独立入口 | 仅登录后可用；不与问答顶栏四钮混用 | C3 |
| 管理 UI | 本站自做，不套 admin-skin | C7 |
| 对话审计 | 有权限角色可审计全部会话 | C5 |
| 超管专属页 | 证书与解锁仅超管可见 | F8 |

**开发任务**：

1. nginx 增加管理入口 location（路径 `PLANNED`）；自做页面。
2. 按 `PERM_CHECKBOX` 显隐；无「进管理模块」则入口与页面均不可用。
3. 把现网 overlay 的配置/重建/明细/热度能力迁到管理页，不改配置默认链路语义。
4. 「对话审计」权限可看全部云端会话；无此权限不能看他人会话。

**不在本 STEP 范围内**：开户角色 CRUD 完整验收（STEP-010）；操作审计数据（STEP-013）；反馈汇总算法（STEP-014）；证书（STEP-015）。本 STEP 可为这些页留入口位，无权限则不展示。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 自定义角色只勾「进管理模块」+「问答明细」 | 能进管理并看明细；不能改配置、不能重建 | AC5 |
| 异常 | 无「进管理模块」访问管理入口或 API | 登录墙或 403 | E2；F8 |
| 边界 | 有「对话审计」的角色 | 能看全部云端会话；普通用户不能 | F5 |

**完成标志**：

- [ ] AC5 通过
- [ ] 未引用 admin-skin
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

### [STEP-010] 超管开户角色、最后一名超管、禁用踢会话

**阶段状态**：`draft`

**目标**：仅超管可建角色并勾 `PERM_CHECKBOX`、开户并指定初始密码、绑一个角色、升/降超管、禁用账号；可多名超管；不能禁用或去掉最后一名启用中超管；禁用立即作废该账号全部 Session。不强制首次改密。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F7 | 建角色勾权限；建/禁用账号；指定初始密码；可升超管；不可去掉最后一名启用超管 | `PRD` |
| 验收 ID | AC6 | 开户指定初始密码能登录；禁用后已打开会话立即失效 | `PRD` |
| 验收 ID | AC15 | 全站仅一名启用超管时，禁用或去掉其超管角色被拒绝 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | 超管角色锁死；预置普通用户 | 用超管登录 |
| STEP-002 | Session 作废机制 | 禁用后旧 Cookie 401 |
| STEP-009 | 管理模块 | 超管可见开户/角色页 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| 角色/账号 CRUD 路径 | `planned` | `PLANNED` | 不适用 | T3 💡；仅超管 |

**输入**：C4；C10；C13；`PERM_SUPER_ONLY`；CSTR-021。

**输出**：超管可开户/配角色；AC6、AC15 成立。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 开户 | 超管指定初始密码；不强制首次改密 | RQ-17 |
| 多名超管 | 可把账号设为超管 | RQ-12 |
| 最后一名 | 不能禁用或删光最后一名启用中的超管 | C4；AC15 |
| 禁用 | 不能登录，且立即作废已有 Session | C13；E4 |
| 权限配置 | 角色上勾选，不在账号上逐项勾选 | C4；C11 废止 |

**开发任务**：

1. 仅超管可开户、改账号角色、改角色权限清单（超管角色清单不可改、角色不可删）。
2. 初始密码可登录；不强制首次改密。
3. 禁用作废该账号全部 Session。
4. 拦截去掉最后一名启用超管（禁用或改角色）。

**不在本 STEP 范围内**：解锁登录锁定（STEP-011）；证书（STEP-015）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 超管开户并指定初始密码、赋普通用户 | 新用户用初始密码能登录，且不必先改密 | AC6；CSTR-010 |
| 异常 | 禁用该账号时其 Session 仍在 | 立即失效，不能再调需登录接口 | AC6；E4 |
| 边界 | 全站仅一名启用超管，禁用或去掉其超管角色 | 拒绝，明确不可 | AC15；E10 |

**完成标志**：

- [ ] AC6、AC15 通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

### [STEP-011] 超管后台解锁登录锁定

**阶段状态**：`draft`

**目标**：超管可在后台解除登录锁定（清失败次数）；解锁后立即可以再登录。解锁记操作审计的写入可在本 STEP 打点，列表展示以 STEP-013 为准。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F7 | 可解锁登录锁定 | `PRD` |
| 验收 ID | AC13 | 超管解锁后立即可以登录 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-002 | 5 次/15 分钟锁定已生效 | 制造锁定 |
| STEP-010 | 超管管理页 | 仅超管可见解锁 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| 解锁路径 | `planned` | `PLANNED` | 不适用 | T3 💡；`PERM_SUPER_ONLY` |

**输入**：C14；RQ-16。

**输出**：超管清失败次数后立即可以登录。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 解锁 | 超管后台解除锁定（清失败次数） | C14 |
| 可见性 | 仅超管，不做勾选项 | §6.1 |

**开发任务**：

1. 超管解锁指定用户名（或账号）的登录锁定，失败次数清零。
2. 非超管无入口、接口 403。

**不在本 STEP 范围内**：锁定规则本身（STEP-002）；审计列表 UI（STEP-013）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 某用户名已锁 15 分钟，超管解锁 | 立即可以正确密码登录 | AC13 |
| 异常 | 普通用户调解锁 | 403 | E2 |
| 边界 | 超管自己被锁，另一名超管解锁 | 可登录（多名超管） | RQ-12；§9.2 |

**完成标志**：

- [ ] AC13 解锁子条款通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

### [STEP-012] 热度分层：chips 与管理页

**阶段状态**：`draft`

**目标**：已登录且能问答的用户可读热度聚合，仅用于空状态 chips（固定 4 + 最多再加 4）；热度管理页仍要「功能热度」权限。未登录不读 chips 热度。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F14 | 能问答的登录用户可读聚合；热度页要「功能热度」权限 | `PRD` |
| 验收 ID | AC16 | 已登录普通用户空状态：固定 4 chips；有热度则可再加最多 4；热度管理页进不去 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-005 | 未登录不能问答 | chips 须先登录 |
| STEP-009 | 热度管理页入口 | 无「功能热度」进不去 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `GET /api/kb/heatmap` | `existing` | `REPO_BASELINE` | SRC-API / L188–196 | chips 用；须登录+知识问答 |
| `refreshHeatChips` | `existing` | `REPO_BASELINE` | SRC-QA-JS / L352–376 | 现网未登录也会打 heatmap |
| `CHIP_FIXED` | `existing` | `REPO_BASELINE` | SRC-QA-JS / L16–32 | 常驻 4 条不改文案 |
| 热度公式 / `logs.heatmap` | `existing` | `REPO_BASELINE` | SRC-LOGS | 不改聚合公式 |

**输入**：C12；F14；CSTR-024。

**输出**：AC16；heatmap 页与 chips 权限分离。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| chips 读 | 已登录且能问答的人可读热度聚合，仅用于空状态 chips | C12 |
| 热度页 | 仍要「功能热度」权限 | C12 |
| 条数 | 固定 4；有热度再加最多 4 | F14；AC16 |

**开发任务**：

1. `GET heatmap`：登录 + 知识问答权限（chips）。
2. 热度管理页：另要「功能热度」。
3. 未登录不请求或不展示热度 chips；固定 4 条仍仅登录后空状态出现（F14「须先登录」）。
4. 不改热度聚合公式、不改 `CHIP_FIXED` 文案。

**不在本 STEP 范围内**：改别名或生成链路。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 普通用户已登录、空状态 | 固定 4 chips；有热度最多再加 4 | AC16 |
| 异常 | 该普通用户进热度管理页 | 进不去 | AC16 |
| 边界 | 未登录 | 不展示热度 chips、不能靠 chips 提问 | F14 |

**完成标志**：

- [ ] AC16 通过
- [ ] heatmap 公式未改
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

### [STEP-013] 操作审计列表

**阶段状态**：`draft`

**目标**：登录成败、开户、改角色、改配置、重建、改密、证书、解锁锁定记操作审计：谁、何时、动作、对象、IP；配置只记字段名，不记 Key/私钥；可筛列表。与问答明细不是同一份数据。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F10 | 上列动作记审计；配置只记字段名，不记 Key/私钥 | `PRD` |
| 验收 ID | AC8 | 超管改配置或点重建后，操作审计能看到对应动作（配置只见字段名） | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-009 | 管理模块有操作审计页 | 打开列表 |
| STEP-010 | 能开户/改角色 | 这些动作可被记录 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `qa_rounds` | `existing` | `REPO_BASELINE` | SRC-SQL | 不是操作审计表；禁止混用 |
| 审计表/列表路径 | `planned` | `PLANNED` | 不适用 | T2/T3 💡 |
| `PUT /api/kb/config` | `existing` | `REPO_BASELINE` | SRC-API / L109–112 | AC8 触发 |

**输入**：C6；CSTR-014；T6 不把 API Key、私钥、密码写入审计。

**输出**：可筛操作审计列表；AC8。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 记录范围 | 登录成败、开户、改角色、改配置、重建、改密、证书、解锁锁定 | F10 |
| 字段 | 谁、何时、动作、对象、IP；配置只记字段名 | F10 |
| 禁止 | 不记 Key/私钥/密码 | F10；T6 |
| 分家 | 与问答明细不是同一份数据 | §6.3 |

**开发任务**：

1. 独立审计存储（表名 `PLANNED`）。
2. 在 F10 所列动作处写入；配置变更只落字段名。
3. 管理端「操作审计」权限可筛列表。

**不在本 STEP 范围内**：问答明细内容改口径；证书启用逻辑（STEP-015 只在此打点）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 超管改配置或点重建 | 审计列表有对应动作；配置只见字段名 | AC8 |
| 异常 | 无「操作审计」权限 | 无入口、403 | F8 |
| 边界 | 改密/解锁 | 有记录且无密码明文 | F10 |

**完成标志**：

- [ ] AC8 通过
- [ ] 未写入 Key/私钥/密码
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

### [STEP-014] 反馈汇总

**阶段状态**：`draft`

**目标**：管理端反馈汇总聚合已有赞/踩；被踩列表能进原明细；无新采集口、不新增采集字段。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F11 | 聚合已有赞/踩；被踩列表进原明细；不新采集 | `PRD` |
| 验收 ID | AC9 | 存在赞/踩轮次时能统计并点进原明细；无新采集口 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-006 | 赞踩已按提问人写入 `feedback` | 库内有 up/down |
| STEP-009 | 管理模块 | 「反馈汇总」权限页 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `qa_rounds.feedback` | `existing` | `REPO_BASELINE` | SRC-SQL / L25–26 | 唯一采集源 |
| 明细页 | `existing`→迁管理端 | `REPO_BASELINE` | SRC-QA-JS `openRounds` | 被踩进原明细 |

**输入**：C6；CSTR-015。

**输出**：汇总页；AC9。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 不新采集 | 只用现有 `feedback` | F11 |
| 被踩 | 列表可进原明细 | F11 |

**开发任务**：

1. 只读聚合 `up`/`down`。
2. 被踩项跳转已有明细（管理端明细页）。
3. 不新增采集 API/字段。

**不在本 STEP 范围内**：改赞踩权限（STEP-006 已做）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 存在赞/踩轮次，有权限者打开汇总 | 能统计；踩可点进原明细 | AC9 |
| 异常 | 无「反馈汇总」权限 | 无入口、403 | F8 |
| 边界 | 页面上不出现新的采集控件 | 无新采集口 | AC9 |

**完成标志**：

- [ ] AC9 通过
- [ ] `feedback` 列未改结构
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

### [STEP-015] 证书保存与手动启用/关闭 HTTPS

**阶段状态**：`draft`

**目标**：仅超管可上传 PEM 或使用挂载文件；上传只保存；点「启用 HTTPS」后，在标准 80/443 下 HTTP 跳 HTTPS；可关闭回 HTTP；坏证书不能启用。不做网关产品、不做 ACME。本机非标准端口不强制跳转。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F12 | 上传只保存；启用后对外 HTTPS、HTTP 跳转；可关闭；坏证书不能启用 | `PRD` |
| 验收 ID | AC10 | 上传不点启用仍 HTTP；启用后标准 80/443 下 HTTP 跳 HTTPS；可关闭 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-010 | 超管身份 | 仅超管可见证书页 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `nginx.conf` `listen 80` | `existing` | `REPO_BASELINE` | SRC-NGINX / L6 | TLS 终止在 nginx，不在 FastAPI |
| compose 证书卷 | `planned` | `PLANNED` | 不适用 | T1 |
| 证书 API | `planned` | `PLANNED` | 不适用 | T3 💡 |
| 体积上限 | 不填 | `PRD` | SRC-PRD / §2.3 | 用户未给数字，禁止编造 |

**输入**：C9；RQ-13；E5；E8；CSTR-016；CSTR-017。

**输出**：AC10；私钥不回显。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 上传 | 只保存；不自动启用 | C9 |
| 启用 | 仅超管手动点启用后 HTTP→HTTPS | C9 |
| 关闭 | 可关闭回 HTTP | C9 |
| 坏证书 | 不启用、维持当前协议；明确失败原因 | E5 |
| 首次 HTTP 传私钥 | 允许（用户选择的引导方式） | E8 |

**开发任务**：

1. 超管上传或识别挂载 PEM；私钥不回显。
2. 启用前校验，失败不切换协议。
3. 标准 80/443 启用后 HTTP 跳 HTTPS；关闭回 HTTP。
4. 非标准端口不强制跳转。
5. 不实现 ACME、不在后台改端口/绑定。

**不在本 STEP 范围内**：compose 映射宿主机 443（STEP-016）；网关产品。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 超管上传后不点启用 | 仍 HTTP | AC10 |
| 正常 | 再点启用（标准 80/443） | HTTP 跳 HTTPS；可再关闭 | AC10 |
| 异常 | 非法/不匹配证书后点启用 | 不启用；维持当前协议；明确失败 | E5 |
| 边界 | 非超管上传/启用 | 403 | RQ-13 |

**完成标志**：

- [ ] AC10 通过
- [ ] 无体积上限数字编造
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

### [STEP-016] compose 80/443 与后台改不了端口

**阶段状态**：`draft`

**目标**：同一套 Docker 可在服务器用 `.env` / compose 映射 80 与 443；MySQL/Qdrant 仍只绑本机；compose 正文不含 `0.0.0.0`；后台启用 HTTPS 不能单靠后台打开宿主机 443。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F13 | 可绑公网 80/443；MySQL/Qdrant 不因公网改成对外暴露；后台改不了端口映射 | `PRD` |
| 验收 ID | AC11 | 服务器未映射 443 时仅后台启用，不能单靠后台打开宿主机 443 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-015 | 后台「启用 HTTPS」存在 | 未映射 443 时启用不能打开宿主 443 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `site/docker-compose.yml` ports | `existing` | `REPO_BASELINE` | SRC-COMPOSE / L15–18、L35–36、L44–46 | 保持 127.0.0.1 变量写法；增加 443 映射方式 `PLANNED` |
| `test_compose_bind_localhost_and_no_3306` | `existing` | `CONTRACT` | SRC-CONTRACT / L29–41 | 继续禁止正文 `0.0.0.0`；端口正则按实测修正，不得为匹配正则把 `0.0.0.0` 写进正文 |
| `.env.example` | `existing` | `REPO_BASELINE` | SRC-ENV | 公网端口/绑定用 env，不进管理后台 |
| TLS 端口变量名 | `planned` | `PLANNED` | 不适用 | T5 拟 `HAYYO_TLS_PORT` 仅候选 |

**输入**：C1；C9；CSTR-020；E6。

**输出**：AC11；本机默认仍 `127.0.0.1:18765` HTTP 可测。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 公网端口 | 用 compose / `.env`，不进管理后台 | C9 |
| 数据口 | MySQL/Qdrant 不因公网改成对外暴露 | F13；T6 |
| 443 | 未映射时后台启用无法对外 HTTPS | E6；AC11 |

**开发任务**：

1. compose 支持映射 80 与 443 的变量方式；默认本机 loopback 行为不丢。
2. 不把 `0.0.0.0` 写进 compose 正文。
3. 管理后台无端口/绑定/域名面板。
4. 契约测试仍禁止 `0.0.0.0`；按需修正端口抽取，使其与变量写法一致。

**不在本 STEP 范围内**：ACME；改问答链路。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 本机默认 compose | 仍可在 127.0.0.1:18765 HTTP 测登录问答 | F13；C1 |
| 异常 | 未映射宿主机 443，仅后台启用 | 不能单靠后台打开宿主机 443 | AC11 |
| 边界 | 读 compose 正文 | 无 `0.0.0.0`；MySQL/Qdrant 仍 127.0.0.1 | CSTR-020 |

**完成标志**：

- [ ] AC11 通过
- [ ] 契约测试无 `0.0.0.0` 仍成立
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

## 进度区块

> 路径：保留在本 STEP 草稿内。`site/docs/design/kb-auth/` 在拆解时尚未约定独立进度文件。  
> PRD 来源：`site/docs/design/kb-auth/PRD-账号体系与管理模块-v2.md`  
> STEP 来源：`steps-draft.md`  
> 当前阶段结果：`PASS_WITH_RISKS`

### 进度总览

| 完成数 | 总数 | 当前状态 |
|---|---|---|
| 0 | 16 | `NOT_STARTED` |

### STEP 明细

| STEP | 功能名称 | 需求 ID | 验收 ID | 前置 STEP | 状态 | 证据 |
|---|---|---|---|---|---|---|
| STEP-001 | 账号角色会话表与空库引导超管 | F7 | — | 无 | `NOT_STARTED` | — |
| STEP-002 | 登录登出、7 天 Cookie、失败锁定 | F1 | AC1、AC13（锁）、AC18 | STEP-001 | `NOT_STARTED` | — |
| STEP-003 | 自己改密并立即作废 Session | F2 | AC17（改密） | STEP-002 | `NOT_STARTED` | — |
| STEP-004 | 现有运维 API 按 Session 与角色拒绝 | F8 | AC12 | STEP-001、STEP-002 | `NOT_STARTED` | — |
| STEP-005 | 问答登录墙；图/索引匿名 | F3、F4 | AC2、AC3 | STEP-002 | `NOT_STARTED` | — |
| STEP-006 | 提问与赞踩身份取 Session | F6 | AC14 | STEP-002、STEP-005 | `NOT_STARTED` | — |
| STEP-007 | 云端对话隔离，不迁 localStorage | F5 | AC4 | STEP-002 | `NOT_STARTED` | — |
| STEP-008 | 问答顶栏去四钮、账号菜单、契约测试 | F9 | AC7、AC17（菜单） | STEP-002、STEP-003 | `NOT_STARTED` | — |
| STEP-009 | 独立管理模块按角色展示 | F8、F5 | AC5 | STEP-004、STEP-008 | `NOT_STARTED` | — |
| STEP-010 | 超管开户角色、最后一名超管、禁用踢会话 | F7 | AC6、AC15 | STEP-001、STEP-009 | `NOT_STARTED` | — |
| STEP-011 | 超管后台解锁登录锁定 | F7 | AC13（解锁） | STEP-002、STEP-010 | `NOT_STARTED` | — |
| STEP-012 | 热度分层：chips 与管理页 | F14 | AC16 | STEP-005、STEP-009 | `NOT_STARTED` | — |
| STEP-013 | 操作审计列表 | F10 | AC8 | STEP-009、STEP-010 | `NOT_STARTED` | — |
| STEP-014 | 反馈汇总 | F11 | AC9 | STEP-006、STEP-009 | `NOT_STARTED` | — |
| STEP-015 | 证书保存与手动启用/关闭 HTTPS | F12 | AC10 | STEP-010 | `NOT_STARTED` | — |
| STEP-016 | compose 80/443 与后台改不了端口 | F13 | AC11 | STEP-015 | `NOT_STARTED` | — |

### 阻断与来源变化

| 日期 | STEP | 类型 | 证据或变化 | 处理结果 |
|---|---|---|---|---|
| — | — | — | — | — |

状态只使用 `NOT_STARTED`、`IN_PROGRESS`、`DONE`、`BLOCKED`。只有完成标志全部有验证证据时才能标为 `DONE`。

## 自检

- [x] 所有需求 F1–F14、RQ-01～RQ-19 均映射到 STEP
- [x] 所有验收 AC1–AC18 均映射到 STEP
- [x] 每个 STEP 的需求 ID、验收 ID、依赖和范围明确（STEP-001 无独立 AC，只为 AC1 供输入）
- [x] 未增加 PRD 中不存在的业务语义；未把 T 节 💡 路径/表名/环境变量写成已批准事实
- [x] 未使用 `[自定义]` 补造业务字段或值；证书体积上限未编造
- [x] 所有路径和符号标记 `existing` / `planned` / `unverified`
- [x] `existing` 引用绑定 `source_id` 与 locator
- [x] 关键 `unverified` 未表述为可执行事实；无 `RUNTIME`
- [x] 草稿未自称已验证或可执行
- [x] 阶段只返回五种结果之一并在本阶段停止

## 非阻断风险

1. 契约测试锁死顶栏四钮：`test_site_contract.py` 仍断言四钮存在。STEP-008 必须改断言，否则 CI 红。
2. 已有 MySQL 卷不会重跑 `init.sql`：新表须沿用 `ensure_feedback_columns` 同类启动补齐；挂载点 `PLANNED`。
3. compose 端口正则：`test_compose_bind_localhost_and_no_3306` 用 `127.0.0.1:\d+:\d+` 抽取，与现网 `${HAYYO_WEB_PORT:-18765}` 字面量可能不匹配。本轮未跑 pytest。STEP-016 改 compose 时须以实测为准修正断言，且正文仍禁止 `0.0.0.0`。
4. `test_feedback.py` 无 Session：STEP-006 后须带 Cookie，否则红。
5. T 节名词均为 💡：`/kb-admin/`、`KB_BOOTSTRAP_*`、Cookie 名、新表名、新 API 路径不是 USER_DECISION。
6. 两份旧 PRD 口径残留：kb-qa v3 仍写本期不登录/顶栏四钮；反馈 PRD 仍写顶栏不动。以本专题覆盖，不改那两份文件（CSTR-011）。
7. 本机 18765 与 443 不一致：§6.3 非标准端口不强制跳转（PRD 标 💡）。STEP-015 不得自造跳转端口。
8. 无 `RUNTIME`：未起 Docker、未跑现网登录。

## 阶段结果

**`PASS_WITH_RISKS`**

- 模式：`standalone`（本阶段结束）
- 产出：本文件 `steps-draft.md`
- 不是 `steps-verified.md`，不宣布 `STEPS_VERIFIED`
- 不生成里程碑计划，不开始开发
- 下一阶段：`$step-doc-review` 完整复审
