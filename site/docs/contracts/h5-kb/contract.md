# H5 关系图与文档索引 · 实现契约

> 现行实现合同。给改工作台关系图两视图与文档索引的人与 AI 用。
> 需求仍以 [`../../design/h5-kb/PRD-H5知识库-v1.md`](../../design/h5-kb/PRD-H5知识库-v1.md) 为准（本期 L1+L2；附录 L3 **不是**本契约，问答见 [`../kb-qa/contract.md`](../kb-qa/contract.md)）。  
> 主题换皮见 [`../h5-theme/contract.md`](../h5-theme/contract.md)。本模块不新增鉴权。页面结构更新：2026-10-03，用户明确要求问答优先、统一图标并优化其余三页（对照本地运行页面）。

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
| 四 Tab 有序 | 知识问答 `qa`、客户端 ↔ 后台 `admin`、客户端交叉 `client`、文档索引 `kb` |
| 落地视图 | `app.js` `bootLanding` → `setView("qa")`（关系图不是默认页） |
| 图谱数据 | `window.FEATURE_DATA`（`data.js`） |
| 文档清单 | `GET /prd/llm-manifest.json` 的 `scan_roots`（排除 changelog、`/history/`） |
| 打开文档 | 站点根绝对路径 `"/" + docPath`，例如 `/prd/design/vip/PRD.md` |
| 搜索上限 | `MAX_RESULTS = 20`；浏览器内建索引，**不是** Qdrant `chunk_id` |
| 对外 API | `app.js` / `kb.js` **不含** `"/api/kb"` |
| 默认打开 | 文档索引进入时若无当前路径 → `prd/INDEX.md` |

代码锚点：`site/feature-interaction/{index.html,app.js,data.js,kb.js,ui-icons.js,workbench.css}`，`prd/llm-manifest.json`。

## 3. 视图与登录

| `data-view` | 行为 |
|---|---|
| `admin` / `client` | 关系图；`.app` 无 `kb-active`；`#kbWorkspace` hidden |
| `kb` | `.app.kb-active`；`#kbWorkspace` 显示；`KB.onEnter()` |
| `qa` | `.app.qa-active`；问答工作区；本契约不覆盖其鉴权 |

关系图 / 文档索引随整站受 nginx `/_kb_site_gate` 登录保护；未登录302到 `/login/?next=...`，不是匿名入口。登录后的文档阅读不依赖 Qdrant，停 Qdrant 后仍可打开已知文档 P，且 `KB.getCurrentPath() = P`。详见 [账号契约 §5](../kb-auth/contract.md#5-h5)。

`GraphApp.setView`、`GraphApp.redrawTheme`、`KB.openDocument` / `getCurrentPath` / `getScanRoots` 是跨 Tab 稳定出口。

## 4. 关系图

- 节点与边只来自 `FEATURE_DATA`；不编造未写明的边。
- 域色读 CSS 变量（`domainColor`），换皮后走 `redrawTheme`，不改布局算法。
- 点节点打开的是图谱详情，不是自动改问答检索。从节点进文档：走 `KB.openFromHref` / `openDocument`，path 仍是 `prd/...`。
- 页面结构为标题与搜索、业务域/功能目录、图谱、关系详情；≤980px 时功能目录与详情为抽屉。公共图标由 `HayyoIcons` 提供，颜色跟随当前主题。
- 两视图、搜索和筛选后自动适应可见节点；手动拖拽或缩放后保留用户镜头，点「适应画布」恢复自动适应。全局隐藏关系文字，选中节点后显示相关文字与详情依据。
- 搜索显示匹配节点及其直接关联，同时服从业务域筛选。「只看关联」进一步收窄到选中节点的直接关联；取消选中后恢复全部筛选结果。功能目录与关系条目可定位节点。
- 四 Tab 支持左右方向键、Home/End；节点支持 Enter/空格选择；Esc 关闭抽屉并取消图谱选中。

## 5. 文档索引

**列表**：`scan_roots` 过滤后渲染；标签用 `listLabel`（客户端功能名来自 `FEATURE_DATA`）。总览 `prd/INDEX.md`、`prd/VERSIONS.md`、`prd/PROJECT_OVERVIEW.md` 只出现在列表，不是关系图节点。

目录按业务域、运营后台及总览与规范分组。正文为居中阅读栏，右侧章节目录跟随阅读位置；≤980px 时文档目录和章节目录为抽屉。搜索结果显示在左栏，可返回完整目录。隐藏的旧版面板不占据正文空间。

**打开**：`fetch` 站点根 Markdown，页内渲染。支持 hash / 标题滚动。功能 PRD 可列 `history/` 目录（静态站目录列表），changelog 标非现行。

文档和旧版目录请求各自校验请求序号，迟到响应不能覆盖新页面；清空/替换搜索词后，旧检索结果不得重新出现。文档内相对链接改写为站点根路径。原文定位优先 hash，失效时可用标题回退；检索词优先在对应章节高亮。用户开始滚动或选择新目标后，不再执行旧定位的延迟重试。后台章节的「查看关系」必须进入客户端 ↔ 后台视图并选中对应节点。

**搜索**：`ensureIndex` 把清单内文档拉到浏览器，按标题/正文/路径子串匹配；结果 ≤20。该次搜索**不请求** `/api/kb`。  
特例（验收 AC11，写在代码里）：查询恰好「官方房置顶」时，可命中 `prd/design/room-list/PRD.md` 中的「官方房临时置顶」。不要当随机模糊搜索去推广。
当前原文直接使用「官方房置顶」时按原词高亮；只有正文确实包含旧称才使用旧称高亮。

后台 `admin/PRD.md` 命中优先带章节 `anchor` 或 `headingLevel ≥ 2` 的块。

## 6. 查 bug 优先点

1. **NO_KB_API_GRAPH**：不要让 `app.js` / `kb.js` 去打 `/api/kb`（重建、热度、ask 都不属于本功能）。
2. **路径**：文档必须从站点根 `/prd/...` 取，不要用相对 `../` 绑死在 `/feature-interaction/` 子目录。
3. **搜索 ≠ 向量**：结果 path 来自 manifest 扫描的 Markdown，不要改成 `chunk_id`。
4. **history / changelog**：默认清单排除；旧版只从功能页「查看旧版」进入。
5. **四 Tab 顺序与文案**：2026-10-03 用户明确改为问答优先，按 §2 的顺序回归；标签内允许装饰图标。
6. **AC11 特例**：删掉「官方房置顶 → 官方房临时置顶」会让既有验收失败；若改匹配规则，先改 PRD/STEP。

## 7. 回归锚点

| 文件 | 覆盖 |
|---|---|
| `site/kb-api/tests/test_site_contract.py` | 四 Tab 文案与顺序、`#kbWorkspace` |
| `site/kb-api/tests/test_auth_m2.py` | 关系图视图静态、登录墙不挡图谱 |
| `site/feature-interaction/tests/kb-navigation.test.cjs` | 旧文档失败、同路径响应乱序、清空搜索期间索引完成 |
| `site/docs/design/h5-kb/steps-verified.md` | L1/L2 完成标志与 AC11 |

阅读器的请求时序由 Node 测试覆盖；改阅读器时仍需用浏览器验证列表、PRD、搜索高亮、目录定位、关系回跳和小屏抽屉。外部索引服务隔离属于既有验收项，本次结构增量未重测停服场景。
