# 账号体系与管理模块 · 实现契约

> 现行实现合同。给改本站登录 / 问答身份 / 管理站 / 证书的人与 AI 用。  
> 需求仍以 [`../../design/kb-auth/PRD-账号体系与管理模块-v2.md`](../../design/kb-auth/PRD-账号体系与管理模块-v2.md) 为准；本文件冻结**落地符号、鉴权矩阵、查 bug 优先点**。  
> 阶段快照：[`M1-契约草案.md`](../../design/kb-auth/M1-契约草案.md) … [`M4-契约草案.md`](../../design/kb-auth/M4-契约草案.md)，冲突以本文件为准。  
> 契约总入口：[`../INDEX.md`](../INDEX.md)。日期：2026-09-20（M1–M4 用户本机验收后整合）

## 1. 怎么用

| 你要做的事 | 读 |
|---|---|
| 改接口鉴权、401/403、Cookie | §3 鉴权矩阵、§4 API |
| 改 H5 登录墙 / 顶栏 / 会话 | §5、`site/feature-interaction/qa.js` |
| 改管理站入口或角色页 | §6、`site/kb-admin/`、nginx `/kb-admin/` |
| 查越权 / 串会话 / 漏打点 | §8 优先于翻 PRD |
| 对照回归 | §9 测试文件 |

不要写进 `prd/design/auth-login` 或 `prd/design/admin`。不要套 `workspace/_kit/admin-skin/`。不要改 `pipeline.py` / `indexer.py` 来做鉴权。

## 2. 落地符号

| 名 | 值 |
|---|---|
| Cookie | `hayyo_kb_sid`（HttpOnly、SameSite=Lax、Path=/、Max-Age=604800；Secure 仅 HTTPS） |
| 引导 | `KB_BOOTSTRAP_USER` / `KB_BOOTSTRAP_PASSWORD`（仅账号表空时创建一次） |
| 管理 URL | `/kb-admin/`；nginx `auth_request` → `GET /api/kb/auth/admin-gate` |
| 会话表 | `kb_conversations`；上限 40；删会话不删 `qa_rounds` |
| 审计表 | `kb_audit_logs`（≠ `qa_rounds`） |
| 本地旧对话键 | `hayyo-kb-qa-conversations-v1`；**登录后不导入云端** |
| HTTP 端口 | `HAYYO_WEB_PORT` 默认 18765 → 容器 80 |
| TLS 端口 | `HAYYO_TLS_PORT` 默认 18769 → 容器 443；默认宿主机 443 连不上 |
| 证书开关 | `DATA_DIR/https.enabled`；私钥不回显 |
| JWT | 无；响应体无 token；无自助注册 |

表：`kb_roles`、`kb_role_permissions`、`kb_accounts`、`kb_sessions`、`kb_login_locks`、`kb_audit_logs`、`kb_conversations`；`qa_rounds` 保留。已有 MySQL 卷靠启动 `CREATE IF NOT EXISTS`，不重跑 `init.sql`。

代码锚点：`site/kb-api/app/main.py`（`auth_guard` / `_ops_perm` / `_is_public`）、`auth_store.py`、`conv_store.py`、`tls_store.py`、`site/docker/nginx.conf`、`site/docker-compose.yml`。

## 3. 鉴权矩阵

中间件分档（`main.py`）：

1. 白名单：不要求 Session（handler 仍可 401）。
2. 页级勾选：`_ops_perm` 命中则须登录且有该勾选，**不叠加「进管理模块」**（R-API-DOOR）。
3. 其余：须登录；个别路径再查勾选或超管。

