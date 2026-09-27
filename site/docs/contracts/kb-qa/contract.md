# 知识问答主链路 · 实现契约

> 现行实现合同。给改检索 / 切块 / 重排 / 流式回答 / 日志的人与 AI 用。  
> 需求仍以 [`../../design/kb-qa/PRD-知识问答-v3.md`](../../design/kb-qa/PRD-知识问答-v3.md) 为准；本文件冻结**落地符号、接口形态、查 bug 优先点**。  
> 登录、会话隔离、运维入口见 [`../kb-auth/contract.md`](../kb-auth/contract.md)。赞踩 / 刷新 / 空状态 chips / 对话区样式见 [`../kb-qa-feedback/contract.md`](../kb-qa-feedback/contract.md)。  
> 阶段快照：`design/kb-qa/Hayyo-知识问答-M1…M4-契约草案.md`。**冲突以本文件为准**（M1「鉴权放行」、M4「顶栏明细 overlay / 鉴权本期放行」已作废）。  
> 契约总入口：[`../INDEX.md`](../INDEX.md)。日期：2026-09-20（对照现网代码合并）

## 1. 怎么用

| 你要做的事 | 读 |
|---|---|
| 改切块、两库、重建 | §2、§4 `reindex`、`chunking.py` / `indexer.py` |
| 改改写 / 分路 / 重排 / 数字校验 | §5、`pipeline.py`（**鉴权不要写进这两文件**） |
| 改 SSE 事件或健康检查 | §4 |
| 改问答 Tab 发送/出处/生成中锁 | §6、`qa.js` |
| 查串库、发明 ID、数字泄漏 | §7 |
| 对照回归 | §8 |

不要把本站问答写进 `prd/design/*/PRD.md`。不要用 h5-kb 附录 L3 当现行合同。

## 2. 落地符号

| 名 | 值 |
|---|---|
| HTTP 前缀 | `/api/kb`；浏览器只打本机 nginx，`proxy_buffering off` |
| 浏览器入口 | `http://127.0.0.1:18765/feature-interaction/`（默认 Tab 落地知识问答） |
| 切块源 | 只扫 `prd/design/<feature>/brief/current.md` 的 `chunk:default` |
| 跳过 | `chunk:no`、`chunk:related-row` |
| collection | `hayyo-client`；`feature_id=admin` → `hayyo-admin` |
| embedding | `text-embedding-v4`，1024 维，上限 8192 token；超长不入库、不二次切、不截断，进失败清单 |
| 重排 / 生成 | `qwen3.7-text-rerank` / `deepseek-flash`；thinking=关闭 |
| 默认配置 | K=64，n=8，历史=5，temperature=0.2；落盘 `DATA_DIR/kb-config.json` |
| 日志表 | `hayyo_kb.qa_rounds`（存法 B：浏览器会话 ≠ 轮次；删对话不删行） |
| Key | `DASHSCOPE_API_KEY`、`DEEPSEEK_API_KEY` 仅服务端；健康检查只回「已配置 / 未配置」 |

compose（现网）：`127.0.0.1` 发布；`HAYYO_WEB_PORT` 默认 18765→80，`HAYYO_TLS_PORT` 默认 18769→443，`HAYYO_MYSQL_HOST_PORT` 默认 18766→3306，`HAYYO_QDRANT_HOST_PORT` 默认 18767→6333。`kb-api` 不发布。禁止 `0.0.0.0`、禁止把宿主机 3306 映出来。TLS 细则见 kb-auth。

代码锚点：`site/kb-api/app/{main,pipeline,indexer,chunking,store,logs,config_store,settings}.py`，`site/feature-interaction/qa.js`。

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

只读名 = `READONLY_FIELDS`：embedding 型号/维度、重排型号、改写/回答型号、thinking=关闭、Key 状态、collection 名称、切块口径。  
可改名 = `WRITABLE_FIELDS`：召回 K、重排 n、历史轮数、temperature、系统 Prompt、改写 Prompt。  
保存只写可改项，对**后续轮**生效。Prompt 正文以 `settings.py` 现行常量为准，不要把过期默认文案抄进契约。

### `POST /api/kb/reindex`

成功：`ok=true`，含 `scanned`、`changed[]`、`failed[]`、`chunk_count`。清单行 `action ∈ {增,改,删,失败}`。缺 DashScope Key：HTTP 400，`error_type=missing_key`。Qdrant 不可用：503，`index_not_ready`。同 `(path, chunk_id)` 且 hash 相同不重复 embed；消失的点 `action=删`。

### `POST /api/kb/ask`

请求 JSON：`conversation_id, round_id, query, history[], last_chunks[]`。响应 `text/event-stream`。

| event | 数据要点 |
|---|---|
| `stage` | `rewrite` \| `retrieve` \| `rerank` \| `generate` |
| `rewrite` | `rewrite_query, same_topic, named_feature_ids`（仅仓库已有功能 ID） |
| `retrieve` | `mode=single\|multi, lanes[], paths[], count` |
| `rerank` | `c_gen[]` 公开身份（无全文 `content`，有 `excerpt`） |
| `token` | 流式增量 |
| `refuse` | 0 块系统拒答；`status=empty` |
| `citations` | 与本轮 `C_gen` 同一多重集 |
| `done` | `status ∈ {success,refuse,empty,interrupted}`；`log_written` |
| `error` | `type ∈ {missing_key,index_not_ready,rewrite_fail,retrieve_fail,rerank_fail,gen_fail}` |
| `log` | `{written:false}` 时前端提示「本轮日志未写入」 |

