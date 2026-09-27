---
title: "H5 工作台主题切换 STEP 验证版"
status: "verified"
stage_result: "PASS_WITH_RISKS"
prd: "site/docs/design/h5-theme/PRD-H5工作台主题切换-v1.md"
prd_sha256: "7a894778b4199c3c68b7c5e955b32033d9cc8ad6a839e732e884c95b416997e6"
draft: "site/docs/design/h5-theme/steps-draft.md"
draft_sha256: "32fa3078f2c790a7e142e147789bbe6b8c991647ad4e7e3b98ee1575cdb4e951"
created: "2026-09-19"
note: "step-doc-review 验证版。2026-09-19 USER_DECISION「按建议」修订首次默认为边缘行者粉；不覆盖 steps-draft.md。可进入里程碑编排，不宣布开始开发。"
---

# H5 工作台主题切换 STEP 验证版

> **现行权威**：[`PRD-H5工作台主题切换-v1.md`](PRD-H5工作台主题切换-v1.md)（status=已确认待实施）。  
> **独立增量**：不替代 [`../h5-kb/PRD-H5知识库-v1.md`](../h5-kb/PRD-H5知识库-v1.md)、[`../kb-qa/PRD-知识问答-v3.md`](../kb-qa/PRD-知识问答-v3.md)、[`../kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md`](../kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md)。  
> **原文草稿**（保留）：[`steps-draft.md`](steps-draft.md)。  
> 宿主：http://127.0.0.1:18765/feature-interaction/ 。实现状态：仅有 `?theme=` 预览，正式顶栏切换未实施。  
> 本文件 **verified**。2026-09-19 按 USER_DECISION 修订 G3/AC18/AC21/CSTR-004/005（首次默认边缘行者粉、`:root` 对调）。草稿未覆盖。standalone 审查后的九维结论仍适用；本修订不另开优化轮。不自动开始写业务代码。

## 来源摘要

事实标签只用：`USER_DECISION`、`PRD`、`CONTRACT`、`REPO_BASELINE`、`RUNTIME`、`PLANNED`、`UNVERIFIED`。本轮无 `RUNTIME`（未把正式切换跑成现网行为）。本轮无独立 Contract 文件；契约测试见 SRC-CONTRACT。

| source_id | 路径 | 状态 | SHA-256 | 本轮核实 |
|---|---|---|---|---|
| SRC-PRD | `site/docs/design/h5-theme/PRD-H5工作台主题切换-v1.md` | `existing` | `7a894778b4199c3c68b7c5e955b32033d9cc8ad6a839e732e884c95b416997e6` | 全文含 2026-09-19 USER_DECISION：首次默认 `d-edgerunners`；`:root` 对调；`themes/default.css` 为蓝灰；G1–G4；AC1–AC23 |
| SRC-INDEX | `site/docs/design/h5-theme/INDEX.md` | `existing` | `1f087eb9becb0d0b5dee677db8018160dc7cf5b25ae8650565a07bfb2d99bf29` | 专题入口；首次默认边缘行者粉；现行 STEP 为 `steps-verified.md` |
| SRC-HTML | `site/feature-interaction/index.html` | `existing` | `a4d27615ffb970deda1a7219674cd88ef26ba6ab13a29d2ccf49f63664f64190` | 四 Tab `data-view` admin/client/kb/qa；`<head>` 引 `theme-preview.js`；`#qaTopActions`；`data-qa-config`/`reindex`/`rounds`/`heatmap`；无主题 `<select>` |
| SRC-PREVIEW | `site/feature-interaction/theme-preview.js` | `existing` | `8c25db3946f6a77391c48c1fde5a128612b8c1b825a3252e9f9848738d81ad57` | 仅 `?theme=` 且 id 在 `NAMES` 时加载 CSS；无 `default`；无 `localStorage`；`mountBar`；无 `applyTheme` |
| SRC-APP | `site/feature-interaction/app.js` | `existing` | `49ccca29088af321b95f9e86e25a8d89e2c2bd3f56cb26d6a82aa453f63c4e78` | `domainColor` 读 CSS 变量；`layoutAdmin`/`layoutClient`/`applyLayout` 为静态列布局（**无力导向**）；`renderGraph` 把节点圆点 `fill` 与 marker `#4a5160`/`#6ea8fe` 写进 SVG；`window.GraphApp` 仅 `setView`/`selectNode`/`getSelectedId`/`getLastGraphView` |
| SRC-CSS | `site/feature-interaction/style.css` | `existing` | `d8e0750698d99f6a04a019b3339a62866ff3e3323b7f213e8084e754f73ce20f` | `:root --accent: #6ea8fe`；`--reach: #c4a6ff`；`.tab.active` 用 `var(--accent-soft)`；`.edge { stroke: #4a5160 }`；`.edge.active { stroke: var(--accent) }`；`.app:not(.qa-active) .qa-top-actions { display: none }`；`@media (max-width: 980px)` 只改工作区栅格 |
| SRC-QA-CSS | `site/feature-interaction/qa.css` | `existing` | `af129a9d7dd9a6fe1f9c629ce1c0c10fad9bf8044555c8dac24e92ea46aea752` | `.qa-send { background: var(--accent) }`；`.qa-conv-item.active` 用 `--accent` / `--accent-soft`；`.qa-overlay-card { background: var(--bg-elevated) }` |
| SRC-QA-JS | `site/feature-interaction/qa.js` | `existing` | `30e5389e3eea73435a0c85f4d109b700ef74ff6fa608cb50e829a5d5d768d130` | 本轮只读；问答发送/出处/赞踩刷新；本期不改业务 |
| SRC-KB-JS | `site/feature-interaction/kb.js` | `existing` | `803e4228d906b0f65a3d5f49ed5cffa91cd0a2172460d096b652fb30a0ed8efc` | 本轮只读；`GraphApp.setView("kb")` |
| SRC-APPLY | `site/feature-interaction/themes/_apply.css` | `existing` | `d96f1e8319acc7886028b5ffccdb97e4973c4fadbc84c58417454b5757c8b7ed` | 硬编码色接到变量；`.edge { stroke: var(--edge) }`；含 `.theme-preview-bar` |
| SRC-THEME-A | `site/feature-interaction/themes/a-gits.css` | `existing` | `c4e250ec27901a608a49f340153b61d90cf206eaceb2a1d87c0bdb3eca499754` | `--accent: #7ec8d0` |
| SRC-THEME-B | `site/feature-interaction/themes/b-2049.css` | `existing` | `ac7585e676eaa1bd50b768da4dc220400f23002ed75f71df15b75fbfa818bbb5` | `--accent: #e08a2c` |
| SRC-THEME-C | `site/feature-interaction/themes/c-nightcity.css` | `existing` | `db0245060d553b641f2572e586d3d0733b53623ddbde52bfc11b6c420700cba4` | `--accent: #fcee0a`；`--reach: #ff2a6d` |
| SRC-THEME-D | `site/feature-interaction/themes/d-edgerunners.css` | `existing` | `dce7b86065d63b61a8c31338de1973156e6d57edc34e82f84c865ff324c1b48c` | `--accent: #ff3cac`；`--reach: #ff3cac` |
| SRC-THEME-CP | `site/feature-interaction/themes/c-prime.css` | `existing` | `a997b668511343faede677736d819513ed03c0776632519f1f47c4fb696618bf` | `--accent: #fcee0a`；`--reach: #c77dff` |
| SRC-THEME-DEFAULT | `site/feature-interaction/themes/default.css` | `planned` | 不适用 | 实施时新增：现行 `style.css` `:root` 蓝灰 token；须含 `--edge: #4a5160` |
| SRC-GALLERY | `site/feature-interaction/themes/index.html` | `existing` | `d0bddc2710a0f0b2ce75364f26c4ccf2f2e719eab2f5ca321dc016f198789891` | 对照页已链到 `/feature-interaction/?theme=…&view=…`；显示名带「A ·」前缀，与 PRD `<select>` 文案不完全相同 |
| SRC-CONTRACT | `site/kb-api/tests/test_site_contract.py` | `existing` | `f7983d5bca9ad078f9b19545f4e26003e988398bd7f36daf34de089aa9c369ad` | 见下：本轮重读为 `labels ==` 有序相等 |
| SRC-COMPOSE | `site/docker-compose.yml` | `existing` | （文件头惯例，本轮读 L4–L5） | 在 `site/` 执行 `docker compose up -d`；或仓库根 `docker compose -f site/docker-compose.yml up -d` |

