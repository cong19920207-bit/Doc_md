# H5 关系图与文档索引 · 实现契约

> 现行实现合同。给改工作台前三个 Tab（关系图两视图 + 文档索引）的人与 AI 用。  
> 需求仍以 [`../../design/h5-kb/PRD-H5知识库-v1.md`](../../design/h5-kb/PRD-H5知识库-v1.md) 为准（本期 L1+L2；附录 L3 **不是**本契约，问答见 [`../kb-qa/contract.md`](../kb-qa/contract.md)）。  
> 主题换皮见 [`../h5-theme/contract.md`](../h5-theme/contract.md)。登录墙只挡问答，不挡本功能。日期：2026-09-20（对照现网代码）

## 1. 怎么用

| 你要做的事 | 读 |
|---|---|
| 改四个 Tab / 切视图 | §3、`index.html`、`app.js` `setView` |
| 改关系图节点/边 | §4、`data.js` `FEATURE_DATA` |
| 改文档列表 / 打开 / 搜索 | §5、`kb.js` |
| 查误打问答 API、搜崩向量 | §6 |
| 对照回归 | §7 |

权威正文仍是各功能 `prd/design/<id>/PRD.md`。H5 只展示与检索，不另建第二套知识正文。不要把本站写进 `prd/design/`。

## 2. 落地符号

| 名 | 值 |
|---|---|
| 工作台 | `/feature-interaction/` |
| 四 Tab 有序 | 客户端 ↔ 后台 `admin`、客户端交叉 `client`、文档索引 `kb`、知识问答 `qa` |
| 落地视图 | `app.js` `bootLanding` → `setView("qa")`（关系图不是默认页） |
| 图谱数据 | `window.FEATURE_DATA`（`data.js`） |
| 文档清单 | `GET /prd/llm-manifest.json` 的 `scan_roots`（排除 changelog、`/history/`） |
| 打开文档 | 站点根绝对路径 `"/" + docPath`，例如 `/prd/design/vip/PRD.md` |
| 搜索上限 | `MAX_RESULTS = 20`；浏览器内建索引，**不是** Qdrant `chunk_id` |
| 对外 API | `app.js` / `kb.js` **不含** `"/api/kb"` |
| 默认打开 | 文档索引进入时若无当前路径 → `prd/INDEX.md` |

代码锚点：`site/feature-interaction/{index.html,app.js,data.js,kb.js}`，`prd/llm-manifest.json`。

## 3. 视图与匿名

| `data-view` | 行为 |
|---|---|
| `admin` / `client` | 关系图；`.app` 无 `kb-active`；`#kbWorkspace` hidden |
| `kb` | `.app.kb-active`；`#kbWorkspace` 显示；`KB.onEnter()` |
| `qa` | `.app.qa-active`；问答工作区；本契约不覆盖其鉴权 |

关系图 / 文档索引**匿名可开**。停 Qdrant 后仍可打开已知文档 P，且 `KB.getCurrentPath() = P`。

`GraphApp.setView`、`GraphApp.redrawTheme`、`KB.openDocument` / `getCurrentPath` / `getScanRoots` 是跨 Tab 稳定出口。

## 4. 关系图

- 节点与边只来自 `FEATURE_DATA`；不编造未写明的边。
- 域色读 CSS 变量（`domainColor`），换皮后走 `redrawTheme`，不改布局算法。
- 点节点打开的是图谱详情，不是自动改问答检索。从节点进文档：走 `KB.openFromHref` / `openDocument`，path 仍是 `prd/...`。

## 5. 文档索引

**列表**：`scan_roots` 过滤后渲染；标签用 `listLabel`（客户端功能名来自 `FEATURE_DATA`）。总览 `prd/INDEX.md`、`prd/VERSIONS.md`、`prd/PROJECT_OVERVIEW.md` 只出现在列表，不是关系图节点。

**打开**：`fetch` 站点根 Markdown，页内渲染。支持 hash / 标题滚动。功能 PRD 可列 `history/` 目录（静态站目录列表），changelog 标非现行。

**搜索**：`ensureIndex` 把清单内文档拉到浏览器，按标题/正文/路径子串匹配；结果 ≤20。该次搜索**不请求** `/api/kb`。  
特例（验收 AC11，写在代码里）：查询恰好「官方房置顶」时，可命中 `prd/design/room-list/PRD.md` 中的「官方房临时置顶」。不要当随机模糊搜索去推广。

后台 `admin/PRD.md` 命中优先带章节 `anchor` 或 `headingLevel ≥ 2` 的块。

## 6. 查 bug 优先点

1. **NO_KB_API_GRAPH**：不要让 `app.js` / `kb.js` 去打 `/api/kb`（重建、热度、ask 都不属于本功能）。
2. **路径**：文档必须从站点根 `/prd/...` 取，不要用相对 `../` 绑死在 `/feature-interaction/` 子目录。
3. **搜索 ≠ 向量**：结果 path 来自 manifest 扫描的 Markdown，不要改成 `chunk_id`。
4. **history / changelog**：默认清单排除；旧版只从功能页「查看旧版」进入。
5. **四 Tab 顺序与文案**：回归测试钉死标签数组，不要为了「问答优先」改 Tab 顺序（落地页可以是 qa）。
6. **AC11 特例**：删掉「官方房置顶 → 官方房临时置顶」会让既有验收失败；若改匹配规则，先改 PRD/STEP。

## 7. 回归锚点

| 文件 | 覆盖 |
|---|---|
| `site/kb-api/tests/test_site_contract.py` | 四 Tab 文案与顺序、`#kbWorkspace` |
| `site/kb-api/tests/test_auth_m2.py` | 关系图视图静态、登录墙不挡图谱 |
| `site/docs/design/h5-kb/steps-verified.md` | L1/L2 完成标志与 AC11 |

无独立 pytest 覆盖每一次 `openDocument`；改阅读器时用浏览器走：列表 → 打开 PRD → 搜索 → 停索引服务仍能打开已知 path。
