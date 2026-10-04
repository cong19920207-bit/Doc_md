# 账号体系与管理模块 · 实现契约

> 现行实现合同。给改本站登录 / 问答身份 / 管理站 / 证书的人与 AI 用。  
> 账号基础需求见 [账号体系 v2](../../design/kb-auth/PRD-账号体系与管理模块-v2.md)；多轮编排后台增量见 [后台 v1.1](../../design/kb-qa-multdesign/PRD-Hayyo知识问答工作台管理后台-v1.1-正式确认版.md)。本文件记录当前实现，未落地条款见 §14。\
> 旧账号 M1～M4 与多轮编排 M1～M8 草案保留为阶段快照；当前实现以正式契约为准。整合映射和回归证据见 [专题进度](../../design/kb-qa-multdesign/steps-verified.md#2026-10-03-开发收尾与正式契约整合)。\
> 契约总入口：[`../INDEX.md`](../INDEX.md)。更新：2026-10-04。覆盖权限拆分、消息/执行审计、实际删除、配置发布、隔离测试、九工作区及文档迁移后的静态边界与 TLS 隔离。

## 1. 怎么用

| 你要做的事 | 读 |
|---|---|
| 改接口鉴权、401/403、Cookie | §3 鉴权矩阵、§4 API |
| 改 H5 登录墙 / 顶栏 / 会话 | §5、`site/feature-interaction/qa.js` |
| 改管理站入口或角色页 | §6、`site/kb-admin/`、nginx `/kb-admin/` |
| 查越权 / 串会话 / 漏打点 | §8 优先于翻 PRD |
| 对照回归 | §9 测试文件、专题进度 |
| 改对话审计、执行详情、实际删除 | §10 |
| 改配置、Prompt、调试、发布 | §11 |
| 改问题、知识来源、Memory 运维 | §12 |
| 改诊断、概览、热度、审计 | §13 |

不要写进 `site/core-docs/prd/design/auth-login` 或 `site/core-docs/prd/design/admin`。不要套 `workspace/_kit/admin-skin/`。不要改 `pipeline.py` / `indexer.py` 来做鉴权。

## 2. 落地符号

| 名 | 值 |
|---|---|
| Cookie | `hayyo_kb_sid`（HttpOnly、SameSite=Lax、Path=/、Max-Age=604800；Secure 仅 HTTPS） |
| 引导 | `KB_BOOTSTRAP_USER` / `KB_BOOTSTRAP_PASSWORD`（仅账号表空时创建一次） |
| 管理 URL | `/kb-admin/`；nginx `auth_request` → `GET /api/kb/auth/admin-gate` |
| 会话表 | `kb_conversations`；取消 40 条上限；用户删除为隐藏；超管实际删除见 §10 |
| 审计表 | `kb_audit_logs`（≠ `qa_rounds`） |
| 本地旧对话键 | `hayyo-kb-qa-conversations-v1`；**登录后不导入云端** |
| HTTP 端口 | `HAYYO_WEB_PORT` 默认 18765 → 容器 80 |
| TLS 端口 | `HAYYO_TLS_PORT` 默认 18769 → 容器 443；默认宿主机 443 连不上 |
| 证书目录 | `TLS_DIR`；缺省为 `DATA_DIR/tls`，Compose 显式设为 `/tls` |
| 证书开关 | `TLS_DIR/https.enabled`（Compose 为 `/tls/https.enabled`）；私钥不回显 |
| JWT | 无；响应体无 token；无自助注册 |

账号表仍为 `kb_roles`、`kb_role_permissions`、`kb_accounts`、`kb_sessions`、`kb_login_locks`、`kb_audit_logs`。消息/执行事实见 [kb-qa §9](../kb-qa/contract.md#9-消息事实执行版本与保存)；问题、索引任务和删除操作由对应 Store 启动建表/补列。已有卷不重跑 `init.sql`，启动迁移按缺列/索引增补，不能只依赖 `CREATE TABLE IF NOT EXISTS`。

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
| `GET /api/kb/auth/admin-gate` | **401** | 无「进管理模块」**403** | 204 |
| `GET /api/kb/health` | 200（仍匿名） | 200 | 200 |
| `POST /api/kb/ask` | 401（非 SSE done） | 无「知识问答」403 | SSE |
| `GET /api/kb/heatmap` | 401 | 无「知识问答」403 | 200（给 chips） |
| `GET /api/kb/admin/heatmap` | 401 | 无「功能热度」403 | 200（热度页） |
| `GET /api/kb/config` | 401 | 无「配置查看」且无「Prompt查看」403 | 按查看权限过滤 |
| `PUT /api/kb/config` | 401 | 参数须配置查看+编辑，Prompt 须 Prompt查看+编辑 | 保存草稿，混合字段全有权才写 |
| `POST /api/kb/config/publish`、`rollback` | 401 | 须配置发布+配置查看+Prompt查看 | 审阅修订并过发布门禁 |
| `POST /api/kb/config/discard`、`restore-draft` | 401 | 须两种查看+两种编辑 | 整包草稿操作 |
| `GET /api/kb/config/ops/{op_id}` | 401 | 无配置发布403 | 查已完成操作 |
| `/api/kb/admin/test-runs*`、`GET /api/kb/admin/test-cases` | 401 | 须 Prompt调试+Prompt查看+配置查看 | 本人测试/超管，来源另校验 |
| `POST /api/kb/admin/test-cases` | 401 | 无配置发布403 | 建立用例，当前无编辑/删除接口 |
| `POST /api/kb/reindex` | 401 | 无「重建」403 | 2xx |
| `GET /api/kb/rounds`、`GET /api/kb/rounds/{id}` | 401 | 无「问答明细」403 | 200 |
| `POST /api/kb/rounds/{id}/feedback` | 401 | 非提问人 403（管理员也 403） | 提问人 2xx |
| `/api/kb/conversations*` | 401 | 只能触达自己的 id；他人 404 | 自己的 CRUD |
| `GET /api/kb/admin/conversations*`、`GET /api/kb/rounds/{id}/context/{msg_id}` | 401 | 无「对话审计」403 | 保留事实与指定历史原文 |
| `POST /api/kb/admin/conversations/{id}/purge`、`GET /api/kb/admin/purge-ops/{op_id}` | 401 | 非超管403 | 实际删除 / 查结果 |
| `/api/kb/admin/issues*` | 401 | 无「问题处理」403 | 来源另按原文权限校验 |
| `/api/kb/admin/knowledge-sources*`、`GET /api/kb/admin/memory-coverage` | 401 | 无「知识源查看」403 | 受控来源与覆盖，禁止任意接入 |
| `GET /api/kb/admin/index-tasks*` | 401 | 无知识源查看且无重建403 | 任务分页与详情 |
| `POST /api/kb/admin/index-tasks/{id}/retry`、`memory-backfill`、`memory-coverage/complete` | 401 | 无重建403 | 重试/回填；手工宣告覆盖完成始终拒绝 |
| `GET /api/kb/admin/overview` | 401 | 无数据概览403 | 仅聚合 |
| `GET /api/kb/admin/diagnostics`、`GET /api/kb/admin/diag-events*`、`POST .../{id}/ack` | 401 | 无健康403 | 观察/标记已查看，不修复故障 |
| `GET /api/kb/admin/audits` | 401 | 无「操作审计」403 | 200 |
| `GET /api/kb/admin/feedback-summary`、`GET /api/kb/admin/feedback*` | 401 | 无「反馈汇总」403 | 200 |
| `/api/kb/admin/accounts*` `/roles*` `/unlock` `/tls*` `/perms` `/perm-migration` `/login-lock` | 401 | 非超管 403 | 超管 2xx |
| 浏览器 `GET /kb-admin/` | nginx **302 到 /login/** | 无大门 **403** | 页面 200 |

锁定：同一 `username` 连续 5 次失败锁 15 分钟；第 6 次即使密码正确 401。错密文案「用户名或密码不正确」；锁定含「稍后重试」。比较用户名不是 IP。

Session：绝对 7 天；登出 / 改密 / 禁用 → `SESSION_DEAD`（须登录接口 401）。不强制首次改密。

普通用户预设角色初始只有「知识问答」，权限按角色分配，不在账号上逐项勾选；超管 `is_super` 视为全勾选。`PERM_CHECKBOX` 现为 18 项：知识问答、进管理模块、配置查看、配置编辑、Prompt查看、Prompt编辑、Prompt调试、配置发布、重建、问答明细、功能热度、对话审计、健康、操作审计、反馈汇总、知识源查看、数据概览、问题处理。旧「配置」停用且不自动映射到新权限，`/admin/perm-migration` 报告受影响角色和账号数；`PENDING_PERMS` 当前为空。

`GET /chunk` 与本人 `GET /rounds/{exec_id}/status` 要「知识问答」，状态查询不走「问答明细」。本人会话接口只校验登录与归属，不额外要求知识问答。

写接口校验 Origin，缺省看 Referer；按 hostname 与 Host 或 `KB_TRUSTED_ORIGINS` 比较（不是完整 scheme/port 比较）。`Origin: null` 拒绝；两头均缺失允许非浏览器调用。拒绝为 403 `csrf_rejected`。

## 4. API 终态

| 方法路径 | 行为要点 |
|---|---|
| `POST /api/kb/auth/login` | Set-Cookie；体 `{ok,id,username}` |
| `POST /api/kb/auth/logout` | 作废 Session、清 Cookie |
| `GET /api/kb/auth/me` | `id` = `ME_ID`；带 `permissions` / `is_super` |
| `POST /api/kb/auth/password` | 旧密+新密；成功后该账号全部 Session 死；审计无密码 |
| `POST /api/kb/ask` | `user_id` 只取 Session，忽略请求体 `user_id`；现网 `owner_id` / `tenant_id` / `role` 仍可读请求体写入日志 |
| `POST /api/kb/rounds/{id}/feedback` | 仅提问人；写库失败不阻断问答链路 |
| `GET/POST /api/kb/conversations` | 按 `ME_ID` 隔离，无 40 条淘汰；用户列表 offset 分页 |
| `GET/PUT/DELETE /api/kb/conversations/{id}` | 只能操作自己的；删除为隐藏，清空走独立服务端边界接口 |
| `PUT /api/kb/config` | 只写草稿；审计 `config_update` 记录字段名，不记录正文或密钥 |
| `POST /api/kb/reindex` | 审计 `reindex`，主体操作者 `ME_ID` |
| `GET /api/kb/admin/feedback-summary` | 保留旧入口；当前版本绑定反馈与新列表见 kb-qa-feedback §9 |
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

- 四 Tab 有序：知识问答、客户端 ↔ 后台、客户端交叉、文档索引（2026-10-03 用户明确要求问答优先）。
- 整站页面由 nginx `/_kb_site_gate` 登录保护，关系图和文档索引也需 Session；未登录跳 `/login/?next=...`。`/login/` 及 API 自鉴权例外；静态阅读本身不依赖模型/Qdrant。
- 未登录问答：`#qaLoginUser` / `#qaLoginPass` / `#qaLoginSubmit`；`#qaSend` 不得发出成功 ask。登出后再打开仍是登录墙。
- 顶栏无配置/重建/明细/热度四钮；保留 `#qaHealth`。账号菜单 {退出, 修改密码}。有「进管理模块」才有 `ADMIN_ENTRY` → `/kb-admin/`。
- 登录且有知识问答：空状态 `CHIP_FIXED` 四对 + 热度 chip 最多 4；未登录不请求 heatmap。热度**页**走管理站，要「功能热度」。
- 登录后对话列表权威为云端，不把 `hayyo-kb-qa-conversations-v1` 写入云端。

### 5.1 独立登录页（2026-10-03）

- `/login/` 自带匿名可加载的 `login.css`、`login.js`、`ion-scene.js` 和内联H图标，不依赖登录后工作台资源。桌面为离子互动区与登录表单双栏，小屏按自身样式收缩；不受工作台主题存储控制。
- 登录模块底部按“Hayyo｜你的知识，有处可寻｜浙ICP备2026035072号-2”排列，文案无句号，分隔线样式及两侧间距一致；备案号链接工信部备案查询网站，沿用底部字号和颜色，窄屏换行后不保留行首分隔线。
- `#loginForm` 复用 `/auth/me` 和 `/auth/login`，已有Session直接进入目标。`next` 只接受站内单斜线开头且无反斜线/协议的路径，拒绝再次进入login路径，其他值回退 `/feature-interaction/`。
- 提交期间禁止重复请求、按钮禁用并设置 `aria-busy`；失败保留输入并用文本提示，成功清空密码后跳转。密码显隐更新 `aria-pressed`/名称，不改变登录载荷。
- 动效有离子涡环、引力扭结、星核脉动、流光薄膜、H共振五种形态，支持自动/三种手选颜色、拖动、鼠标拖尾和代码雨。暂停、页面隐藏与不可见时停止动画调度；减少动态效果偏好默认静态，显式形态/颜色控件仍可用；WebGL不可用保留静态背景，不影响登录表单。显示恢复不能覆盖用户暂停选择。
- 自动化回归：`site/login/tests/login.test.cjs`（请求、重定向、显隐与失败反馈）、`scene-controls.test.cjs`（静态偏好、暂停、恢复和WebGL回退）。

## 6. 管理站

- 自做 `site/kb-admin/`，不引用 admin-skin，不跟随 H5 主题。页面怎么摆：[`../../design/kb-admin-ui/INDEX.md`](../../design/kb-admin-ui/INDEX.md)。
- 无「进管理模块」：问答顶栏无入口；URL 403。
- 壳为顶栏 + 九工作区：总览、问答、问题、配置、知识与记忆、调试、运行状态、操作记录、访问管理。无内容的入口不显示；工作区不等于权限。按原接口权限独立请求，页面打开不自动调用模型、重建或回填。
- 顶栏健康点仅当角色有「健康」，保留原健康字段；运行状态工作区读取完整依赖诊断。`GET /api/kb/health` 继续匿名。
- `ROLE_MINGXI` = {进管理模块, 问答明细}：能看总览里的失败轮次和问答「全部轮次」；无配置、重建、热度、反馈、记录、访问。`PUT config` / `POST reindex` → 403。
- 页级接口只按勾选，不叠加大门。只勾「问答明细」、不勾大门：无管理 UI，curl `GET /rounds` 仍可能 200。
- 证书 / 开户 / 解锁仅超管，都在「访问管理」；证书是单独页签。后台无端口面板。

## 7. TLS 与 compose

- Web 只读挂载 `site/release/www` 为 `/usr/share/nginx/html`；API 只读挂载 `site/core-docs` 为 `/core-docs`。两处 bind mount 均禁止 Docker 在源缺失时自动创建空目录。不得重新挂载整仓库或整个 `site` 为 Web 根；文件选择、保留页面例外及本地刷新以 [H5 契约 §8](../h5-kb/contract.md#8-核心文档与受控发布) 为准。
- `/`、`/site`、`/site/` 重定向到 `/feature-interaction/`，工作台与已发布的 `/prd/...` 仍经 Session 门保护；不能由访问地址获得管理员身份。`/kb-admin/` 另经管理员门，已登录但无「进管理模块」返回 403。
- `autoindex off`，历史选单使用生成的 JSON；未发布文件不存在于 Web 根，兜底路径返回 404。不存在合法首页的目录不提供文件列表。保留的 `/admin-skin-demo/` 与两个复盘汇总页也受登录门保护；旧 `/workspace/_kit/admin-skin/...` 仅为该原型的 URL 跳转，不开放其他工作区。`/docs/`、`/site/docs/` 及物理 `/site/core-docs/...` 不是文档公开入口。
- 证书存储由 `TLS_DIR=/tls` 指定，使用独立 `kb-tls-data` 卷（API 可写、Web 只读）。API 数据仍在 `kb-api-data:/data`，Web 不挂载该数据卷。API 启动调用 `TlsStore.migrate_legacy(DATA_DIR)`，完成后 Web 才按 API 健康检查启动。
- 旧 `/data` 迁移只复制 `cert.pem`、`key.pem`、`pending-cert.pem`、`pending-key.pem`、`state.json`、`https.enabled`，保留原件；新旧同名内容冲突或符号链接会报错，不覆盖目标。未完成迁移可补齐缺失文件；成功写入 `/tls/.legacy-migrated`，后续启动不覆盖新证书。配置、审计等其他数据不得随证书迁移进入 TLS 卷。

- 上传仅保存待启用证书；`pending` 标明与活动证书不同或尚未启用，`last_enable_error`、`last_enable_error_at` 记录最近启用失败；`port_note` 说明非标准端口行为。坏证书启用失败不替换活动证书、不改变现有开关。
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
| `site/kb-api/tests/test_core_docs_migration.py` | TLS 独立目录、白名单复制、冲突保护、中断恢复和后续启动不覆盖 |
| `site/kb-api/tests/test_publication.py` | 发布产物排除源码、配置、测试和未授权工作区文件 |

追加回归：`test_m3_admin_base.py`、`test_m4_admin_observe.py`、`test_m7_exec.py`、`test_m7_index.py`、`test_m7_issues.py`、`test_m7_purge.py`、`test_m8_config.py`、`test_m8_rest.py`、`test_admin_review_regressions.py`（均在 `site/kb-api/tests/`）；管理站原生 Node 交互回归在 `site/kb-admin/tests/admin-contract.test.cjs`，覆盖角色确认/预览、超管只读和固定规则只读。测试通过范围见专题进度，不由本表推定真实模型质量。

比较键与验收符号定义见 [`../../design/kb-auth/steps-verified.md`](../../design/kb-auth/steps-verified.md) 比较表（`SESSION_DEAD`、`ROLE_MINGXI`、`AUDIT_CFG` 等）。

迁移后的实际 HTTP 角色矩阵、文档 URL、目录列表及 TLS 本地验证见[迁移执行记录](../../design/core-docs-migration/execution/核心文档迁移开发执行记录.md)。生产尚未部署，生产证书迁移及标准 80/443 跳转未在本轮实测；不能由本地证据推定线上状态。


## 10. 对话审计、执行详情与实际删除

### 10.1 列表与事实读取

后台分页统一由 `listing.py` 输出 `items, next_cursor, has_more, total, coverage{complete,note}, data_cutoff, time_field, stored_tz, tz`；默认 50、最多 200，游标以时间+id 保持稳定。无可计算总数时为 null，不以当前页长度冒充总量。存储 UTC，默认按 Asia/Shanghai 解释日期；错误游标400 `bad_cursor`，读取失败503 `list_unavailable`，不能显示成无数据。旧 rounds 未传page_size时默认limit=100、上限500；显式page_size走统一规则。按feature_id的旧筛选只在最近limit条内过滤并标coverage不完整；用户会话仍为offset分页，不能混用。

- `/admin/conversations` 可按账号、会话、标题/消息关键词、时间、可见性、是否清空和交互状态筛选，包含隐藏但排除实际删除。关键词扫描有5000候选上限，覆盖受限须说明；旧历史缺少信息不填完整回合数。更新时间筛选与末条消息时间分开。
- `/admin/conversations/{id}` 按 seq 展示服务端已保存事实、清空边界、隐藏标志、逻辑回合与所有回答版本；查看旧版不切换采用版本。旧 payload 只作有限只读兼容，不覆盖消息事实。
- `/rounds/{id}` 的 `exec_view` 分七组：输入与上下文、路由与任务、历史恢复、改写与知识、生成/检查/修正、预算与异常、交付与保存。六类状态独立，旧版缺失明示未知。
- 明细中的历史 id 不等于正文权限。`/rounds/{id}/context/{msg_id}` 要对话审计且该消息确在快照引用中；执行查看者不能由 id 扩大到全会话原文。敏感读取记审计，跳转目标继续校验自身权限。

### 10.2 超管实际删除

`POST /admin/conversations/{conv_id}/purge` 要超管、明确 `confirm` 会话 id；与用户隐藏不同。操作先持久化 running，再设置 `purged_at`/隐藏及缓存屏障，阻断继续写入和来源副本读取；屏障失败不继续删正文。清理服务端消息、Runtime、Memory/索引，以及关联问题和测试副本中的正文。问题标题、现象、关闭依据和追加记录均清理；保留必要关系/状态和最小审计，不复制新正文。

响应含 op_id；重复请求返回已有操作，`GET /admin/purge-ops/{op_id}` 查持久状态。部分失败是 partial，不记成功；结果写入无法确定时503 `purge_result_unknown`，不能重试后猜成功。当前不承诺清理数据库备份、外部副本或已经被用户另存的内容。所有者普通 DELETE 不执行此清理。

## 11. 配置包、Prompt 与隔离测试

### 11.1 草稿、发布和版本

- 配置落盘 `DATA_DIR/kb-config.json`。`GET /config` 分别过滤参数/Prompt 的 writable、readonly、draft、published、history；同时返回权限、package_id、draft_rev、固定规则、话术池和预算。
- `PUT /config` 只保存草稿；可带期望 `rev`，冲突409 `draft_conflict`，冲突中的草稿也按权限过滤。混合字段必须同时满足各自查看和编辑；审计实际动作名为 `config_update`。
- `POST /config/publish` 须已审阅的精确 `rev`、非空说明并通过发布门禁。`op_id` 绑定操作类型和修订，重复同一操作返回已有结果；复用为别的操作/修订409。操作记录及单调修订跨重启保留；`/config/ops/{op_id}` 只查已完成结果。
- 发布、草稿、历史和操作记录一起以临时文件、fsync、原子替换保存；落盘失败回退内存。ask 受理时深拷贝生效包，在途执行不受后来发布影响。
- `POST /config/rollback` 将历史整包作为一次新发布，仍过门禁；含旧40条淘汰或 schema=v0/0 的包拒绝。页面走 `/config/restore-draft` 恢复历史整包为新修订草稿，审阅测试后再发布；`/config/discard` 只丢弃精确修订草稿，修订不归零。恢复/丢弃整包须两种查看和两种编辑。
- L1 10回合/5000tokens、最多一次修正、当前会话范围和取消40条淘汰均为固定规则，写入拒绝。Key、模型、collection 只读；已配置不代表可用。故障重试、分类兜底、在线换模型尚未接入。
- `history_recovery=false` 只停用历史追溯，L1 仍有效。显式追溯预算缺字段/空值/0不能发布启用；默认未配置预算使用代码默认有限值，不能解释为无限；parallel 不得大于 calls。
- ack 与 out_of_scope 两个话术池分别配置和取用，发布时都必须有启用文本，不互借；不得含密钥。旧 `history_turns` 与 `rewrite_prompt` 仅兼容存储，前者不再截断 L1、后者不再覆盖 Rewriter；`system_prompt` 仍实际生效。

### 11.2 Prompt 与页面行为

注册职责：router、task_prep、rewriter、check、repair、smalltalk、clarify、restate、recall 已接入；generate 为未接入，禁止保存 `prompts.generate`。已接入职责都读取执行所绑定包的正文，启动不以旧默认覆盖已发布正文。

`prompts.py/check_prompts` 当前只检查登记/接入状态、非空、职责必需关键词与 Router 禁词（tool_call/function_call/tools）。没有完整变量/Schema/渲染/长度静态验证，不能将保存成功等同于结构或模型质量通过。页面可以预览将发送的原文，预览不调用模型。

配置三个页签共用草稿表单，切换不丢输入；固定规则只读。独立发布者可审阅发布但无保存按钮；离开未保存配置/角色须提示。发布先显示实际差异与非空说明，提交所审阅的修订，冲突不能自行抓新版本发布。取消审阅后隐藏说明不妨碍保存。旧页面异步响应不得覆盖新工作区；具体页面规则以 [管理站页面规则](../../design/kb-admin-ui/INDEX.md) 为准。

### 11.3 隔离调试与关键用例

- `POST /admin/test-runs` 异步202；GET列表/详情/compare读取持久结果，存储 `DATA_DIR/tests/book.json`，重启遗留 queued/running 标 interrupted。结果只给本人或超管，读取/对比时复核来源当前权限与有效性。
- 调试统一须 Prompt调试+Prompt查看+配置查看。会话导入须对话审计、显式 message_ids；按 exec_id 导入须问答明细，仅给该次提问/回复，不能带入无权历史。真实知识须知识问答或知识源查看；合成输入不要求原文权限。
- 单职责走实际模型/解析器，整链路复用 `_ask_flow`。消息、Runtime、Memory 在测试副本中；Memory 独立 collection，embedding 计入预算；合成 Knowledge 明示合成。隐藏/清空/实际删除使来源副本失效，结果查询不能继续展示失效正文。
- 有限预算控制调用、步骤、估算tokens与秒数，默认16/24/24000/120；服务端分别计算 schema_ok、biz_resolved、预期拒答和断言，不信客户端 passed。simulate_tool 是模拟证据，不能冒充真实通过或满足发布。
- 对比独立标注输入、来源和时间基准是否相同。测试不写生产消息/Runtime/Memory、不计生产概览或热度；测试数据域单独统计，估算tokens不是供应商计费值。
- `/admin/test-cases` 当前仅GET列表、POST建立；建立须配置发布。关键用例必须同用例版本、精确配置修订与快照、来源仍有效且实际达到预期；未完成预算不能通过。无关键用例阻断发布，非关键失败仅警告。
- 发布按改动实际职责检查分支覆盖，两话术池各自经过对应分支；停用追溯可由整链路验证，不强制跑已停用 Recall。当前采用整修订保守失效，不复用无关字段变更前的旧测试；通过不保证零幻觉。

## 12. 问题、知识来源与索引任务

### 12.1 问题闭环

`GET/POST /admin/issues`、`GET/POST /admin/issues/{id}`、`POST /admin/issues/{id}/notes`：问题处理权限、单一处理人、open/doing/closed，可重开；处理记录只追加。关联反馈、执行、索引任务或异常由服务端查源并绑定真实会话，不能信客户端 conv_id 或因此获得源正文权限。关联本身不复制长正文；实际删除清理副本，见 §10。

关闭必须有依据，声称已验证须有 retested；发布配置不自动关闭问题。反馈仍是提问人对特定版本的评价，管理员处理问题不改用户赞踩。详细反馈关联见 [反馈契约 §9](../kb-qa-feedback/contract.md#9-管理反馈列表与问题关联)。

### 12.2 知识来源与任务

- `/admin/knowledge-sources`、`/admin/knowledge-sources/detail` 仅列受控 brief，详情返回当前块内容/hash/索引一致性。不存在或读取失败如实报错；不接纳任意路径或新来源，POST拒绝。来源列表游标分页。
- `POST /reindex` 为 Knowledge 重建；`POST /admin/memory-backfill` 为 Memory 回填；`GET /admin/index-tasks`、`/{id}` 查任务，`POST /{id}/retry` 建新任务并关联原任务，保留旧失败记录。
- 重叠受理检查全部运行中任务，不能只查最近100条；MySQL命名锁串行受理。不同知识/Memory任务按范围冲突，部分失败计真实失败，不宣称完成；任务分页、阶段、进度和详情由 `index_tasks.py` 管理。
- `GET /admin/memory-coverage?conv_id=` 返回实际覆盖、应索引/已索引、空洞、积压、失败、generation、来源质量和 stale_ids；不带聊天正文。旧时间不可靠标受限，不能确定的数量为null。`manual_complete=false`，POST `/admin/memory-coverage/complete` 始终400 `manual_complete_forbidden`。
- 回填/重建不恢复用户隐藏或清空可见性；Memory 是派生索引，消息事实源与检索范围仍以 kb-qa §11 为准。

## 13. 审计、诊断与运行概览

### 13.1 写操作审计

审计字段含 op_id、result（accepted/success/failed/unknown）、error_code、object_type、操作者角色、changed_fields、before_ver/after_ver、relation、reason。高风险操作先持久 accepted，失败503 `audit_unavailable` 并阻断业务写；同一审计行补最终结果，补写失败保留 accepted 待核实，不重复执行或补造成功。敏感读取的审计尽力记录，失败不扩大读取权限。

密码、API Key、私钥、完整 Prompt/问答正文不进审计；明文变化以字段名、版本和关系表达。审计完整性计数为进程内观测，重启清零；页面空列表不能证明历史无失败。

### 13.2 诊断与异常

`GET /admin/diagnostics` 只主动探测 MySQL/Qdrant，不调用模型、不重建；消息、Runtime、Knowledge、Memory、模型、配置、审计分别呈现。Memory连接和绑定生效包读取当前状态，Key只说明已配置。事件存 `DATA_DIR/diag/events.jsonl`，5MB轮转并保留.1～.3；失败使用有界进程内缓冲（最多500），明确 observation.limited。

`GET /admin/diag-events`、`/{id}` 读事件，`POST /{id}/ack` 仅追加已查看记录，不解除保存阻塞/删除失败，也不代表故障修复。关联会话/执行入口仍查目标权限；日志不存消息正文。模型诊断只覆盖已有上报点，Router错误当前保留在Runtime，尚无对应旁路 model_error 事件，不能由“诊断无错误”断言链路无故障。

### 13.3 统计与热度

`GET /admin/overview` 默认生产域，默认7天、最大92天，按执行 created_at 和明确时区计算；真实SQL聚合，无旧前端缓存拼总数。请求/逻辑回合/执行、业务/技术/检查/保存、非知识分支、未知旧记录分别计数；比例须保留分子分母，不能把未知当成功或零失败。调用次数来自call_usage，供应商计费tokens未记录。测试域来自test book，状态、调用与估算用量另计。

`GET /admin/heatmap` 的v2口径按真正使用Knowledge且有选用功能的执行去重，旧记录另列。扫描有20000上限，coverage说明截断；chips旧 `/heatmap` 窗口5000仍单独兼容。总览“需关注”条件为非success或被踩，分页前筛选；不是“问题未处理”，关闭关联问题不改变历史执行结果。

## 14. 当前限制与验收边界

- Generate完整职责未接入；Prompt静态验证未覆盖原STEP所列完整变量/Schema/渲染/长度；关键测试用例只有建立与列表，没有编辑/删除接口。这些有效需求仍未完成，不因本次契约同步而取消。
- 诊断“是否仍在发生”等完整筛选/下钻、执行详情部分筛选尚未完整落地；Router旁路诊断缺口见 §13.2。真实模型输出质量、故障场景与供应商计费不由自动化替身测试证明。
- 发布结果采用整修订失效；故障重试/分类兜底/在线换模型未接入；不把模拟工具结果计作真实发布证据。
- 消息/版本/Memory的剩余边界见 kb-qa §12。开发批次与文档收尾的状态、历史证据和本轮验证分列在专题进度；不能据本契约宣称整个PRD已验收通过。
