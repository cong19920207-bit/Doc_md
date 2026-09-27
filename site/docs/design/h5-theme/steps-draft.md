---
title: "H5 工作台主题切换 STEP 草稿"
status: "draft"
stage_result: "PASS_WITH_RISKS"
prd: "site/docs/design/h5-theme/PRD-H5工作台主题切换-v1.md"
prd_sha256: "26a383a38f52b6638378f0126cab4ed5897c26ac51fc0077090d75b06bea2e48"
created: "2026-09-19"
note: "本文件是草稿，未经 step-doc-review 完整复审前不得当作已验证或可执行计划。不宣布 STEPS_VERIFIED，不生成里程碑，不开始开发。"
---

# H5 工作台主题切换 STEP 草稿

> **现行权威**：[`PRD-H5工作台主题切换-v1.md`](PRD-H5工作台主题切换-v1.md)（status=已确认待实施）。  
> **独立增量**：不替代 [`../h5-kb/PRD-H5知识库-v1.md`](../h5-kb/PRD-H5知识库-v1.md)、[`../kb-qa/PRD-知识问答-v3.md`](../kb-qa/PRD-知识问答-v3.md)、[`../kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md`](../kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md)。  
> 宿主：http://127.0.0.1:18765/feature-interaction/ 。实现状态：仅有 `?theme=` 预览，正式顶栏切换未实施。  
> 本文件 **draft**。不得当作 `steps-verified.md`。

## 来源摘要

事实标签只用：`USER_DECISION`、`PRD`、`CONTRACT`、`REPO_BASELINE`、`RUNTIME`、`PLANNED`、`UNVERIFIED`。本轮无 `RUNTIME`（未把正式切换跑成现网行为）。本轮无独立 Contract 文件；契约测试见 SRC-CONTRACT。

| source_id | 路径 | 状态 | SHA-256 | 本轮核实 |
|---|---|---|---|---|
| SRC-PRD | `site/docs/design/h5-theme/PRD-H5工作台主题切换-v1.md` | `existing` | `26a383a38f52b6638378f0126cab4ed5897c26ac51fc0077090d75b06bea2e48` | 全文；G1–G4；§4 范围；§5.1 六套 id/显示名；§5.2 原生 `<select>`；键 `hayyo-h5-theme`；AC1–AC23；§6 A/B/C |
| SRC-INDEX | `site/docs/design/h5-theme/INDEX.md` | `existing` | `b584d24527c005c0b9b19a4fac1b4c8752ad4eae51831201e7730bfdb1b16c1f` | 专题入口；权威指向 PRD；本轮已挂 `steps-draft.md`（草稿，非验证版） |
| SRC-HTML | `site/feature-interaction/index.html` | `existing` | `a4d27615ffb970deda1a7219674cd88ef26ba6ab13a29d2ccf49f63664f64190` | 四 Tab `data-view` admin/client/kb/qa；`<head>` 引 `theme-preview.js`；`#qaTopActions`；无主题 `<select>` |
| SRC-PREVIEW | `site/feature-interaction/theme-preview.js` | `existing` | `8c25db3946f6a77391c48c1fde5a128612b8c1b825a3252e9f9848738d81ad57` | 仅 `?theme=` 且 id 在 `NAMES` 时加载 CSS；无 `default`；无 `localStorage`；`mountBar`；无 `applyTheme` |
| SRC-APP | `site/feature-interaction/app.js` | `existing` | `49ccca29088af321b95f9e86e25a8d89e2c2bd3f56cb26d6a82aa453f63c4e78` | `domainColor` 读 CSS 变量；`renderGraph`/`renderFilters`/`renderDetail`；`window.GraphApp` 仅 `setView`/`selectNode`/`getSelectedId`/`getLastGraphView`；无换肤重绘入口 |
| SRC-CSS | `site/feature-interaction/style.css` | `existing` | `d8e0750698d99f6a04a019b3339a62866ff3e3323b7f213e8084e754f73ce20f` | `:root --accent: #6ea8fe`；`.app:not(.qa-active) .qa-top-actions { display: none }`；`@media (max-width: 980px)` 只改工作区栅格 |
| SRC-QA-CSS | `site/feature-interaction/qa.css` | `existing` | `af129a9d7dd9a6fe1f9c629ce1c0c10fad9bf8044555c8dac24e92ea46aea752` | `.qa-send { background: var(--accent) }`；`.qa-overlay` 用现网变量 |
| SRC-QA-JS | `site/feature-interaction/qa.js` | `existing` | `30e5389e3eea73435a0c85f4d109b700ef74ff6fa608cb50e829a5d5d768d130` | 本轮只读；问答发送/出处/赞踩刷新；本期不改业务 |
| SRC-KB-JS | `site/feature-interaction/kb.js` | `existing` | `803e4228d906b0f65a3d5f49ed5cffa91cd0a2172460d096b652fb30a0ed8efc` | 本轮只读；`GraphApp.setView("kb")` |
| SRC-APPLY | `site/feature-interaction/themes/_apply.css` | `existing` | `d96f1e8319acc7886028b5ffccdb97e4973c4fadbc84c58417454b5757c8b7ed` | 硬编码色接到变量；含 `.theme-preview-bar` |
| SRC-THEME-A | `site/feature-interaction/themes/a-gits.css` | `existing` | `c4e250ec27901a608a49f340153b61d90cf206eaceb2a1d87c0bdb3eca499754` | `--accent: #7ec8d0` |
| SRC-THEME-B | `site/feature-interaction/themes/b-2049.css` | `existing` | `ac7585e676eaa1bd50b768da4dc220400f23002ed75f71df15b75fbfa818bbb5` | `--accent: #e08a2c` |
| SRC-THEME-C | `site/feature-interaction/themes/c-nightcity.css` | `existing` | `db0245060d553b641f2572e586d3d0733b53623ddbde52bfc11b6c420700cba4` | `--accent: #fcee0a`；`--reach: #ff2a6d` |
| SRC-THEME-D | `site/feature-interaction/themes/d-edgerunners.css` | `existing` | `dce7b86065d63b61a8c31338de1973156e6d57edc34e82f84c865ff324c1b48c` | `--accent: #ff3cac`；`--reach: #ff3cac` |
| SRC-THEME-CP | `site/feature-interaction/themes/c-prime.css` | `existing` | `a997b668511343faede677736d819513ed03c0776632519f1f47c4fb696618bf` | `--accent: #fcee0a`；`--reach: #c77dff` |
| SRC-GALLERY | `site/feature-interaction/themes/index.html` | `existing` | `d0bddc2710a0f0b2ce75364f26c4ccf2f2e719eab2f5ca321dc016f198789891` | 对照页链到 `/?theme=…&view=…`；显示名带「A ·」前缀，与 PRD `<select>` 文案不完全相同 |
| SRC-CONTRACT | `site/kb-api/tests/test_site_contract.py` | `existing` | `f7983d5bca9ad078f9b19545f4e26003e988398bd7f36daf34de089aa9c369ad` | `test_fourth_tab_and_no_chips_or_process` 断言四 Tab 文案多重集；加 `<select>` 只要不改 `.tab` 按钮即可 |

