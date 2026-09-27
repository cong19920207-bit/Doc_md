---
title: "Hayyo-知识问答-M2-契约草案"
status: "IMPLEMENTATION_INCREMENT"
milestone: "M2"
created: "2026-09-17"
note: "已实现接口增量。重建与「K 对检索生效」缺 Key，闸门证据未齐。执行器不判定里程碑通过。"
---

# Hayyo-知识问答-M2-契约草案

覆盖 STEP-007、008、016。008「再问反映新文」仍归 M3 联测。

## 索引

| 对象 | 约定 |
|---|---|
| 切块 | 只扫 `prd/design/<feature>/brief/current.md` 的 `chunk:default` |
| 跳过 | `chunk:no`、`chunk:related-row` |
| collection | `hayyo-client`；`feature_id=admin` → `hayyo-admin` |
| embedding | `text-embedding-v4`，维度 1024，上限 8192 token；超长不入库、不二次切、不截断，进失败清单 |
| payload | `path, feature_id, chunk_id, section, heading, anchor, content, content_hash, collection`；`user_id/owner_id/tenant_id/role` 本期空串 |
| 对账 | 同 `(path, chunk_id)` 且 hash 相同不重复 embed；消失的点 `action=删` |

## `POST /api/kb/reindex`

成功：`ok=true`，含 `scanned`、`changed[]`、`failed[]`、`chunk_count`。

清单行：`path, chunk_id, action ∈ {增,改,删,失败}, old_hash, new_hash`；失败行另有 `reason`。

缺 DashScope Key：HTTP 400，`error_type=missing_key`。Qdrant 不可用：503，`index_not_ready`。

## 配置 `GET/PUT /api/kb/config`

只读名集合 = `READONLY_FIELDS`：embedding 型号、embedding 维度、重排型号、改写/回答型号、thinking=关闭、Key 状态、collection 名称、切块口径。

可改名集合 = `WRITABLE_FIELDS`：召回 K、重排 n、历史轮数、temperature、系统 Prompt、改写 Prompt。

Key 状态 ∈ {已配置, 未配置}。保存只写可改项到 `DATA_DIR/kb-config.json`，对后续轮生效，本轮进行中不变。

默认：K=64，n=8，历史=5，temperature=0.2。型号只读：`qwen3.7-text-rerank`、`deepseek-flash`、thinking=关闭。
