---
title: 本站实现契约
updated: "2026-10-04"
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
| 账号 / 管理站 / 配置发布 / 调试 / 运维 | [`kb-auth/contract.md`](kb-auth/contract.md) | [`../design/kb-auth/INDEX.md`](../design/kb-auth/INDEX.md) |
| 知识问答主链路 / 多轮 / Memory | [`kb-qa/contract.md`](kb-qa/contract.md) | [`../design/kb-qa/INDEX.md`](../design/kb-qa/INDEX.md) |
| 问答反馈与对话样式 | [`kb-qa-feedback/contract.md`](kb-qa-feedback/contract.md) | [`../design/kb-qa-feedback/INDEX.md`](../design/kb-qa-feedback/INDEX.md) |
| H5 关系图 / 文档索引 / 核心文档发布 | [`h5-kb/contract.md`](h5-kb/contract.md) | [`../design/h5-kb/PRD-H5知识库-v1.md`](../design/h5-kb/PRD-H5知识库-v1.md) |
| H5 工作台主题 | [`h5-theme/contract.md`](h5-theme/contract.md) | [`../design/h5-theme/INDEX.md`](../design/h5-theme/INDEX.md) |

## 核心文档迁移整合

2026-10-04 已按本会话确认的迁移决定同步现行契约，不另建第二份正式合同：

| 约束对象 | 唯一落点 |
|---|---|
| 文档唯一源、物理/逻辑路径、发布选择、manifest/历史清单、本地刷新 | [H5 §8](h5-kb/contract.md#8-核心文档与受控发布)；阅读器消费规则在同契约 §5 |
| API 文档根、异常扫描保护、知识块/旧引用兼容、启动降级 | [知识问答 §2/§4](kb-qa/contract.md#4-api-终态) |
| 静态登录门、目录列表、Docker 挂载、TLS 独立卷与旧证书迁移 | [账号 §7](kb-auth/contract.md#7-tls-与-compose) |
| 新主题资源登记发布清单 | [主题 §3](h5-theme/contract.md#3-行为) |

迁移文件、自动化、本地 HTTP/角色矩阵及 Chrome 验收证据归[既有迁移执行记录](../design/core-docs-migration/execution/核心文档迁移开发执行记录.md)。纯目录迁移未改变问答反馈 API、主题偏好或产品业务规则。生产未部署；上线包与回退为尚未执行的步骤 6，不把历史本地证据当成线上结果。

## 多轮编排整合

M1～M8 的实现增量已按功能并入上表前三份契约。需求入口另见 [多轮编排与后台](../design/kb-qa-multdesign/INDEX.md)，逐 STEP 落点、当前验证与未完成条款见 [收尾记录](../design/kb-qa-multdesign/steps-verified.md#2026-10-03-开发收尾与正式契约整合)。草案保留历史快照，不新建重复的正式合同。

## 校验口径（防幻觉）

写进契约的路径、常量、事件名必须能在仓库搜到。禁止发明未实现的 API。过期草案（例如 kb-qa M1「鉴权放行」、M4「顶栏明细 overlay」）不得抄回正式契约。