**发现门（不填具体值、不宣称已决定）：**

- 换肤后调用哪一层 GraphApp API：现网无专用方法（SRC-APP）。PRD 要求调用现有 `renderFilters`/`renderGraph`，**不得改布局算法**。包装函数名按已核实项目约定确定（`PLANNED`）。
- `theme-preview.js` 是否改名为 `theme.js`：PRD §6 步骤 A 写「可改名」，本草稿不选定文件名。
- 顶栏 `<select>` 的 class 名与具体像素：PRD 只要求高度/边框对齐现网顶栏控件（`PLANNED`）。
- `?view=` 预览参数：PRD §5.4 写正式切换不依赖、可保留；不是 G1 验收条件。

启动命令（`REPO_BASELINE`，compose 文件头惯例）：在 `site/` 执行 `docker compose up -d`；或仓库根 `docker compose -f site/docker-compose.yml up -d`。宿主 URL：http://127.0.0.1:18765/feature-interaction/ 。

## 对象比较约定

| 符号 | 定义 | 来源 |
|---|---|---|
| `MAIN_TABS` | 文本多重集 {「客户端 ↔ 后台」,「客户端交叉」,「文档索引」,「知识问答」}，大小 4 | SRC-HTML；SRC-CONTRACT；AC20 |
| `THEME_IDS` | `default` / `a-gits` / `b-2049` / `c-nightcity` / `d-edgerunners` / `c-prime` | PRD §5.1 |
| `THEME_LABELS` | 顺序：现网蓝灰、攻壳青、2049 琥珀、夜之城黄、边缘行者粉、黄主色 | PRD §5.1 |
| `STORAGE_KEY` | `hayyo-h5-theme` | PRD §5.3 |
| `DEFAULT_ACCENT` | `#6ea8fe` | SRC-CSS `:root --accent`；AC9、AC21 |

对照页卡片标题（SRC-GALLERY）带「A · 攻壳青」等前缀，**不是** `THEME_LABELS`。下拉框必须用 `THEME_LABELS`。

## 输入清单

### 本期有效需求

PRD 未使用 `RQ-*`。有效需求 ID 沿用 PRD 已有编号 **G1–G4**。未编号约束用 `CSTR-*`，不新造 `RQ-*`。

