---
title: 知识问答（工程专题）
updated: "2026-09-20"
---

# 知识问答 · 本专题怎么读

> 这是 **本仓库工程** 专题，不是 Hayyo 产品功能规则。产品规则仍只在 `prd/design/<功能>/PRD.md`。

## 文件夹

| 路径 | 放什么 | 默认读 | 权威 |
|---|---|---|---|
| [`PRD-知识问答-v3.md`](PRD-知识问答-v3.md) | 当前需求与实施口径 | **改问答 / 检索 / 日志时必读** | 工程 canonical；**本夹唯一现行 PRD** |
| [`../../contracts/kb-qa/contract.md`](../../contracts/kb-qa/contract.md) | 落地符号、SSE、切块、查 bug 点 | **改实现 / 对照回归时必读** | 现行实现契约（总入口 [`../../contracts/INDEX.md`](../../contracts/INDEX.md)） |
| [`Hayyo-知识问答-STEP-验证版.md`](Hayyo-知识问答-STEP-验证版.md) | STEP 验证版 | **按 STEP 实施时读** | 验证版；权威需求仍是 v3 PRD |
| [`Hayyo-知识问答-实施计划.md`](Hayyo-知识问答-实施计划.md) | 里程碑编排（M1–M4） | **按阶段开发时读** | 只改分组与顺序，不改 STEP |
| [`../../../../knowledge/INDEX.md`](../../../../knowledge/INDEX.md) | 讲解 / 案例 / 示意（仓库根 `knowledge/`） | **要理解链路时再读**；不当需求合同 | 讲解；冲突以 v3 为准 |
| [`history/`](history/INDEX.md) | 旧版 PRD、STEP 草稿、r1 快照、审查过程 | **不默认读** | 已被 v3 / 现行验证版替代 |
| `workspace/kb-qa-proto/` | mock 原型（Demo A/B） | 调交互时读 | 非正式 kb-api、非正式现网第四 Tab |
| [`../kb-qa-feedback/`](../kb-qa-feedback/INDEX.md) | 反馈、刷新、对话区样式 | **改那些时读新夹，不读本夹 v3** | 独立专题 v2 |

不要把讲解稿或原型写进 `prd/design/`。日志页 / 热度页也是本站点工程后台，不写入 `prd/design/admin/`。

**v2 已过期**，不是实施依据。v3 写「沿用」的条款视为 v3 并入，不要打开 `history/PRD-知识问答-v2.md` 当现行合同。

## 任务

| 你要做的事 | 打开 |
|---|---|
| 改需求、验收、模型选型、分路规则 | [`PRD-知识问答-v3.md`](PRD-知识问答-v3.md) |
| 看落地 API / SSE / 切块 / 查串库 | [`../../contracts/kb-qa/contract.md`](../../contracts/kb-qa/contract.md) |
| 改复制 / 赞 / 踩 / 刷新、对话区居中栏、空状态建议问句 | [`../kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md`](../kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md) |
| 按 STEP 实施 | [`Hayyo-知识问答-STEP-验证版.md`](Hayyo-知识问答-STEP-验证版.md) |
| 看里程碑顺序（M1–M4） | [`Hayyo-知识问答-实施计划.md`](Hayyo-知识问答-实施计划.md) |
| 搞懂单路 / 多意图、K 与 n、改写和回答是不是同一个模型 | [`../../../../knowledge/INDEX.md`](../../../../knowledge/INDEX.md) |
| 对照「等级2+VIP5+拉新」或「VIP 有多少等级」整轮怎么走 | [`../../../../knowledge/案例-跨功能与单功能.md`](../../../../knowledge/案例-跨功能与单功能.md) |
| 看旧口径、草稿、审查 Diff | 仅在对比时打开 [`history/INDEX.md`](history/INDEX.md) |
