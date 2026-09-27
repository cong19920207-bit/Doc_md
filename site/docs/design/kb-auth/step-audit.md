---
title: "文档工作台账号体系与管理模块 STEP 审查报告"
mode: "standalone / review-repair"
round: 1
input_step: "site/docs/design/kb-auth/steps-draft.md"
input_step_sha256: "04084933604275c406b92fe2ae23b71f0a614904bd03ae0351505af99485aee8"
verified: "site/docs/design/kb-auth/steps-verified.md"
verified_sha256: "01baa00d5af52732005d8a63562ff276ec885f247ed477039d2cca132f7dfe66"
prd: "site/docs/design/kb-auth/PRD-账号体系与管理模块-v2.md"
prd_sha256: "b005262b4e8b97d5acd99d37349a0a96c246ef940ea58208c0422239dfdedd4a"
created: "2026-09-19"
note: "第一轮 review-repair。草稿未覆盖。用户确认点 1 选 B。只修现有来源能唯一确定的项 + 该 USER_DECISION。"
---

# 文档工作台账号体系与管理模块 STEP 审查报告

**模式**：`standalone` / `review-repair`（第一轮）  
**原文**（未覆盖）：[`steps-draft.md`](steps-draft.md) SHA `04084933604275c406b92fe2ae23b71f0a614904bd03ae0351505af99485aee8`  
**验证版**：[`steps-verified.md`](steps-verified.md) SHA `01baa00d5af52732005d8a63562ff276ec885f247ed477039d2cca132f7dfe66`  
**对照 PRD**：[`PRD-账号体系与管理模块-v2.md`](PRD-账号体系与管理模块-v2.md) SHA `b005262b4e8b97d5acd99d37349a0a96c246ef940ea58208c0422239dfdedd4a`  
**v1**：不作依据。

无 `RUNTIME`。本专题业务代码未实施。本轮只修现有来源能唯一确定的项，外加用户 2026-09-19 对确认点 1 的回复「B」。未把大门叠加到页级接口（用户未选该方案）。

---

## 1. 九维总览评分

| 维度 | 首次审查（草稿） | 完整复审（验证版） |
|---|---|---|
| 1 幻觉 | ⚠️ 1 | ✅ 0 |
| 2 遗漏 | ❌ 8 | ✅ 0 |
| 3 冲突 | ❌ 2 | ✅ 0 |
| 4 不清晰 | ❌ 3 | ✅ 0（风险 R-API-DOOR / health `PLANNED`） |
| 5 依赖顺序 | ❌ 4 | ✅ 0 |
| 6 验收可测性 | ❌ 9 | ✅ 0 |
| 7 决策覆盖 | ❌ 4 | ✅ 0 |
| 8 技术债 | ✅ 0 | ✅ 0 |
| 9 代码事实 | ⚠️ 1 | ⚠️ 0（INDEX SHA 会随本夹更新漂移，不阻断） |

维度 8：本次审查未发现问题。PRD 无 `TD-*`，未新造技术债编号。

---

## 2. 逐 STEP 问题（首次审查 → 本轮处置）