| ID | 摘要 | 来源 |
|---|---|---|
| G1 | 顶栏下拉框能选 6 套之一，四个 Tab 配色立刻跟上 | PRD §2.3 |
| G2 | 刷新、关标签再开同一浏览器，仍是上次那套 | PRD §2.3 |
| G3 | 从未选过的人看到现网蓝灰 | PRD §2.3 |
| G4 | 问答、关系图、文档索引、配置/明细/热度弹层行为与换皮前一致 | PRD §2.3 |

### 本期有效验收

AC1–AC23（PRD §7）。

### 未编号约束（CSTR）

| ID | 摘要 | 来源 |
|---|---|---|
| CSTR-001 | 只做工作台 SPA；不做 `/docs/`、admin-skin、复盘、原型、Hayyo App | PRD §4.2 |
| CSTR-002 | 不改四 Tab 信息结构、问答接口、图谱数据/布局算法 | PRD §4.2、§5.5、§6.A.4 |
| CSTR-003 | 控件为原生 `<select>`，不要自定义带色点菜单 | PRD §5.2；USER_DECISION「2」 |
| CSTR-004 | 存储键 `hayyo-h5-theme`；非法或空 = `default`；不写服务器 | PRD §5.3、§3 |
| CSTR-005 | `default` 不加载额外皮肤文件；非 default 同时加载对应 css + `_apply.css` | PRD §5.1 |
| CSTR-006 | 主题 `<select>` 四个 Tab 都显示，不放进 `#qaTopActions` | PRD §5.2、§6.B.3；SRC-CSS `.app:not(.qa-active) .qa-top-actions` |
| CSTR-007 | 不把本增量写进 `prd/design/*/PRD.md`，不改 h5-kb / kb-qa / kb-qa-feedback 正文 | PRD §4.2 |
| CSTR-008 | 日常不依赖 `?theme=`；合法 `?theme=` 写入 `localStorage` | PRD §5.4 |
| CSTR-009 | 脚本在 `index.html` `<head>`，尽量减少先闪蓝灰 | PRD §6.A.2 |
| CSTR-010 | 对照页可留作图鉴，不是日常入口 | PRD §4.1、§6.C.1 |
| CSTR-011 | 不改 `qa.js` 业务、不改 kb-api | PRD §6.C.2 |
| CSTR-012 | 无登录；主题只在本机 | PRD §3 |

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
| OUT-8 | 重写 `style.css` 结构、引入 React/Vue、把 6 套色内联成一份巨文件 | §6 明确不在本期 |
| OUT-9 | 为 `/docs/` 或 admin-skin 接同一套切换器 | §6 明确不在本期 |

### 技术债

无 PRD 编号技术债。现网预览条与 `?theme=` 仅加载、无 `localStorage`，由本期 STEP 替换，不另开 TD 编号。

## STEP 总览

| STEP | 标题 | 需求 | 验收 | 前置 |
|---|---|---|---|---|
| STEP-001 | 主题运行时：套皮、记住、URL | G2、G3 | AC16、AC17、AC18（默认蓝灰）、AC19 | 无 |
| STEP-002 | 换肤后重绘关系图域色 | G1（图谱表面） | AC8（触达色）、AC11、AC12 | STEP-001 |
| STEP-003 | 顶栏原生主题下拉框 | G1 | AC1–AC7、AC8（发送钮）、AC9、AC10、AC23 | STEP-001 |
| STEP-004 | 去掉底部预览条 | G3 | AC22、AC18（无预览条） | STEP-001 |
| STEP-005 | 四 Tab / 弹层跟色与回归 | G4 | AC13、AC14、AC15、AC20、AC21 | STEP-003 |

建议人读顺序 001→002→003→004→005。编号顺序不表示 004 依赖 003：004 与 003 在 001 之后可并行。

## 需求映射

| 需求 ID | STEP | 本 STEP 承担的条款 |
|---|---|---|
| G1 | STEP-003 | 顶栏下拉框选 6 套，立刻换皮 |
| G1 | STEP-002 | 关系图/筛选色点随当前主题 |
| G2 | STEP-001 | localStorage + 刷新/再开仍在 |
| G3 | STEP-001 | 无记录时 `default` / 现网蓝灰 |
| G3 | STEP-004 | 无痕打开无预览条 |
| G4 | STEP-005 | 问答/文档/弹层行为与 Tab 回归 |

## 验收映射