**SRC-CONTRACT 更正**：草稿 SHA `f7983d5bca9ad078f9b19545f4e26003e988398bd7f36daf34de089aa9c369ad` 与本轮 `shasum` 一致。断言是 `labels == ["客户端 ↔ 后台", "客户端交叉", "文档索引", "知识问答"]`（**有序**，不是多重集）。

**发现门（不填具体值、不宣称已决定）：**

- 换肤后调用哪一层 GraphApp API：现网无专用方法（SRC-APP）。PRD 要求调用现有 `renderFilters`/`renderGraph`（及依赖 `domainColor` 的图例/`renderDetail`），**不得改 `applyLayout` / `layoutAdmin` / `layoutClient`**。包装函数名按已核实项目约定确定（`PLANNED`）。
- `theme-preview.js` 是否改名为 `theme.js`：PRD §6 步骤 A 写「可改名」，本验证版不选定文件名。
- 顶栏 `<select>` 的 class 名与具体像素：PRD 只要求高度/边框对齐现网顶栏控件（`PLANNED`）。
- `?view=` 预览参数：PRD §5.4 写正式切换不依赖、可保留；不是 G1 验收条件。

启动命令（`REPO_BASELINE`，SRC-COMPOSE 文件头）：在 `site/` 执行 `docker compose up -d`；或仓库根 `docker compose -f site/docker-compose.yml up -d`。宿主 URL：http://127.0.0.1:18765/feature-interaction/ 。

## 对象比较约定

比较同一输入快照。颜色用 `COLOR_EQ`：把 computed `rgb()`/`rgba()` 与源 hex 规范化后相等。PRD 要求顺序的对象用有序元组，不改成多重集。

| 符号 | 定义 | 来源 |
|---|---|---|
| `MAIN_TABS_SEQ` | 有序元组 `("客户端 ↔ 后台", "客户端交叉", "文档索引", "知识问答")` | PRD AC20「名字、顺序」；SRC-CONTRACT `labels == […]`；SRC-HTML `.tab` |
| `THEME_IDS` | 集合 `{default, a-gits, b-2049, c-nightcity, d-edgerunners, c-prime}` | PRD §5.1 |
| `THEME_OPTIONS` | 有序 6 元组 `(value, 可见文案)`：`(default, 现网蓝灰)`, `(a-gits, 攻壳青)`, `(b-2049, 2049 琥珀)`, `(c-nightcity, 夜之城黄)`, `(d-edgerunners, 边缘行者粉)`, `(c-prime, 黄主色)` | PRD §5.1「选项顺序固定」；AC2 |
| `THEME_LABELS` | `THEME_OPTIONS` 的文案投影（有序） | PRD §5.1 |
| `THEME_ACCENT` | id → `--accent`：`default=#6ea8fe`，`a-gits=#7ec8d0`，`b-2049=#e08a2c`，`c-nightcity=#fcee0a`，`d-edgerunners=#ff3cac`，`c-prime=#fcee0a` | SRC-CSS（实施后 `:root` 为粉）；SRC-THEME-A～CP；AC4–AC9 |
| `THEME_REACH` | 本验收用到的触达色：`c-prime=#c77dff`，`d-edgerunners=#ff3cac` | SRC-THEME-CP；SRC-THEME-D；AC8；AC11 |
| `STORAGE_KEY` | `hayyo-h5-theme` | PRD §5.3 |
| `FIRST_ID` | `d-edgerunners`（空/非法存储的生效 id；不自动写入空键） | USER_DECISION 2026-09-19；PRD G3、§5.1、§5.3 |
| `FIRST_ACCENT` | `#ff3cac` | SRC-THEME-D；AC18、AC21 |
| `BLUE_ACCENT` | `#6ea8fe`（id=`default` 现网蓝灰） | 现行 SRC-CSS `:root --accent`；AC9 |
| `DEFAULT_EDGE` | `#4a5160`（蓝灰连线；写入 `themes/default.css` 的 `--edge`） | SRC-CSS `.edge`；PRD §5.1 |
| `COLOR_EQ(a,b)` | 同一快照下规范化颜色相等 | 验收方法 |
| `ROOT_ACCENT(id)` | `getComputedStyle(document.documentElement).getPropertyValue("--accent")` 与 `THEME_ACCENT[id]` 满足 `COLOR_EQ` | AC4–AC9、AC16、AC21 |
| `QA_SEND_BG(id)` | `.qa-send` 的 `background-color` 与 `THEME_ACCENT[id]` 满足 `COLOR_EQ` | AC4–AC9 |
| `CONV_ACTIVE(id)` | 当前 `.qa-conv-item.active` 的 `border-color`/`background-color` 分别与 `--accent` / `--accent-soft` 满足 `COLOR_EQ` | AC4、AC7；§5.5 会话选中 |
| `TAB_ACTIVE(id)` | `.tab.active` 的 `background-color` 与当前 `--accent-soft` 满足 `COLOR_EQ` | PRD §5.5「Tab 选中态」 |
| `REACH_FILTER(id)` | 筛选条上可见文案为「账号触达」的 `.dot` 背景色与 `THEME_REACH[id]`（或当前 `--reach`）满足 `COLOR_EQ` | AC8、AC11 |
| `REACH_NODES(id)` | 当前图中 `FEATURE_DATA` 域为「账号触达」且可见的节点：每个 `circle` 的 `fill` 与 `THEME_REACH[id]`（或当前 `--reach`）满足 `COLOR_EQ`；比较键为节点 `data-id`，不是圆点个数 | AC8、AC11 |
| `EDGE_STROKE(id)` | 非激活 `path.edge` 的 computed `stroke`：`id=default` 时与 `DEFAULT_EDGE` 满足 `COLOR_EQ`；`id=FIRST_ID` 或空存储时与当前 `--edge`（基线 `#4a3060`）满足 `COLOR_EQ`；其余 id 与该主题 `--edge` 满足 `COLOR_EQ`。激活 `path.edge.active` 的 `stroke` 与当前 `--accent` 满足 `COLOR_EQ` | PRD §5.5「连线」；SRC-THEME-D；SRC-APPLY |
| `EDGE_MARKERS(id)` | 重绘后 `#arrow path` 的 fill 与当前非激活连线色满足 `COLOR_EQ`；`#arrow-active path` 的 fill 与当前 `--accent` 满足 `COLOR_EQ`（现网 `renderGraph` 写死 `#4a5160` / `#6ea8fe`） | PRD §5.5；SRC-APP L155–161 |
| `FILTER_DOTS(id)` | 筛选条每个可见域 chip 的 `(标签文本, .dot 规范化背景色)` 多重集 = 各标签对应 `DOMAIN_VAR` 在当前主题下的 computed 值 | SRC-APP `DOMAIN_VAR`；§5.5 域色点 |
| `THEME_SHEETS(id)` | `id` 为 `FIRST_ID` 或存储空/非法：`document` 中无 `href` 以 `themes/default.css`、`themes/a-gits.css`…`c-prime.css` 或 `themes/_apply.css` 结尾的 stylesheet（不要求加载 `d-edgerunners.css`）。`id=default`：同时存在 `themes/default.css` 与 `themes/_apply.css`。其余非 `FIRST_ID`：同时存在 `themes/{id}.css` 与 `themes/_apply.css` | CSTR-005；USER_DECISION |
| `STORAGE_VAL` | `localStorage.getItem(STORAGE_KEY)`；合法则 ∈ `THEME_IDS`。非法或空视为未选，**生效 id=`FIRST_ID`**，不把非法值当皮肤，空键不自动写入 | CSTR-004 |
| `SELECT_EL` | 顶栏原生 `select[aria-label="主题"]`，不在 `#qaTopActions` 内 | AC1、AC3；CSTR-006 |
| `TOP_ACTIONS` | `#qaTopActions` 内仍有 `data-qa-config`、`data-qa-rounds`、`data-qa-heatmap`、`data-qa-reindex` | SRC-HTML；SRC-CONTRACT；AC15 |
| `OVERLAY_CARD(id)` | 打开的 `.qa-overlay-card` 的 `background-color` 与当前 `--bg-elevated` 满足 `COLOR_EQ` | AC15；SRC-QA-CSS |
| `PREVIEW_BAR_ABSENT` | 工作台文档树无 `.theme-preview-bar`；工作台可见文本不含「正在预览」「返回对照页」作为底栏文案 | AC22、AC18 |
| `GALLERY_HREFS` | 对照页六套卡片「问答」链接为 `/feature-interaction/?theme={id}&view=qa`，`id` 遍历非 `default` 的五套 + 对照页现有项；本轮核实已存在，实施后集合不得改成非工作台地址 | PRD §6.C.1；SRC-GALLERY |
| `DOC_OPEN_ID` | 文档索引当前打开篇的稳定标识（现网列表项身份 / 正文标题，以实施时已核实的 kb 选中态为准，比较同一篇，不比「还能打开一篇」的个数） | AC10「当前打开文档仍在」；AC13 |
| `KB_LINK_COLOR(id)` | `.kb-article a` 的 `color` 与 `THEME_ACCENT[id]` 满足 `COLOR_EQ` | AC13；SRC-CSS `.kb-article a` |