| 路径 | 未登录 | 已登录无对应勾选 | 有勾选 / 超管 |
|---|---|---|---|
| `POST /api/kb/auth/login` `logout` | 放行 | — | — |
| `GET /api/kb/auth/me` | 401 | 200 | 200 |
| `GET /api/kb/auth/admin-gate` | **403** | 无「进管理模块」**403** | 204 |
| `GET /api/kb/health` | 200（仍匿名） | 200 | 200 |
| `POST /api/kb/ask` | 401（非 SSE done） | 无「知识问答」403 | SSE |
| `GET /api/kb/heatmap` | 401 | 无「知识问答」403 | 200（给 chips） |
| `GET /api/kb/admin/heatmap` | 401 | 无「功能热度」403 | 200（热度页） |
| `GET\|PUT /api/kb/config` | 401 | 无「配置」403 | 2xx |
| `POST /api/kb/reindex` | 401 | 无「重建」403 | 2xx |
| `GET /api/kb/rounds`、`GET /api/kb/rounds/{id}` | 401 | 无「问答明细」403 | 200 |
| `POST /api/kb/rounds/{id}/feedback` | 401 | 非提问人 403（管理员也 403） | 提问人 2xx |
| `/api/kb/conversations*` | 401 | 只能触达自己的 id；他人 404 | 自己的 CRUD |
| `GET /api/kb/admin/conversations` | 401 | 无「对话审计」403 | 全站云端 id |
| `GET /api/kb/admin/audits` | 401 | 无「操作审计」403 | 200 |
| `GET /api/kb/admin/feedback-summary` | 401 | 无「反馈汇总」403 | 200 |
| `/api/kb/admin/accounts*` `/roles*` `/unlock` `/tls*` `/perms` | 401 | 非超管 403 | 超管 2xx |
| 浏览器 `GET /kb-admin/` | nginx **403** | 无大门 **403** | 页面 200 |

锁定：同一 `username` 连续 5 次失败锁 15 分钟；第 6 次即使密码正确 401。错密文案「用户名或密码不正确」；锁定含「稍后重试」。比较用户名不是 IP。

Session：绝对 7 天；登出 / 改密 / 禁用 → `SESSION_DEAD`（须登录接口 401）。不强制首次改密。

`ROLE_USER` 勾选恰好 {知识问答}。超管 `is_super` 视为全勾选。`PERM_CHECKBOX` 十项中文：知识问答、进管理模块、配置、重建、问答明细、功能热度、对话审计、健康、操作审计、反馈汇总。不在账号上逐项勾权限。

## 4. API 终态

| 方法路径 | 行为要点 |
|---|---|
| `POST /api/kb/auth/login` | Set-Cookie；体 `{ok,id,username}` |
| `POST /api/kb/auth/logout` | 作废 Session、清 Cookie |
| `GET /api/kb/auth/me` | `id` = `ME_ID`；带 `permissions` / `is_super` |
| `POST /api/kb/auth/password` | 旧密+新密；成功后该账号全部 Session 死；审计无密码 |
| `POST /api/kb/ask` | `user_id` 只取 Session，忽略请求体 `user_id`；现网 `owner_id` / `tenant_id` / `role` 仍可读请求体写入日志 |
| `POST /api/kb/rounds/{id}/feedback` | 仅提问人；写库失败不阻断问答链路 |
| `GET/POST /api/kb/conversations` | 按 `ME_ID` 隔离，上限 40 |
| `GET/PUT/DELETE /api/kb/conversations/{id}` | 只能操作自己的；删除不删 `qa_rounds` |
| `PUT /api/kb/config` | 审计 `config_update`；可见字段名 = 本次 writable 键；无 Key/私钥/密码 |
| `POST /api/kb/reindex` | 审计 `reindex`，主体操作者 `ME_ID` |
| `GET /api/kb/admin/feedback-summary` | 被踩列表 `round_id` 集合 = 库内 `feedback=down`；无新采集口 |
| `POST /api/kb/admin/accounts` | 开户指定初始密码与角色 |
| `PATCH /api/kb/admin/accounts/{id}` | 启用/禁用/改角色；禁用立即作废 Session；不能去掉最后一名启用超管 |
| `GET/POST /api/kb/admin/roles`、`PUT .../permissions` | 勾选只用 `PERM_CHECKBOX`；超管角色清单不可改 |
| `POST /api/kb/admin/unlock` | 清失败次数后立即能登录 |
| `POST /api/kb/admin/tls` | 只保存 PEM，不启用 |
| `POST /api/kb/admin/tls/enable` | 校验通过才写开关；坏证书协议不变 |
| `POST /api/kb/admin/tls/disable` | 关闭回 HTTP |
| `GET /api/kb/admin/tls` | `scheme=http`、`redirect_https=false`（非标准端口）；无私钥 |

KDF：`pbkdf2_sha256`。无 `/auth/register`。

## 5. H5

- 四 Tab 有序：客户端 ↔ 后台、客户端交叉、文档索引、知识问答（回归保持，不升格为产品顺序）。
- 关系图 / 文档索引匿名；`app.js` / `kb.js` 不含 `"/api/kb"`。
- 未登录问答：`#qaLoginUser` / `#qaLoginPass` / `#qaLoginSubmit`；`#qaSend` 不得发出成功 ask。登出后再打开仍是登录墙。
- 顶栏无配置/重建/明细/热度四钮；保留 `#qaHealth`。账号菜单 {退出, 修改密码}。有「进管理模块」才有 `ADMIN_ENTRY` → `/kb-admin/`。
- 登录且有知识问答：空状态 `CHIP_FIXED` 四对 + 热度 chip 最多 4；未登录不请求 heatmap。热度**页**走管理站，要「功能热度」。
- 登录后对话列表权威为云端，不把 `hayyo-kb-qa-conversations-v1` 写入云端。

