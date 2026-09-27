---
title: "H5 工作台主题切换 STEP 审查报告"
mode: "standalone / review-repair"
round: 1
input_step: "site/docs/design/h5-theme/steps-draft.md"
input_step_sha256: "32fa3078f2c790a7e142e147789bbe6b8c991647ad4e7e3b98ee1575cdb4e951"
verified: "site/docs/design/h5-theme/steps-verified.md"
verified_sha256: "a03ec15431637f6843436d6b85dfa5a3ba8ba45a9b3fc959ec694aef534b7f67"
prd: "site/docs/design/h5-theme/PRD-H5工作台主题切换-v1.md"
prd_sha256: "26a383a38f52b6638378f0126cab4ed5897c26ac51fc0077090d75b06bea2e48"
created: "2026-09-19"
note: "第一轮 review-repair。草稿未覆盖。只修现有来源能唯一确定的项。"
---

# H5 工作台主题切换 STEP 审查报告

**模式**：`standalone` / `review-repair`（第一轮）  
**原文**（未覆盖）：[`steps-draft.md`](steps-draft.md) SHA `32fa3078f2c790a7e142e147789bbe6b8c991647ad4e7e3b98ee1575cdb4e951`  
**验证版**：[`steps-verified.md`](steps-verified.md) SHA `a03ec15431637f6843436d6b85dfa5a3ba8ba45a9b3fc959ec694aef534b7f67`  
**对照 PRD**：[`PRD-H5工作台主题切换-v1.md`](PRD-H5工作台主题切换-v1.md) SHA `26a383a38f52b6638378f0126cab4ed5897c26ac51fc0077090d75b06bea2e48`

无 `RUNTIME`。本增量正式切换未实施。本轮只修现有来源能唯一确定的项，未替用户选择产品语义（未选定 `theme.js` 文件名，未选定 `<select>` class / 像素）。

---

## 1. 九维总览评分

| 维度 | 首次审查（草稿） | 完整复审（验证版） |
|---|---|---|
| 1 幻觉 | ❌ 1 | ✅ 0 |
| 2 遗漏 | ❌ 5 | ✅ 0 |
| 3 冲突 | ❌ 2 | ✅ 0 |
| 4 不清晰 | ⚠️ 2 | ✅ 0 |
| 5 依赖顺序 | ⚠️ 1 | ✅ 0 |
| 6 验收可测性 | ❌ 4 | ✅ 0 |
| 7 决策覆盖 | ❌ 3 | ✅ 0 |
| 8 技术债 | ✅ 0 | ✅ 0 |
| 9 代码事实 | ❌ 1 | ⚠️ 0（风险见 R1/R6） |

无问题章节：维度 8 技术债。PRD 无 `TD-*`，草稿未新造技术债编号。本次审查未发现问题。

---

## 2. 逐 STEP 问题（首次审查）

