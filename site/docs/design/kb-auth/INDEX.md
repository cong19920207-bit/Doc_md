---
title: 账号体系与管理模块（工程专题）
updated: "2026-10-03"
---

# 账号体系与管理模块

> 这是 **本仓库工程** 专题，不是 Hayyo 产品登录，也不是运营后台。  
> 产品登录规则仍在 [`prd/design/auth-login/PRD.md`](../../../../prd/design/auth-login/PRD.md)。  
> 本站管理模块**不要**写入 [`prd/design/admin/`](../../../../prd/design/admin/PRD.md)，也不套 [`workspace/_kit/admin-skin/`](../../../../workspace/_kit/admin-skin/INDEX.md)。  
> 检索基线见 [`知识问答v3`](../kb-qa/PRD-知识问答-v3.md)；多轮生成、消息事实与后台增量见下方 kb-qa-multdesign。账号基础需求保留在本夹，当前权限/接口以正式契约为准。\
> v1 在 [`history/`](history/INDEX.md)，**不默认读**。

> 多轮编排与新版后台增量另见 [kb-qa-multdesign](../kb-qa-multdesign/INDEX.md)；M1～M8已按现有功能并入正式契约，剩余项与当前回归见该专题收尾记录。本夹早期计划的状态不代表当前代码状态。

## 文件夹

| 路径 | 放什么 | 默认读 | 权威 |
|---|---|---|---|
| [`PRD-账号体系与管理模块-v2.md`](PRD-账号体系与管理模块-v2.md) | 需求、决策、验收、技术扩展 | **改账号 / 管理模块 / 证书启用时必读** | 本专题 canonical；**本夹唯一现行 PRD** |
| [`../../contracts/kb-auth/contract.md`](../../contracts/kb-auth/contract.md) | 落地符号、鉴权矩阵、查 bug 点 | **改实现 / 查越权 / 对照回归时必读** | 现行实现契约（总入口 [`../../contracts/INDEX.md`](../../contracts/INDEX.md)） |
| [`steps-verified.md`](steps-verified.md) | STEP 验证版与进度 | 按 STEP 开发时必读 | 现行 STEP；草稿不覆盖 |
| [`实施计划.md`](实施计划.md) | 四里程碑编排 | 按阶段开发时必读 | 只编排 STEP，不改需求/STEP 正文；原阶段快照，当前见收尾记录 |
| [`steps-draft.md`](steps-draft.md) | STEP 草稿 | 对照拆解原文 | 已被验证版替代，不覆盖验证版 |
| [`step-audit.md`](step-audit.md) | STEP 审查报告 | 对照审查结论时读 | 第一轮 review-repair：`PASS_WITH_RISKS` |
| [`history/`](history/INDEX.md) | v1 全文 | **不默认读** | 已被 v2 替代 |

不要把本文写进 `prd/design/`。不要把本专题文件放进 `design/kb-qa/` 或 `design/h5-kb/`。

## 任务

| 你要做的事 | 打开 |
|---|---|
| 看登录范围、角色、管理模块、证书、验收 | [`PRD-账号体系与管理模块-v2.md`](PRD-账号体系与管理模块-v2.md) |
| 看落地 API / 鉴权 / 查越权 | [`../../contracts/kb-auth/contract.md`](../../contracts/kb-auth/contract.md) |
| 改管理站页面结构或加管理页 | [`../kb-admin-ui/INDEX.md`](../kb-admin-ui/INDEX.md) |
| 按 STEP 开发、看进度 | [`steps-verified.md`](steps-verified.md) |
| 按阶段开发 | [`实施计划.md`](实施计划.md) |
| 看 STEP 草稿原文 | [`steps-draft.md`](steps-draft.md) |
| 看 STEP 审查 | [`step-audit.md`](step-audit.md) |
| 对比 v1 口径 | 仅此时打开 [`history/INDEX.md`](history/INDEX.md) |
| 改问答检索 / 生成 / 日志口径 | [`../kb-qa/PRD-知识问答-v3.md`](../kb-qa/PRD-知识问答-v3.md) |
| 改赞踩 / 对话区样式 | [`../kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md`](../kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md) |
| 改关系图 / 文档索引阅读 | [`../h5-kb/PRD-H5知识库-v1.md`](../h5-kb/PRD-H5知识库-v1.md) |
