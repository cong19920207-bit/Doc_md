---
title: "Hayyo 知识问答 STEP 审查报告"
mode: "standalone / review-repair"
round: 2
input_step: "site/docs/design/kb-qa/history/Hayyo-知识问答-STEP-验证版-r1.md"
input_step_sha256: "8924616f9eef59aeebe40b2b3b327b3123eb763fb8d0dd03e94ce6b4050adf88"
source_draft: "site/docs/design/kb-qa/history/Hayyo-知识问答-STEP-草稿.md"
source_draft_sha256: "ca87fefb34b8f87603a069637247ee887c210f23d250c6c6a8c1eb9c35f30711"
verified: "site/docs/design/kb-qa/Hayyo-知识问答-STEP-验证版.md"
verified_sha256: "89c8ba8dc0d3a1c5494ebca9c79293315bdf696444e9faea8b4179e2e8b7ca86"
prd: "site/docs/design/kb-qa/PRD-知识问答-v3.md"
prd_sha256: "52e7b5b6f0876cf28defcbeeaf3bdc46c71d90de028c29bebf92e1b725e28965"
v2_status: "expired"
created: "2026-09-17"
note: "第二轮 review-repair。草稿与 r1 快照未覆盖。权威仅 v3。业务代码 NOT_STARTED。"
---

# Hayyo 知识问答 STEP 审查报告

> 本文已迁入 `history/`，**不默认读**。实施只读 [`../Hayyo-知识问答-STEP-验证版.md`](../Hayyo-知识问答-STEP-验证版.md)；过程稿目录见 [`INDEX.md`](INDEX.md)。

**模式**：`standalone` / `review-repair`（第二轮）  
**本轮原文**（未覆盖）：[`Hayyo-知识问答-STEP-验证版-r1.md`](Hayyo-知识问答-STEP-验证版-r1.md) SHA `8924616f…`  
**草稿**（仍未覆盖）：[`Hayyo-知识问答-STEP-草稿.md`](Hayyo-知识问答-STEP-草稿.md)  
**现行验证版**：[`../Hayyo-知识问答-STEP-验证版.md`](../Hayyo-知识问答-STEP-验证版.md) SHA `89c8ba8d…`  
**对照 PRD**：[`../PRD-知识问答-v3.md`](../PRD-知识问答-v3.md)（**唯一现行权威**）  
**v2**：[`PRD-知识问答-v2.md`](PRD-知识问答-v2.md) **已过期**，不是实施依据（`USER_DECISION`）

无 `RUNTIME` 证据。业务代码 `NOT_STARTED`。

第二轮 `review-only` 对 r1 结论为 `FAILED_VALIDATION`（AC1/AC22 `role=tab`；v2 仍当现行来源）。本轮只修证据唯一确定的项，然后完整复审。

---

## 用户决定（本轮）

| 项 | 结论 | 标签 |
|---|---|---|
| 现行权威 | 只认 PRD v3 | `USER_DECISION` |
| v2 | 已过期，不作为实施依据 | `USER_DECISION` |
| 沿用条款 | v3 写「沿用 / 同 v2」的视为 v3 并入，不打开 v2 当现行合同 | `PRD` + `USER_DECISION` |

---

## 1. 九维总览评分

| 维度 | r1 再审（修正前） | 第二轮完整复审 |
|---|---|---|
| 1 幻觉 | ⚠️ | ✅（残留风险见 §9） |
| 2 遗漏 | ⚠️ | ✅ |
| 3 冲突 | ⚠️ | ✅ |
| 4 不清晰 | ✅ | ✅ |
| 5 依赖顺序 | ✅ | ✅ |
| 6 验收可测性 | ❌ | ✅ |
| 7 决策覆盖 | ⚠️ | ✅ |
| 8 技术债 | ✅ | ✅ |
| 9 代码事实 | ⚠️ | ✅ |

维度 4、5、8 本轮修正前后均未发现新问题。

## 2. 逐 STEP 问题（第二轮）

| STEP | 问题 | 严重度 | 本轮处置 |
|---|---|---|---|
| 文首 / 来源表 / 002 | 把过期 v2 当现行 locator | warn | SRC-PRD-V2 标 `expired`；Key 名改引 v3 R6 并入 |
| 003 / 018 / 019 | AC1、AC22 用 `role=tab`，现网按钮无该属性 | error | 改为 `MAIN_TAB_NODES` = `header .tabs .tab`（与 `els.tabs` 一致） |
| 002 / 008 | CSTR-037「配置是否就绪」无比较键 | warn | 002 健康检查补该字段；008 仍只测块数 |
| 010 / 012 / 013 | AC8 的 E3 未直接挂提问路径 | warn | AC8 拆到 010 检索 5xx、012 重排 5xx、013 生成 5xx |
| CSTR-026 / OUT-22 | 出处只在过期 v2 | warn | 改引 v3 本期范围 + USER_DECISION |

其余 STEP 本次未发现新的确定性错误。

## 3. 需求 / 决策覆盖（复审）

F1–F21、RQ-01～RQ-21（RQ-10=OUT/D1）、G1–G7、v3 有效 C（含替代后的 C6/C13、C18′、C30–C38）、R1–R12、E1–E12、CSTR-001～038、OUT-1～24、D1–D3、T7 均有落点。覆盖口径：**v3 正文 + v3 明示并入**，不再把 history/v2 当现行来源。

