---
title: H5 工作台主题切换（工程专题）
updated: "2026-09-20"
---

# H5 工作台主题切换

> 这是 **本仓库工程** 专题，不是 Hayyo 产品功能规则。产品规则仍只在 `prd/design/<功能>/PRD.md`。  
> **工作台** = http://127.0.0.1:18765/feature-interaction/ 这一页（四个 Tab）。  
> **下拉框** = 顶栏里的原生主题选择框。  
> **首次默认** = 未选过时是边缘行者粉；「现网蓝灰」仍可选手动选。

## 文件夹

| 路径 | 放什么 | 默认读 | 权威 |
|---|---|---|---|
| [`PRD-H5工作台主题切换-v1.md`](PRD-H5工作台主题切换-v1.md) | 需求、实施顺序、验收清单 | **改主题切换时必读** | 本专题 canonical；**本夹唯一现行 PRD** |
| [`../../contracts/h5-theme/contract.md`](../../contracts/h5-theme/contract.md) | 落地符号、默认色、查 bug 点 | **改实现 / 对照回归时必读** | 现行实现契约（总入口 [`../../contracts/INDEX.md`](../../contracts/INDEX.md)） |
| [`steps-verified.md`](steps-verified.md) | STEP 验证版与进度 | 按 STEP 开发时必读 | 现行 STEP；草稿 `steps-draft.md` 不覆盖 |
| [`step-audit.md`](step-audit.md) | STEP 审查报告 | 对照审查结论时读 | 九维审查与 Diff |
| [`execution/H5工作台主题切换开发执行记录.md`](execution/H5工作台主题切换开发执行记录.md) | 执行证据 | 核对实施结果时读 | 不改需求 |
| [`../../../feature-interaction/themes/`](../../../feature-interaction/themes/) | 对照页与皮肤 CSS | 看配色时打开 | 视觉文件；规则以 PRD 为准 |

不要把本文写进 `prd/design/`。不要把本专题文件放进 `design/h5-kb/` 或 `design/kb-qa/`。

## 任务

| 你要做的事 | 打开 |
|---|---|
| 看范围、主题清单、下拉框行为、验收 | [`PRD-H5工作台主题切换-v1.md`](PRD-H5工作台主题切换-v1.md) |
| 看落地键名 / 默认粉 / 挂皮规则 | [`../../contracts/h5-theme/contract.md`](../../contracts/h5-theme/contract.md) |
| 按 STEP 开发、看进度 | [`steps-verified.md`](steps-verified.md) |
| 看 STEP 审查 | [`step-audit.md`](step-audit.md) |
| 在浏览器里预览五套皮肤 | http://127.0.0.1:18765/feature-interaction/themes/ |
| 改关系图 / 文档索引需求 | [`../h5-kb/PRD-H5知识库-v1.md`](../h5-kb/PRD-H5知识库-v1.md) |
| 改知识问答主链路 | [`../kb-qa/PRD-知识问答-v3.md`](../kb-qa/PRD-知识问答-v3.md) |