| STEP | 类型 | 严重度 | 问题 | 证据 | 本轮处置 |
|---|---|---|---|---|---|
| 002 | `[幻觉]` `[代码事实错误]` | error | 开发任务写「不修改力导向/相机/边数据」。现网 `applyLayout` 只调用 `layoutAdmin`/`layoutClient` 静态列坐标，**没有**力导向 | SRC-APP L107–137 | 改为禁止改 `applyLayout`/`layoutAdmin`/`layoutClient` |
| 002 | `[遗漏]` | error | PRD §5.5 必须变色含「图谱节点域色**与连线**」；草稿输出只写筛选点/圆点/图例 | PRD §5.5；SRC-CSS `.edge`；SRC-APPLY `.edge { stroke: var(--edge) }`；SRC-APP marker 写死 `#4a5160`/`#6ea8fe` | 补 `EDGE_STROKE` / `EDGE_MARKERS` |
| 003 | `[遗漏]` | warn | §5.5「Tab 选中态」无比较方法。现网 `.tab.active { background: var(--accent-soft) }` | PRD §5.5；SRC-CSS L81–84 | 补 `TAB_ACTIVE` |
| 003/005 | `[遗漏]` `[验收不可测]` | error | AC10 规则含「当前打开文档仍在」；草稿只测问答会话，且 003 把文档划给 005 却未映射 | PRD AC10 规则列 | AC10 文档子条款 → 005，比较 `DOC_OPEN_ID` |
| 001 | `[遗漏]` | warn | CSTR-008：非法 `?theme=` 未测；`?theme=default` 未测 | PRD §5.3、§5.4 | 001 补两行 |
| 004 | `[遗漏]` | warn | §6.C.1「链接改为打开工作台」未验收。现网对照页已链到工作台 | PRD §6.C.1；SRC-GALLERY | 补 `GALLERY_HREFS`，不要求改「A ·」标题 |
| 全表 | `[冲突]` | error | `MAIN_TABS` 写成文案**多重集**；PRD AC20 要求顺序；契约是 `labels ==` 有序相等 | PRD AC20；SRC-CONTRACT L14 | 改为 `MAIN_TABS_SEQ` |
| 003 | `[冲突]` | warn | 测试行把契约测试标成「AC20 的前置」，但 003 来源映射不含 AC20，易把 AC20 做成 003 | 草稿 003 测试表 | 改为 CSTR-002 保护；AC20 完成只在 005 |
| 001～005 | `[验收不可测]` | error | 完成标志只有「验收断言全部通过」，无比较键 | skill 维度 6 | 验证版验收映射写明对象比较方法 |
| 005 | `[不清晰]` | warn | AC15「弹层跟黄主色体系」无投影 | PRD AC15；SRC-QA-CSS `.qa-overlay-card` | `OVERLAY_CARD` = 卡片背景 vs `--bg-elevated` |
| 005 | `[依赖问题]` | warn | AC21 观感「与加下拉框之前一致」不含预览条，但 005 只前置 003 | PRD AC21、AC22 | 005 前置改为 003+004 |
| 映射 | `[遗漏]` `[决策覆盖]` | error | 需求映射只有 G1–G4；CSTR-001～012、OUT-1～9 无落点表 | skill 维度 7 | 补约束映射、排除映射 |
| 映射 | `[决策覆盖]` | warn | G4「关系图行为」只映射 005，而 005 明确不改 `app.js`；点选/拖拽实际在 002 | PRD G4；草稿 005 不在范围 | G4 图谱行为 → 002 |

未发现：无来源 `TD-*`；无主题 id/显示名/存储键被改写；无 `RUNTIME` 伪称。

---

## 3. 需求 / 决策覆盖（复审）

G1–G4、AC1–AC23、CSTR-001～012、OUT-1～OUT-9 均有落点。未新造 `RQ-*` / `TD-*`。

| ID | 验证版落点 |
|---|---|
| G1 | 003（下拉与 Tab/发送/会话色）；002（图谱表面） |
| G2 | 001 |
| G3 | 001（默认蓝灰）；004（无预览条） |
| G4 | 002（图谱点选/拖拽/筛选）；005（问答/文档/弹层/Tab） |
| CSTR-001～012 | 见验证版约束映射 |
| OUT-1～OUT-9 | 全部 STEP 不在范围内 |
| §8 回滚 | 不是开发 STEP；按 PRD §8 执行 |

USER_DECISION「2」= 原生 `<select>` → CSTR-003 / STEP-003。

---

## 4. 验收覆盖（复审）

