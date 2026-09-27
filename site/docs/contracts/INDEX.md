---
title: 本站实现契约
updated: "2026-09-20"
---

# 实现契约

> 按**功能**分夹，不放进某个专题的 PRD/STEP 目录。  
> 改实现、查越权、对照回归：先打开本夹对应功能的 `contract.md`。需求仍读 `design/<功能>/` 的现行 PRD。  
> 符号以代码为准；草案与本文件冲突，以本文件为准。

## 约定

| 路径 | 放什么 |
|---|---|
| `contracts/<功能>/contract.md` | 该功能现行实现合同（落地符号、鉴权、查 bug 点） |
| 本 `INDEX.md` | 功能 → 契约 路由 |

新功能落地后在本表加一行，夹名与 `design/` 专题夹一致（如 `kb-auth`、`kb-qa`）。不要在 `design/<功能>/` 里再放一份正式 `contract.md`。

## 功能

| 功能 | 契约 | 需求入口 |
|---|---|---|
| 账号 / 管理站 / 证书 | [`kb-auth/contract.md`](kb-auth/contract.md) | [`../design/kb-auth/INDEX.md`](../design/kb-auth/INDEX.md) |
| 知识问答主链路 | [`kb-qa/contract.md`](kb-qa/contract.md) | [`../design/kb-qa/INDEX.md`](../design/kb-qa/INDEX.md) |
| 问答反馈与对话样式 | [`kb-qa-feedback/contract.md`](kb-qa-feedback/contract.md) | [`../design/kb-qa-feedback/INDEX.md`](../design/kb-qa-feedback/INDEX.md) |
| H5 关系图 / 文档索引 | [`h5-kb/contract.md`](h5-kb/contract.md) | [`../design/h5-kb/PRD-H5知识库-v1.md`](../design/h5-kb/PRD-H5知识库-v1.md) |
| H5 工作台主题 | [`h5-theme/contract.md`](h5-theme/contract.md) | [`../design/h5-theme/INDEX.md`](../design/h5-theme/INDEX.md) |

## 校验口径（防幻觉）

写进契约的路径、常量、事件名必须能在仓库搜到。禁止发明未实现的 API。过期草案（例如 kb-qa M1「鉴权放行」、M4「顶栏明细 overlay」）不得抄回正式契约。