对照页卡片标题（SRC-GALLERY）带「A · 攻壳青」等前缀，**不是** `THEME_LABELS`。下拉框必须用 `THEME_OPTIONS` 文案。

## 输入清单

### 本期有效需求

PRD 未使用 `RQ-*`。有效需求 ID 沿用 PRD 已有编号 **G1–G4**。未编号约束用 `CSTR-*`，不新造 `RQ-*`。

| ID | 摘要 | 来源 |
|---|---|---|
| G1 | 顶栏下拉框能选 6 套之一，四个 Tab 配色立刻跟上 | PRD §2.3 |
| G2 | 刷新、关标签再开同一浏览器，仍是上次那套 | PRD §2.3 |
| G3 | 从未选过的人看到边缘行者粉 | PRD §2.3；USER_DECISION |
| G4 | 问答、关系图、文档索引、配置/明细/热度弹层行为与换皮前一致 | PRD §2.3 |

### 本期有效验收

AC1–AC23（PRD §7）。

### 未编号约束（CSTR）

| ID | 摘要 | 来源 |
|---|---|---|
| CSTR-001 | 只做工作台 SPA；不做 `/docs/`、admin-skin、复盘、原型、Hayyo App | PRD §4.2 |
| CSTR-002 | 不改四 Tab 信息结构、问答接口、图谱数据/布局算法 | PRD §4.2、§5.5、§6.A.4 |
| CSTR-003 | 控件为原生 `<select>`，不要自定义带色点菜单 | PRD §5.2；USER_DECISION「2」 |
| CSTR-004 | 存储键 `hayyo-h5-theme`；非法或空 = 生效 `FIRST_ID`；已存 `default` 不迁移；不写服务器 | PRD §5.3、§3；USER_DECISION |
| CSTR-005 | `FIRST_ID`/空/非法不加载额外皮肤；`default` 加载 `themes/default.css` + `_apply.css`；其余 id 加载对应 css + `_apply.css` | PRD §5.1；USER_DECISION |
| CSTR-006 | 主题 `<select>` 四个 Tab 都显示，不放进 `#qaTopActions` | PRD §5.2、§6.B.3；SRC-CSS `.app:not(.qa-active) .qa-top-actions` |
| CSTR-007 | 不把本增量写进 `prd/design/*/PRD.md`，不改 h5-kb / kb-qa / kb-qa-feedback 正文 | PRD §4.2 |
| CSTR-008 | 日常不依赖 `?theme=`；合法 `?theme=` 写入 `localStorage`；非法 query 不当作皮肤 | PRD §5.4、§5.3 |
| CSTR-009 | 脚本在 `index.html` `<head>`；`:root` 已是粉，减少先闪蓝灰 | PRD §6.A.2、§6.A.4；USER_DECISION |
| CSTR-010 | 对照页可留作图鉴，不是日常入口；链接打开工作台（可带 `?theme=`） | PRD §4.1、§6.C.1 |
| CSTR-011 | 不改 `qa.js` 业务、不改 kb-api | PRD §6.C.2 |
| CSTR-012 | 无登录；主题只在本机 | PRD §3 |

未把 PRD §8 回滚写成开发 STEP：回滚说明不是本期功能，按 PRD §8 执行即可。

### 排除项 / 本期不做

| ID | 项 | 来源 |
|---|---|---|
| OUT-1 | `/docs/` Markdown 目录换皮 | §4.2 |
| OUT-2 | admin-skin、复盘、`workspace/` 原型 | §4.2 |
| OUT-3 | Hayyo App 客户端 | §4.2 |
| OUT-4 | 浅色模式、自定义上传皮肤、同步其他电脑 | §4.2 |
| OUT-5 | 改 Tab 结构、问答接口、图谱数据 | §4.2 |
| OUT-6 | 写入 `prd/design/` 或改 kb-qa / h5-kb / kb-qa-feedback 正文 | §4.2 |
| OUT-7 | 自定义带色点主题菜单 | §5.2 |
| OUT-8 | 重写 `style.css` 布局结构、引入 React/Vue、把 6 套色内联成一份巨文件。允许替换 `:root` token 并抽出 `themes/default.css` | §6 明确不在本期；USER_DECISION |
| OUT-9 | 为 `/docs/` 或 admin-skin 接同一套切换器 | §6 明确不在本期 |

### 技术债

无 PRD 编号技术债。现网预览条与 `?theme=` 仅加载、无 `localStorage`，由本期 STEP 替换，不另开 TD 编号。

## STEP 总览

| STEP | 标题 | 需求 | 验收 | 前置 |
|---|---|---|---|---|
| STEP-001 | 主题运行时：套皮、记住、URL | G2、G3 | AC16、AC17、AC18（默认粉）、AC19 | 无 |
| STEP-002 | 换肤后重绘关系图域色与连线 | G1（图谱表面）、G4（图谱点选/拖拽/筛选） | AC8（触达色）、AC11、AC12 | STEP-001 |
| STEP-003 | 顶栏原生主题下拉框 | G1 | AC1–AC7、AC8（发送钮）、AC9、AC10（Tab/会话）、AC23 | STEP-001 |
| STEP-004 | 去掉底部预览条 | G3 | AC22、AC18（无预览条） | STEP-001 |
| STEP-005 | 四 Tab / 弹层跟色与回归 | G4 | AC10（打开文档）、AC13、AC14、AC15、AC20、AC21 | STEP-003、STEP-004 |

建议人读顺序 001→002→003→004→005。002 / 003 / 004 在 001 之后可并行。005 需要顶栏可切换且预览条已去掉（AC21 观感不含底栏）。

## 需求映射

| 需求 ID | STEP | 本 STEP 承担的条款 |
|---|---|---|
| G1 | STEP-003 | 顶栏下拉框选 6 套，立刻换皮（含 Tab 选中态、发送钮、会话选中） |
| G1 | STEP-002 | 关系图/筛选色点/连线随当前主题 |
| G2 | STEP-001 | localStorage + 刷新/再开仍在 |
| G3 | STEP-001 | 无记录时生效 `FIRST_ID` / 边缘行者粉 |
| G3 | STEP-004 | 无痕打开无预览条 |
| G4 | STEP-002 | 关系图点选、拖拽、筛选与换皮前一致 |
| G4 | STEP-005 | 问答/文档/弹层行为与 Tab 回归 |

## 约束映射

