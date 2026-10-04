# 运营后台原型底稿

> 现网皮 + 对照表 + User list 金标准。**不是**产品权威。规则仍以 [`../../../site/core-docs/prd/design/admin/PRD.md`](../../../site/core-docs/prd/design/admin/PRD.md) 为准。

| 用途 | 打开 |
|---|---|
| 现网菜单 ↔ PRD 锚点 | [`inventory.md`](inventory.md) |
| 改页时给 LLM 的约束 | [`LLM.md`](LLM.md) |
| 金标准（现网 User list，可进 Word 的干净页） | [`gold/index.html`](gold/index.html) |
| 补丁示例（现网 / 改后对照，非真实需求） | [`index.html`](index.html) |
| 菜单原始树 | [`evidence/menu-tree-2026-09-04.json`](evidence/menu-tree-2026-09-04.json) |
| 执行记录 | [`execution/运营后台开发执行记录.md`](execution/运营后台开发执行记录.md) |

## 已确认口径

- 视觉和「现在有什么」跟现网；规则跟 PRD 正文；文档图不参与定稿
- 对照用 `admin/PRD.md` **锚点**，不用会重复的章节号
- 无 PRD 章节的现网页：台账保留，确认前不写入 `admin/PRD.md`
- 改已有页：原页为底，只做点名增量
- Word：放金标准或改后页的**干净截图**，不要带「变更」黄标；字段表必须同步改
- 不整站另存 CSS，不一次做 183 页可点后台

## 本轮台账摘要（2026-09-04 FAT）

叶子页 183（菜单路径 + 内页 URL）。**没有**整站页面/弹窗存档；字段只核过 User list。

菜单级对照（2026-09-04 二次校验后）：`matched` 104、`overlay` 16（拉新绑 `#admin-referral-v130`）、`live-only` 50、`uncertain` 13。此前 `matched` 125 偏高，已按「同一页」收紧，不再把「同一大类」标成已对齐。