| AC | 比较键 | 复审 |
|---|---|---|
| AC1 | 四个 `data-view` 下 `SELECT_EL` 可见 | 通过 |
| AC2 | `(value,text)` 有序 = `THEME_OPTIONS` | 通过 |
| AC3 | tagName=`SELECT` | 通过 |
| AC4 | `QA_SEND_BG(a-gits)`；`CONV_ACTIVE` | 通过 |
| AC5 | `QA_SEND_BG(b-2049)` + 该皮肤 `--bg` | 通过 |
| AC6 | `QA_SEND_BG(c-nightcity)` | 通过 |
| AC7 | `QA_SEND_BG` + `CONV_ACTIVE`（粉） | 通过 |
| AC8 | 003：`QA_SEND_BG(c-prime)`；002：`REACH_NODES`/`REACH_FILTER` 比 `#c77dff` 且非品红，键为节点 `data-id` | 通过 |
| AC9 | `QA_SEND_BG(default)`；`THEME_SHEETS(default)` | 通过 |
| AC10 | 003：Tab `data-view` + 会话身份；005：`DOC_OPEN_ID` 同一篇 | 通过 |
| AC11 | `REACH_NODES(d-edgerunners)`；选中 `data-id`；拖拽不改其他 id 集合 | 通过 |
| AC12 | 筛选前后可见节点 `data-id` **集合** | 通过 |
| AC13 | `DOC_OPEN_ID`；`KB_LINK_COLOR` | 通过 |
| AC14 | 提问或出处/赞踩刷新仍可点（不改 `qa.js`） | 通过 |
| AC15 | `TOP_ACTIONS` 四键；四次 `OVERLAY_CARD(c-nightcity)` | 通过 |
| AC16 | 刷新后 `STORAGE_VAL` 与 `ROOT_ACCENT` 同一 id | 通过 |
| AC17 | 再开后同上 | 通过 |
| AC18 | 001：`THEME_SHEETS(default)`；004：`PREVIEW_BAR_ABSENT` | 通过 |
| AC19 | 本次与去掉 query 再刷新均为 `c-nightcity` | 通过 |
| AC20 | `.tab` 文案有序 = `MAIN_TABS_SEQ` | 通过 |
| AC21 | 无痕无 query：`QA_SEND_BG(default)` + `PREVIEW_BAR_ABSENT` + `SELECT_EL` | 通过 |
| AC22 | 任意主题与 `?theme=` 均 `PREVIEW_BAR_ABSENT` | 通过 |
| AC23 | 视口 &lt; 980px：`SELECT_EL` 与输入/发送布局盒不相交 | 通过 |

---

## 5. 技术债与排除项

无 PRD 明示 `TD-*`。未新增技术债编号。OUT-1～OUT-9 全部落入各 STEP「不在范围内」。

---

## 6. 依赖与代码事实核查

```text
001 无前置
002 ← 001
003 ← 001
004 ← 001
005 ← 003 + 004
```

002 / 003 / 004 可并行。无环。002 不依赖 003（可用 `applyTheme` 验图谱）。

本轮已读：PRD、草稿、INDEX、`index.html`、`theme-preview.js`、`app.js`（含 `domainColor`/`applyLayout`/`renderGraph`/`GraphApp`）、`style.css`、`qa.css`、`qa.js`/`kb.js`（只读确认）、`themes/*.css`、`_apply.css`、对照页、`test_site_contract.py`、`docker-compose.yml` 文件头。hashes 与草稿来源表一致（INDEX 在审查后改入口，验证版已记新 SHA）。无 `RUNTIME`。

现网事实补正（草稿未写错路径，但写错布局类型）：

- `applyLayout` = 静态左右列 / 按域分列，不是力导向
- SVG marker fill 在 `renderGraph` 写死现网色，换肤必须随重绘更新，否则 §5.5 连线不完整
- `:root` 无 `--edge`；default 连线为 `#4a5160`

---

## 7. 首次审查结论

对草稿：`FAILED_VALIDATION`。

原因：存在由现有来源唯一确定的结构/映射/验收问题（对象比较方法缺失、`MAIN_TABS` 顺序、§5.5 连线、AC10 文档子条款、CSTR/OUT 覆盖表、力导向幻觉）。`review-only` 不得宣称草稿已通过。本轮已按 `review-repair` 修正。

---

## 8. 修正 Diff（草稿 → 验证版）

原文：`steps-draft.md`（保留）。修正写入 `steps-verified.md`。

