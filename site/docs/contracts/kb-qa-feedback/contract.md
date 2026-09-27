# 知识问答 · 反馈与对话样式 · 实现契约

> 现行实现合同。给改赞/踩/刷新、空状态 chips、右侧对话排版的人与 AI 用。  
> 需求仍以 [`../../design/kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md`](../../design/kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md) 为准。  
> 不修订 v3 主链路；检索公式、切块、Prompt 以 [`../kb-qa/contract.md`](../kb-qa/contract.md) 为准。提问人身份以 [`../kb-auth/contract.md`](../kb-auth/contract.md) 为准。  
> v1 在 `design/kb-qa-feedback/history/`，不默认读。日期：2026-09-20（对照现网代码）

## 1. 怎么用

| 你要做的事 | 读 |
|---|---|
| 改复制 / 赞 / 踩 / 刷新 | §3、§4、`qa.js` `actionBarHtml` / `setFeedback` / `regen` |
| 改空状态建议问句 | §5、`CHIP_FIXED`、`refreshHeatChips` |
| 改对话区宽度 / 输入卡片 | §6、`qa.css` `.qa-col` |
| 查明细反馈、越权改赞踩 | §7 |
| 对照回归 | §8 |

不要把本增量写进 `design/kb-qa/` 或 `prd/design/`。不要加「链接」「更多」键。

## 2. 落地符号

| 名 | 值 |
|---|---|
| 库字段 | `qa_rounds.feedback`：`up` / `down` / 空；`feedback_at` |
| 界面文案 | 赞 / 踩 / 未评价（`feedbackUiFromRow`） |
| 写接口 | `POST /api/kb/rounds/{round_id}/feedback`，体 `{feedback: "up"\|"down"\|null}` |
| 未写入提示 | `UNWRITTEN_HINT` =「本轮日志未写入，反馈不会进明细」 |
| 常驻 chips | `CHIP_FIXED` 四条（全文既是 title 也是 query） |
| 热度 chips | heatmap Top 4，问句 = `{display_name\|\|feature_id} 有哪些现行规则？`（**不是**名为 `CHIP_HEAT` 的常量） |
| 内容柱 | `.qa-col` `max-width: 768px` |
| 明细反馈展示 | 管理站问答明细（H5 顶栏不再放明细钮；`qa.js` overlay 函数可能残留） |

代码锚点：`site/feature-interaction/qa.js`、`qa.css`、`site/kb-api/app/logs.py` `set_feedback`、`main.py` `set_round_feedback`。

## 3. 鉴权与归属

| 路径 | 未登录 | 已登录非提问人 | 提问人 |
|---|---|---|---|
| `POST /api/kb/rounds/{id}/feedback` | 401 | **403**（有明细权限的管理员也 403） | 2xx |
| `GET /api/kb/heatmap`（chips） | 401 | 无「知识问答」403 | 200 |

一轮一个反馈值，跟提问人 `qa_rounds.user_id`（Session）绑定。不要改回匿名白名单。写库失败不阻断问答主路径。

## 4. 操作条

`actionBarHtml`：

- 有完整回答正文（`hasAnswerBody`，含拒答但仍有文本）：复制、赞、踩、刷新。
- 纯错误提示：只出刷新。
- 用户气泡、生成中（`pending`）：无操作条。

**赞/踩**：空 / 赞 / 踩 互斥；点另一键覆盖；再点当前键取消。浏览器先改 `m.feedback`；`logWritten` 为真才 POST；未写入只留浏览器并提示 `UNWRITTEN_HINT`。

**刷新**：不新增用户气泡；该条进生成中；新 `round_id` 走现有 `POST /api/kb/ask` 全链路。`query` / `history` / `last_chunks` 用该轮首次发送快照。`state.busy` 时拒绝刷新，toast「生成中…」，不发起第二路。只刷新当前最后一条且成功时，才把 `conv.lastChunks` 换成新的进生成块。

**复制**：toast「已复制回答」（现网 `copyText`）。

## 5. 空状态 chips

仅当前对话 `messages` 为空（含清空后）。点击 = `send(query)`。

- 常驻 4 条：`CHIP_FIXED`（链接支付权益、代充三套账、Game Center、VIP 保级对照；短标题与全文相同）。
- 已登录且有「知识问答」：再请求 heatmap，按 `items` 顺序最多追加 4 条模板问句。未登录**不**请求 heatmap。
- 热度中文名：服务端 `c20_display_name`（`load_aliases` 第一条含汉字；否则 `feature_aliases.json` 该项第一项；再否则 `feature_id`）。前端用 `display_name || feature_id`。

覆盖 v3「无建议问法 chips」的现网口径（C22）；「无过程栏」仍以 v3 / kb-qa 契约为准。

## 6. 对话区样式

- 消息列、chips、输入卡片同一居中栏 `.qa-col`（约 768px）；更窄随 `.qa-main` 收缩。
- 用户问句：栏内右侧圆角块。回答：无厚边框、占满栏。出处与操作条在回答下。
- 输入：`.qa-composer` 卡片，发送在卡片内右下；Enter 发送、Shift+Enter 换行。
- 不改左侧会话列表结构、四个主 Tab。

## 7. 查 bug 优先点

1. **FB_OWNER**：管理员有明细权限也不能改他人 `feedback`。
2. **刷新形态**：对话里不得因刷新再插一条用户气泡；明细应多一行新 `round_id`。
3. **写库失败**：不得假装明细已有赞踩。
4. **chips 双路径**：不要把空状态 heatmap 改成要「功能热度」勾选。
5. **CHIP_FIXED 正文**：四条测题是产品指定全文，不要换成 VIP/拉新简单句。
6. **生成中锁**：刷新与发送同一把 `state.busy`。
7. **不要**把明细 overlay 再挂回 H5 顶栏（入口已迁管理站）。

## 8. 回归锚点

| 文件 | 覆盖 |
|---|---|
| `site/kb-api/tests/test_feedback.py` | 库字段、C20 中文名、CHIP_FIXED、操作条键、内容柱、反馈 API（现网带 Session） |
| `site/kb-api/tests/test_auth_m2.py` | ROUND_UID、提问人赞踩 |
| `site/kb-api/tests/test_auth_m3.py` | 热度 chips 静态、heatmap 权限 |
| `site/kb-api/tests/test_site_contract.py` | 允许 `qa-chip`；无过程栏 |
