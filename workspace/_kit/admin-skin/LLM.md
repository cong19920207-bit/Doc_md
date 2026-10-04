# 改后台页时给 LLM 的约束

> 配套 [`inventory.md`](inventory.md)。**不要改** [`../../../site/core-docs/prd/design/admin/PRD.md`](../../../site/core-docs/prd/design/admin/PRD.md)，除非用户明确要求把某条 `live-only` 升格进现行需求。

## 权威顺序

1. 现网该页：视觉、菜单、现有字段（金标准或对照表 URL）
2. `admin/PRD.md` **现行锚点**正文：规则、校验、权限；同一主题后文覆盖前文
3. 文档图：不参与定稿

## 改已有页

- 对照表是菜单级（路径 + URL）。除 User list 外，不要假定已保存该页字段、Tab、弹窗
- 对照表先定位：`matched` / `overlay` / `live-only` / `uncertain`
- `overlay` 只绑新锚点（拉新用 `#admin-referral-v130`）
- 以金标准或现网结构为改前稿，只做点名增量
- 未点名的列、筛选、按钮、弹窗、壳一律冻结
- 不要换皮（保持 layui-admin：深壳浅表、主按钮 `#009688`）
- `live-only` 可出现在原型台账里，确认前不写进 PRD

## 加新页

- 壳和金标准列表/弹窗为底
- 字段按现行 PRD 锚点填
- 侧栏只加这一项

## 进 Word / PRD 图

- 只用干净页截图（[`gold/index.html`](gold/index.html) 或改后页去掉「变更」黄标）
- 同时改字段表；不要只换图