CSTR-037 四分量：002 负责 qdrant / 配置是否就绪 / Key；008 负责块数。AC8 的 E3/E4 分别由 010/012 与 013 直接验证。未新造 `TD-*` / `RQ-*`。

## 4. 验收覆盖（复审）

| AC | 比较键摘要 | 复审 |
|---|---|---|
| AC1 | `MAIN_TAB_NODES` 文本序列+相邻；工作区 `id≠kbWorkspace` | 通过 |
| AC2 | 召回/`C_gen`/出处三重集，path 含 `VIP_BRIEF` | 通过 |
| AC3 | `same_topic=true`；`C_gen.path` 含 `VIP_BRIEF` | 通过 |
| AC4 | 回答数字 ⊆ `C_gen` 正文数字 | 通过 |
| AC5 | 条件：互斥块身份均被引用 | 通过 |
| AC6 | `getCurrentPath()`=出处 path；`conv_id` 不变 | 通过 |
| AC7 | 002 失败类型；020 `getCurrentPath()=P` | 通过 |
| AC8 | 010 检索 5xx；012 重排 5xx；013 生成 5xx + 出处=`C_gen` | 通过 |
| AC9 | 清单 `(path, chunk_id, action)`；再问联测 | 通过 |
| AC10 | path 前缀 `ADMIN_BRIEF_PREFIX`，仅 010 | 通过 |
| AC11 | `data-view=admin` active；无 `kb-active` | 通过 |
| AC12 | ≤20 条；请求不含 kb-api；非 chunk_id | 通过 |
| AC13 | 只读/可改字段集合相等；Key 无明文 | 通过 |
| AC14 | 出处空、气泡空、上轮 messages 多重集不变 | 通过 |
| AC15 | `truncate18`、messages 不相交、刷新 conv 集合 | 通过 |
| AC16 | conv_id 删除；`round_id` 明细仍在 | 通过 |
| AC17 | `filter.feature_id` ⊇ 三 ID；保底 ∈ `C_gen` | 通过 |
| AC18 | `status=interrupted`；无半段成功气泡 | 通过 |
| AC19 | 详情投影 = 写入快照 | 通过 |
| AC20 | `(feature_id,count)` 多重集 = C34 聚合 | 通过 |
| AC21 | chip=0；过程栏=0；`MAIN_TABS` 大小 4 | 通过 |
| AC22 | `MAIN_TAB_NODES` 多重集仍 = `MAIN_TABS`；conv_id 往返不变 | 通过 |
| AC23 | disabled；conv_id 不变；可切 kb | 通过 |
| AC24 | 提示未写入；round_id 集合不含本轮 | 通过 |

## 5. 技术债与排除项（复审）

无 `TD-*`。T7 仍为接受项。OUT-22 改为「不在 v3 本期范围」，不再引用过期 v2 排除表。OUT-24 仍追溯 v3 §11。

## 6. 依赖与代码事实（复审）

依赖图与 r1 相同，无环。本轮已再核：`.tab` 无 `role="tab"`、`els.tabs = document.querySelectorAll(".tab")`、`openDocument`/`headingText`、compose 仅 nginx、PRD v3 SHA `52e7b5b6…`、r1 SHA `8924616f…`。无 `RUNTIME`。无 `contract.md`。

## 7. 本轮首次审查结论（修正前）

对 r1 验证版：`FAILED_VALIDATION`。原因：AC1/AC22 比较键与现网 DOM 唯一矛盾；v2 仍被列为现行来源。对话中的 review-only 未改文件。

## 8. 修正 Diff（r1 → 现行验证版）

原文：`Hayyo-知识问答-STEP-验证版-r1.md`（保留）。修正写入 `Hayyo-知识问答-STEP-验证版.md`。草稿仍未覆盖。

| 项 | r1 内容 | 修正内容 | 来源 | 影响 |
|---|---|---|---|---|
| 权威声明 | v2 只用于沿用条款定位 | v3 唯一现行；v2 `expired` | `USER_DECISION`；v3 文首 | 文首、来源表 |
| SRC-PRD-V2 | `existing`，作 F/AC/C locator | `expired`，本轮不作 locator | 同上 | 来源表、002 |
| Key 名 | `SRC-PRD-V2 / R6` | `SRC-PRD-V3 / R6`（两 Key 并入） | v3 R6 | 002 |
| AC1 / AC22 | `role=tab` | `MAIN_TAB_NODES` = `.tabs .tab` | `REPO_BASELINE`；v3 AC1/AC22/C36 | 003、018、019、对象约定 |
| CSTR-037 | 002 无「配置是否就绪」 | 002 健康检查含该字段 | v3 A5 | 002、008 范围 |
| AC8 | 仅 013 | 010 检索 5xx、012 重排 5xx、013 生成 5xx | 沿用 AC8 + E3/E4 | 010、012、013 |
| CSTR-026 / OUT-22 | 出处 v2 §4.2 | v3 本期范围 + USER_DECISION | v3 文首 | 输入清单 |
| CSTR-038 / payload | 混写 v2 §4.1 / T2 | v3 G5/C13/F14；§6.2 索引 | v3 | 007 |