| ID | STEP | 处置 |
|---|---|---|
| CSTR-001 | 全部 STEP「不在范围内」 | 不改 `/docs/`、admin-skin、App |
| CSTR-002 | STEP-002、STEP-003、STEP-005 | 不改布局算法、Tab 结构、问答接口、图谱数据 |
| CSTR-003 | STEP-003 | 原生 `<select>` |
| CSTR-004 | STEP-001 | `STORAGE_KEY`；非法/空=生效 `FIRST_ID`；已存 `default` 不迁移 |
| CSTR-005 | STEP-001 | `THEME_SHEETS` |
| CSTR-006 | STEP-003 | `SELECT_EL` 不在 `#qaTopActions` |
| CSTR-007 | 全部 STEP「不在范围内」 | 不改产品 PRD / 三份专题正文 |
| CSTR-008 | STEP-001 | 合法 query 写入；非法 query 回退 `FIRST_ID` |
| CSTR-009 | STEP-001 | 脚本留在 `<head>` |
| CSTR-010 | STEP-004 | 对照页可留；`GALLERY_HREFS` |
| CSTR-011 | STEP-005；STEP-001～004 不在范围 | 不改 `qa.js` 业务、不改 kb-api |
| CSTR-012 | STEP-001 | 只写 `localStorage` |

## 排除映射

OUT-1～OUT-9 → 全部 STEP「不在范围内」。OUT-7 另由 STEP-003 控件形态覆盖。OUT-8 由 STEP-001 文件加载策略覆盖。

## 验收映射

| 验收 ID | STEP | 本 STEP 承担的子条款 | 对象比较方法 |
|---|---|---|---|
| AC1 | STEP-003 | 四 Tab 都有主题下拉框 | 每个 `data-view` 下 `SELECT_EL` 可见 |
| AC2 | STEP-003 | 6 个选项文案与顺序 | `select` 的 `(value,text)` 有序元组 = `THEME_OPTIONS` |
| AC3 | STEP-003 | 原生 `<select>` | 控件 tagName=`SELECT`；无自定义色点菜单 DOM |
| AC4 | STEP-003 | 攻壳青：发送钮/选中浅青 | `QA_SEND_BG(a-gits)`；`CONV_ACTIVE(a-gits)` |
| AC5 | STEP-003 | 2049 琥珀：主色偏橙、底暖黑 | `QA_SEND_BG(b-2049)`；`--bg` 为该皮肤文件值 |
| AC6 | STEP-003 | 夜之城黄：发送钮荧光黄 | `QA_SEND_BG(c-nightcity)` |
| AC7 | STEP-003 | 边缘行者粉：发送钮/选中品红 | `QA_SEND_BG(d-edgerunners)`；`CONV_ACTIVE(d-edgerunners)` |
| AC8 | STEP-003 | 黄主色：发送钮为黄 | `QA_SEND_BG(c-prime)` |
| AC8 | STEP-002 | 黄主色：关系图「账号触达」为紫而非品红 | `REACH_FILTER(c-prime)` 与 `REACH_NODES(c-prime)` = `#c77dff`，且 `COLOR_EQ` 不成立于 `#ff3cac` |
| AC9 | STEP-003 | 切回现网蓝灰，主色 `BLUE_ACCENT` | `QA_SEND_BG(default)`；`ROOT_ACCENT(default)`；`THEME_SHEETS(default)` |
| AC10 | STEP-003 | 换主题不刷新；当前 Tab、当前会话仍在 | 换肤前后 `data-view` 相同；同一会话列表项仍 `.active`（稳定会话身份，不比会话个数） |
| AC10 | STEP-005 | 当前打开文档仍在 | 换肤前后 `DOC_OPEN_ID` 相同 |
| AC11 | STEP-002 | 客户端 ↔ 后台：域色随主题，节点可点可拖 | `FILTER_DOTS`；`REACH_NODES(d-edgerunners)`；换肤后仍可 `selectNode` 与拖拽；换肤前后 `getSelectedId` 不变 |
| AC12 | STEP-002 | 客户端交叉：换皮后筛选仍可用 | 切 `data-view=client` 后换肤；chip 开关仍改变可见节点 `data-id` 集合（比较 id 集合，不比个数） |
| AC13 | STEP-005 | 文档索引换皮后能打开一篇 | 攻壳青下 `DOC_OPEN_ID` 有值；`KB_LINK_COLOR(a-gits)` |
| AC14 | STEP-005 | 知识问答换肤后提问/出处/赞踩刷新仍可用 | 换肤后仍能发送或打开已有出处；已有回答上赞/踩/刷新仍可点（不改 `qa.js` 业务） |
| AC15 | STEP-005 | 配置/明细/热度/重建弹层跟当前主题 | `TOP_ACTIONS` 四键仍在；夜之城黄下逐个打开，每次 `OVERLAY_CARD(c-nightcity)` |
| AC16 | STEP-001 | 非默认主题刷新仍在 | 刷新后 `STORAGE_VAL` 与 `ROOT_ACCENT` 同一 id |
| AC17 | STEP-001 | 关标签再开仍在 | 再开后同上 |
| AC18 | STEP-001 | 无痕/清空存储第一次是边缘行者粉 | `STORAGE_VAL` 空或非法 → `ROOT_ACCENT(FIRST_ID)`；`THEME_SHEETS(FIRST_ID)`；空键不自动写成 `d-edgerunners` |
| AC18 | STEP-004 | 无底部预览条 | `PREVIEW_BAR_ABSENT` |
| AC19 | STEP-001 | `?theme=c-nightcity` 写入存储，刷新仍在 | 本次 `ROOT_ACCENT(c-nightcity)`；`STORAGE_VAL=c-nightcity`；去掉 query 再刷新仍该 id |
| AC20 | STEP-005 | Tab 名字顺序切换方式不变 | `.tab` 可见文案有序元组 = `MAIN_TABS_SEQ`；仍靠 `data-view` 按钮切换 |
| AC21 | STEP-005 | 无主题参数且未选过时观感是边缘行者粉（多一个选择框除外） | 无痕无 query：`ROOT_ACCENT(FIRST_ID)`、`QA_SEND_BG(FIRST_ID)`、`PREVIEW_BAR_ABSENT`、存在 `SELECT_EL` 且当前值为 `FIRST_ID` |
| AC22 | STEP-004 | 工作台任意主题无预览条 | `PREVIEW_BAR_ABSENT`（含带 `?theme=`） |
| AC23 | STEP-003 | 窄于约 980px 下拉框能用、不挡住发问 | 问答 Tab、视口宽 &lt; 980px：`SELECT_EL` 可打开；其布局盒与 `#qaInput` / `.qa-send` 无相交 |

## 完整 STEP 提示词

### [STEP-001] 主题运行时：套皮、记住、URL

**阶段状态**：`verified`