| STEP | 类型 | 首次 | 问题 | 本轮处置 |
|---|---|---|---|---|
| 001～016 | `[验收不可测]` | error | 完成标志「AC 通过」，无比较键 | 验证版对象比较约定 + 各 STEP 测试绑定符号 |
| 002 | `[遗漏]` | error | AC1「登出后问答不可问」未映射 005 | AC1 → 002+005；005 测 `QA_LOGIN_WALL` |
| 002 | `[遗漏]` | warn | F10 登录成败无打点 | 002 写审计行；013 列表；F10 映射含 002 |
| 003 | `[遗漏]` | warn | F2 菜单未映射 008 | F2 → 003、008 |
| 004 | `[遗漏]` | error | GET config、GET rounds/{id} 未纳入 | `OPS_READ_WRITE` 五条路径 |
| 004/005 | `[不清晰]` `[依赖问题]` | error | ask 401 责任不清 | 中间件分档表；005 前置 004 |
| 004/012 | `[依赖问题]` | error | 012 未前置 004 | 012 前置 004+005+009 |
| 005 | `[验收不可测]` | error | AC2 无观察对象 | `GRAPH_VIEWS`；`NO_KB_API_GRAPH` |
| 007 | `[验收不可测]` | error | AC4 无会话 id 集合 | `CONV_IDS(u)`；与 `CONV_KEY_IDS` 交集为空 |
| 007 | `[不清晰]` | warn | 会话 CRUD 登录校验归属 | 分档：004 未登录 401；007 做隔离；007 前置 004 |
| 008 | `[验收不可测]` | warn | 四钮/菜单未绑集合 | `TOP_OPS_FOUR=∅`；`ACCOUNT_MENU` |
| 008 | `[不清晰]` | warn | Tab 多重集 vs 契约有序 | `MAIN_TABS` 产品多重集；`MAIN_TABS_SEQ` 仅保持现网契约 |
| 009 | `[冲突]` | error | 测试改写 AC5 前置 | `USER_DECISION` B：`ROLE_MINGXI`={进管理模块, 问答明细} |
| 009 | `[验收不可测]` | error | 「能看明细」无 round_id；UI/接口未分 | 明细 round_id；无入口 **且** PUT/POST 403 |
| 012 | `[验收不可测]` | error | 只比条数 | `CHIP_FIXED` 四对；`CHIP_HEAT`←`ITEMS4` |
| 013 | `[验收不可测]` `[不清晰]` | error | 无审计投影；写入点不清 | `AUDIT_CFG`/`AUDIT_REINDEX`；打点分 STEP；013 前置 002+004+009 |
| 014 | `[验收不可测]` | error | 无 round_id 集合 | `SUMMARY_DOWN = DOWN_IDS` |
| 015/016 | `[依赖问题]` | error | AC10 跳转挂在 015 | 015：未启用/关闭/坏证书/非标准不跳；016：`TLS_REDIR`+AC11 |
| 全表 | `[决策覆盖]` | error | CSTR/OUT/G 无落点 | 约束/排除/G 映射表 |
| 全表 | `[代码事实]` | warn | SRC-INDEX SHA 过期 | 验证版更新；注明随后 INDEX 再改会漂移 |

未发现：无来源 `TD-*`；未把 💡 名词写成 USER_DECISION；无 RUNTIME 伪称。

---

## 3. 需求 / 决策覆盖（复审）

F1–F14、G1–G6、C1–C15（C11 废止）、RQ-01～RQ-19、CSTR-001～024、OUT-1～12 均有落点。未新造 `RQ-*` / `TD-*`。

| ID | 验证版落点 |
|---|---|
| F2 | 003 改密；008 菜单 |
| F8 | 004 接口；009 UI |
| F10 | 002/003/010/011/015 打点；013 列表 |
| G5 | CSTR-001 |
| AC1 | 002 登录接口；005 登出后墙 |
| AC5 | 009；前置 `ROLE_MINGXI`（B） |
| AC10 | 015 非跳转子条款；016 `TLS_REDIR` |
| C11 | 010 不在账号上勾权限 |

---

## 4. 验收覆盖（复审）

| AC | STEP | 比较键 |
|---|---|---|
| AC1 | 002、005 | `AUTH_COOKIE`；`SESSION_DEAD`；`QA_LOGIN_WALL` |
| AC2 | 005 | `GRAPH_VIEWS`；`NO_KB_API_GRAPH` |
| AC3 | 005 | `ASK_UNAUTH`；`QA_LOGIN_WALL` |
| AC4 | 007 | `CONV_IDS` 相等；与旧 `CONV_KEY_IDS` 交集空 |
| AC5 | 009 | `ROLE_MINGXI`；round_id；配置/重建无入口且 403 |
| AC6 | 010 | 初始密码 `ME_ID`；禁用 `SESSION_DEAD` |
| AC7 | 008 | `TOP_OPS_FOUR=∅`；`QA_HEALTH` |
| AC8 | 013 | `AUDIT_CFG`；`AUDIT_REINDEX` |
| AC9 | 014 | `SUMMARY_DOWN=DOWN_IDS` |
| AC10 | 015、016 | `TLS_HTTP` / `TLS_REDIR` |
| AC11 | 016 | `HOST_443_CLOSED` |
| AC12 | 004 | `OPS_READ_WRITE` → `STATUS_DENY` |
| AC13 | 002、011 | `LOCK_RULE`；解锁后 `ME_ID` |
| AC14 | 006 | `FB_OWNER` 同一 `round_id` |
| AC15 | 010 | 启用超管人数仍 ≥ 1 |
| AC16 | 012 | `CHIP_FIXED`；`CHIP_HEAT` |
| AC17 | 003、008 | `ACCOUNT_MENU`；`SESSION_DEAD` |
| AC18 | 002 | 7 天 `SESSION_DEAD` |