未改 PRD 正文，未改业务代码。未填端口/语言/路径前缀。未覆盖草稿与 r1。

## 9. 完整复审结论

从 PRD v3、`USER_DECISION`（v2 过期）、本轮已读代码与现行验证版重新走九维：r1 的 `error` 已收敛；无产品语义未决。

**阶段结果：`PASS_WITH_RISKS`**

可使用 [`../Hayyo-知识问答-STEP-验证版.md`](../Hayyo-知识问答-STEP-验证版.md)。不得自动开始写业务代码。

### 非阻断风险

1. kb-api 语言、HTTP 前缀、MySQL 端口、别名表路径、服务镜像名：`PLANNED`。
2. 无 `RUNTIME`；无自动化测试命令。
3. 默认 64/8/5/对话上限 40 不是硬验收。
4. 日志保留天数未定。
5. 配置抽屉 vs overlay 未指定（CSTR-025）。
6. 改写漏点名无专路：PRD 已接受。
7. AC4/AC5 为条件比较（无互斥块/无数字时不编造）。
8. AC3「退款相关」用 `same_topic` + `VIP_BRIEF`，不编造 chunk_id。
9. `truncate18` 按「约 18 字」取前 18 字；原型省略号不写入硬验收。
10. 001 服务名未定，比较「三依赖可列」而非镜像字符串。
11. v3 未抄录沿用 AC/C/E 全文（并入指针在 v3）；不打开过期 v2 当合同。
12. Key 环境变量名经 v3 R6 并入；v3 正文只写「两 Key」。

### 阻断项

无。

### 产物

| 角色 | 路径 |
|---|---|
| 草稿（未覆盖） | `site/docs/design/kb-qa/history/Hayyo-知识问答-STEP-草稿.md` |
| r1 验证版（未覆盖） | `site/docs/design/kb-qa/history/Hayyo-知识问答-STEP-验证版-r1.md` |
| 现行验证版 | `site/docs/design/kb-qa/Hayyo-知识问答-STEP-验证版.md` |
| 本报告 | `site/docs/design/kb-qa/history/Hayyo-知识问答-STEP-审查.md` |

业务代码尚未实施（`NOT_STARTED`）。本阶段停止。

---

## 附录 A：第一轮 review-repair（r1，保留）

以下为对草稿的第一轮审查与 r1 验证版结论，当时验证版 SHA `8924616f…`。第二轮已在上文覆盖其 `PASS_WITH_RISKS` 主张中关于 `role=tab` 与 v2 现行来源的部分。

## 1. 九维总览评分（第一轮）

| 维度 | 首次审查（草稿） | 完整复审（验证版） |
|---|---|---|
| 1 幻觉 | ⚠️ | ✅（残留风险见 §9） |
| 2 遗漏 | ❌ | ✅ |
| 3 冲突 | ⚠️ | ✅ |
| 4 不清晰 | ❌ | ✅ |
| 5 依赖顺序 | ❌ | ✅ |
| 6 验收可测性 | ❌ | ✅ |
| 7 决策覆盖 | ⚠️ | ✅ |
| 8 技术债 | ✅ | ✅ |
| 9 代码事实 | ⚠️ | ✅ |

维度 8 两次均未发现问题。

## 2. 逐 STEP 问题（首次审查摘要）

首次 `review-only` 的 `error` 不删，处置见 §8；逐条原文见附录。

| STEP | 问题 | 严重度 | 本轮处置 |
|---|---|---|---|
| 001 | AC7 误挂 Compose | `error` | 001 只保留 G2 比较键 |
| 001 | compose 启动命令不清 | `warn` | 以 compose 文件头两条命令为准 |
| 005 | AC15 隐藏依赖 013（环） | `error` | AC15 只比较用户问句/标题/conv_id，不要求生成 |
| 005 | AC16 未挂 017/018 | `error` | 拆浏览器侧 / 日志侧 |
| 006 | AC23 未前置 013 | `error` | 前置 005+013 |
| 007 | payload 无预留账号字段 | `error` | CSTR-038；四字段本期空 |
| 007 | AC10 误挂切块 | `error` | AC10 仅 010 |
| 012 | 强制前置 011 | `error` | 仅 `named≥2` 时前置 011 |
| 004/013 | 阶段文案职责不清 | `warn` | 004 槽位；013 驱动 |
| 009/011/018/019/020 等 | 无比较键 | `error` | 验收映射表写稳定键 |
| 014 | 0 块拒答前置 013 | `warn` | 0 块只前置 012 |
| 017 | 发送无主路径；AC18 需生成中 | `warn` | F2 发送=005 触发；017 先 running；AC18 联测 013 |
| 接口 | 健康检查未入 STEP | `warn` | 002 Key/Qdrant；008 块数 |
| §11 | 工程 PRD 禁写入产品 PRD | `warn` | CSTR-036、OUT-24 |
| 来源 SHA | 三份 brief 无哈希 | `warn` | 已补 |
| 模板 | 多数 STEP 缺输入/输出块 | `error`（复审发现） | 各 STEP 已补；总表约定防漂移 |

## 3. 需求 / 决策覆盖（复审）