**目标**：不依赖顶栏控件，也能按 `THEME_IDS` 挂/卸皮肤 CSS，把选择写入 `STORAGE_KEY`，合法 `?theme=` 与刷新后仍生效；无记录或非法值时生效边缘行者粉（`FIRST_ID`）。把 `style.css` `:root` 换成与 `themes/d-edgerunners.css` 相同的 token；现行蓝灰抽到 `themes/default.css`。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | G2 | 刷新、关标签再开同一浏览器，仍是上次那套 | `PRD` |
| 需求 ID | G3 | 从未选过的人看到的是边缘行者粉 | `PRD`；`USER_DECISION` |
| 验收 ID | AC16 | 选非默认主题后刷新，仍是那套 | `PRD` |
| 验收 ID | AC17 | 关标签再打开工作台，仍是那套 | `PRD` |
| 验收 ID | AC18 | 清 `localStorage` 或无痕窗口，第一次是边缘行者粉 | `PRD`（本 STEP 只验默认粉与 `THEME_SHEETS`，预览条见 STEP-004） |
| 验收 ID | AC19 | 从对照页带 `?theme=c-nightcity` 进来，本次即夜之城黄，且刷新仍在 | `PRD` |
| 约束 ID | CSTR-004 | 非法或空 = 生效 `FIRST_ID`；已存 `default` 不迁移 | `PRD`；`USER_DECISION` |
| 约束 ID | CSTR-005 | `FIRST_ID` 不加载额外皮肤；`default` 加载 `themes/default.css` + `_apply.css` | `PRD`；`USER_DECISION` |
| 约束 ID | CSTR-008 | 合法 `?theme=` 写入存储 | `PRD` |
| 约束 ID | CSTR-009 | 脚本在 `<head>` | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| 无 | — | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `theme-preview.js` IIFE、`NAMES`、`addSheet` | `existing` | `REPO_BASELINE` | SRC-PREVIEW / 文件头至 `addSheet("themes/_apply.css")` | 改成可挂可卸运行时的底 |
| `index.html` `<script src="theme-preview.js">` | `existing` | `REPO_BASELINE` | SRC-HTML / `<head>` | 保持在 head 以减少闪色 |
| `themes/{id}.css`、`themes/_apply.css` | `existing` | `REPO_BASELINE` | SRC-THEME-A～CP、SRC-APPLY | 非 `FIRST_ID` 的加载对 |
| `themes/default.css` | `planned` | `PRD` §5.1 | SRC-THEME-DEFAULT | 现网蓝灰 token |
| `style.css` `:root` 对调为边缘行者 | `planned` | `PRD` §6.A.4；`USER_DECISION` | SRC-CSS / SRC-THEME-D | 首次无额外文件 |
| `applyTheme(id)` | `planned` | `PRD` §6.A.3 | 不适用 | 非法 id 回退 `FIRST_ID` |
| 运行时文件名是否改为 `theme.js` | `planned` | `PRD` §6.A「可改名」 | 不适用 | 不在本 STEP 选定 |

**输入**：

- `THEME_IDS` / `THEME_ACCENT` / `STORAGE_KEY` / `THEME_SHEETS` / `FIRST_ID` / CSTR-004 / CSTR-005 / CSTR-008 / CSTR-009
- 现有五套 css + `_apply.css` + 现网 `style.css`；实施时新增 `themes/default.css`

**输出**：

- 可调用的 `applyTheme(id)`（全局，供 STEP-003）
- 首屏按存储或合法 `?theme=` 套色；`THEME_SHEETS` 成立
- 合法 `?theme=` 写入 `STORAGE_KEY`；非法 query 不写入该非法值

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| `THEME_IDS` | 见对象约定 | §5.1 |
| `STORAGE_KEY` | `hayyo-h5-theme` | §5.3 |
| 非法或空 | 生效 `FIRST_ID`；空键不自动写入 | §5.3、§6.A.3；USER_DECISION |
| `FIRST_ID` 文件 | 不加载额外皮肤（`:root` 已是粉） | §5.1 |
| `default` | 加载 `themes/default.css` + `_apply.css` | §5.1 |
| 其余非 `FIRST_ID` | 对应 `themes/{id}.css` + `_apply.css` | §5.1 |
| `?theme=` | 合法则本次使用并写入存储；非法则当 `FIRST_ID`，不写非法值 | §5.4、§5.3 |

**开发任务**：

1. 把仅 `?theme=` 才加载的预览脚本收成运行时：解析存储与 URL → `applyTheme`。
2. 把 `style.css` `:root` 换成与 `d-edgerunners.css` 相同的 token；把现行蓝灰 `:root` 写入 `themes/default.css`（含 `--edge: #4a5160`）。
3. `FIRST_ID` / 空 / 非法：卸掉主题 link。`default` 挂 `themes/default.css` 与 `_apply.css`。其余 id 挂指定 css 与 `_apply.css`。
4. 脚本留在 `<head>`。本 STEP 不要做顶栏 `<select>`、不要重绘图谱（STEP-002/003）。
5. 用控制台 `applyTheme` 或 URL 验证下表；本 STEP 无 UI 时「选主题」= 调用 `applyTheme`。已存 `default` 的本机须仍为蓝灰。

**不在本 STEP 范围内**：

- 顶栏下拉框（STEP-003）
- 图谱重绘 API（STEP-002）
- 删除预览条（STEP-004）
- OUT-1～OUT-9；不改 `qa.js` / kb-api；不改三份专题 PRD 正文

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | `applyTheme('a-gits')` 后刷新 | `STORAGE_VAL=a-gits`；`ROOT_ACCENT(a-gits)`；`THEME_SHEETS(a-gits)` | AC16 |
| 正常 | 套非 `FIRST_ID` 后关掉标签再打开同一浏览器 | `STORAGE_VAL` 与 `ROOT_ACCENT` 仍为该 id | AC17 |
| 正常 | `/?theme=c-nightcity` 打开 | 本次 `ROOT_ACCENT(c-nightcity)`；`STORAGE_VAL=c-nightcity` | AC19 |
| 正常 | 上一行后再打开无 query 的工作台 | 仍 `ROOT_ACCENT(c-nightcity)` | AC19 |
| 正常 | `/?theme=default` | `THEME_SHEETS(default)`；`STORAGE_VAL=default`；`ROOT_ACCENT(default)` = `BLUE_ACCENT` | AC9 的存储侧；CSTR-005 |
| 正常 | 存储已是 `default` 时刷新 | 仍 `ROOT_ACCENT(default)`，不迁成粉 | CSTR-004 |
| 异常 | `localStorage` 写入非 `THEME_IDS` 的值后刷新 | `ROOT_ACCENT(FIRST_ID)`；`THEME_SHEETS(FIRST_ID)`；不把非法值当皮肤 | AC18；CSTR-004 |
| 异常 | `/?theme=not-a-theme` | `ROOT_ACCENT(FIRST_ID)`；不把 `not-a-theme` 写成生效皮肤 | CSTR-008 |
| 边界 | 无痕窗口打开无 query | 存储键空；`ROOT_ACCENT(FIRST_ID)`；`THEME_SHEETS(FIRST_ID)` | AC18 |

**完成标志**：

- [ ] 上表每一行的 `STORAGE_VAL` / `ROOT_ACCENT` / `THEME_SHEETS` 断言通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-002] 换肤后重绘关系图域色与连线

**阶段状态**：`verified`

**目标**：`applyTheme` 之后，关系图节点圆点、筛选色点、图例、连线（含箭头 marker）随 CSS 变量更新；节点仍可点、可拖，筛选仍可用。不改 `applyLayout` / `layoutAdmin` / `layoutClient`。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | G1 | 选完四个 Tab 配色立刻跟上（本 STEP 负责图谱表面） | `PRD` |
| 需求 ID | G4 | 关系图行为与换皮前一致（点选/拖拽/筛选） | `PRD` |
| 验收 ID | AC8 | 关系图「账号触达」为紫而非品红（黄主色） | `PRD` |
| 验收 ID | AC11 | 客户端 ↔ 后台：域色点随主题变，节点仍可点、可拖 | `PRD` |
| 验收 ID | AC12 | 客户端交叉：同样换皮，筛选仍可用 | `PRD` |
| 约束 ID | CSTR-002 | 不得改布局算法、图谱数据 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | `applyTheme` 已能切换 css 变量 | 无痕套 `c-prime` 后 `getComputedStyle` 的 `--reach` 与 `THEME_REACH[c-prime]` 满足 `COLOR_EQ` |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `domainColor` | `existing` | `REPO_BASELINE` | SRC-APP / `function domainColor` | 绘制时读 `--social` 等 |
| `renderGraph` / `renderFilters` / `renderDetail` | `existing` | `REPO_BASELINE` | SRC-APP `function renderGraph` / `renderFilters` / `renderDetail` | 换肤后必须再调用 |
| `applyLayout` / `layoutAdmin` / `layoutClient` | `existing` | `REPO_BASELINE` | SRC-APP L107–137 | **静态列布局**；不得改算法 |
| `window.GraphApp` | `existing` | `REPO_BASELINE` | SRC-APP / `window.GraphApp = { setView, selectNode, … }` | 现无换肤入口 |
| `renderGraph` marker `fill="#4a5160"` / `"#6ea8fe"` | `existing` | `REPO_BASELINE` | SRC-APP L155–161 | 重绘时须改随主题，否则连线箭头不跟色 |
| 换肤重绘包装 | `planned` | `PRD` §6.A.4 | 不适用 | 只调现有渲染，不改布局函数体 |
| `c-prime.css --reach` | `existing` | `REPO_BASELINE` | SRC-THEME-CP / `--reach: #c77dff` | AC8 紫色 |
| `d-edgerunners.css --reach` | `existing` | `REPO_BASELINE` | SRC-THEME-D / `--reach: #ff3cac` | AC11 触达偏粉 |