---

## 5. 技术债与排除项

T7 四条接受。OUT-1～12 验证版有排除映射表。未新造 `TD-*`。维度 8 通过。

---

## 6. 依赖与代码事实核查（复审）

**依赖**：001→002→003；002+001→004；002+004→005/007；005→006；002+003→008；004+008→009；001+009→010；002+010→011；004+005+009→012；002+004+009→013；006+009→014；010→015→016。无循环。

**代码事实**：`auth_passthrough` L69–72、四钮 L38–44、`user_id: null` L787–790、`CHIP_FIXED` L16–32 与验证版定位符一致。新路由仍 `PLANNED`。

---

## 7. 首次审查结论（历史）

草稿 `FAILED_VALIDATION`。见本文件上一版 review-only。Q-AC5 当时未决。

---

## 8. 修正 Diff

草稿未覆盖。验证版相对草稿的确定性修正：

| 项 | 原内容 | 修正内容 | 来源 | 影响映射 |
|---|---|---|---|---|
| AC5 前置 | 测试写「进管理模块+问答明细」，与 AC5 原文冲突 | `ROLE_MINGXI`={进管理模块, 问答明细}；无大门无入口/403 | `USER_DECISION` B | AC5→009 |
| 大门 vs 接口 | 未写 | 页级接口不叠加大门；风险 R-API-DOOR | B 未选「接口也要大门」 | F8 |
| 比较键 | 仅符号草稿、完成标志笼统 | 全表集合/多重集/状态码 | skill 维度 6 | 全部 AC |
| AC1 | 仅 002 | 002+005 | PRD AC1「问答不可问」 | AC1 |
| F2 | 仅 003 | 003+008 | PRD F2 顶栏菜单 | F2 |
| OPS 路径 | 三条 | 含 GET config、GET rounds/{id} | F8/G2；SRC-API | AC12 仍测原三条，读接口一并保护 |
| 中间件 | 白名单 PLANNED 无分档 | 须登录 / 管理权限分档 | 消除 004 vs 005/007/012 | 依赖 |
| 012 前置 | 005、009 | +004 | heatmap 401 | F14 |
| 007 前置 | 002 | +004 | 会话 CRUD 401 | F5 |
| 013 前置 | 009、010 | 002、004、009 | AC8 不依赖开户；登录打点来自 002 | F10 |
| AC10 | 全在 015 | 跳转在 016 | CSTR-017；compose 端口 | AC10、AC11 |
| G/CSTR/OUT | 无落点表 | 已补 | 维度 7 | — |
| F10 | 仅 013 | 各动作 STEP 打点 + 013 列表 | F10 原文动作列表 | F10 |

未改：T 节 💡 名词仍不填具体值；不改 PRD/v3/反馈 PRD 正文；不开始开发。

---

## 9. 完整复审结论、阶段结果、风险和阻断项

从 PRD、代码基线与验证版重新走九维：结构/映射/依赖/比较键已收敛。Q-AC5 已由用户选 B 收口，不再 `BLOCKED`。

**阶段结果：`PASS_WITH_RISKS`**

- 已生成 [`steps-verified.md`](steps-verified.md)
- 草稿未覆盖
- 不宣布开发已开始，不生成里程碑

**阻断项**：无。

**非阻断风险**：见验证版「非阻断风险」1–10。只要风险列表非空，不得标 `PASS`。

**下一阶段**：用户明确要求后才可 `$milestone-step-execution` 排期；在此之前不写业务代码。