F1–F21、RQ-01～RQ-21（RQ-10=OUT）、G1–G7、C 沿用与 v3 有效项、R1–R12、E1–E12、CSTR-001～038、OUT-1～24、D1–D3、T7、v2 T3 健康检查均有落点。F2 发送主路径写在验证版功能清单。C30 映射 009+011。未新造 `TD-*` / `RQ-*`。

## 4. 验收覆盖（复审）

| AC | 比较键摘要 | 复审 |
|---|---|---|
| AC1 | tab 文本序列+相邻；工作区 `id≠kbWorkspace` | 通过 |
| AC2 | 召回/`C_gen`/出处三重集，path 含 `VIP_BRIEF` | 通过 |
| AC3 | `same_topic=true`；`C_gen.path` 含 `VIP_BRIEF` | 通过 |
| AC4 | 回答数字 ⊆ `C_gen` 正文数字 | 通过 |
| AC5 | 条件：互斥块身份均被引用 | 通过 |
| AC6 | `getCurrentPath()`=出处 path；`conv_id` 不变 | 通过 |
| AC7 | 002 失败类型；020 `getCurrentPath()=P` | 通过 |
| AC8 | 无成功气泡；出处多重集=`C_gen` | 通过 |
| AC9 | 清单 `(path, chunk_id, action)`；再问联测 | 通过 |
| AC10 | path 前缀 `ADMIN_BRIEF_PREFIX`，仅 010 | 通过 |
| AC11 | `data-view=admin` active；无 `kb-active` | 通过 |
| AC12 | ≤20 条；请求不含 kb-api；非 chunk_id | 通过 |
| AC13 | 只读/可改字段集合相等；Key 无明文 | 通过 |
| AC14 | 出处空、气泡空、上轮 messages 多重集不变 | 通过 |
| AC15 | `truncate18`、messages 不相交、刷新 conv 集合 | 通过 |
| AC16 | conv_id 删除；`round_id` 明细仍在 | 通过 |
| AC17 | `filter.feature_id` ⊇ 三 ID；保底 ∈ `C_gen` | 通过 |
| AC18 | `status=interrupted`；无半段成功气泡 | 通过 |
| AC19 | 详情投影 = 写入快照 | 通过 |
| AC20 | `(feature_id,count)` 多重集 = C34 聚合 | 通过 |
| AC21 | chip=0；过程栏=0；`MAIN_TABS` 大小 4 | 通过 |
| AC22 | tab 多重集不变；conv_id 往返不变 | 通过 |
| AC23 | disabled；conv_id 不变；可切 kb | 通过 |
| AC24 | 提示未写入；round_id 集合不含本轮 | 通过 |

## 5. 技术债与排除项（复审）

同首次：T7 六条有处置，无 `TD-*`。OUT-24 新增且可追溯到 v3 §11。

## 6. 依赖与代码事实（复审）

```text
001 → 002 → 009 → 010 → 011
001 → 007 → 008
              010 → 012 → 013 → 006
                    012 → 014
                    013 → 015 → 020
003 → 004 → 005 → 009
      004 → 008, 016, 018
017 ← 001, 009；（AC18 联测 013）
018 ← 017, 004
019 ← 017, 018
016 ← 002, 004
012 在 named<2 时不前置 011
014 在 0 块时不前置 013
```

无环。代码 locator 与首次审查一致（三 Tab、`setView`、`openDocument`/`headingText`、compose 仅 nginx、brief 抽样）。brief SHA 已补。无 `RUNTIME`。

## 7. 首次审查结论

对草稿：`FAILED_VALIDATION`（映射、依赖、验收比较键）。`review-only` 当时未修。全文见附录。

## 8. 修正 Diff

原文：`Hayyo-知识问答-STEP-草稿.md`（保留）。修正写入 `Hayyo-知识问答-STEP-验证版.md`。

| 项 | 原内容（草稿） | 修正内容 | 来源 | 影响 |
|---|---|---|---|---|
| AC7 映射 | 001+002+020 | 001 去掉 AC7，改 G2 比较键；002 失败类型；020 打开 path | v3 AC7、G2 | 001/002/020 |
| compose 命令 | 「按现有方式」 | 文件头：`-f site/docker-compose.yml` 或在 `site/` 执行 | SRC-COMPOSE | 001 |
| AC15 | 隐含要生成 | 只比较用户问句/标题/conv_id | v3 AC15；避免 005↔013 环 | 005 |
| AC16 | 只 005 | 005 删 conv；017/018 保留 round_id | v3 AC16 | 005/017/018 |
| AC23 前置 | 仅 005 | 005+013 | v3 AC23 | 006 |
| payload | 无账号预留 | 四字段本期空 | G5；v2 §4.1 | 007、CSTR-038 |
| AC10 | 007+010 | 仅 010 | v3 AC10 | 007/010 |
| 012 前置 | 010 且 011 | named≥2 才要 011 | v3 C30 | 012 |
| 014 前置 | 012 且 013 | 0 块只 012 | v3 C26 | 014 |
| 比较键 | 叙述句 | 验收映射表稳定 ID/多重集 | skill 维度 6 | AC1–AC24 |
| 发送主路径 | 未写清 | 005 触发；017 先 running；009 改写 | v3 §6.2 步骤 1 | F2 |
| AC18 | 017 未写联测 | 013 未完成不得 DONE | v3 C35 | 017 |
| 健康检查 | 无 | 002 Key/Qdrant；008 块数 | v2 T3；A5 | CSTR-037 |
| §11 | 无单独 OUT | CSTR-036、OUT-24 | v3 §11 | 文档禁写 |
| brief SHA | 「—」 | 三份 SHA 已填 | REPO_BASELINE | 来源摘要 |
| 阶段文案 | 004/013 混 | 004 槽位、013 驱动 | F17、AC21 | 004/013 |
| 模板字段 | 多数 STEP 无输入/输出 | 每 STEP 补输入/输出/业务定义；总表约定防漂移 | STEP 模板 | 002–020 |

