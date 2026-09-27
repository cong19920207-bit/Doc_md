---
title: "知识问答 · 反馈与对话样式 STEP 审查报告"
mode: "standalone / review-repair"
round: 1
input_step: "site/docs/design/kb-qa-feedback/steps-draft.md"
input_step_sha256: "6d034a290a0d1c055a2a1d2dfb0b52f2a228d29e6240b76f72d81d44d1e8c947"
verified: "site/docs/design/kb-qa-feedback/steps-verified.md"
verified_sha256: "3b650445d4c2304524f3a3b89e0999c82574f8de903be2e4bb9d38d37a0feb99"
prd: "site/docs/design/kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md"
prd_sha256: "1923bb41a8520401cd34eab9fc36f4050a194a7185d91d157b360eaae4c4fc59"
created: "2026-09-17"
note: "第一轮 review-repair。草稿未覆盖。用户指示：无需确认的确定性项直接修。"
---

# 知识问答 · 反馈与对话样式 STEP 审查报告

**模式**：`standalone` / `review-repair`（第一轮）  
**原文**（未覆盖）：[`steps-draft.md`](steps-draft.md) SHA `6d034a290a0d1c055a2a1d2dfb0b52f2a228d29e6240b76f72d81d44d1e8c947`  
**验证版**：[`steps-verified.md`](steps-verified.md) SHA `3b650445d4c2304524f3a3b89e0999c82574f8de903be2e4bb9d38d37a0feb99`  
**对照 PRD**：[`PRD-知识问答-反馈与对话样式-v2.md`](PRD-知识问答-反馈与对话样式-v2.md) SHA `1923bb41a8520401cd34eab9fc36f4050a194a7185d91d157b360eaae4c4fc59`  
**v1**：不作依据。

无 `RUNTIME`。本增量业务代码未实施。本轮只修现有来源能唯一确定的项，未替用户选择产品语义。

用户指示：「没有我确认的就直接修复」。无 `BLOCKED` 级待确认项。

---

## 1. 九维总览评分

| 维度 | 首次审查（草稿） | 完整复审（验证版） |
|---|---|---|
| 1 幻觉 | 通过（有风险） | 通过（有风险） |
| 2 遗漏 | 失败 | 通过 |
| 3 冲突 | 失败 | 通过 |
| 4 不清晰 | 失败 | 通过（有风险） |
| 5 依赖顺序 | 失败 | 通过 |
| 6 验收可测性 | 失败 | 通过 |
| 7 决策覆盖 | 失败 | 通过 |
| 8 技术债 | 通过 | 通过 |
| 9 代码事实 | 通过（有风险） | 通过（有风险） |

## 2. 逐 STEP 问题（首次审查摘要 → 本轮处置）

| STEP | 问题 | 首次 | 本轮处置 |
|---|---|---|---|
| 001 | 完成标志无字段集合比较 | `warn` | 改为 `BIND_FIELDS` |
| 002 | AC1 无按钮身份集；占位与完成混淆；AC4 用个数 | `warn` | `ACTION_KEYS` 多重集；完成只验键与复制 |
| 002 | CSTR-013 复制未测 | `warn` | 002 补 busy 时复制 |
| 003 | 完成标志笼统；路径「核实后再落」 | `warn` | 按 round GET 回读；路径固定为 PRD T3 拟议值 `PLANNED` |
| 004 | AC7「文案族」 | `error` | `UNWRITTEN_HINTS` = PRD 已写三句 |
| 005 | AC6「该行」无 `round_id` | `error` | 详情/列表均按同一 `round_id` |
| 006 | AC3 条数/+1；刷新后未换消息 `round_id`；AC12 无 fid 快照 | `error` | 用户 `id` 多重集；`round_id` 集合等式；消息换新 id、快照不变；`count_after=count_before+1` |
| 007 | 「或保持不拉满」vs C17 | `error` | 只保留「放入新内容柱」 |
| 007/008 | AC9 无宽度相等 | `warn` | `COL_PAIR` |
| 009 | AC11 不前置 002 | `error` | 前置 002+007 |
| 010 | 热度只比个数；常驻只测 1 句；F5 未映射 | `error` | `CHIP_HEAT`；`CHIP_FIXED` 四对；F5→010 |
| 011 | Tab 比「4」；前置缺 002 | `error` | `MAIN_TAB_NODES` 文案多重集；前置含 002 |
| 映射 | C11 总表漏 008；RQ 未占行；T6 未写禁止编造 | `warn` | 已补 |