**输入**：

- STEP-001 的 `applyTheme`
- 现网 `domainColor` 已按变量取色，但 SVG `circle fill` 与 marker fill 写在渲染时刻；蓝灰主题连线走 `DEFAULT_EDGE`；`FIRST_ID` 走 `:root --edge`

**输出**：

- 换主题后 `FILTER_DOTS`、`REACH_NODES`、`EDGE_STROKE`、`EDGE_MARKERS` 与当前主题一致
- 拖拽、点选、域筛选行为与换皮前相同（比较选中 `data-id` 与筛选后可见 `data-id` 集合）

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 黄主色触达 | 「账号触达」为紫而非品红 | AC8 |
| 边缘行者粉触达 | 触达节点偏粉 | AC11 怎么验 |
| 不得改布局算法 | 不修改 `applyLayout`/`layoutAdmin`/`layoutClient` 的坐标公式 | §6.A.4；CSTR-002；SRC-APP |

**开发任务**：

1. 在 `applyTheme` 成功换 css 后，若 `GraphApp` 已在，重绘筛选与图（及依赖 `domainColor` 的图例/详情色点）。
2. 不修改 `applyLayout`/`layoutAdmin`/`layoutClient`、不改边数据。首次加载若 css 已在 `renderGraph` 前生效，允许只保证「之后再 applyTheme」重绘。
3. 重绘时 marker fill 不得再写死现网蓝灰；须满足 `EDGE_MARKERS`。
4. 用 `c-prime` 与 `d-edgerunners` 按 `REACH_NODES` 对照「账号触达」。

**不在本 STEP 范围内**：

- 顶栏 `<select>`（STEP-003）
- 文档索引/问答回归（STEP-005）
- 改 `FEATURE_DATA` 或边生成
- 把布局改成力导向或其他算法

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | `applyTheme('c-prime')` 后打开客户端 ↔ 后台 | `REACH_FILTER(c-prime)` 与 `REACH_NODES(c-prime)` 为紫 `#c77dff`，与 `#ff3cac` 不 `COLOR_EQ` | AC8 |
| 正常 | `applyTheme('d-edgerunners')` 后点选、拖拽一节点 | `REACH_NODES(d-edgerunners)` 偏粉；该节点 `data-id` 仍可选中；拖拽只改该 id 的位置，不改其他 id 集合 | AC11 |
| 正常 | 切到客户端交叉后再换主题 | 开关某一域 chip 前后，可见节点 `data-id` 集合按该域过滤变化 | AC12 |
| 正常 | `FIRST_ID` 或空存储下看非激活连线 | `EDGE_STROKE(FIRST_ID)` 与 `EDGE_MARKERS(FIRST_ID)` 成立 | §5.5 |
| 正常 | `applyTheme('default')` 后看非激活连线 | `EDGE_STROKE(default)` 与 `DEFAULT_EDGE` 满足 `COLOR_EQ` | §5.5；AC9 |
| 异常 | `GraphApp` 尚未挂上时先 `applyTheme` | 不抛错；图稍后首次绘制用当前变量 | AC11 |
| 边界 | 从 `c-prime` 再 `applyTheme('d-edgerunners')` | 同一批「账号触达」`data-id` 的 fill 从 `#c77dff` 变为 `#ff3cac`，无需刷新 | AC8、AC11 |
| 边界 | 换肤前已选中节点 A | 换肤后 `GraphApp.getSelectedId()` 仍为 A | G4 |

**完成标志**：

- [ ] `REACH_NODES` / `REACH_FILTER` / `FILTER_DOTS` / `EDGE_STROKE` / `EDGE_MARKERS` 按上表通过
- [ ] `applyLayout`/`layoutAdmin`/`layoutClient` 坐标公式未改
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-003] 顶栏原生主题下拉框

**阶段状态**：`verified`

**目标**：工作台顶栏出现「主题」+ 原生 `<select>`，六选项为 `THEME_OPTIONS`，四个 Tab 都看得到；改选项即 `applyTheme`，不必刷新。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | G1 | 顶栏下拉框能选 6 套之一，选完四个 Tab 配色立刻跟上 | `PRD` |
| 验收 ID | AC1 | 顶栏有「主题」原生下拉框；四个 Tab 各自都在 | `PRD` |
| 验收 ID | AC2 | 选项正好 6 个，文案与 §5.1 一致 | `PRD` |
| 验收 ID | AC3 | 就是系统 `<select>` | `PRD` |
| 验收 ID | AC4 | 选攻壳青后发送钮/选中态变浅青 | `PRD` |
| 验收 ID | AC5 | 选 2049 琥珀后主色偏橙、底偏暖黑 | `PRD` |
| 验收 ID | AC6 | 选夜之城黄后发送钮为荧光黄 | `PRD` |
| 验收 ID | AC7 | 选边缘行者粉后发送钮/选中会话为品红 | `PRD` |
| 验收 ID | AC8 | 选黄主色后发送钮为黄 | `PRD`（触达紫归 STEP-002） |
| 验收 ID | AC9 | 选现网蓝灰后回到 `#6ea8fe` | `PRD` |
| 验收 ID | AC10 | 换主题不必刷新；当前 Tab、当前会话仍在 | `PRD`（打开文档归 STEP-005） |
| 验收 ID | AC23 | 窄于约 980px 时主题下拉框仍能用，不挡住发问 | `PRD` |
| 约束 ID | CSTR-003 | 原生 `<select>` | `PRD`；USER_DECISION「2」 |
| 约束 ID | CSTR-006 | 不放进 `#qaTopActions` | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | `applyTheme` 与存储 | 无 UI 时 URL/`applyTheme` 已能换皮 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `header.topbar` | `existing` | `REPO_BASELINE` | SRC-HTML / `<header class="topbar">` | 插入点：Tab **之外**、非 `#qaTopActions` |
| `#qaTopActions` / `.app:not(.qa-active) .qa-top-actions` | `existing` | `REPO_BASELINE` | SRC-HTML；SRC-CSS `.app:not(.qa-active) .qa-top-actions` | 主题框不得放进该容器 |
| `MAIN_TABS_SEQ` 契约 | `existing` | `REPO_BASELINE` | SRC-CONTRACT / `labels == […]` | 本 STEP 不得改四个 `.tab` 文案或顺序（AC20 完成在 STEP-005） |
| `.qa-send` | `existing` | `REPO_BASELINE` | SRC-QA-CSS / `background: var(--accent)` | AC4–AC9 看发送钮 |
| `.tab.active` | `existing` | `REPO_BASELINE` | SRC-CSS / `background: var(--accent-soft)` | §5.5 Tab 选中态 |
| `<select>` 样式 class | `planned` | `PRD` §6.B.2 | 不适用 | 只对齐高度/边框 |
| `@media (max-width: 980px)` | `existing` | `REPO_BASELINE` | SRC-CSS 两处 max-width 980px | 现只改工作区；AC23 需实测顶栏 |

**输入**：

- STEP-001 `applyTheme`、`THEME_OPTIONS`、CSTR-003、CSTR-006
- USER_DECISION：控件选「2」= 原生 `<select>`

**输出**：

- 顶栏可见「主题」文字 + `SELECT_EL`
- 选项有序元组 = `THEME_OPTIONS`；当前 `value` = 已生效 id
- 变更即换皮并写入存储，不跳转

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 控件 | 原生 `<select>`，不要色点菜单 | §5.2；USER_DECISION「2」 |
| 显示名 | `THEME_OPTIONS` 文案（无「A ·」前缀） | §5.1 |
| 位置 | 顶栏右侧，四个 Tab 之外；四 Tab 都显示 | §5.2 |
| 标签 | 旁边写「主题」；`aria-label="主题"` | §5.2 |