| 项 | 原内容 | 修正内容 | 来源 | 影响映射 |
|---|---|---|---|---|
| 布局算法 | 「不修改力导向」 | 不改 `applyLayout`/`layoutAdmin`/`layoutClient` | SRC-APP L107–137 | 002 |
| 连线 | 未验收 | `EDGE_STROKE` / `EDGE_MARKERS` | PRD §5.5；SRC-CSS；SRC-APP L155–161 | 002 |
| Tab 选中 | 未测 | `TAB_ACTIVE` | PRD §5.5；SRC-CSS | 003 |
| AC10 文档 | 未映射 | 005 比较 `DOC_OPEN_ID` | PRD AC10 | 005 |
| MAIN_TABS | 文案多重集 | `MAIN_TABS_SEQ` 有序元组 | AC20；SRC-CONTRACT `labels ==` | 003 保护、005 完成 |
| 完成标志 | 「断言全部通过」 | 验收表写比较键 | skill 维度 6 | 全 STEP |
| CSTR/OUT | 只有清单 | 约束映射 + 排除映射 | skill 维度 7 | 全表 |
| G4 图谱 | 只在 005 | 002 承担点选/拖拽/筛选 | PRD G4 | 002 |
| 005 前置 | 仅 003 | 003+004 | AC21 观感不含预览条 | 005 |
| 非法 query | 未测 | `?theme=not-a-theme` / `?theme=default` | §5.3、§5.4 | 001 |
| 对照页链接 | 未验 | `GALLERY_HREFS`（现网已满足） | §6.C.1 | 004 |
| 003 与 AC20 | 「AC20 的前置」 | 不宣称完成 AC20 | 映射一致性 | 003 |
| 对象表 | 无 accent/reach/edge 投影 | `THEME_OPTIONS`/`THEME_ACCENT`/`THEME_REACH`/`COLOR_EQ` 等 | 各 CSS；PRD §5.1 | 全 AC |
| INDEX | 只挂草稿 | 验证后入口改挂 verified（草稿保留） | 专题夹惯例 | SRC-INDEX |

未改 PRD 正文，未改业务代码。未覆盖草稿。未选定运行时文件名、未选定 select 的 class/像素。

---

## 9. 完整复审结论

从 PRD v1、本轮已读代码与验证版重新走九维：首次 `error` 已收敛；无产品语义未决。

**阶段结果：`PASS_WITH_RISKS`**

可使用 [`steps-verified.md`](steps-verified.md)。不得自动开始写业务代码。standalone 在此停止。

### 残留风险

| ID | 风险 | 为何不阻断 |
|---|---|---|
| R1 | `GraphApp` 换肤包装函数名 `PLANNED` | PRD 允许调用现有 `render*` |
| R2 | 动态 `<link>` 仍可能 FOUC | PRD 只要求「尽量」 |
| R3 | 对照页「A ·」标题 ≠ 下拉文案 | PRD 未要求改对照页标题 |
| R4 | 980px 媒体查询不覆盖顶栏 | AC23 已改为布局盒不相交，实施时实测 |
| R5 | 契约测试只锁 `.tab` 有序文案 | 加 `<select>` 不改 `.tab` 即可 |
| R6 | default 无 `--edge` 变量 | 已用 `DEFAULT_EDGE` 写死比较值 |

### 阻断项

无。

### 本阶段停止

不进入里程碑编排，不开始开发。下一步若要按阶段实施，需用户显式调用里程碑 / 开工指令。

---

## 10. 修订附录（2026-09-19 USER_DECISION「按建议」）

不是第二轮九维复审。用户确认三项建议后，只改 PRD 与 `steps-verified.md` 中被覆盖的条款；草稿仍保留。未改业务代码。

| 确认点 | 落入条款 |
|---|---|
| 空存储默认边缘行者粉；已存 `default` 不迁移 | G3、§5.1、§5.3、AC18、AC21、CSTR-004、STEP-001 |
| `:root` 写成粉；蓝灰抽 `themes/default.css` | §6.A.4、CSTR-005、OUT-8 例外、R2/R6 |
| risk 不另开优化轮 | 验证版风险表注明随 STEP 做 / 不改对照页 |

PRD 新 SHA：`7a894778b4199c3c68b7c5e955b32033d9cc8ad6a839e732e884c95b416997e6`。

