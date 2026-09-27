# H5 工作台主题切换 · 实现契约

> 现行实现合同。给改工作台配色、顶栏下拉、本地记忆的人与 AI 用。  
> 需求仍以 [`../../design/h5-theme/PRD-H5工作台主题切换-v1.md`](../../design/h5-theme/PRD-H5工作台主题切换-v1.md) 为准。  
> 不改四个 Tab 结构、不改问答检索、不改图谱数据。日期：2026-09-20（对照现网代码）

## 1. 怎么用

| 你要做的事 | 读 |
|---|---|
| 改主题清单 / 默认色 | §2、`style.css` `:root`、`themes/*.css` |
| 改下拉或记忆 | §3、`theme-preview.js`、`index.html` |
| 改换皮后图谱色 | `app.js` `redrawTheme` / `domainColor` |
| 查闪蓝灰、空键被写入 | §4 |
| 对照回归 | §5 |

不要写进 `prd/design/`，不要改 kb-qa / h5-kb 正文来换皮。文件名仍是 `theme-preview.js`（未改名为 `theme.js`）。

## 2. 落地符号

| 名 | 值 |
|---|---|
| 存储键 | `hayyo-h5-theme` |
| 首次默认 | `FIRST_ID = "d-edgerunners"`（边缘行者粉） |
| 合法 id | `default`、`a-gits`、`b-2049`、`c-nightcity`、`d-edgerunners`、`c-prime` |
| 基线 | `style.css` `:root` = 边缘行者 token（`--accent: #ff3cac`） |
| 蓝灰皮肤 | `themes/default.css`（须含 `--edge: #4a5160`） |
| 挂皮标记 | `link[data-hayyo-theme-sheet]` |
| 控件 | 顶栏 `<label class="theme-picker">` + `<select aria-label="主题">` |

加载规则：生效 id 为 `d-edgerunners`（含空/非法视同该项）**不**挂额外皮肤。其余 5 个 id 同时加载 `themes/<id>.css` + `themes/_apply.css`。`themes/d-edgerunners.css` 留给对照页图鉴，工作台默认路径不必加载它。

下拉选项顺序（与 HTML 一致）：现网蓝灰、攻壳青、2049 琥珀、夜之城黄、边缘行者粉、黄主色。边缘行者粉带 `selected`，即使不是列表第一项。

## 3. 行为

`applyTheme(id, opts)`：

- 非法 id → 生效 `d-edgerunners`，**不写入**该非法值。
- 合法 id：默认写入 `localStorage`；`opts.write === false` 不写（启动时空键/非法键走这条）。
- URL `?theme=` 且合法：本次用该 id **并写入**（对照页跳入）。非法 query：生效粉且不写。
- 空存储：生效粉，**不自动写入空键**。已写入 `default` 的本机保持蓝灰，不迁移成粉。
- 换皮后调用 `GraphApp.redrawTheme()`（等皮肤 link load，双 `rAF`）。

主题只存在本机，不写服务器、不跟账号。工作台无底部「正在预览」条。对照页 `/feature-interaction/themes/` 可保留当图鉴。

四个 Tab 都看得到下拉；不藏在问答动作区。

## 4. 查 bug 优先点

1. **首次闪色**：未选过的人必须直接是粉基线，不要先套蓝灰再换。
2. **空键**：无痕 / 清空存储不得被写成 `d-edgerunners` 或 `default`。
3. **非法值**：不当作现网蓝灰。
4. **已存 default**：不要做「全员迁移到粉」。
5. **换皮范围**：只动 CSS 变量与图谱重绘；禁止顺手改 ask / 搜索 / Tab 文案。
6. **脚本位置**：`theme-preview.js` 仍在 `index.html` `<head>`，尽量早于首屏。

## 5. 回归锚点

无独立 pytest 文件。核对：

| 对象 | 断言 |
|---|---|
| `index.html` | `aria-label="主题"`；六个 `option value` 与 §2 一致；`theme-preview.js` 在 head |
| `theme-preview.js` | `STORAGE_KEY`、`FIRST_ID`、`THEME_IDS` 六键 |
| `style.css` `:root` | `--accent: #ff3cac` |
| `themes/default.css` | `--edge: #4a5160`、`--accent: #6ea8fe` |
| 浏览器 | 未选过为粉；选蓝灰刷新仍蓝灰；`?theme=a-gits` 写入存储；非法 `?theme=` 为粉且不写非法值 |