**开发任务**：

1. 在 `index.html` 顶栏加标签与 `<select>`，选项硬编码为 `THEME_OPTIONS`（不要用对照页「A ·」文案）。
2. 绑定 `change` → `applyTheme`；打开页面时 option 与**已生效 id** 一致（存储空则当前项为 `FIRST_ID`，不是列表第一项「现网蓝灰」）。
3. 样式仅对齐现网顶栏控件。四个 Tab 都可见。`TAB_ACTIVE` 随主题变。
4. 不改 `qa.js` 发送逻辑。验 AC4–AC10（Tab/会话）、AC23。

**不在本 STEP 范围内**：

- 图谱触达色与连线（STEP-002）
- 去掉预览条（STEP-004）
- 打开文档仍在、文档/弹层专项（STEP-005）
- 宣称 AC20 完成（本 STEP 只保证不改 `.tab` 按钮）
- OUT-7 自定义菜单

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 依次点四个 `.tab` | 每个 `data-view` 下 `SELECT_EL` 可见且不在 `#qaTopActions` | AC1、AC3；CSTR-006 |
| 正常 | 点开选项 | `(value,text)` 有序 = `THEME_OPTIONS` | AC2 |
| 正常 | 知识问答依次选攻壳青 / 琥珀 / 夜之城黄 / 粉 / 黄主色 / 现网蓝灰 | `QA_SEND_BG` 与 `TAB_ACTIVE` 符合该 id；攻壳青与粉另验 `CONV_ACTIVE` | AC4–AC9；§5.5 |
| 正常 | 问答选中一会话后换主题 | 不刷新；当前 `data-view` 仍为 qa；同一会话身份仍 `.active` | AC10 |
| 边界 | 无痕打开问答 Tab | `SELECT_EL.value === FIRST_ID`；`QA_SEND_BG(FIRST_ID)` | G3；AC21 的控件侧 |
| 边界 | 窗口宽约 980px 以下，问答 Tab | `SELECT_EL` 可打开；布局盒与 `#qaInput`、`.qa-send` 不相交 | AC23 |
| 保护 | 改完 HTML 后跑契约测试 | `labels == MAIN_TABS_SEQ` 仍成立 | CSTR-002（AC20 完成在 005） |

**完成标志**：

- [ ] `SELECT_EL` 与 `THEME_OPTIONS` 有序相等
- [ ] AC4–AC9 的 `QA_SEND_BG` / `CONV_ACTIVE` / `TAB_ACTIVE` / `ROOT_ACCENT` 通过
- [ ] AC10 的 Tab 与会话身份在换肤前后相同
- [ ] AC23 布局盒不相交
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-004] 去掉底部预览条

**阶段状态**：`verified`

**目标**：工作台任意主题都不再出现「正在预览 / 返回对照页 / 看现网」底栏。对照页 `/themes/` 可以保留，且仍打开工作台。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | G3 | 从未选过的人看到边缘行者粉（并与预览条无关） | `PRD`；`USER_DECISION` |
| 验收 ID | AC22 | 底部不再出现「正在预览 / 返回对照页」条 | `PRD` |
| 验收 ID | AC18 | 无痕打开，无底部预览条 | `PRD`（本 STEP 验无条） |
| 约束 ID | CSTR-010 | 对照页可留；链接打开工作台 | `PRD` §6.C.1 |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | 运行时不再把预览当唯一入口 | `applyTheme` 不依赖底栏链接也能换皮 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `mountBar` / `.theme-preview-bar` | `existing` | `REPO_BASELINE` | SRC-PREVIEW `mountBar`；SRC-APPLY `.theme-preview-bar` | 删除或不再挂载 |
| `themes/index.html` | `existing` | `REPO_BASELINE` | SRC-GALLERY | `GALLERY_HREFS`；不要求改卡片标题 |

**输入**：

- 现网预览条实现
- PRD §4.1、§6.B.4、§6.C.1、CSTR-010

**输出**：

- 工作台满足 `PREVIEW_BAR_ABSENT`
- 对照页仍可打开；`GALLERY_HREFS` 仍指向工作台（不要求改「A ·」标题）

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 预览条 | 「正在预览 / 返回对照页」底栏，正式切换后去掉 | §4.1、AC22 |
| 对照页 | 可留当图鉴，不是日常入口 | CSTR-010 |

**开发任务**：

1. 运行时不再 `mountBar`；可删除 `_apply.css` 中仅服务于预览条的规则（若无其它引用）。
2. 不要删除 `themes/*.css` 皮肤文件。
3. 无痕打开工作台：无底栏。带 `?theme=` 打开：无底栏（换皮靠运行时）。
4. 保持对照页链接打开工作台（现网已满足 `GALLERY_HREFS`，不要改成非工作台地址）。

**不在本 STEP 范围内**：

- 改对照页六套色值或「A ·」标题
- 顶栏 `<select>`（STEP-003）
- 改 kb-api

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 工作台 `applyTheme` 任意 `THEME_IDS` | `PREVIEW_BAR_ABSENT` | AC22 |
| 正常 | 无痕打开无 query | `PREVIEW_BAR_ABSENT` | AC18 |
| 边界 | `/?theme=a-gits` | `ROOT_ACCENT(a-gits)` 且 `PREVIEW_BAR_ABSENT` | AC22 |
| 边界 | 打开 `/feature-interaction/themes/` | 页可打开；`GALLERY_HREFS` 仍为工作台 `?theme=` 链接 | CSTR-010 |

**完成标志**：

- [ ] 工作台任意主题与带 `?theme=` 均 `PREVIEW_BAR_ABSENT`
- [ ] `GALLERY_HREFS` 仍指向工作台
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-005] 四 Tab / 弹层跟色与回归

**阶段状态**：`verified`

**目标**：用顶栏切换主题后，文档索引能打开文档且换肤后仍是同一篇，知识问答能提问/看出处/赞踩刷新，配置与明细/热度/重建弹层跟当前主题；四 Tab 名字顺序不变；无主题参数且未选过时除多一个选择框外是边缘行者粉观感。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | G4 | 问答、文档索引、配置/明细/热度弹层行为与换皮前一致 | `PRD`（图谱行为在 STEP-002） |
| 验收 ID | AC10 | 当前打开文档仍在 | `PRD` |
| 验收 ID | AC13 | 文档索引：列表/正文/链接色跟着变，能打开一篇文档 | `PRD` |
| 验收 ID | AC14 | 知识问答：提问、出处、赞踩刷新仍可用 | `PRD` |
| 验收 ID | AC15 | 配置 / 问答明细 / 功能热度 / 重建索引弹层跟当前主题 | `PRD` |
| 验收 ID | AC20 | 四个 Tab 名字、顺序、切换方式与改前相同 | `PRD` |
| 验收 ID | AC21 | 无主题参数且未选过时观感是边缘行者粉（多一个选择框除外） | `PRD`；`USER_DECISION` |
| 约束 ID | CSTR-011 | 不改 `qa.js` 业务、不改 kb-api | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-003 | 顶栏能切换 6 套 | `THEME_OPTIONS` 与 `SELECT_EL` 已通过 |
| STEP-004 | 无预览条 | `PREVIEW_BAR_ABSENT`（AC21 观感不含底栏） |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `#kbWorkspace` / `kb.js` | `existing` | `REPO_BASELINE` | SRC-HTML；SRC-KB-JS | AC13 打开文档 |
| `#qaWorkspace` / `qa.js` | `existing` | `REPO_BASELINE` | SRC-QA-JS | AC14；**不改业务** |
| `data-qa-config` / `reindex` / `rounds` / `heatmap` | `existing` | `REPO_BASELINE` | SRC-HTML；SRC-CONTRACT | `TOP_ACTIONS`；AC15 |
| `.qa-overlay-card` | `existing` | `REPO_BASELINE` | SRC-QA-CSS / `background: var(--bg-elevated)` | `OVERLAY_CARD` |
| `.kb-article a` | `existing` | `REPO_BASELINE` | SRC-CSS | `KB_LINK_COLOR` |
| `MAIN_TABS_SEQ` 测试 | `existing` | `REPO_BASELINE` | SRC-CONTRACT `labels ==` | AC20 |

