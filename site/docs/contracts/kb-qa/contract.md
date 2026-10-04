# 知识问答主链路 · 实现契约

> 现行实现合同。给改检索 / 切块 / 重排 / 流式回答 / 日志的人与 AI 用。  
> 检索基线见 [`知识问答 v3`](../../design/kb-qa/PRD-知识问答-v3.md)；多轮编排增量见 [`Phase1 v1.10`](../../design/kb-qa-multdesign/PRD-知识问答多轮对话编排-Phase1-v1.10.md)。本文件记录当前实现，不把尚未落地的 PRD 条款写成已完成。\
> 登录、会话隔离、运维入口见 [`../kb-auth/contract.md`](../kb-auth/contract.md)。赞踩 / 刷新 / 空状态 chips / 对话区样式见 [`../kb-qa-feedback/contract.md`](../kb-qa-feedback/contract.md)。  
> 旧 kb-qa M1～M4 与多轮编排 M1～M8 草案保留为阶段快照；已经被后续实现替代的过渡条款不再是当前契约。整合映射和验证见 [`多轮编排进度`](../../design/kb-qa-multdesign/steps-verified.md#2026-10-03-开发收尾与正式契约整合)。\
> 契约总入口：[`../INDEX.md`](../INDEX.md)。更新：2026-10-04。已整合多轮编排、回答过程、工作台调整与文档迁移后的扫描边界；验证范围与剩余项以进度记录为准。

> 核心文档路径映射与静态发布的共同约定见 [H5 契约 §8](../h5-kb/contract.md#8-核心文档与受控发布)；本契约负责扫描、知识块与旧引用兼容。生产未部署，验证范围见[迁移执行记录](../../design/core-docs-migration/execution/核心文档迁移开发执行记录.md)。

## 1. 怎么用

| 你要做的事 | 读 |
|---|---|
| 改切块、两库、重建 | §2、§4 `reindex`、`chunking.py` / `indexer.py` |
| 改改写 / 分路 / 重排 / 数字校验 | §5、`pipeline.py`（**鉴权不要写进这两文件**） |
| 改 SSE 事件或健康检查 | §4 |
| 改问答 Tab 发送/出处/生成中锁 | §6、`qa.js` |
| 查串库、发明 ID、数字泄漏 | §7 |
| 对照回归 | §8、§12 |
| 改消息、清空、刷新、幂等、保存 | §9 |
| 改 Router、任务、交付检查 | §10 |
| 改 Memory、追溯、回看 | §11 |

不要把本站问答写进 `site/core-docs/prd/design/*/PRD.md`。不要用 h5-kb 附录 L3 当现行合同。

## 2. 落地符号

| 名 | 值 |
|---|---|
| HTTP 前缀 | `/api/kb`；浏览器只打本机 nginx，`proxy_buffering off` |
| 浏览器入口 | `http://127.0.0.1:18765/feature-interaction/`（默认 Tab 落地知识问答） |
| 物理文档根 | `CORE_DOCS_ROOT`；本机默认 `site/core-docs`，Compose 为 `/core-docs`；旧 `REPO_ROOT` 不再读取 |
| 切块源 | 文档根内的 `prd/design/<feature>/brief/current.md`，只扫 `chunk:default`；公开 `path` 仍为 `prd/...` |
| 跳过 | `chunk:no`、`chunk:related-row` |
| collection | `hayyo-client`；`feature_id=admin` → `hayyo-admin` |
| embedding | `text-embedding-v4`，1024 维，上限 8192 token；超长不入库、不二次切、不截断，进失败清单 |
| 重排 / 生成 | `qwen3.7-text-rerank` / `deepseek-flash`；thinking=关闭 |
| 默认配置 | K=64，n=8，temperature=0.2；L1 固定最多 10 个完整回合 / 5000 tokens；配置包落盘 `DATA_DIR/kb-config.json` |
| 日志表 | `hayyo_kb.qa_rounds`（每次执行一行；用户隐藏保留，超管实际删除按 kb-auth §10 清理） |
| Key | `DASHSCOPE_API_KEY`、`DEEPSEEK_API_KEY` 仅服务端；健康检查只回「已配置 / 未配置」 |

compose（本地配置，生产未部署本次变更）：`127.0.0.1` 发布；`HAYYO_WEB_PORT` 默认 18765→80，`HAYYO_TLS_PORT` 默认 18769→443，`HAYYO_MYSQL_HOST_PORT` 默认 18766→3306，`HAYYO_QDRANT_HOST_PORT` 默认 18767→6333。`kb-api` 不发布。禁止 `0.0.0.0`、禁止把宿主机 3306 映出来。TLS 细则见 kb-auth。

代码锚点：`site/kb-api/app/{main,pipeline,indexer,chunking,store,logs,config_store,settings,msg_store,conv_store,l1,migrate,router,tasks,branches,evidence,memory_index,memory_tool,recall,conv_task,answer_process}.py`，`site/feature-interaction/qa.js`。

## 3. 鉴权（本功能叠加，不重复矩阵）

现行中间件见 kb-auth。对本功能：

| 路径 | 要点 |
|---|---|
| `GET /api/kb/health` | **仍匿名** |
| `POST /api/kb/ask` | 须登录 +「知识问答」；未登录 401（不是 SSE `done`） |
| `GET /api/kb/heatmap` | 须登录 +「知识问答」（给 chips，不是热度页） |
| `GET\|PUT /api/kb/config`、`POST /api/kb/reindex`、`GET /api/kb/rounds*` | 页级勾选，不叠加「进管理模块」 |

`user_id` 写入 `qa_rounds` 时取 Session 账号 id，忽略请求体 `user_id`。现网 `owner_id` / `tenant_id` / `role` 仍可读请求体（未剥离）。

## 4. API 终态

### `GET /api/kb/health`

字段：`qdrant_ready`、`config_ready`、`key_dashscope` / `key_deepseek`（已配置 \| 未配置）、`chunk_count`（≥0）、`index_ready`、`startup_error`。响应不得含 Key 字符串。无 `GET /health`。

### `GET/PUT /api/kb/config`

配置查看与 Prompt 查看按权限分别过滤；编辑按所提交字段分别鉴权。`PUT` 只保存草稿，必须经过发布才影响后续新接受的执行；在途执行使用接受时拷贝的配置包。版本、修订冲突、发布、回退、固定规则和 Prompt 槽位的唯一契约见 [kb-auth §11](../kb-auth/contract.md#11-配置包prompt-与隔离测试)。

旧 `history_turns`、`rewrite_prompt` 仅保留兼容存储：前者不再截断服务端 L1，后者不再作为 Rewriter 正文生效。模型、Key、collection、固定规则只读；Key 状态不代表连接可用。

### `POST /api/kb/reindex`

知识重建现在纳入索引任务，受「重建」权限与高风险写审计约束，响应保留扫描/变更/失败信息并附任务记录。进行中的重叠任务返回 409；任务分页、详情、重试及部分失败见 [kb-auth §12](../kb-auth/contract.md#12-问题知识来源与索引任务)。

物理根为 `CORE_DOCS_ROOT`（容器 `/core-docs`，本机默认 `site/core-docs`），扫描清单为该根内 `prd/llm-manifest.json` 的 `scan_roots`。只从匹配 `site/core-docs/prd/design/<id>/PRD.md`（兼容逻辑 `prd/design/<id>/PRD.md`）的条目提取功能，再读取对应 PRD/brief；不是遍历整仓库，也不自动索引新增文档分类或历史版本。

根目录、清单、PRD 或 brief 缺失、功能没有可索引章节、重复知识块标识、brief 越出文档根时，在索引写入前中止；异常不作为合法空语料清除旧索引。仅迁移物理目录时，逻辑 `path`、`chunk_id`、正文 `content_hash`、collection 和由路径/块 ID 派生的点 ID 保持原值，不重写既有问答引用。功能别名与改写提示也从新文档根读取。

启动索引扫描失败时，`startup_error` 保留错误；若能读取已有 Qdrant 点，仍可恢复 BM25，`index_ready` 按已有块数判断。`index_ready=true` 不代表此次扫描成功；已有索引亦不可恢复时为 false。缺模型 Key 的启动分支仍先验证语料，再加载已有索引，不以缺 Key 为由跳过语料保护。

切块仍只扫描受控 brief：同 `(path, chunk_id)` 且 hash 相同不重复 embed；消失的点删除；超长块记失败，不截断。缺 Key / 索引不可用如实失败，不当作零变更成功。

`site/kb-api/tests/test_core_docs_migration.py` 覆盖默认根、稳定逻辑路径、异常语料与空扫描不触碰向量库；文件迁移完整性及实际点 ID/旧引用验证见[迁移执行记录](../../design/core-docs-migration/execution/核心文档迁移开发执行记录.md)。原引用接口的 hash 校验与 404/409/503 约定仍按 §10.3，目录迁移不改变它们。

### `POST /api/kb/ask`

请求 JSON：`conversation_id, round_id, query, client_request_id, op_type`；刷新另带 `logical_round_id`。`round_id` 是兼容名称，表示本次 `exec_id`，不是逻辑回合 id。`history[]`、`last_chunks[]` 不再作为事实输入，L1 与刷新快照均由服务端读取。响应 `text/event-stream`。

| event | 数据要点 |
|---|---|
| `accepted` | User 已保存或刷新已接受：`conversation_id, logical_round_id, exec_id, user_msg_id, seq, op_type` |
| `stage` | 实际阶段，包括 `route`、`task_prep`、`rewrite`、`retrieve`、`rerank`、`generate`、`check`、`repair`，及非知识/历史分支 |
| `process` | `{exec_id, process}`，实际执行过程的完整展示快照 |
| `rewrite` | `rewrite_query, same_topic, named_feature_ids`（仅已有功能 ID） |
| `retrieve` | `mode=single\|multi, lanes[], paths[], count` |
| `rerank` / `citations` | 公开块身份，不含来源全文；知识出处来自本次 `C_gen` |
| `token` | 流式草稿增量，核对后才形成交付结果 |
| `check` | `check_status, replaced, text, round_id`；替换为修正稿或失败说明 |
| `refuse` | 重排无证据的说明，兼容 `status=empty` |
| `done` / `error` | 保留 `status, round_id, log_written`；增加逻辑回合/执行/消息 id、六类 `statuses`、`msg_save, op_type, version_no, adopted, save_blocked, error_type`；按实际路径附历史引用与过程 |
| `log` | `{written:false}` 表示 Runtime 未写入，不推定消息也未保存 |

User 写失败不启动模型。Assistant 保存与 Runtime 保存分别表达，不能用一个 `success` 推定两者均成功。错误包括保存/幂等/忙碌、Router/任务/改写、检索/重排/生成、检查/修正与总超时；字段与终态按实际路径给出，不补造没有执行过的结果。

客户端断线只结束订阅，后台执行继续。没有收到终态时，前端查询 `GET /api/kb/rounds/{exec_id}/status`，不重发 ask；约每 1.5 秒查询一次、最多约 6 分钟。该接口须「知识问答」且仅本人可见执行，非本人/不存在/会话不可见统一 404 `round_not_found`。返回 `terminal, derived, statuses, text, completeness, c_gen, process` 和版本/保存信息。无断点补流；服务重启遗留执行在读取时按中断报告（`service_interrupted`），不因此改写数据库旧行。

执行总截止 300 秒；续执行权租期不延长总截止。超时取消在途调用，保存错误说明，`exec_state=failed, error_type=exec_timeout`；晚到结果不得改写终态。

### 回答过程增量（2026-10-03）

- 过程由 `answer_process.py` 的 `AnswerProcess` 投影实际编排事件，展示实际任务、查询内容、候选/选用片段数量、来源、核对及修正状态。只出现已执行的步骤；不会为闲聊补检索步骤，不输出 Prompt、内部推理文本或来源全文。
- `process = {version:1, exec_id, state, summary, document_count, steps[]}`；每步为 `{id, stage, title, state, details[], sources[]}`。过程状态为 `running/completed/failed/interrupted`，步骤状态为 `running/done/warning/error`。修正后的第二次核对是独立步骤，第一次问题记录保留。
- 原有 SSE 事件保留；实际阶段变化后追加 `process`，`done/error/refuse` 同时携带最新快照。token 不写入过程，过程文字不调用额外 LLM。
- 按执行版本保存 `qa_rounds.answer_process JSON NULL`；已有卷启动时补列。`GET /api/kb/rounds/{exec_id}/status` 返回该版本的 `process`；无旧过程数据时为 `null`，不补造。
- `GET /api/kb/conversations/{conv_id}/answer-history` 返回 `{authoritative, messages[]}`，按服务端有效消息和逻辑回合恢复各回答版本、过程、出处及反馈。只允许会话所有者读取；隐藏会话、清空边界外内容不暴露。`authoritative=false` 时前端兼容原展示缓存。
- thinking 核查：`models_ext.py` 的普通/流式请求显式发送 `thinking.type=disabled`，SSE 解析仅消费 `delta.content`。现有 HTTP 400 兼容重试会移除 `thinking` 参数，因此该回退是否启用推理由提供方默认决定；本增量保留这一策略，没有开启 thinking。

过程是实际执行事件的展示投影，不额外调用 LLM；多轮职责、检查修正与断流机制按本文件 §9～§11。

### 明细 / 热度

`GET /api/kb/rounds`、`GET /api/kb/rounds/{round_id}`：投影须等于写入快照。入口在管理站，**不是** H5 顶栏 overlay、不是第 5 个主 Tab。  
`GET /api/kb/heatmap`：按已写入行的 `C_gen.feature_id` **去重后 +1**（C34）；返回 `{items:[{feature_id,count,display_name}], unclassified}`。空路不计。新记录（`schema_ver≥2`）还须 `used_knowledge_rag=1`；非知识分支不计。旧记录按旧口径单列 `legacy_count`、`legacy_rows`、`unclassified_legacy`。读取窗口仍为最近 5000 行；`C_gen` 无可归属功能时计入相应未归类。`display_name` 由 `c20_display_name` 附加。热度**页**走 `GET /api/kb/admin/heatmap`（kb-auth）。

## 5. 检索、重排、回答

| 条件 | 行为 |
|---|---|
| `named_feature_ids` 长度 0 或 1 | 单路：两库 BM25+向量混合，K 取配置 |
| 长度 ≥2 | 每 ID 一路，`filter.feature_id` 等于该 ID；空路 `count=0, empty=true`，整轮继续 |
| 同主题 | 上一轮块并入重排池（`fill_block_content` 补正文） |
| 保底 | 点名 ≥2 时每个非空分路至少 1 块；点名数 > n 则 `n'=点名功能数` |

公开块身份（`public_c_gen` / `block_identity` 去掉 `content`）：`path, chunk_id, anchor, feature_id, collection, heading, excerpt, content_hash`。  
`named_feature_ids` 必须经 `filter_named_ids`，禁止发明功能 ID。  
出处 `(path, chunk_id)` 多重集 = 本轮 `C_gen`。块外数字由 `post_check_answer` 返回 `numbers_ok=false` 并纳入证据检查失败，最多修正一次；不得只附提示后照常交付。冲突按来源并列、不裁决。检查详情见 §10。

## 6. H5 主链路

- 知识问答 `data-view="qa"` 为第一个 Tab；每条回答可有独立的 `.qa-process` 过程区，展开/收起规则见 [反馈与样式契约 §6.1](../kb-qa-feedback/contract.md#61-回答过程2026-10-03)。本次用户确认覆盖旧版「无过程栏」约束。
- 发送：`POST /api/kb/ask`，`Accept: text/event-stream`。
- 出处点击：`GraphApp.setView('kb')` + `KB.openDocument(path, {hash, headingText})`；再回问答当前 `conv_id` 不变。
- `state.busy=true`：输入 / 发送 / 新建 / 清空 / 切换对话禁用或 toast「生成中」；本轮不中断。允许切到文档索引 `data-view=kb`。
- 未登录：登录墙，`#qaSend` 不得发出成功 ask（kb-auth）。
- 登录后对话列表权威为云端 `kb_conversations`；`CONV_KEY=hayyo-kb-qa-conversations-v1` 仅未登录本地备份，**不得 POST 上云**。
- 顶栏无配置/重建/明细/热度四钮（`qa.js` 里 `openConfig` 等函数可能残留，不得挂回顶栏）。

## 7. 查 bug 优先点

1. **发明功能 ID**：改写结果必须过滤；不要为了「召回更好」放行未知 id。
2. **公开身份漏正文**：`rerank` / `citations` 的 `c_gen` 不得带全文 `content`。
3. **数字泄漏**：数字检查结果必须进入 Evidence check；失败草稿不得作为有效版本交付。
4. **超长块**：oversized 只进失败清单，禁止截断入库。
5. **切块源**：只扫 `brief/current.md` 的 `chunk:default`；不要改去扫 `PRD.md`。
6. **C34 热度**：按 `C_gen.feature_id` 去重计次，不要改成按 `named_feature_ids` 或空路。
7. **删除边界**：用户隐藏不删事实；超管实际删除会清理消息、Runtime、Memory 与关联副本，不能把旧「不删日志」扩大到该管理操作。
8. **鉴权回退**：不要把 ask / heatmap 改回匿名；不要把明细入口做回 H5 顶栏第四钮。
9. **pipeline / indexer**：鉴权、Cookie、角色不要写进这两文件。
10. **健康检查**：不要把 Key 明文或 `GET /health` 加回来。

## 8. 回归锚点

| 文件 | 覆盖 |
|---|---|
| `site/kb-api/tests/test_rules.py` | 切块口径、别名、保底、数字校验、Prompt 迁移 |
| `site/kb-api/tests/test_retrieve_ops.py` | BM25/RRF、C34 热度 |
| `site/kb-api/tests/test_site_contract.py` | 四 Tab、无旧全局 `#qaProcess`、无四钮 |
| `site/kb-api/tests/test_answer_process.py` | 真实步骤、调用次数、持久化版本、异常、检查修正及可见性边界 |
| `site/kb-api/tests/test_auth_m2.py` | ask 401/403、ROUND_UID |
| `site/kb-api/tests/test_auth_m3.py` | 去四钮、heatmap 权限 |

草案里「中间件放行」「顶栏问答明细 overlay」已失效。多轮编排回归锚点追加如下：

| 文件 | 覆盖 |
|---|---|
| `test_m1_conv_facts.py` | 逐消息事实、隐藏、清空、L1 |
| `test_m2_exec_versions.py` | 幂等、互斥、刷新、补存、反馈资格 |
| `test_m5_orchestration.py` | 分路、任务、改写、检查修正、断线与截止 |
| `test_m6_memory.py` | 迁移、索引、检索范围、追溯预算、历史回看 |
| `test_admin_review_regressions.py` | 已发布职责正文、完整 L1、测试隔离等跨模块回归 |

上述 Python 文件位于 `site/kb-api/tests/`；回归结果见专题进度，表格不代表所有真实模型质量已验收。


## 9. 消息事实、执行、版本与保存

### 9.1 存储和标识

| 对象 | 当前含义 |
|---|---|
| `kb_conversations` | 账号会话；`last_seq, clear_seq, hidden_at` 管理顺序与可见性；`run_exec_id, run_until` 管理执行权；`save_block_exec_id` 表示保存阻塞；`purged_at` 由管理实际删除使用 |
| `kb_conv_messages` | 一条实际消息一行；`seq` 在会话内唯一；`round_id` 为 `lr-` 逻辑回合；`round_seq` 为该回合 User 的 seq；请求幂等约束 `UNIQUE(conv_id, client_request_id)` |
| Assistant 版本 | 一次执行对应一条 Assistant/一个版本，`version_no, is_current, exec_id, op_type, completeness` 分别标识；刷新不新增 User |
| `kb_conv_clears` | 每次清空记 `boundary_seq, actor_id` |
| `qa_rounds` | Runtime 每执行一行；`schema_ver=2`，六类状态分开；`snapshot, pending_reply, router, task_prep, rewrite, call_usage, evidence_check, recall, history_refs, answer_process` 为 JSON；`finished_at` 在终态写入，补存不改变 |

新库由 `sql/init.sql` 建表，旧卷由各 Store 启动时查缺补列/索引。消息事实源与 Runtime 分开，不能用客户端 payload 覆盖已保存的原文。

六类状态：

| 字段 | 值 |
|---|---|
| `biz_result` | answered / partial / insufficient / refused / clarify / not_applicable / conflict / missing_context |
| `exec_state` | running / completed / failed / interrupted |
| `check_status` | pass / fail / error / not_run |
| `text_integrity` | complete / truncated / empty |
| `msg_save` | saved / failed / pending / not_applicable |
| `runtime_save` | saved / partial / failed |

空值表示未知。无 `schema_ver` 的旧记录六类状态均返回 null，不补成成功。Runtime 插入阶段为 partial，终态更新成功才为 saved；消息保存结果独立。

### 9.2 会话和消息接口

以下均以 `/api/kb` 为前缀，要求登录且只能操作本人会话；隐藏后本人接口返回 404。

| 方法与路径 | 当前行为 |
|---|---|
| `GET /conversations` | 无 40 条上限；`offset, limit` 分页，默认 50、上限 200，返回 `items, next_offset`；不返回隐藏会话 |
| `POST /conversations` | 创建本人会话 |
| `GET/PUT /conversations/{id}` | 本人读取/更新；已有消息事实时忽略 PUT 的 `messages`；响应带 `saveBlockedExecId` |
| `DELETE /conversations/{id}` | 账号级隐藏，写 `hidden_at`，不删消息/Runtime/Memory；不会恢复到其他设备 |
| `GET /conversations/{id}/messages` | `after_seq, limit`；`items, next_after_seq, clear_seq`，只给有效消息 |
| `POST /conversations/{id}/clear` | 服务端写清空边界；失败 503 `clear_fail`，不伪装清空成功 |
| `GET /conversations/{id}/messages/{msg_id}` | 历史引用回源；不可见 404 `message_not_found`，读取失败 503 `source_unavailable` |
| `GET /conversations/{id}/answer-history` | 见 §4，恢复有效消息、回答版本和过程；前端登录加载/切换会话时读取，兼容缓存并未全部删除 |
| `POST /conversations/{id}/retry-save` | 只补存同一回复，不重生成；可带 `exec_id`；不一致 409 `exec_mismatch`，仍失败 503 `retry_save_fail`，承载丢失 `save_source_lost` 并解除阻塞 |

用户有效范围统一为 `round_seq > clear_seq`。L1、Memory、历史引用、回答版本恢复均遵守清空和隐藏边界；管理员对话审计可按自身权限查看保留事实，见 kb-auth。

### 9.3 L1、互斥、刷新和补写

- L1 只从服务端有效消息组装，最多 10 个完整回合、5000 tokens，整轮保留或淘汰。中日韩按 1 字约 1 token，其余约 4 字符 1 token；原因 `turn_limit/over_budget/empty/read_fail` 记入快照。失败提示、中断片段和不可靠迁移回合不充作完整上下文。
- 同一会话同时只运行一个发送/刷新，执行权租期 300 秒；新阶段续租，终态释放。受理先插 Runtime，再校验归属、查重、抢执行权、保存 User。User 保存失败不调用模型；忙碌返回 `conversation_busy` 和运行执行 id；保存阻塞返回 `save_blocked`。被拒请求仍可有执行记录，但不计新逻辑回合或 Knowledge 调用。
- `client_request_id` 用于发送/刷新幂等；重复请求返回 `duplicate_request` 与既有执行信息，不重新回答。
- 刷新带 `logical_round_id`，原问句与上下文从服务端首次快照读取，包括 `l1_msg_ids, prev_exec_id, cut_seq, time_base`。旧快照缺消息时明确 `snapshot_limited`，不使用今天的上下文补造原现场。旧客户端未带逻辑回合 id 的刷新仅走兼容路径。
- 新回答保存成功、兼容状态为 success/refuse/empty 且交付检查未失败时才采用；事务内切换 `is_current`。失败提示、部分文本、保存失败、检查未通过均不替换原有效版本。
- 首次保存 Assistant 失败后保存补写承载，同文自动重试两次，间隔 0.5 秒、1 秒；仍失败阻塞当前会话。补存只改消息保存字段及关联 id，不重新执行模型、不改业务结果或终态时间。进程内兜底承载重启会丢失，不能承诺一定补回。
- 前端丢弃非当前目标 exec_id 的流事件；忙碌/阻塞保留用户原文；刷新失败恢复原版本；查看旧版只读，不切换服务端采用版本。反馈唯一语义见 kb-qa-feedback。

### 9.4 旧历史迁移

`migrate.py` 启动时仅迁消息表尚无任何行的云端会话，可重复执行。User 与紧随的 Assistant/system 配对；pending 跳过、孤立回答丢弃并记录原因。能与同会话执行、原问句和可靠时间对应的为 `source=migrated`；否则 `migrated_ltd`、exec_id 为空、时间为占位，不进 L1 或按时间定位，但无时间条件时可作为受限候选。迁移不重置清空边界、不恢复隐藏。单会话失败不阻断启动；报告 `DATA_DIR/migrate/q06-report.json` 不存正文。

## 10. 多轮编排与可靠交付

### 10.1 Router 和非知识分支

Router 输出 `route, requires_history, confidence, reason`；route 仅 knowledge_query / conversation_task / ack / smalltalk / out_of_scope / unclear。requires_history 必须 JSON 布尔，confidence 为 0～1 数值且非布尔，reason 非空；多余字段只记录键名。任一非法为 `router_invalid`，调用失败/空响应为 `router_fail`，不降级 unclear、不检索、不重试。低置信度只记录，不自动兜底。

| 分支 | 行为 |
|---|---|
| ack | 独立确认话术池取一句，Router 后不再调用模型；biz_result=not_applicable |
| out_of_scope | 独立范围话术池取一句；biz_result=refused |
| smalltalk | 一次 Smalltalk 调用，使用 L1；不调用 Knowledge/Memory |
| unclear | 一次 Clarification 调用，严格输出非空 `clarification`；不把技术失败冒充反问 |
| knowledge_query / conversation_task | 先做任务准备；纯回看/重述按 §11，其余进入知识链路 |

知识依赖检查在需要知识的分支内。非知识分支仍依赖 Router 及其实际模型需求；不能理解为缺任何 Key 均可工作。两个话术池不得互借，空池 `reply_pool_empty`；闲聊/澄清失败分别记 `smalltalk_fail/clarify_fail/clarify_invalid`。

### 10.2 任务、缺口和改写

- 任务准备输出 `tasks, excluded, information_gaps, response_constraint`；最多 6 个任务，id 唯一；依赖必须存在且不能成环。准备阶段 check 只认 ready / needs_history / needs_user_input / ambiguous / blocked_by_dependency / out_of_scope；knowledge_insufficient 和 error 留给执行阶段。
- 输出非法/调用失败为 `task_prep_invalid/task_prep_fail`，不降级单任务、不重试。就绪项合并执行一次知识链路，缺条件或越界项明确说明；混合交付为 partial。
- 跨轮承接取清空边界之后最近逻辑回合的当前版本，只有 clarify/partial 才恢复原任务、候选和未完成项；不受 L1 窗口限制，不把已交付项自动重做。
- Rewriter v3 输出 `status=ready|needs_context, standalone_query, response_constraint, missing_context[], confidence, named_feature_ids, same_topic`。ready 需非空 query、无缺口；needs_context 将 query 置空且必须有缺口，task_id 必须属于本轮就绪任务。旧 `rewrite_query` 是 standalone_query 的适配字段。
- `same_topic` 只决定复用上轮块，不等于 requires_history。功能 id 仍过滤；任一非法为 rewrite_fail。
- 缺用户条件走澄清；缺历史对象按 §11 同一执行预算追溯，必要时再改写一次；不重新跑 Router。追溯关闭或仍缺材料时说明受限，不把未知写成无规则。

### 10.3 生成、引用与证据检查

- Generate 输入含原句、独立问句、任务/缺口、回答约束、本地提问时间、知识只有当前 brief 的版本说明，以及必要历史原文。刷新沿用原 time_base。历史回答只用于理解，不是现行规则证据；新证据推翻旧结论应更正，冲突并列。
- 要求避免重复或核验时须携带对应此前回答；现有核验目标仍取 L1 最近回答。必需交接缺失报 `generate_contract_fail`。
- 公开来源带 `content_scope=full|excerpt`；仅有摘要时不冒充全文，清空不对应正文的 hash。`GET /api/kb/chunk?path=&chunk_id=&content_hash=` 在原文打开前复核：404 `source_not_found`、409 `source_changed`、503 `source_unavailable`，不在 hash 不符时返回新正文。
- Evidence check 输出 `check_status=pass|fail, issues[{answer_span,evidence_ids,reason}], conflict`。证据 id 只能来自本轮；pass 与问题列表为空一致；非法或空输出/超时是检查异常，不能放行。
- 首检失败、尚未修正且总截止剩余至少 120 秒时，最多一次修正并复查。块外数字加入 fail。检查/修正无技术重试；复查仍失败只保存失败说明，不采用错误稿；检查异常为 error_notice。非知识、澄清或说明出口为 not_run。
- Runtime 记录检查轮次、证据身份、草稿 hash、修正次数、预算停止原因与最终 hash，不存被淘汰草稿全文或证据正文；`call_usage` 由服务端累计，任何分支不归零。
- 任务和交接仍通过请求内 cfg 的 `_task_brief/_task_ids/_handoff` 传入 Pipeline；完整 Generate 职责槽位尚未接入，当前 system_prompt 仍生效，见 kb-auth §11。

## 11. Conversation Memory 与历史回看

### 11.1 派生索引与范围

消息表是事实源，`hayyo-conv-memory` 是独立 Qdrant 派生 collection；1024 维向量、600 字分片，记半开字符区间。User 及已保存、完整、非空 Assistant 才应索引；错误提示和部分回答不计应索引。`kb_mem_index` 以 msg_id 为键，含 conv_id/seq、status(pending/indexed/failed)、chunks、content_hash、attempts/error、gen、updated_at。

保存后异步索引，启动回填缺口；索引失败不阻断消息保存。覆盖按每条应索引消息和 hash 检查：normal / partial / lagging / failed / unknown / not_connected；末尾未完成与中间空洞区分，无连接不能当零命中。用户隐藏/清空不删点；实际删除清点与记录。

MemoryScope 由服务端绑定 account_id、conv_id、before_seq、exclude_round_id、time_base。只查当前会话有效边界内、本问之前且非当前回合的消息。搜索后回源再次检查隐藏、清空、删除和归属，不信客户端扩展范围；跨会话拒绝。

### 11.2 工具与追溯预算

关键词与向量每个缺口各最多 20 条，RRF 合并并重排，最多 5 个候选；没有固定分数阈值，不把第一名当作已确认。重排不可用回退融合顺序并标明；向量故障与关键词结果分别报告。单次 15 秒，不技术重试。

`read` 支持 self/prev/next/around，一次最多 3 回合；长消息只给命中附近最多 1500 字并标范围。时间使用 KB_DISPLAY_TZ 和 time_base；明确时间只在区间内定位，模糊时间最多向前后各放宽一个同等跨度，标已放宽；migrated_ltd 不参与按时间定位。

缺历史对象时才进入受控追溯。默认预算：调用 6 次、判断 4 步、同一步最多派发 3 项、恢复原文最多 6000 tokens；单次 read 最多 3 回合；总截止剩余不足 60 秒不再派发。两处追溯共用同一预算，不归零；预算任一为 0 即关闭，配置包可在合法范围调整或明确停用历史恢复。一次 search 的子查询当前顺序执行，派发上限不等于实际并行执行。

动作只认 search/read/handoff/clarify/finish，服务端校验。只可交接本执行实际读到的回合；连续两步没有新来源停止；多个合理候选需澄清，依赖对象变化需重开相关缺口。没找到只说明当前可检索范围，覆盖不全时加注，不声称从未发生。Runtime recall 只存 id、状态、原因和预算，不存原文。

### 11.3 回看、旧版本与重述

conversation_task 且全部就绪任务为回看/重述时，在知识依赖检查前执行，不调用 Knowledge RAG。回看原样返回已存原文，并标未重新核验、回合/角色/版本/时间；选择旧版本只读，不更改 is_current。仅重述只调整表达并保留不确定性，失败不把原文冒充重述；多轮且目标未指明时使用 L1 指认或澄清，不猜最后一轮。

历史引用含 conversation_id、round_id、message_id、role、version_no、time、time_reliable、range、completeness；存 `history_refs` 并随 done 返回。点击走 §9.2 历史消息接口复核，正文仅放前端内存，不写入展示缓存。

## 12. 当前限制与验证边界

- 无断点补流；重启遗留执行只在读取时报告中断。进程内保存承载或诊断计数重启会丢失。
- 逐任务 knowledge_insufficient 与逐任务拆开检查/交付尚未完整实现，多任务集中检查一份草稿；核验目标仍固定为 L1 最近一条回答。
- 旧 payload 兼容缓存仍存在，但 answer-history 已用于登录加载和切换会话恢复服务端版本；不得再笼统写“前端只读 payload”。
- 不做跨会话记忆、长期记忆、开放式工具循环。配置未接入项与后台诊断限制见 kb-auth §14。
- 自动化替身测试不证明真实模型质量或供应商计费 token；历史真实模型和浏览器证据可在前提不变时复用，本轮结果及未验证范围见进度记录。
