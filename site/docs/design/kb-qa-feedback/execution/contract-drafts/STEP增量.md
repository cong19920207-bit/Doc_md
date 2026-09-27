# STEP 契约增量（非正式）

> 2026-09-18 执行器记录。非正式契约，不替代里程碑 `M{n}-契约草案.md`。  
> 正式路径仍按实施计划：三里程碑闸门通过后再定。

## API

- `POST /api/kb/rounds/{round_id}/feedback`  
  body：`{ "feedback": "up" | "down" | null }`  
  成功：返回该轮行。无此轮：404。非法值：400。
- `GET /api/kb/rounds/{id}` / 列表：行内可含 `feedback`、`feedback_at`。
- `GET /api/kb/heatmap`：仍 `{items, unclassified}`；`items[]` 额外 `display_name`（C20），**不改** `heatmap()` 计数公式。顶栏热度页仍展示 `feature_id`。

## 存储

- `qa_rounds.feedback` VARCHAR(16) NULL，枚举空/`up`/`down`
- `qa_rounds.feedback_at` DATETIME(3) NULL
- 新卷：`init.sql`。已有卷：启动 `LogStore.ensure_feedback_columns()`
- 浏览器消息：`round_id`、`logWritten`、`query`、`historySnapshot`、`lastChunksSnapshot`、`feedback`（空/赞/踩）
- 存储键仍为 `hayyo-kb-qa-conversations-v1`；pending 不落盘

## UI

- 操作条：有正文 `{复制, 赞, 踩, 刷新}`；纯错误 `{刷新}`
- 右侧 `.qa-col`：max-width 768px，水平 padding 24px；消息与输入同宽
- 空状态：`CHIP_FIXED` 4 条；heatmap 前 4 个 `feature_id` 追加 `C20(fid) 有哪些现行规则？`
- 契约测试：允许 qa.js chips；禁止 `#qaProcess`；四 Tab 与顶栏入口不变