| 验收 ID | STEP | 本 STEP 承担的子条款 |
|---|---|---|
| AC1 | STEP-003 | 四 Tab 都有主题下拉框 |
| AC2 | STEP-003 | 6 个选项文案 = `THEME_LABELS` |
| AC3 | STEP-003 | 原生 `<select>` |
| AC4 | STEP-003 | 攻壳青：发送钮/选中浅青 |
| AC5 | STEP-003 | 2049 琥珀：主色偏橙、底暖黑 |
| AC6 | STEP-003 | 夜之城黄：发送钮荧光黄 |
| AC7 | STEP-003 | 边缘行者粉：发送钮/选中品红 |
| AC8 | STEP-003 | 黄主色：发送钮为黄 |
| AC8 | STEP-002 | 黄主色：关系图「账号触达」为紫而非品红 |
| AC9 | STEP-003 | 切回现网蓝灰，主色 `DEFAULT_ACCENT` |
| AC10 | STEP-003 | 换主题不刷新；当前 Tab/会话/文档仍在 |
| AC11 | STEP-002 | 客户端 ↔ 后台：域色随主题，节点可点可拖 |
| AC12 | STEP-002 | 客户端交叉：换皮后筛选仍可用 |
| AC13 | STEP-005 | 文档索引换皮后能打开一篇 |
| AC14 | STEP-005 | 知识问答换肤后提问/出处/赞踩刷新仍可用 |
| AC15 | STEP-005 | 配置/明细/热度/重建弹层跟当前主题 |
| AC16 | STEP-001 | 非默认主题刷新仍在 |
| AC17 | STEP-001 | 关标签再开仍在 |
| AC18 | STEP-001 | 无痕/清空存储第一次是现网蓝灰 |
| AC18 | STEP-004 | 无底部预览条 |
| AC19 | STEP-001 | `?theme=c-nightcity` 写入存储，刷新仍在 |
| AC20 | STEP-005 | `MAIN_TABS` 名字顺序切换方式不变 |
| AC21 | STEP-005 | 无主题参数时除多一个选择框外观感同现网蓝灰 |
| AC22 | STEP-004 | 工作台任意主题无「正在预览 / 返回对照页」条 |
| AC23 | STEP-003 | 窄于约 980px 下拉框能用、不挡住发问 |

## 完整 STEP 提示词

### [STEP-001] 主题运行时：套皮、记住、URL

**阶段状态**：`draft`

**目标**：不依赖顶栏控件，也能按 `THEME_IDS` 挂/卸皮肤 CSS，把选择写入 `STORAGE_KEY`，合法 `?theme=` 与刷新后仍生效；无记录时保持现网蓝灰。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | G2 | 刷新、关标签再开同一浏览器，仍是上次那套 | `PRD` |
| 需求 ID | G3 | 从未选过的人看到的仍是现网蓝灰 | `PRD` |
| 验收 ID | AC16 | 选非默认主题后刷新，仍是那套 | `PRD` |
| 验收 ID | AC17 | 关标签再打开工作台，仍是那套 | `PRD` |
| 验收 ID | AC18 | 清 `localStorage` 或无痕窗口，第一次是现网蓝灰 | `PRD`（本 STEP 只验默认蓝灰，预览条见 STEP-004） |
| 验收 ID | AC19 | 从对照页带 `?theme=c-nightcity` 进来，本次即夜之城黄，且刷新仍在 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| 无 | — | — |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `theme-preview.js` IIFE、`NAMES`、`addSheet` | `existing` | `REPO_BASELINE` | SRC-PREVIEW / 文件头至 `addSheet("themes/_apply.css")` | 改成可挂可卸运行时的底 |
| `index.html` `<script src="theme-preview.js">` | `existing` | `REPO_BASELINE` | SRC-HTML / `<head>` | 保持在 head 以减少闪色 |
| `themes/{id}.css`、`themes/_apply.css` | `existing` | `REPO_BASELINE` | SRC-THEME-A～CP、SRC-APPLY | 非 default 加载对 |
| `applyTheme(id)` | `planned` | `PRD` §6.A.3 | 不适用 | 非法 id 回退 default |
| 运行时文件名是否改为 `theme.js` | `planned` | `PRD` §6.A「可改名」 | 不适用 | 不在本 STEP 选定 |

**输入**：

- `THEME_IDS` / `STORAGE_KEY` / `CSTR-004` / `CSTR-005` / `CSTR-008` / `CSTR-009`
- 现有五套 css + `_apply.css` + 现网 `style.css`

**输出**：

- 可调用的 `applyTheme(id)`（全局，供 STEP-003）
- 首屏按存储或合法 `?theme=` 套色；`default` 不挂额外 css
- 合法 `?theme=` 写入 `STORAGE_KEY`

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| `THEME_IDS` | 见对象约定 | §5.1 |
| `STORAGE_KEY` | `hayyo-h5-theme` | §5.3 |
| 非法或空 | 当作 `default` | §5.3、§6.A.3 |
| `default` 文件 | 不加载额外皮肤 | §5.1 |
| 非 default | 对应 `themes/{id}.css` + `_apply.css` | §5.1 |
| `?theme=` | 合法则本次使用并写入存储 | §5.4 |