未改 PRD 正文，未改业务代码。未填端口/语言/路径前缀。未覆盖草稿。

## 9. 完整复审结论

从 PRD v3、v2 沿用条款、本轮已读代码与验证版重新走九维：首次 `error` 已收敛；模板字段已补齐；无产品语义未决。

**阶段结果：`PASS_WITH_RISKS`**

可使用 [`../Hayyo-知识问答-STEP-验证版.md`](../Hayyo-知识问答-STEP-验证版.md)。不得自动开始写业务代码。

### 非阻断风险

1. kb-api 语言、HTTP 前缀、MySQL 端口、别名表路径、服务镜像名：`PLANNED`。
2. 无 `RUNTIME`；无自动化测试命令。
3. 默认 64/8/5/对话上限 40 不是硬验收。
4. 日志保留天数未定。
5. 配置抽屉 vs overlay 未指定（CSTR-025）。
6. 改写漏点名无专路：PRD 已接受。
7. AC4/AC5 为条件比较（无互斥块/无数字时不编造）。
8. AC3「退款相关」用 `same_topic` + `VIP_BRIEF`，不编造 chunk_id。
9. `truncate18` 按「约 18 字」取前 18 字；原型省略号不写入硬验收。
10. 001 服务名未定，比较「三依赖可列」而非镜像字符串。

### 阻断项

无。

### 产物

| 角色 | 路径 |
|---|---|
| 原文草稿 | `site/docs/design/kb-qa/history/Hayyo-知识问答-STEP-草稿.md` |
| 本报告 | `site/docs/design/kb-qa/history/Hayyo-知识问答-STEP-审查.md` |
| 验证版 | `site/docs/design/kb-qa/Hayyo-知识问答-STEP-验证版.md` |

业务代码尚未实施（`NOT_STARTED`）。本阶段停止。

---

## 附录：首次 review-only 全文（保留）

> 以下为 `review-only` 当时写入的报告原文。当时草稿 SHA `e507959b546074eb970c45d5ba089b0e3d5c5cddfeb06d789b09323b1dba4b1a`。

---
title: "Hayyo 知识问答 STEP 审查报告"
mode: "standalone / review-only"
input_step: "site/docs/design/kb-qa/history/Hayyo-知识问答-STEP-草稿.md"
input_step_sha256: "e507959b546074eb970c45d5ba089b0e3d5c5cddfeb06d789b09323b1dba4b1a"
prd: "site/docs/design/kb-qa/PRD-知识问答-v3.md"
prd_sha256: "52e7b5b6f0876cf28defcbeeaf3bdc46c71d90de028c29bebf92e1b725e28965"
inherited: "site/docs/design/kb-qa/history/PRD-知识问答-v2.md"
created: "2026-09-17"
note: "只审不改。未覆盖草稿原文。不得当作 steps-verified。"
---

# Hayyo 知识问答 STEP 审查报告

**模式**：`standalone` / `review-only`  
**原文**（未覆盖）：[`Hayyo-知识问答-STEP-草稿.md`](Hayyo-知识问答-STEP-草稿.md)  
**对照 PRD**：[`../PRD-知识问答-v3.md`](../PRD-知识问答-v3.md) v3（沿用条款定位 [`PRD-知识问答-v2.md`](PRD-知识问答-v2.md)）  
**验证版**：未生成（本模式不授权修正）

无 `RUNTIME` 证据。业务代码 `NOT_STARTED`。本轮已定向读取 compose、nginx、`feature-interaction`（`index.html` / `app.js` / `kb.js` / `kb-md.js`）、抽样 brief、原型 Demo B。

## 1. 九维总览评分

| 维度 | 状态 | 问题数 |
|---|---|---|
| 1 幻觉 | ⚠️ | 2（warn） |
| 2 遗漏 | ❌ | 4（error 2 / warn 2） |
| 3 冲突 | ⚠️ | 1（warn） |
| 4 不清晰 | ❌ | 4（error 2 / warn 2） |
| 5 依赖顺序 | ❌ | 5（error 3 / warn 2） |
| 6 验收可测性 | ❌ | 多数 AC 缺比较键（error） |
| 7 决策覆盖 | ⚠️ | 2（warn；无 ID 完全未映射） |
| 8 技术债 | ✅ | 0 |
| 9 代码事实 | ⚠️ | 2（warn；claimed `existing` 均能定位） |

无问题章节：维度 8 本次审查未发现问题。

## 2. 逐 STEP 问题、严重度和证据

