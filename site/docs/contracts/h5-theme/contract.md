# H5 工作台主题切换 · 实现契约

> 现行实现合同。给改工作台配色、顶栏下拉、本地记忆的人与 AI 用。  
> 原需求见 [`../../design/h5-theme/PRD-H5工作台主题切换-v1.md`](../../design/h5-theme/PRD-H5工作台主题切换-v1.md)。2026-10-03 用户接受暖夜默认主题，随后明确要求优化主题菜单并适配各主题；以下为更新后的实现口径。
> 本增量只涉及主题入口、展示与切换。日期：2026-10-03（对照本地运行页面）

## 1. 怎么用

| 你要做的事 | 读 |
|---|---|
| 改主题清单 / 默认色 | §2、`style.css` `:root`、`themes/*.css` |
| 改菜单或记忆 | §3、`theme-preview.js`、`index.html`、`workbench.css` |
| 改换皮后图谱色 | `app.js` `redrawTheme` / `domainColor` |
| 查闪蓝灰、空键被写入 | §4 |
| 对照回归 | §5 |

不要写进 `prd/design/`，不要改 kb-qa / h5-kb 正文来换皮。文件名仍是 `theme-preview.js`（未改名为 `theme.js`）。

## 2. 落地符号

| 名 | 值 |
|---|---|
| 存储键 | `hayyo-h5-theme` |
| 首次默认 | `FIRST_ID = "warm-night"`（暖夜） |
| 合法 id | `warm-night`、`default`、`a-gits`、`b-2049`、`c-nightcity`、`d-edgerunners`、`c-prime`；集中在 `THEMES` 清单 |
| 基线 | `style.css` `:root` = 边缘行者 token（`--accent: #ff3cac`） |
| 蓝灰皮肤 | `themes/default.css`（须含 `--edge: #4a5160`） |
| 挂皮标记 | `link[data-hayyo-theme-sheet]` |
| 控件 | `#themeTrigger` 按钮 + `#themeMenu` 浮层，`#themeOptions` 为 `menu`，候选为 `menuitemradio` |
| 当前主题 | `html[data-theme]`、触发器名称及候选 `aria-checked` 同步为实际生效 id |

加载规则：生效 id 为 `d-edgerunners` 时使用 `style.css` 基线，不挂额外皮肤。其余 6 个 id 同时加载 `themes/<id>.css` + `themes/_apply.css`。`themes/d-edgerunners.css` 留给对照页图鉴。

菜单顺序：暖夜、现网蓝灰、攻壳青、2049 琥珀、夜之城黄、边缘行者粉、黄主色。每项包含配色缩略图、名称、简短说明，当前项显示勾选。缩略图使用候选主题实际配色；菜单底色、边框、文字、悬停和选中态使用当前主题变量。

## 3. 行为

`applyTheme(id, opts)`：

- 非法 id → 生效 `warm-night`，**不写入**该非法值。
- 合法 id：默认写入 `localStorage`；`opts.write === false` 不写（启动时空键/非法键走这条）。
- URL `?theme=` 且合法：本次用该 id **并写入**（对照页跳入）。非法 query：生效暖夜且不写。
- 空存储：生效暖夜，**不自动写入空键**。已有合法主题偏好保持原值。
- 换皮后调用 `GraphApp.redrawTheme()`（等皮肤 link load，双 `rAF`）。

主题只存在本机，不写服务器、不跟账号。工作台无底部「正在预览」条。对照页 `/feature-interaction/themes/` 可保留当图鉴。

四个 Tab 都看得到主题入口。点击或方向键展开，打开时聚焦当前主题；上下方向键、Home/End 移动候选，Enter/空格应用。仅移动焦点不改主题。选择后关闭并回到触发器；Esc 关闭且不触发底层图谱的取消选择，Tab 关闭并自然离开控件；点击外部或焦点移出时关闭。

浮层根据触发器和视口定位，左右保留至少 12px，短屏内部滚动。≤600px 时入口显示固定的“主题”文字，≤370px 时只显示图标；无障碍名称始终包含当前完整主题名。刷新后菜单名称、勾选项与实际配色保持一致。

## 4. 查 bug 优先点

1. **启动主题**：默认暖夜；已有合法主题优先，非法 query 的回退显示不能又被旧存储标签覆盖。
2. **空键**：无痕 / 清空存储不得自动写入主题偏好。
3. **非法值**：不当作现网蓝灰。
4. **已存 default**：保持用户已选蓝灰。
5. **换皮范围**：只动 CSS 变量与图谱重绘；禁止顺手改 ask / 搜索 / Tab 文案。
6. **脚本位置**：`theme-preview.js` 仍在 `index.html` `<head>`，尽量早于首屏。

## 5. 回归锚点

无独立 pytest 文件。核对：

| 对象 | 断言 |
|---|---|
| `index.html` | 主题触发器、菜单容器、展开状态；`theme-preview.js` 在 head |
| `theme-preview.js` | `STORAGE_KEY`、`FIRST_ID`、`THEMES` 七项及菜单键盘/关闭行为 |
| `style.css` `:root` | `--accent: #ff3cac` |
| `themes/default.css` | `--edge: #4a5160`、`--accent: #6ea8fe` |
| 浏览器 | 七套主题的实际颜色与勾选项；选择后刷新保持；四 Tab 入口可用；320/390px 视口边界、短屏滚动与键盘操作 |

2026-10-03 本次已验证七套切换、刷新记忆、四 Tab、图谱换色与选中保持、方向键/Home/End/Enter/Esc/Tab、320×480 与 390×844 视口。空存储/非法 query 的写入规则本次以源码核对，未清空用户存储做运行验证。