**开发任务**：

1. 把仅 `?theme=` 才加载的预览脚本收成运行时：解析存储与 URL → `applyTheme`。
2. `default` 卸掉主题 link；非 default 挂指定 css 与 `_apply.css`。
3. 脚本留在 `<head>`。本 STEP 不要做顶栏 `<select>`、不要重绘图谱（STEP-002/003）。
4. 可用控制台或 URL 验证 AC16/17/18/19 中属于本 STEP 的部分。

**不在本 STEP 范围内**：

- 顶栏下拉框（STEP-003）
- 图谱重绘 API（STEP-002）
- 删除预览条（STEP-004）
- OUT-1～OUT-9；不改 `qa.js` / kb-api

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 控制台或 URL 套 `a-gits` 后刷新 | 仍为攻壳青变量（`--accent` 为 `#7ec8d0`） | AC16 |
| 正常 | 套非 default 后关掉标签再打开同一浏览器 | 仍是那套 | AC17 |
| 正常 | `/?theme=c-nightcity` 打开再刷新（可去掉 query） | 仍是夜之城黄 | AC19 |
| 异常 | `localStorage` 写入非 `THEME_IDS` 的值后刷新 | 现网蓝灰，`--accent` 为 `DEFAULT_ACCENT` | AC18 |
| 边界 | 无痕窗口打开无 query | 现网蓝灰；不加载 `themes/a-gits.css` 等 | AC18 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-002] 换肤后重绘关系图域色

**阶段状态**：`draft`

**目标**：`applyTheme` 之后，关系图节点圆点、筛选色点、图例随 CSS 变量更新；节点仍可点、可拖，筛选仍可用。不改布局算法。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | G1 | 选完四个 Tab 配色立刻跟上（本 STEP 负责图谱表面） | `PRD` |
| 验收 ID | AC8 | 关系图「账号触达」为紫而非品红（黄主色） | `PRD` |
| 验收 ID | AC11 | 客户端 ↔ 后台：域色点随主题变，节点仍可点、可拖 | `PRD` |
| 验收 ID | AC12 | 客户端交叉：同样换皮，筛选仍可用 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | `applyTheme` 已能切换 css 变量 | 无痕套 `c-prime` 后 `getComputedStyle` 的 `--reach` 为 `#c77dff` |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `domainColor` | `existing` | `REPO_BASELINE` | SRC-APP / `function domainColor` | 绘制时读 `--social` 等 |
| `renderGraph` / `renderFilters` / `renderDetail` | `existing` | `REPO_BASELINE` | SRC-APP | 换肤后必须再调用 |
| `window.GraphApp` | `existing` | `REPO_BASELINE` | SRC-APP / `window.GraphApp = { setView, selectNode, … }` | 现无换肤入口 |
| 换肤重绘包装 | `planned` | `PRD` §6.A.4 | 不适用 | 只调现有渲染，不改 `applyLayout` 算法 |
| `c-prime.css --reach` | `existing` | `REPO_BASELINE` | SRC-THEME-CP / `--reach: #c77dff` | AC8 紫色 |
| `d-edgerunners.css --reach` | `existing` | `REPO_BASELINE` | SRC-THEME-D / `--reach: #ff3cac` | AC11 触达偏粉 |

**输入**：

- STEP-001 的 `applyTheme`
- 现网 `domainColor` 已按变量取色，但 SVG `fill` 写在渲染时刻

**输出**：

- 换主题后筛选点、节点圆点、空选图例颜色与当前 `:root` 一致
- 拖拽、点选、域筛选行为与换皮前相同

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 黄主色触达 | 「账号触达」为紫而非品红 | AC8 |
| 边缘行者粉触达 | 触达节点偏粉 | AC11 怎么验 |
| 不得改布局算法 | 调用现有渲染 | §6.A.4；CSTR-002 |

**开发任务**：

1. 在 `applyTheme` 成功换 css 后，若 `GraphApp` 已在，重绘筛选与图（及依赖 `domainColor` 的图例）。
2. 不修改力导向/相机/边数据。首次加载若 css 已在 `renderGraph` 前生效，允许只保证「之后再 applyTheme」重绘。
3. 用 `c-prime` 与 `d-edgerunners` 对照「账号触达」圆点。

**不在本 STEP 范围内**：