| STEP | 类型 | 严重度 | 问题 | 证据 |
|---|---|---|---|---|
| 总览 / 001 | `[验收不可测]` | `error` | AC7 被映射到 STEP-001，但 AC7 的可观察结果是「失败说明可读 + 文档索引仍能打开」，001 只加 compose 服务 | v3 AC7；草稿验收映射与 STEP-001 测试表把「停 Qdrant / 端口声明」写成 AC7 |
| 001 | `[不清晰]` | `warn` | 「按现有 compose 方式 up」未写清命令；PRD 写仓库根 `docker compose up -d`，文件头是 `-f site/docker-compose.yml` | v3 §2.1；SRC-COMPOSE 第 3–4 行 |
| 005 | `[依赖问题]` | `error` | AC15「各问一句」需要发送→改写→生成，正文只前置 STEP-004 | v3 AC15、F2；草稿 STEP-005 前置仅 004，并写「可与后续 STEP 联测」 |
| 005 / 映射 | `[遗漏]` | `error` | AC16「日志明细里旧轮次仍在」只映射 STEP-005，未映射 017/018 | v3 AC16 关联 F16、F18 |
| 006 | `[依赖问题]` | `error` | AC23 前置是「已发送且生成未结束」，006 只前置 005，未前置 013 | v3 AC23；草稿 STEP-006 自承「完整 AC23 需 STEP-013」但依赖表未写 |
| 007 | `[遗漏]` | `error` | G5 / v2 §4.1 要求向量 payload 预留账号字段（本期空）；007 的 payload 列表无 `tenant_id` / `owner_id` | v3 G5「payload 预留账号字段」；v2 §4.1；草稿 STEP-007 业务定义 payload 仅 path/feature_id/chunk_id/section/heading/anchor/content_hash/collection |
| 007 / 010 | `[验收不可测]` | `error` | AC10 被映射到 007「库侧」；AC10 的操作是「问纯后台字段」并看出处 path | v3 AC10；skill：只能由直接验证该对象的 STEP 覆盖 |
| 012 | `[依赖问题]` | `error` | 单路 AC2 重排被强制前置 STEP-011（分路）。点名 0/1 时 011 不是必要前置 | v3 F5/F6/C30；草稿 STEP-012 前置 010 **且** 011 |
| 004 / 013 | `[不清晰]` | `warn` | F17 阶段文案拆在 004「槽位」与 013「驱动」，004 的 AC21 测不到阶段文案是否出现 | v3 F17、AC21 |
| 009 | `[验收不可测]` | `error` | AC3「按 VIP 退款相关块答」无文档/块身份比较键 | v3 AC3；草稿只写定性 |
| 011 | `[验收不可测]` | `error` | AC17「各至少一路」未规定比较键（如本轮检索调用上的 `feature_id` 集合） | v3 AC17、C30 |
| 014 | `[依赖问题]` | `warn` | 系统 0 块拒答不需要 013，却前置 013 | v3 C26；草稿 STEP-014 前置 012、013 |
| 015 | `[代码事实错误]` | `warn` | 开发任务写 `openDocument`（hash/headingText），与 `kb.js` 一致；但验收映射 AC6 仍是叙述句，未把 path/hash 写成比较键 | SRC-H5-KB `openDocument` 第 356–393 行确有 `hash` / `headingText` |
| 017 | `[依赖问题]` | `warn` | 前置「STEP-009～STEP-014」，发送编排（谁先写 `running`）无主 STEP | v3 §6.2 步骤 1、F18 |
| 018 / 019 | `[验收不可测]` | `error` | AC19/AC20 要求「这些字段/这些 feature_id」，未写同一快照下的投影或多重集比较 | v3 AC19、AC20、C33、C34 |
| 020 | `[验收不可测]` | `error` | AC11「与现网一致」无比较对象（如 `data-view`、`selectedId`、图节点集合） | v3 AC11；现网 `app.js` `setView` / `visibleIds` |
| 全文 | `[幻觉]` | `warn` | 完成标志四条通用勾选（「验收断言全部通过」）不能单独执行；真实断言应落在各 STEP 测试表的比较键上 | skill 维度 6；草稿每 STEP 完成标志相同 |
| 全文 | `[幻觉]` | `warn` | 来源摘要 SRC-BRIEF-MARK / UL / REF 标 `existing` 但 SHA 为「—」，与同表其它 `existing` 证据强度不一致 | 草稿来源摘要第 34–36 行；本轮已读三份 brief，文件存在 |
| 接口 | `[遗漏]` | `warn` | v2 T3「健康检查」语义（qdrant / 配置就绪 / 块数 / Key 是否已配）v3 A5 写「v2 接口沿用」，无 STEP 处置 | v2 T3；v3 A5 |
| §11 | `[遗漏]` | `warn` | 「不要把本文写进 `prd/design/*/PRD.md`」未单列 CSTR/OUT，仅被 OUT-11 部分覆盖 | v3 §11 |

未单列的 STEP-002/003/008/016 本次无独立 `error`。其 AC13/AC1/AC9 仍受维度 6 总账约束。

## 3. 需求 / 决策覆盖