改写失败：不检索、不生成、无出处、无成功气泡。生成失败：丢弃半段，不展示成功气泡。客户端断开：`interrupted`，回答正文空。写库失败不改变问答主路径成败；明细与热度不含该轮。

库内 `status` 另有 `running, rewrite_fail, gen_fail`（写库用，不一定都出现在 SSE `done`）。

### 明细 / 热度

`GET /api/kb/rounds`、`GET /api/kb/rounds/{round_id}`：投影须等于写入快照。入口在管理站，**不是** H5 顶栏 overlay、不是第 5 个主 Tab。  
`GET /api/kb/heatmap`：按已写入行的 `C_gen.feature_id` **去重后 +1**（C34）；返回 `{items:[{feature_id,count,display_name}], unclassified}`。空路不计。无 `C_gen` 的写入轮计入「未归类」。`display_name` 由 `c20_display_name` 附加。热度**页**走 `GET /api/kb/admin/heatmap`（kb-auth）。

## 5. 检索、重排、回答

| 条件 | 行为 |
|---|---|
| `named_feature_ids` 长度 0 或 1 | 单路：两库 BM25+向量混合，K 取配置 |
| 长度 ≥2 | 每 ID 一路，`filter.feature_id` 等于该 ID；空路 `count=0, empty=true`，整轮继续 |
| 同主题 | 上一轮块并入重排池（`fill_block_content` 补正文） |
| 保底 | 点名 ≥2 时每个非空分路至少 1 块；点名数 > n 则 `n'=点名功能数` |

公开块身份（`public_c_gen` / `block_identity` 去掉 `content`）：`path, chunk_id, anchor, feature_id, collection, heading, excerpt, content_hash`。  
`named_feature_ids` 必须经 `filter_named_ids`，禁止发明功能 ID。  
出处 `(path, chunk_id)` 多重集 = 本轮 `C_gen`。回答数字集合 ⊆ `C_gen` 正文数字，否则改口文档未写（`post_check_answer`）。冲突：并列摘录、不选边。

## 6. H5 主链路

- 第四 Tab `data-view="qa"`；无过程栏（无 `#qaProcess`）。
- 发送：`POST /api/kb/ask`，`Accept: text/event-stream`。
- 出处点击：`GraphApp.setView('kb')` + `KB.openDocument(path, {hash, headingText})`；再回问答当前 `conv_id` 不变。
- `state.busy=true`：输入 / 发送 / 新建 / 清空 / 切换对话禁用或 toast「生成中」；本轮不中断。允许切到文档索引 `data-view=kb`。
- 未登录：登录墙，`#qaSend` 不得发出成功 ask（kb-auth）。
- 登录后对话列表权威为云端 `kb_conversations`；`CONV_KEY=hayyo-kb-qa-conversations-v1` 仅未登录本地备份，**不得 POST 上云**。
- 顶栏无配置/重建/明细/热度四钮（`qa.js` 里 `openConfig` 等函数可能残留，不得挂回顶栏）。

## 7. 查 bug 优先点

1. **发明功能 ID**：改写结果必须过滤；不要为了「召回更好」放行未知 id。
2. **公开身份漏正文**：`rerank` / `citations` 的 `c_gen` 不得带全文 `content`。
3. **数字泄漏**：生成后必须 `post_check_answer`；不要为了流畅关掉。
4. **超长块**：oversized 只进失败清单，禁止截断入库。
5. **切块源**：只扫 `brief/current.md` 的 `chunk:default`；不要改去扫 `PRD.md`。
6. **C34 热度**：按 `C_gen.feature_id` 去重计次，不要改成按 `named_feature_ids` 或空路。
7. **存法 B**：删云端/本地对话不得 DELETE `qa_rounds`。
8. **鉴权回退**：不要把 ask / heatmap 改回匿名；不要把明细入口做回 H5 顶栏第四钮。
9. **pipeline / indexer**：鉴权、Cookie、角色不要写进这两文件。
10. **健康检查**：不要把 Key 明文或 `GET /health` 加回来。

## 8. 回归锚点

| 文件 | 覆盖 |
|---|---|
| `site/kb-api/tests/test_rules.py` | 切块口径、别名、保底、数字校验、Prompt 迁移 |
| `site/kb-api/tests/test_retrieve_ops.py` | BM25/RRF、C34 热度 |
| `site/kb-api/tests/test_site_contract.py` | 四 Tab、无过程栏、无四钮 |
| `site/kb-api/tests/test_auth_m2.py` | ask 401/403、ROUND_UID |
| `site/kb-api/tests/test_auth_m3.py` | 去四钮、heatmap 权限 |

草案里「中间件放行」「顶栏问答明细 overlay」以本文件 §3 / §6 为准。