- 顶栏 `<select>`（STEP-003）
- 文档索引/问答回归（STEP-005）
- 改 `FEATURE_DATA` 或边生成

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | `applyTheme('c-prime')` 后打开客户端 ↔ 后台 | 「账号触达」色点为紫（`--reach` `#c77dff`），不是品红 | AC8 |
| 正常 | `applyTheme('d-edgerunners')` 后点选、拖拽一节点 | 触达偏粉；点选与拖拽仍可用 | AC11 |
| 正常 | 切到客户端交叉后再换主题 | 筛选 chip 仍可开关，图跟着滤 | AC12 |
| 异常 | `GraphApp` 尚未挂上时先 `applyTheme` | 不抛错；图稍后首次绘制用当前变量 | AC11 |
| 边界 | 从 `c-prime` 再 `applyTheme('d-edgerunners')` | 触达从紫变为品红，无需刷新 | AC8、AC11 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-003] 顶栏原生主题下拉框

**阶段状态**：`draft`

**目标**：工作台顶栏出现「主题」+ 原生 `<select>`，六选项文案为 `THEME_LABELS`，四个 Tab 都看得到；改选项即 `applyTheme`，不必刷新。

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
| 验收 ID | AC10 | 换主题不必刷新；当前 Tab、会话、打开文档仍在 | `PRD` |
| 验收 ID | AC23 | 窄于约 980px 时主题下拉框仍能用，不挡住发问 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | `applyTheme` 与存储 | 无 UI 时 URL/`applyTheme` 已能换皮 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `header.topbar` | `existing` | `REPO_BASELINE` | SRC-HTML / `<header class="topbar">` | 插入点：Tab **之外**、非 `#qaTopActions` |
| `#qaTopActions` / `.app:not(.qa-active) .qa-top-actions` | `existing` | `REPO_BASELINE` | SRC-HTML；SRC-CSS 约 L323 | 主题框不得放进该容器 |
| `MAIN_TABS` 契约 | `existing` | `REPO_BASELINE` | SRC-CONTRACT / `labels == […]` | 不得改四个 `.tab` 文案 |
| `.qa-send` | `existing` | `REPO_BASELINE` | SRC-QA-CSS / `background: var(--accent)` | AC4–AC9 看发送钮 |
| `<select>` 样式 class | `planned` | `PRD` §6.B.2 | 不适用 | 只对齐高度/边框 |
| `@media (max-width: 980px)` | `existing` | `REPO_BASELINE` | SRC-CSS 约 L603–609 | 现只改工作区；AC23 需实测顶栏 |

**输入**：

- STEP-001 `applyTheme`、`THEME_LABELS`、CSTR-003、CSTR-006
- USER_DECISION：控件选「2」= 原生 `<select>`

**输出**：

- 顶栏「主题」标签 + `<select aria-label="主题">`
- 选项顺序与文案 = `THEME_LABELS`；当前项 = 已生效 id
- 变更即换皮并写入存储，不跳转

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 控件 | 原生 `<select>`，不要色点菜单 | §5.2；USER_DECISION「2」 |
| 显示名 | `THEME_LABELS`（无「A ·」前缀） | §5.1 |
| 位置 | 顶栏右侧，四个 Tab 之外；四 Tab 都显示 | §5.2 |
| 标签 | 旁边写「主题」；`aria-label="主题"` | §5.2 |

**开发任务**：

1. 在 `index.html` 顶栏加标签与 `<select>`，选项硬编码为 §5.1（不要用对照页「A ·」文案）。
2. 绑定 `change` → `applyTheme`；打开页面时 option 与存储一致。
3. 样式仅对齐现网顶栏控件。四个 Tab 都可见。
4. 不改 `qa.js` 发送逻辑。验 AC4–AC10、AC23。

**不在本 STEP 范围内**：

- 图谱触达色（STEP-002）
- 去掉预览条（STEP-004）
- 文档/弹层专项（STEP-005）
- OUT-7 自定义菜单

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 四个 Tab 各看一眼 | 都有「主题」`<select>` | AC1、AC3 |
| 正常 | 点开选项 | 6 项，文案=现网蓝灰…黄主色 | AC2 |
| 正常 | 知识问答依次选攻壳青 / 琥珀 / 夜之城黄 / 粉 / 黄主色 / 现网蓝灰 | 发送钮与选中态符合 AC4–AC9 | AC4–AC9 |
| 正常 | 问答选中一会话后换主题 | 仍在该会话、不刷新 | AC10 |
| 边界 | 窗口宽约 980px 以下，问答 Tab | 下拉可用，不挡住输入与发送 | AC23 |
| 异常 | 契约测试四 Tab 文案 | 仍等于 `MAIN_TABS` | AC20 的前置；本 STEP 不得改 Tab 按钮 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-004] 去掉底部预览条

**阶段状态**：`draft`