| 集合 | 覆盖结论 |
|---|---|
| F1–F21 | 均有映射。F2 拆到 005/009/013，缺少「点击发送」主路径 STEP（见维度 4/5） |
| RQ-01～RQ-12.1、RQ-13～RQ-21 | 均有落点。RQ-10 → OUT-13 / D1，正确不开发 |
| G1–G7 | 有映射。G5 payload 预留账号字段在向量侧未写入 007（error） |
| C1–C5、C7–C12、C14–C29、C6/C13 v3、C18′、C30–C38 | 均至少映射一处。C30 总表只写 009，011 正文有 C30 定义，覆盖不完整（warn） |
| R1–R12、E1–E12 | 有落点 |
| D1–D3、OUT-1～OUT-23 | 无实施 STEP，符合延期/排除 |
| A1 / A3 空路声明、不得发明功能 ID | 落入 011/013/009 |
| A2「用户纠正 / 只搜某文档」 | D1，正确 |
| A5 / v2 T3 健康检查 | 未映射（warn） |
| CSTR-001～035 | 有清单；CSTR-035 来自 v2 T4，与 `app.js` `/` 快捷键一致 |

未新造 `RQ-*`。未把 D1–D3 做成开发 STEP。

## 4. 验收覆盖

| AC | 映射 STEP | 对象比较方法（草稿现状） | 复审 |
|---|---|---|---|
| AC1 | 003 | 叙述：右侧出现 Tab、独立工作区 | 失败：未规定 tablist 文本序列 / 工作区根节点身份 |
| AC2 | 010、012、013 | 叙述：基于 VIP brief 块 + 可点出处 | 失败：未比较出处 `path`/`chunk_id` 与进生成集；跳转在 015 |
| AC3 | 009 | 叙述：VIP 退款相关块 | 失败：无 brief 路径或 chunk 身份 |
| AC4 | 014 | 叙述：不编造表 | 失败：未规定回答中的数字/表相对生成集做投影比较 |
| AC5 | 014 | 叙述：并列摘录 | 失败：未规定两条互斥块的稳定 ID 均可见 |
| AC6 | 015 | 叙述：落到对应节、对话仍在 | 失败：未写 `openDocument` 后 `currentPath` = 出处 path，锚点 = hash 或 headingText |
| AC7 | 001、002、020 | 叙述：失败可读、索引仍能打开 | 失败：001 不应承载该 ID；打开后文档路径未比较 |
| AC8 | 013 | 叙述：无无出处完整规则答 | 失败：出处列表未与本轮 Top n 身份多重集比较 |
| AC9 | 007、008 | 叙述：清单含增/改/删 | 失败：未写清单比较键 `(path, chunk_id, action)` 对同一编辑快照 |
| AC10 | 007、010 | 「出处路径含 `admin/brief`」 | 部分：有 path 子串，但 007 不应映射该 AC |
| AC11 | 020 | 「与现网一致」 | 失败：无 `data-view` / 选中 / 节点集合比较 |
| AC12 | 020 | 叙述：仍关键词、不走向量 | 失败：未规定 `#kbSearch` 请求集合不含 kb-api，结果仍走 `kb.js` `search` |
| AC13 | 016、002 | 叙述：只读不可改、无 Key 明文 | 失败：未把只读字段集合与 v3 §6.1 清单做多重集相等 |
| AC14 | 009 | 叙述：无出处无完整回答 | 部分：缺上一轮 messages 身份比较 |
| AC15 | 005 | 叙述：标题/不串/刷新仍在 | 失败：未比较 title 与首问截断、两对话 message 列表不相交、刷新后 conv id 集合 |
| AC16 | 005 | 叙述：列表去掉；日志仍在 | 失败：缺 conv id / 日志 round id 比较；未映射 017/018 |
| AC17 | 011、012 | 「三功能各至少一路」 | 失败：未比较本轮分路调用的 `feature_id` 集合与 `{user-level, vip, referral}` |
| AC18 | 017 | 叙述：`interrupted`、无半段 | 失败：缺 round id 与 status 取值比较 |
| AC19 | 018 | 列出应见字段 | 失败：未要求与该轮写入快照逐字段相等（含摘录 ≤500 字、分路统计） |
| AC20 | 019 | 叙述：各 +1、未归类 | 失败：未比较 `(feature_id, count)` 多重集 = 按 C34 对同一批已写入行聚合 |
| AC21 | 004 | 无 chips、无过程栏 | 接近：仍应规定 DOM 不存在过程栏节点 / chip 按钮 |
| AC22 | 018、019、015 | 叙述：独立工作区、无第 5/6 Tab | 失败：未比较 tab 文本集合大小=4、当前 conv id 往返不变 |
| AC23 | 006 | 叙述：不切换、可切文档索引 | 部分：应比较生成中 `conv id` 不变、busy 仍真 |
| AC24 | 017 | 叙述：提示未写入、明细无该轮 | 失败：未比较明细/热度 round id 集合不含本轮 |

skill 要求：缺明确比较键时，`review-only` **不得**返回 `PASS` / `PASS_WITH_RISKS`。

## 5. 技术债与排除项

未新造 `TD-*`。处置与 PRD 一致：

| 项 | 草稿处置 | 复审 |
|---|---|---|
| brief pending-review | 接受；出处可跳转 | 通过 |
| 文档索引仍索引 PRD | 接受；D2 | 通过 |
| 无评测集 | 手工 AC | 通过 |
| 账号未做 | D3 | 通过 |
| 无范围过滤 | D1 | 通过 |
| 改写漏点名 | 接受；原句仍检索 | 通过（v3 T7） |