**输入**：

- 已可切换的主题且无预览条
- 现网问答/文档/弹层行为（CSTR-011）

**输出**：

- AC10 文档身份、AC13–AC15、AC20–AC21 的浏览器证据
- 契约测试四 Tab 有序断言仍绿
- `qa.js` 业务与 kb-api 源文件无本期业务改动

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 必须变色 | 顶栏、Tab 选中、发送、会话选中、图谱域色与连线、文档链接、弹层与出处 | §5.5（图谱部分 STEP-002 已覆盖） |
| 必须不变 | Tab 数量与名字、三栏/对话布局、检索与问答接口、节点数据、赞踩刷新 | §5.5 |
| `MAIN_TABS_SEQ` | 见对象约定 | AC20 |

**开发任务**：

1. 不改 `qa.js` 提问/赞踩/刷新公式；不改 kb-api。
2. 在「攻壳青」打开一篇文档（记下 `DOC_OPEN_ID`），换一次主题后仍是该篇（AC10、AC13）。
3. 换肤后发一句或点已有出处/赞踩刷新（AC14）。
4. 在「夜之城黄」打开配置、明细、热度、重建，每次 `OVERLAY_CARD(c-nightcity)`（AC15）。
5. 跑 `test_fourth_tab_and_no_chips_or_process`；无痕无 query 对照 `QA_SEND_BG(FIRST_ID)`（AC21）。

**不在本 STEP 范围内**：

- 新造主题 id
- 给 `/docs/` 或 admin 接切换器
- STEP-002 已覆盖的图谱拖拽/筛选/连线（本 STEP 不重复改 `app.js` 布局）

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 攻壳青 + 文档索引打开一篇 | `DOC_OPEN_ID` 有值；`KB_LINK_COLOR(a-gits)` | AC13 |
| 正常 | 上一篇仍打开时换到另一主题 | `DOC_OPEN_ID` 不变 | AC10 |
| 正常 | 换肤后知识问答 | 能提问或打开已有出处；已有回答上赞/踩/刷新可点 | AC14 |
| 正常 | 夜之城黄打开配置/明细/热度/重建 | 四次均 `OVERLAY_CARD(c-nightcity)`；`TOP_ACTIONS` 仍在 | AC15 |
| 正常 | 点四个 Tab | `.tab` 文案有序 = `MAIN_TABS_SEQ`；切换仍靠这些按钮 | AC20 |
| 边界 | 无痕、无 `?theme=`、存储空 | `QA_SEND_BG(FIRST_ID)`；`SELECT_EL.value === FIRST_ID`；`PREVIEW_BAR_ABSENT`；仅多 `SELECT_EL` | AC21 |
| 异常 | 契约测试 | `labels == MAIN_TABS_SEQ` 通过 | AC20 |

**完成标志**：

- [ ] `DOC_OPEN_ID` 在换肤前后为同一篇
- [ ] `KB_LINK_COLOR` / `OVERLAY_CARD` / `TOP_ACTIONS` / `MAIN_TABS_SEQ` / `QA_SEND_BG(FIRST_ID)` 按上表通过
- [ ] `qa.js` 与 kb-api 无本期业务改动
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

## 自检

- [x] 所有需求 G1–G4 与验收 AC1–AC23 均映射到 STEP，并写出对象比较方法
- [x] CSTR-001～012 与 OUT-1～OUT-9 有映射
- [x] 每个 STEP 的需求 ID、验收 ID、依赖和范围明确
- [x] 未增加 PRD 中不存在的业务语义（未新造 RQ / TD；未改主题 id/显示名/存储键）
- [x] 未使用 `[自定义]` 补造业务字段或值
- [x] 所有路径和符号标记 `existing` / `planned` / `unverified`
- [x] `existing` 绑定 source_id 与 locator
- [x] 关键项无「当成已实现」的 unverified 运行时断言
- [x] 本文件为验证版；草稿未覆盖
- [x] 阶段结果为五种之一：`PASS_WITH_RISKS`

## 非阻断风险

| ID | 风险 | 为何不阻断 |
|---|---|---|
| R1 | `GraphApp` 无现成换肤 API，需包装现有 `render*` | PRD 已允许调用现有渲染；名称 `PLANNED`。**不另开优化轮**，STEP-002 必须做 |
| R2 | 切到非基线主题时动态 `<link>` 仍可能短暂 FOUC | 首次打开已由 `:root` 对调消化；PRD 对其余主题只要求「尽量」 |
| R3 | 对照页显示名带「A ·」，与下拉框 `THEME_OPTIONS` 不一致 | PRD 未要求改对照页文案；**不优化** |
| R4 | AC23 现网 980px 媒体查询不覆盖顶栏 | 待 STEP-003 按布局盒不相交实测；挡住再改 CSS |
| R5 | 契约测试只锁四 Tab 按钮文案有序相等 | 加 `<select>` 只要不改 `.tab` 即可；回归该测试，不改测试迁就下拉框 |
| R6 | 基线对调后 `:root` 带 `--edge`；蓝灰靠 `themes/default.css` 的 `--edge: #4a5160` | USER_DECISION 已消化原「default 无 --edge」；实施时写入蓝灰文件即可 |

## 阶段结果

`PASS_WITH_RISKS`

必要 PRD 与工作台代码已读。验证版覆盖 G1–G4、AC1–AC23、CSTR、OUT。风险均为非阻断。无 `RUNTIME`。

**本阶段停止。** 可使用本文件做里程碑编排。不自动开始开发。

## 进度

> 路径：本文件（专题夹无独立进度文档约定）  
> PRD 来源：`site/docs/design/h5-theme/PRD-H5工作台主题切换-v1.md`  
> STEP 来源：`steps-verified.md`（原文 `steps-draft.md` 保留）  
> 当前阶段结果：`PASS_WITH_RISKS`

### 进度总览

| 完成数 | 总数 | 当前状态 |
|---|---|---|
| 5 | 5 | `DONE` |

### STEP 明细

| STEP | 功能名称 | 需求 ID | 验收 ID | 前置 STEP | 状态 | 证据 |
|---|---|---|---|---|---|---|
| STEP-001 | 主题运行时 | G2、G3 | AC16、AC17、AC18、AC19 | 无 | `DONE` | 见 `execution/H5工作台主题切换开发执行记录.md` |
| STEP-002 | 图谱域色与连线重绘 | G1、G4 | AC8、AC11、AC12 | STEP-001 | `DONE` | 同上 |
| STEP-003 | 顶栏原生下拉框 | G1 | AC1–AC7、AC8、AC9、AC10、AC23 | STEP-001 | `DONE` | 同上 |
| STEP-004 | 去掉预览条 | G3 | AC22、AC18 | STEP-001 | `DONE` | 同上 |
| STEP-005 | 四 Tab / 弹层回归 | G4 | AC10、AC13、AC14、AC15、AC20、AC21 | STEP-003、STEP-004 | `DONE` | 同上 |

### 阻断与来源变化

| 日期 | STEP | 类型 | 证据或变化 | 处理结果 |
|---|---|---|---|---|
| 2026-09-19 | — | 审查 | `step-doc-review` 验证版 | 草稿保留；本文件为现行 STEP |
| 2026-09-19 | 001 | USER_DECISION | 首次默认改为 `d-edgerunners`；`:root` 对调；已存 `default` 不迁移；risk 不另开优化轮 | 已写入 PRD 与本文件 |
| 2026-09-19 | 001–005 | 执行 | 独立执行验证版 STEP；宿主 18765 RUNTIME | 五项 `DONE`；`qa.js` 未改 |