**目标**：工作台任意主题都不再出现「正在预览 / 返回对照页 / 看现网」底栏。对照页 `/themes/` 可以保留。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | G3 | 从未选过的人看到现网蓝灰（并与预览条无关） | `PRD` |
| 验收 ID | AC22 | 底部不再出现「正在预览 / 返回对照页」条 | `PRD` |
| 验收 ID | AC18 | 无痕打开，无底部预览条 | `PRD`（本 STEP 验无条） |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | 运行时不再把预览当唯一入口 | `applyTheme` 不依赖底栏链接也能换皮 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `mountBar` / `.theme-preview-bar` | `existing` | `REPO_BASELINE` | SRC-PREVIEW `mountBar`；SRC-APPLY `.theme-preview-bar` | 删除或不再挂载 |
| `themes/index.html` | `existing` | `REPO_BASELINE` | SRC-GALLERY | CSTR-010 可留图鉴 |

**输入**：

- 现网预览条实现
- PRD §4.1、§6.B.4、CSTR-010

**输出**：

- 工作台 DOM 无 `.theme-preview-bar`，文案不含「正在预览」
- 对照页仍可打开（不要求改卡片标题）

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 预览条 | 「正在预览 / 返回对照页」底栏，正式切换后去掉 | §4.1、AC22 |
| 对照页 | 可留当图鉴，不是日常入口 | CSTR-010 |

**开发任务**：

1. 运行时不再 `mountBar`；可删除 `_apply.css` 中仅服务于预览条的规则（若无其它引用）。
2. 不要删除 `themes/*.css` 皮肤文件。
3. 无痕打开工作台：无底栏。带 `?theme=` 打开：无底栏（换皮靠运行时）。

**不在本 STEP 范围内**：

- 改对照页六套色值
- 顶栏 `<select>`（STEP-003）
- 改 kb-api

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 工作台选任意主题 | 底栏无「正在预览」「返回对照页」 | AC22 |
| 正常 | 无痕打开无 query | 无预览条 | AC18 |
| 边界 | `/?theme=a-gits` | 可套攻壳青，但仍无预览条 | AC22 |
| 异常 | 打开 `/feature-interaction/themes/` | 对照页仍能打开（图鉴） | CSTR-010 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-005] 四 Tab / 弹层跟色与回归

**阶段状态**：`draft`

**目标**：用顶栏切换主题后，文档索引能打开文档，知识问答能提问/看出处/赞踩刷新，配置与明细/热度/重建弹层跟当前主题；四 Tab 名字顺序不变；无主题参数时除多一个选择框外仍是现网蓝灰观感。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | G4 | 问答、关系图、文档索引、配置/明细/热度弹层行为与换皮前一致 | `PRD` |
| 验收 ID | AC13 | 文档索引：列表/正文/链接色跟着变，能打开一篇文档 | `PRD` |
| 验收 ID | AC14 | 知识问答：提问、出处、赞踩刷新仍可用 | `PRD` |
| 验收 ID | AC15 | 配置 / 问答明细 / 功能热度 / 重建索引弹层跟当前主题 | `PRD` |
| 验收 ID | AC20 | 四个 Tab 名字、顺序、切换方式与改前相同 | `PRD` |
| 验收 ID | AC21 | 无主题参数时现网蓝灰观感与加下拉框之前一致（多一个选择框除外） | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-003 | 顶栏能切换 6 套 | AC1–AC2 已通过 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `#kbWorkspace` / `kb.js` | `existing` | `REPO_BASELINE` | SRC-HTML；SRC-KB-JS | AC13 打开文档 |
| `#qaWorkspace` / `qa.js` | `existing` | `REPO_BASELINE` | SRC-QA-JS | AC14；**不改业务** |
| `data-qa-config` / `reindex` / `rounds` / `heatmap` | `existing` | `REPO_BASELINE` | SRC-HTML；SRC-CONTRACT | AC15 |
| `.qa-overlay` | `existing` | `REPO_BASELINE` | SRC-QA-CSS | 弹层吃 CSS 变量 |
| `MAIN_TABS` 测试 | `existing` | `REPO_BASELINE` | SRC-CONTRACT | AC20 |

**输入**：

- 已可切换的主题
- 现网问答/文档/弹层行为（CSTR-011）

**输出**：

- AC13–AC15、AC20–AC21 的浏览器证据
- 契约测试四 Tab 断言仍绿

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 必须变色 | 顶栏、Tab 选中、发送、会话选中、图谱域色、文档链接、弹层与出处 | §5.5 |
| 必须不变 | Tab 数量与名字、三栏/对话布局、检索与问答接口、节点数据、赞踩刷新 | §5.5 |
| `MAIN_TABS` | 见对象约定 | AC20 |

**开发任务**：

1. 不改 `qa.js` 提问/赞踩/刷新公式；不改 kb-api。
2. 在「攻壳青」打开一篇文档（AC13）；换肤后发一句或点已有出处/赞踩刷新（AC14）。
3. 在「夜之城黄」打开配置、明细、热度、重建（AC15）。
4. 跑 `test_fourth_tab_and_no_chips_or_process`；无痕无 query 对照蓝发送钮（AC21）。