OUT-1～OUT-23、D1–D3 均在排除/延期清单。原型过程栏、chips、剧本条未进入开发任务。

## 6. 依赖与代码事实核查

草稿依赖（编号不隐含顺序；以各 STEP 前置表为准）：

```text
001 → 002 → 009
001 → 007 → 008
      007 → 010 → 011 → 012 → 013 → 014
                              012 → 014
                              013 → 015 → 020
003 → 004 → 005 → 006
      004 → 008, 016, 018
001 + 009～014 → 017 → 018 → 019
003 + 015 → 020
016 ← 002 + 004
```

无循环。确定性依赖错误见第 2 节：012 多余前置 011；006/005 隐藏需要 013；AC16 跨 017/018 未入映射。

**代码事实（本轮实读，与草稿 `existing` 一致）：**

| 声称 | 核实 |
|---|---|
| 三 Tab，`data-view` = admin/client/kb，无问答 | `index.html` 第 16–19 行 |
| `setView` 仅 kb / 关系图 | `app.js` `function setView` |
| `/` 聚焦 `#search` / `#kbSearch` | `app.js` 约第 478–486 行 |
| `window.KB.openDocument` / `scrollToTarget`；`headingText` | `kb.js` 第 278、356、826 行 |
| `{#锚点}` → heading id；HTML 注释丢掉 | `kb-md.js` `pushHeading`；`nodeType === 8` |
| compose 仅 `web`，`127.0.0.1:18765`，注释 3306/3307 | `docker-compose.yml` |
| nginx 无 kb-api 反代 | `nginx.conf` |
| vip `{#logic-wealth}` 保级/财富值 | `prd/design/vip/brief/current.md` |
| admin / user-level / referral `chunk:default` | 已读文首与 scope 块 |
| auth-login 同时有 `chunk:no` / `related-row` / `default` | 已读 |
| Demo B 右栏 `#qaProcess`；`STAGE_LABEL`；toast 第 288 行；`MAX_CONVS = 40` | 原型文件，非正式 |
| 无 kb-api 目录 | 仓库 glob 为空 |
| 无 `package.json` | 仓库根不存在 |

发现门（语言、路径前缀、MySQL 端口、别名表落点）标 `PLANNED` 符合 v3 §9.4。这些**不**等于缺少代码仓，故不判 `DOCUMENT_ONLY`。它们决定的是实施细节，不是 AC 能否在 UI/日志上表达；AC 不可测来自主文比较键缺失。

## 7. 首次审查结论

对 [`Hayyo-知识问答-STEP-草稿.md`](Hayyo-知识问答-STEP-草稿.md)：

**阶段结果：`FAILED_VALIDATION`**

原因（`review-only` 不授权修正，输入仍未通过）：

1. 多数 AC 只有叙述性预期，没有同一快照下的稳定 ID / 字段投影 / 多重集比较（维度 6）。
2. AC7、AC10、AC16 映射到未直接验证该条款的 STEP（维度 2/6/7）。
3. 依赖：012 多余前置 011；006/005 的生成中/各问一句依赖被隐藏（维度 5）。
4. G5 向量 payload 预留账号字段未写入 007（维度 2）。

不是 `BLOCKED`：无新的产品语义未决（D1–D3 仍为延期）。  
不是 `DOCUMENT_ONLY`：判断所需代码/契约已读；缺口是草稿结构，不是仓库缺失。  
不得生成 `steps-verified.md`。

## 8. 修正 Diff

不适用（`review-only`）。原文未覆盖。

若后续明确要求 `review-repair`，可自动修的确定项包括：改 AC 映射、补比较键、拆 012 前置、把 006 前置 013、007 payload 补本期空的预留字段、健康检查并入 002/008。端口/语言/路径前缀仍只能保持 `PLANNED`，不得用「最佳判断」填值。

## 9. 完整复审结论

本模式不做修正，无第二轮复审。首次九维结论即本阶段结论。

**阶段结果：`FAILED_VALIDATION`**

### 非阻断风险（即便修好结构仍会留下）

1. kb-api 语言、HTTP 前缀、MySQL 端口、别名表路径：`PLANNED`，实施前停止门。
2. 无 `RUNTIME`；无自动化测试命令。
3. 默认 K/n/历史轮数/对话上限 40 不是硬验收。
4. 日志保留天数未定。
5. 配置页抽屉 vs overlay 未指定（CSTR-025）。
6. 改写漏点名无专路：PRD 已接受。
7. AC4/AC5 部分依赖模型行为，比较键只能约束「生成集身份 + 不得宣称唯一现行」，不能规定模型必检出冲突。

### 阻断项

无产品语义阻断。本阶段因结构/验收校验失败而停止。

### 产物

| 角色 | 路径 |
|---|---|
| 原文草稿（已按 title 改名） | `site/docs/design/kb-qa/history/Hayyo-知识问答-STEP-草稿.md` |
| 本报告 | `site/docs/design/kb-qa/history/Hayyo-知识问答-STEP-审查.md` |
| 验证版 | 无 |

业务代码尚未实施（`NOT_STARTED`）。本阶段停止。
