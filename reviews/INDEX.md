# 复盘

> 数据 / 运营复盘工作区。**不是**产品权威。规则仍以 [`../prd/INDEX.md`](../prd/INDEX.md) 为准。  
> 每个分析一个子目录；新分析新建目录并登记本表。最后更新：2026-09-14。

## 任务 → 打开

| 任务 | 目录 | 原始数据 | 汇总 |
|---|---|---|---|
| 拉新运营复盘 | `referral/` | （无单独底表） | [`referral/summary/index.html`](referral/summary/index.html) |
| 拉新与付费简报 | `getnew/` | [`getnew/source/`](getnew/source/) | [`getnew/summary/index.html`](getnew/summary/index.html) |

后续定向任务按同样方式加行，例如充值、休闲游戏：新建 `reviews/<分析>/`，不要把不相关文件堆在已有分析里。

## 约定

- 只放复盘产物。不改写 `prd/`。
- 子目录名优先用短分析名，或与 `prd/design/<id>` 对齐的功能 ID。
- 每次分析内部固定两层：`source/` 原始 / 整理前的表；`summary/` 汇总页与结论。
- `source/` 不进产品扫描。
- 旧路径 `referral-ops-review/` 已迁到 `reviews/referral/`。旧文件 `reviews/<分析>/index.html` 仅作跳转到 `summary/`。