**不在本 STEP 范围内**：

- 新造主题 id
- 给 `/docs/` 或 admin 接切换器
- STEP-002 已覆盖的图谱拖拽/筛选（本 STEP 不重复改 `app.js` 布局）

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 攻壳青 + 文档索引打开一篇 | 能读正文，链接色随主题 | AC13 |
| 正常 | 换肤后知识问答 | 提问或已有出处/赞踩刷新仍可用 | AC14 |
| 正常 | 夜之城黄打开配置/明细/热度/重建 | 弹层跟黄主色体系 | AC15 |
| 正常 | 点四个 Tab | 名字顺序与切换方式同改前 | AC20 |
| 边界 | 无痕、无 `?theme=`、存储空 | 蓝发送钮 `DEFAULT_ACCENT`；仅多主题 `<select>` | AC21 |
| 异常 | 契约测试 | 四 Tab 文案断言通过 | AC20 |

**完成标志**：

- [ ] 当前 STEP 的验收断言全部通过
- [ ] 未改变其他 STEP 的范围或来源需求
- [ ] 新发现的路径、符号和契约证据已更新状态
- [ ] 进度记录已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

## 自检

- [x] 所有需求 G1–G4 与验收 AC1–AC23 均映射到 STEP
- [x] 每个 STEP 的需求 ID、验收 ID、依赖和范围明确
- [x] 未增加 PRD 中不存在的业务语义（未新造 RQ；未改主题 id/显示名/存储键）
- [x] 未使用 `[自定义]` 补造业务字段或值
- [x] 所有路径和符号标记 `existing` / `planned` / `unverified`
- [x] `existing` 绑定 source_id 与 locator
- [x] 关键项无「当成已实现」的 unverified 运行时断言
- [x] 草稿未自称已验证或可执行
- [x] 阶段结果为五种之一：`PASS_WITH_RISKS`

## 非阻断风险

| ID | 风险 | 为何不阻断 |
|---|---|---|
| R1 | `GraphApp` 无现成换肤 API，需包装现有 `render*` | PRD 已允许调用现有渲染；名称 `PLANNED` |
| R2 | 动态插入 `<link>` 仍可能短暂 FOUC | PRD 只要求「尽量」；head 脚本已核实存在 |
| R3 | 对照页显示名带「A ·」，与下拉框 `THEME_LABELS` 不一致 | PRD 未要求改对照页文案；下拉框以 §5.1 为准 |
| R4 | AC23 现网 980px 媒体查询不覆盖顶栏 | 待 STEP-003 实测；不改变业务语义 |
| R5 | 契约测试只锁四 Tab 按钮文案 | 加 `<select>` 只要不改 `.tab` 即可；STEP-003/005 须回归该测试 |

## 阶段结果

`PASS_WITH_RISKS`

必要 PRD 与工作台代码已读。草稿结构完整，覆盖 G1–G4 与 AC1–AC23。风险均为非阻断。

**本阶段停止。** 不宣布 `STEPS_VERIFIED`，不生成里程碑计划，不开始开发。正式执行前需 `step-doc-review` 产出 `steps-verified.md`。

## 进度

> 路径：本文件（专题夹无独立进度文档约定）  
> PRD 来源：`site/docs/design/h5-theme/PRD-H5工作台主题切换-v1.md`  
> STEP 来源：`steps-draft.md`  
> 当前阶段结果：`PASS_WITH_RISKS`

### 进度总览

| 完成数 | 总数 | 当前状态 |
|---|---|---|
| 0 | 5 | `NOT_STARTED` |

### STEP 明细

| STEP | 功能名称 | 需求 ID | 验收 ID | 前置 STEP | 状态 | 证据 |
|---|---|---|---|---|---|---|
| STEP-001 | 主题运行时 | G2、G3 | AC16、AC17、AC18、AC19 | 无 | `NOT_STARTED` | — |
| STEP-002 | 图谱域色重绘 | G1 | AC8、AC11、AC12 | STEP-001 | `NOT_STARTED` | — |
| STEP-003 | 顶栏原生下拉框 | G1 | AC1–AC7、AC8、AC9、AC10、AC23 | STEP-001 | `NOT_STARTED` | — |
| STEP-004 | 去掉预览条 | G3 | AC22、AC18 | STEP-001 | `NOT_STARTED` | — |
| STEP-005 | 四 Tab / 弹层回归 | G4 | AC13、AC14、AC15、AC20、AC21 | STEP-003 | `NOT_STARTED` | — |

### 阻断与来源变化

| 日期 | STEP | 类型 | 证据或变化 | 处理结果 |
|---|---|---|---|---|
| — | — | — | — | — |
