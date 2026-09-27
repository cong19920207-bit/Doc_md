---
title: "Hayyo-知识问答-M3-契约草案"
status: "IMPLEMENTATION_INCREMENT"
milestone: "M3"
created: "2026-09-17"
note: "已实现接口增量。改写/检索/重排/流式依赖两 Key，闸门证据未齐。执行器不判定里程碑通过。"
---

# Hayyo-知识问答-M3-契约草案

覆盖 STEP-009～015、006；008 再问在本里程碑联测。

## `POST /api/kb/ask`

请求 JSON：`conversation_id, round_id, query, history[], last_chunks[]`。账号四字段可空。响应 `text/event-stream`。

| event | 数据要点 |
|---|---|
| `stage` | `rewrite` \| `retrieve` \| `rerank` \| `generate` |
| `rewrite` | `rewrite_query, same_topic, named_feature_ids`（仅已有功能 ID） |
| `retrieve` | `mode=single\|multi, lanes[], paths[], count` |
| `rerank` | `c_gen[]` 公开身份（无全文 `content`，有 `excerpt`） |
| `token` | 流式增量 |
| `refuse` | 0 块系统拒答；`status=empty` |
| `citations` | 与本轮 `C_gen` 同一多重集 |
| `done` | `status ∈ {success,refuse,empty,interrupted}`；`log_written` |
| `error` | `type ∈ {missing_key,index_not_ready,rewrite_fail,retrieve_fail,rerank_fail,gen_fail}` |
| `log` | `{written:false}` 时前端提示「本轮日志未写入」 |

改写失败：不检索、不生成、无出处、无成功气泡。生成 5xx：丢弃半段，不展示成功气泡。客户端断开：`interrupted`，回答正文空。

## 检索与重排

| 条件 | 行为 |
|---|---|
| `named_feature_ids.length` 为 0 或 1 | 单路：两库 BM25+向量混合，K 取配置 |
| `length≥2` | 每 ID 一路，`filter.feature_id` 等于该 ID；空路 `count=0, empty=true`，整轮继续 |
| 同主题 | 上一轮块并入重排池 |
| 保底 | 点名 ≥2 时每个非空分路至少 1 块；点名数 > n 则 `n'=点名功能数` |

公开块身份：`path, chunk_id, anchor, feature_id, collection, heading, excerpt, content_hash`。

## 回答与出处

- 出处 `(path, chunk_id)` 多重集 = 本轮 `C_gen`。
- 回答数字集合 ⊆ `C_gen` 正文数字；否则改为声明文档未写。
- 冲突：提示词要求并列摘录、不选边。
- 点击出处：`GraphApp.setView('kb')` + `KB.openDocument(path, {hash, headingText})`；再回问答 `conv_id` 不变。

## 生成中锁定

`state.busy=true` 时：输入/发送/新建/删除/切换对话禁用或 toast「生成中」；本轮不中断。允许切到文档索引 `data-view=kb`。