## 6. 管理站

- 自做 `site/kb-admin/`，不引用 admin-skin。
- 无「进管理模块」：顶栏无入口；URL 403。
- `ROLE_MINGXI` = {进管理模块, 问答明细}：能看明细；无配置/重建入口；`PUT config` / `POST reindex` → 403。
- 页级接口只按勾选，不叠加大门。只勾「问答明细」、不勾大门：无管理 UI，curl `GET /rounds` 仍可能 200。
- 证书 / 开户 / 解锁仅超管。后台无端口面板。

## 7. TLS 与 compose

- 上传 ≠ 启用。坏证书启用失败，对外仍 HTTP。
- Host 带非标准端口（如 `:18765`）即使已启用也不强制 301 HTTPS。
- compose 正文无 `0.0.0.0`；MySQL/Qdrant 仍绑 127.0.0.1。无 ACME、无后台改端口。
- 本机默认 `127.0.0.1:18765` HTTP 可登录问答。把 `HAYYO_TLS_PORT` 设为 443 才占宿主机 443。
- 标准 80/443 且已启用时的跳转：nginx `$kb_std_port` + `/tls/https.enabled`（默认环境未测特权端口）。

## 8. 查 bug 优先点

按越权 / 串数据 / 机密泄漏排，而不是按文件名扫。

1. **R-API-DOOR**：管理 UI 有大门，页级 API 没有。修「没入口却能改配置」时先分清是 UI 还是 API。
2. **提问人赞踩**：有明细权限的管理员不能改他人 `feedback`；不要改回匿名白名单。
3. **会话隔离**：`/conversations/{id}` 不得靠猜 id 读到别人；对话审计接口才能列全站 id。
4. **最后一名启用超管**：禁用或去掉超管角色必须 403，人数仍 ≥ 1。
5. **禁用踢会话**：禁用后旧 Cookie 调 `/me` 必须 401，不是「还能用到过期」。
6. **`user_id` 伪造**：ask 请求体里的 `user_id` 必须忽略。
7. **CONV_KEY**：登录成功路径不得把 localStorage 会话 POST 上云。
8. **审计泄漏**：`kb_audit_logs` / audits API 不得出现密码、PEM 私钥、API Key。
9. **热度双路径**：chips 用 `/heatmap` + 知识问答；管理页用 `/admin/heatmap` + 功能热度。不要把 chips 改成要「功能热度」。
10. **`qa.js` 残留 overlay**：顶栏四钮已删，但 `openConfig` / `openReindex` 等函数可能仍在；不应再挂回顶栏。
11. **health 仍匿名**：不要误把健康灯做成须登录，除非另开需求。
12. **证书**：启用失败不得改 `https.enabled`；GET tls 不得回显 key。
13. **compose**：禁止写 `0.0.0.0`；不要把宿主机 3306 映出来。
14. **「健康」勾选**：`PERM_CHECKBOX` 有该项，管理站也能勾；**不**挡住 `GET /api/kb/health`（该接口仍匿名）。没有 `GET /health`。

## 9. 回归锚点

| 文件 | 覆盖 |
|---|---|
| `site/kb-api/tests/test_auth_m1.py` | 引导、Cookie、锁定、改密、OPS 401/403 |
| `site/kb-api/tests/test_auth_m2.py` | 登录墙静态、ask 403、ROUND_UID、会话隔离 |
| `site/kb-api/tests/test_auth_m3.py` | 去四钮、admin-gate、ROLE_MINGXI、开户/禁用/解锁、对话审计 |
| `site/kb-api/tests/test_auth_m4.py` | 审计字段、反馈汇总、证书三态、compose 无端口面板 |
| `site/kb-api/tests/test_site_contract.py` | 四 Tab、无四钮、compose 127.0.0.1 与端口变量 |
| `site/kb-api/tests/test_feedback.py` | 赞踩带 Session |

比较键与验收符号定义见 [`../../design/kb-auth/steps-verified.md`](../../design/kb-auth/steps-verified.md) 比较表（`SESSION_DEAD`、`ROLE_MINGXI`、`AUDIT_CFG` 等）。
