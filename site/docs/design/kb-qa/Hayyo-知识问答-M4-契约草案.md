---
title: "Hayyo-知识问答-M4-契约草案"
status: "IMPLEMENTATION_INCREMENT"
milestone: "M4"
created: "2026-09-17"
note: "已实现接口增量。interrupted/停库/成功投影缺 RUNTIME。执行器不判定里程碑通过。"
---

# Hayyo-知识问答-M4-契约草案

覆盖 STEP-017、018、019、020。

## 存法 B

浏览器会话 ≠ MySQL 轮次。删对话不删 `qa_rounds`。

表 `hayyo_kb.qa_rounds`：`round_id` PK；`conv_id`；原句/改写/`same_topic`/`named_feature_ids`/`lanes`/`c_gen`/`answer`；`status ∈ {running,success,refuse,rewrite_fail,gen_fail,empty,interrupted}`；`models` JSON；账号四字段可空。

写失败不改变问答主路径成败；SSE 提示「本轮日志未写入」；明细与热度不含该轮。

生成未结束且客户端断开、写库成功：`status=interrupted`；UI 成功气泡不含半段正文。

## 明细 `GET /api/kb/rounds` / `GET /api/kb/rounds/{round_id}`

详情投影字段：原句、改写句、`named_feature_ids`、每路 `(feature_id,count,empty)`、`C_gen` 元数据与 `excerpt`、回答全文或错误态、`status`。须等于写入快照。

入口：顶栏「问答明细」。形态 overlay，不是第 5 个主 Tab。关闭后 `conv_id` 不变。`MAIN_TAB_NODES` 仍 = `MAIN_TABS`。

## 热度 `GET /api/kb/heatmap`

按已写入行的 `C_gen.feature_id` 去重后 +1（C34）。返回 `{items:[{feature_id,count} 降序], unclassified}`。空路不计。无 `C_gen` 的成功写入轮计入「未归类」。入口 overlay，同样不是主 Tab。

## 现网三 Tab（020）

| 对象 | 约定 |
|---|---|
| 关系图 | `setView('admin'\|'client')` 现网路径；`.app` 无 `kb-active`；`#kbWorkspace` hidden |
| 文档索引 | `#kbSearch` 结果 ≤20；path 来自现网关键词索引，不是向量 `chunk_id`；该次请求 URL 不含 `/api/kb` |
| 停 Qdrant 后 | 仍可打开已知文档 P，`KB.getCurrentPath()=P` |
| 鉴权 | 中间件预留，本期放行 |