## 3. 需求 / 决策覆盖（复审）

F1–F9、C1–C23、RQ-01～RQ-04（并入 C18/C20/C23/C22）、G1–G4、E1–E8、A7、CSTR-001～020、OUT-1～13、T7 四条均有落点。

| ID | 验证版落点 |
|---|---|
| F1 | 002 |
| F2 | 001、003、004、006 |
| F3 | 001、006 |
| F4 | 003、005 |
| F5 | 007、008、010 |
| F6 | 008 |
| F7 | 009 |
| F8 | 010 |
| F9 | 002、006 |
| C17 | 007（阶段文案入柱）、009（出处折叠） |
| C11 | 008、010 |
| E1 | 004 / AC7（PRD 表内写成 AC6 的笔误不改 PRD） |

未新造 `TD-*` / `RQ-*`。

## 4. 验收覆盖（复审）

| AC | 比较键 | 复审 |
|---|---|---|
| AC1 | 剪贴板=`m.text`；`ACTION_KEYS`=`{复制,赞,踩,刷新}` | 通过 |
| AC2 | 同一消息 id 上 `FEEDBACK_UI` 序列 | 通过 |
| AC3 | 用户消息 id 多重集不变；客户端 id 不变；`round_id` 集合=旧∪{新}；新行 `original_query`=首次 query | 通过 |
| AC4 | `ACTION_KEYS`=`{刷新}` | 通过 |
| AC5 | toast=「生成中…」；in-flight ask=1；发送 busy 不新增用户 id | 通过 |
| AC6 | 同一 `round_id` 的详情与列表行反馈=赞 | 通过 |
| AC7 | `FEEDBACK_UI`=赞；明细集合不含该 `round_id`；提示∈`UNWRITTEN_HINTS` | 通过 |
| AC8 | `CHIP_FIXED` 四对；`CHIP_HEAT`；欢迎沿用 `emptyHtml` | 通过 |
| AC9 | `COL_PAIR` | 通过（约 768px 不设硬门） |
| AC10 | 柱宽 < `.qa-main`；不贴死 | 通过（约 24px 不设硬门） |
| AC11 | 右圆角块；相对现网 1px 边框去掉；出处与 `ACTION_KEYS` 在下 | 通过 |
| AC12 | 指定 `feature_id` 的 count 快照 +1 或从无到 1 | 通过 |
| AC13 | `MAIN_TAB_NODES` 文案=`MAIN_TABS`；左栏 CRUD；`TOP_ACTIONS` | 通过 |
| C23 | 追问 `last_chunks` 身份 | 通过 |
| C20 抽样 | `vip`→用户VIP；`yallapay`→链接支付（`load_aliases` 复核） | 通过 |

## 5. 技术债与排除项（复审）

T7 四条处置不变。OUT-13 / CSTR-020：不编造日志保留天数。无新增无来源 `TD-*`。

## 6. 依赖与代码事实（复审）

```text
001、002、003、007 无前置
004 ← 001+002+003
005 ← 003+004
006 ← 001+002
008 ← 007
009 ← 002+007
010 ← 007+008
011 ← 002+007+008+009+010
```

无环。006 刷新成功后消息 `round_id` 换新、快照不变，供后续 004 打新轮。

本轮未改仓库业务代码。locator / SHA 与草稿来源表一致（PRD `1923bb41…`，qa.js `44019a56…` 等）。无 `RUNTIME`。

## 7. 首次审查结论

