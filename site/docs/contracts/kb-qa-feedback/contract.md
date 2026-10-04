# 知识问答 · 反馈与对话样式 · 实现契约

> 现行实现合同。给改赞/踩/刷新、空状态 chips、右侧对话排版的人与 AI 用。  
> 交互需求以 [`../../design/kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md`](../../design/kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md) 为准；2026-10-03 用户另行批准的页面结构增量见 §6。
> 多轮刷新/版本语义同时依据 [Phase1 v1.10](../../design/kb-qa-multdesign/PRD-知识问答多轮对话编排-Phase1-v1.10.md)；检索、消息事实与编排以 [`../kb-qa/contract.md`](../kb-qa/contract.md) 为准。提问人身份以 [`../kb-auth/contract.md`](../kb-auth/contract.md) 为准。\
> v1 在 `design/kb-qa-feedback/history/`，不默认读。更新：2026-10-03。整合版本反馈、后台处理与当日样式；回归与收尾见 [专题进度](../../design/kb-qa-multdesign/steps-verified.md#2026-10-03-开发收尾与正式契约整合)。

## 1. 怎么用

| 你要做的事 | 读 |
|---|---|
| 改复制 / 赞 / 踩 / 刷新 | §3、§4、`qa.js` `actionBarHtml` / `setFeedback` / `regen` |
| 改空状态建议问句 | §5、`CHIP_FIXED`、`refreshHeatChips` |
| 改对话区宽度 / 输入卡片 | §6、`qa.css` `.qa-col` |
| 查明细反馈、越权改赞踩 | §3、§7、§9 |
| 对照回归 | §8 |

不要把本增量写进 `design/kb-qa/` 或 `site/core-docs/prd/design/`。不要加「链接」「更多」键。

## 2. 落地符号

| 名 | 值 |
|---|---|
| 库字段 | `qa_rounds.feedback`：`up` / `down` / 空；`feedback_at` |
| 界面文案 | 赞 / 踩 / 未评价（`feedbackUiFromRow`） |
| 写接口 | `POST /api/kb/rounds/{round_id}/feedback`，体 `{feedback: "up"\|"down"\|null}`，可选 `assistant_msg_id` 校验目标 |
| 未写入提示 | `UNWRITTEN_HINT` =「本轮日志未写入，反馈不会进明细」 |
| 常驻 chips | `CHIP_FIXED` 四条（全文既是 title 也是 query；另有仅用于卡片标题的 label） |
| 热度 chips | heatmap Top 4，问句 = `{display_name\|\|feature_id} 有哪些现行规则？`（**不是**名为 `CHIP_HEAT` 的常量） |
| 内容柱 | `.qa-col` `max-width: 768px` |
| 明细反馈展示 | 管理站问答明细（H5 顶栏不再放明细钮；`qa.js` overlay 函数可能残留） |

代码锚点：`site/feature-interaction/qa.js`、`qa.css`、`site/kb-api/app/logs.py` `set_feedback`、`main.py` `set_round_feedback`。

## 3. 鉴权与归属

| 路径 | 未登录 | 已登录非提问人 | 提问人 |
|---|---|---|---|
| `POST /api/kb/rounds/{id}/feedback` | 401 | **403**（有明细权限的管理员也 403） | 2xx |
| `GET /api/kb/heatmap`（chips） | 401 | 无「知识问答」403 | 200 |

每次执行/回答版本一个反馈值，`round_id` 是兼容名称，实际指 exec_id；与提问人 `qa_rounds.user_id`（Session）及该执行 Assistant 绑定。刷新生成新的执行，新版本不继承旧反馈；查看旧版再评价仍改旧执行，不能重定向到当前有效版。

新记录必须 `msg_save=saved`、有 `assistant_msg_id` 且 status 为 success/refuse/empty，否则409 `feedback_not_allowed`；未保存、失败提示、中断回复不能反馈。可选 assistant_msg_id 与已绑定目标不符为409 `feedback_target`；旧记录缺新Schema仍按兼容规则接收。不合法值400，不存在404，写入失败500；空串/null取消。不要改回匿名白名单，失败不阻断问答主路径。

## 4. 操作条

`actionBarHtml`：

- 有完整回答正文（`hasAnswerBody`，含拒答但仍有文本）：复制、刷新；未保存回复不开放赞踩。历史版本与当前版按各自执行身份展示反馈，版本切换不更改服务端采用版本。
- 纯错误提示：只出刷新。
- 用户气泡、生成中（`pending`）：无操作条。

**赞/踩**：空 / 赞 / 踩互斥，点另一键覆盖、再点当前键取消。浏览器先改当前查看版本的 `m.feedback` 并同步版本；`logWritten` 为真才POST。Runtime未写入或普通网络/服务失败时提示 `UNWRITTEN_HINT`，本地值不代表服务端已有记录；409 `feedback_not_allowed` 会回退原值。未保存回复在操作条及 handler 两处阻止反馈。

**刷新**：不新增用户气泡；新 exec_id（兼容字段 round_id）与原 logical_round_id 走 `POST /api/kb/ask`。服务端使用首次提问的原文、L1消息id、前次执行、cut_seq和time_base快照，不信客户端 history/last_chunks。新回复只有完整保存并满足交付条件才采用；失败恢复原有效版。原版本、反馈、出处和回答过程保留可读，切换只影响查看。

`state.busy` 时拒绝刷新且不发第二路；保存阻塞先补存，不重新生成。同会话跨端互斥、请求幂等、断流状态查询由 [主链路契约 §9](../kb-qa/contract.md#9-消息事实执行版本与保存) 定义。`conv.lastChunks` 只是兼容展示缓存，不能作为服务端事实。

**复制**：toast「已复制回答」（现网 `copyText`）。

## 5. 空状态 chips

仅当前对话 `messages` 为空（含清空后）且无保存阻塞。点击 = `send(query)`。保存阻塞时仍显示原有重试保存入口。

- 常驻 4 条：`CHIP_FIXED`，卡片短标题为「链接支付权益」「币商转账规则」「游戏使用限制」「VIP 保级规则」。正文与发送的产品指定全文保持一致。
- 已登录且有「知识问答」：再请求 heatmap，按 `items` 顺序最多追加 4 条模板问句。未登录**不**请求 heatmap。
- 热度中文名：服务端 `c20_display_name`（`load_aliases` 第一条含汉字；否则 `feature_aliases.json` 该项第一项；再否则 `feature_id`）。前端用 `display_name || feature_id`。

覆盖 v3「无建议问法 chips」的现网口径（C22）；旧「无过程栏」约束由用户 2026-10-03 批准的 §6.1 覆盖。

## 6. 对话区样式

2026-10-03 用户接受 [Figma 三套方案](https://www.figma.com/design/03hF7L8hHavkgwYSy5xU8d) 中「A 暖深色首屏 + C 按需出处」的建议，覆盖旧 PRD 中相应视觉和左侧结构约束；不改变问答、反馈及引用的接口语义。

- 消息列、chips、输入卡片同一居中栏 `.qa-col`（约 768px）；更窄随 `.qa-main` 收缩。
- 空状态依次为介绍、输入卡片、四张场景卡与最近常问。介绍、建议问句和消息列表使用独立容器；热度刷新不重建输入框。
- 用户问句：栏内右侧圆角块。回答：无厚边框、占满栏。出处与操作条在回答下。
- 助手正文使用 `KBMarkdown.parse(text, {safeText:true})` 排版标题、粗体、列表、引用、代码和表格。流式片段使用同一路径；原始 HTML、链接、图片只作为文本显示，不生成活动链接或远程图片。用户与系统消息继续转义为纯文本。文档阅读器沿用默认解析方式。
- 出处入口为「查看出处 · N」，按需显示右侧面板。卡片显示库别、可用的功能名称、章节、实际引用摘要、路径及原文入口；摘要最多 180 字并限制四行，缺少摘要时不补造。原有引用定位字段与复核逻辑保留。
- 输入：`.qa-composer` 卡片，发送在卡片内右下；Enter 发送、Shift+Enter 换行。
- 会话按本地日期分「今天 / 更早」，保留新建、切换、删除、清空及分页。
- 同日后续用户明确要求四个主 Tab 改为「知识问答、客户端 ↔ 后台、客户端交叉、文档索引」。导航、品牌、会话及回答操作统一使用 `ui-icons.js` 的几何线框图标；共享布局覆盖在 `workbench.css`，沿用当前主题颜色。
- ≤1200px 时出处为右侧抽屉；≤980px 时会话列表改为顶部横向列表；≤600px 时场景卡单列。
- 新增 `warm-night`（暖夜）主题，空或非法主题设置默认使用它；已有合法主题偏好仍生效。主题选择器可以切换全部旧主题。

### 6.1 回答过程（2026-10-03）

- 在每版助手回答上方显示「回答过程」，采用独立底色、较弱正文色、步骤连线及明确状态文字，与正式答案区分。文案来自实际执行事件与已产生的业务结果；不展示或模拟模型内部推理。
- 正文出现前默认展开；首次收到正文即自动收起，核对期间标题继续显示当前状态。用户手动展开/收起后，本轮后续更新尊重手动选择。展开不触发滚到底部。
- 展示已识别问题、实际任务与缺少条件、检索查询及范围、候选数量、选用片段和文档数量、参考来源、核对/修正结果。无结果、错误与待补信息如实显示，不补造成功步骤。
- 过程中的来源按钮复用现有原文定位与校验；不会显示未经选用的全文。短回应按实际步骤显示，不填充固定长流程。
- 过程按 `exec_id` 绑定回答版本，切换旧版同时切换过程。重新打开会话由 `answer-history` 恢复默认有效版本；旧回答缺少过程时不显示虚构面板。
- 过程开关支持键盘、`aria-expanded` 和焦点保留；小屏允许标题换行，动效遵循 `prefers-reduced-motion`。

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
| `site/kb-api/tests/test_m2_exec_versions.py` | 版本隔离、未保存/失败反馈拒绝、刷新与补存 |
| `site/kb-api/tests/test_m4_admin_observe.py`、`test_m7_issues.py`、`test_admin_review_regressions.py` | 反馈分页/详情、问题关联、处理状态分页前筛选 |
| `site/kb-api/tests/test_feedback.py` | 库字段、C20 中文名、CHIP_FIXED、操作条键、内容柱、反馈 API（现网带 Session） |
| `site/kb-api/tests/test_auth_m2.py` | ROUND_UID、提问人赞踩 |
| `site/kb-api/tests/test_auth_m3.py` | 热度 chips 静态、heatmap 权限 |
| `site/kb-api/tests/test_site_contract.py` | 允许 `qa-chip`；无旧全局 `#qaProcess` |
| `site/feature-interaction/tests/kb-md.test.cjs` | 回答 Markdown 排版、部分流式文本、HTML/链接/图片转义、起始分隔线与注释内容保留 |
| `site/feature-interaction/tests/qa-process.test.cjs` | 自动展开/收起、手动状态、阅读位置、版本恢复与文案转义 |


## 9. 管理反馈列表与问题关联

- `GET /api/kb/admin/feedback`、`/{exec_id}` 要「反馈汇总」，管理员只读评价，不能改用户赞踩。详情固定展示被评价的实际版本、执行/逻辑回合/消息id、版本号和是否当前版本，不以刷新后的答案替换评价对象。无明确版本绑定的旧记录标 legacy，不推定当前版。
- 列表默认 value=down，可选 up/all；默认按 feedback_at，可切执行 created_at。账号、会话、执行、消息、route、时间、处理状态与游标都由服务端筛选。handled 可为 yes/no/open/doing/closed，条件在 SQL 分页前生效，不能只过滤当前页。响应沿用 kb-auth §10 的分页与覆盖信封，读取失败不是空结果。
- 详情可附 issue_ids/issue_status；“有处理记录”和用户评价分开。跳执行或对话仍要求目标原文权限；仅反馈权限可看反馈详情，不依赖 `/rounds/{id}`。原 `/admin/feedback-summary` 兼容保留，不增第二套采集。
- 建立/关联/处理问题走 `admin/issues` 并另要「问题处理」；关闭必须留依据，重测结论与关闭状态不能倒改反馈。问题详情与实际删除正文清理的唯一契约在 [kb-auth §12](../kb-auth/contract.md#12-问题知识来源与索引任务)。
- 清空/隐藏不等于管理员实际删除；实际删除会清理对应执行与关联正文副本。用户侧答案恢复遵守本人可见性，规则见主链路，不能用后台保留事实绕过用户范围。