对草稿：`FAILED_VALIDATION`（见上一轮 `review-only` 报告；本文 §2 保留问题表）。

## 8. 修正 Diff（草稿 → 验证版）

原文：`steps-draft.md`（保留）。修正写入 `steps-verified.md`。

| 项 | 原内容 | 修正内容 | 来源 | 影响映射 |
|---|---|---|---|---|
| 对象约定 | Tab 比大小；热度比条数；无提示允许集 | `MAIN_TAB_NODES`/`ACTION_KEYS`/`BIND_FIELDS`/`CHIP_HEAT`/`COL_PAIR`/`UNWRITTEN_HINTS`/`TOP_ACTIONS` | PRD AC/C；REPO | 全 AC |
| AC3 | 气泡条数、行数 +1 | id 多重集与 `round_id` 集合 | AC3 | 006 |
| AC6 | 「该行」 | 同一 `round_id` | AC6 | 005 |
| AC7 | 文案族 | `UNWRITTEN_HINTS` 三句 | §6.2；E1；E2 | 004 |
| AC8 | 只测一句；热度个数 | 四对 `CHIP_FIXED`；`CHIP_HEAT` | A7；§6.2 | 010 |
| AC12 | 「可再 +1」 | 指定 fid 的 count 快照 | AC12；`heatmap()` | 006 |
| AC13 | 「仍为 4」 | 文案多重集；`TOP_ACTIONS` | AC13；C7 | 011 |
| 006 | 未换消息 `round_id` | 新 id + 快照不变 | F2；C2；C3 | F2→006 |
| 007 | 入柱或保持不拉满 | 只入柱 | C17 | 007 |
| 009 前置 | 仅 007 | 002+007 | AC11 | 009 |
| 011 前置 | 007–010 | +002 | AC13 完成本期 UI | 011 |
| F5 | 仅 007 | 007+008+010 | F5 | 映射 |
| C11 总表 | 010/011 | 008+010 | C11 | 映射 |
| RQ-01～04 | 未占行 | 并入对应 C | PRD §5 | 覆盖表 |
| 反馈路径 | 核实后再落 | T3 拟议路径 `PLANNED` | PRD T3 | 003 |
| T6 | 无 | CSTR-020 / OUT-13 | T6 | 003 不做 |
| CSTR-013 复制 | 未测 | 002 busy 复制 | C18 | 002 |

未改 PRD 正文，未改业务代码。未覆盖草稿。未替「约 768px」选定硬像素。

## 9. 完整复审结论

从 PRD v2、本轮已读代码与验证版重新走九维：首次 `error` 已收敛；无产品语义未决。

**阶段结果：`PASS_WITH_RISKS`**

可使用 [`steps-verified.md`](steps-verified.md)。不得自动开始写业务代码。standalone 在此停止。

### 非阻断风险

1. 已有 MySQL 卷需启动补列或手工 ALTER。  
2. 反馈写入路由现网不存在；采用 PRD T3 拟议路径，`PLANNED`。  
3. C20 接到 `qa.js` 的调用点现网无唯一接口。  
4. 现网 `refuse` 为 `role: "system"`；出现规则以 C5 为准。  
5. C22：改现网测试、不改 v3 正文。  
6. 「约 768px / 约 24px」不设硬像素门。  
7. 无 `RUNTIME`。  
8. PRD E1 验收编号写成 AC6，覆盖以正文为准。  
9. pytest 解释器 / `.venv` 本轮未核实。  
10. 刷新 toast 必须是「生成中…」，不得套用 `lockGuard` 旧句。

---

## 自检

- [x] 九维首次审查完整（保留）
- [x] 每个问题都有来源和严重度
- [x] 只修了唯一可证实的问题
- [x] 原文、首次审查和 Diff 均保留
- [x] 修正后从完整来源重新复审
- [x] 修正一轮，未超过两轮
- [x] 业务歧义没有被「最佳判断」代替
- [x] 完整通过（含风险）才生成 `steps-verified.md`
- [x] 已返回五种结果之一并在本阶段停止
