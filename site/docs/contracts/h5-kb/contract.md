# H5 关系图与文档索引 · 实现契约

> 现行实现合同。给改工作台关系图两视图、文档索引与核心文档发布的人与 AI 用。
> 需求仍以 [`../../design/h5-kb/PRD-H5知识库-v1.md`](../../design/h5-kb/PRD-H5知识库-v1.md) 为准（本期 L1+L2；附录 L3 **不是**本契约，问答见 [`../kb-qa/contract.md`](../kb-qa/contract.md)）。  
> 主题换皮见 [`../h5-theme/contract.md`](../h5-theme/contract.md)。本模块不新增鉴权。页面结构更新：2026-10-03，用户明确要求问答优先、统一图标并优化其余三页（对照本地运行页面）。

> 2026-10-04 迁移契约同步：核心文档的物理位置、逻辑路径及受控发布规则见 §8；后端扫描保护见 [问答契约 §4](../kb-qa/contract.md#4-api-终态)，登录门与证书隔离见 [账号契约 §7](../kb-auth/contract.md#7-tls-与-compose)。生产未部署，验证范围见[迁移执行记录](../../design/core-docs-migration/execution/核心文档迁移开发执行记录.md)。

## 1. 怎么用

| 你要做的事 | 读 |
|---|---|
| 改四个 Tab / 切视图 | §3、`index.html`、`app.js` `setView` |
| 改关系图节点/边 | §4、`data.js` `FEATURE_DATA` |
| 改文档列表 / 打开 / 搜索 | §5、`kb.js` |
| 改文档源 / 发布清单 / 本地刷新 | §8、`site/scripts/build_site.py`、`site/preview.sh` |
| 查误打问答 API、搜崩向量 | §6 |
| 对照回归 | §7 |

权威正文的唯一物理位置是 `site/core-docs/prd/design/<id>/PRD.md`。H5 只展示与检索，不另建第二套知识正文。不要把本站写进 `site/core-docs/prd/design/`。

## 2. 落地符号

| 名 | 值 |
|---|---|
| 工作台 | `/feature-interaction/` |
| 四 Tab 有序 | 知识问答 `qa`、客户端 ↔ 后台 `admin`、客户端交叉 `client`、文档索引 `kb` |
| 落地视图 | `app.js` `bootLanding` → `setView("qa")`（关系图不是默认页） |
| 图谱数据 | `window.FEATURE_DATA`（`data.js`） |
| 文档清单 | `GET /prd/llm-manifest.json` 的 `scan_roots`（发布器投影后的逻辑路径；排除 changelog、`/history/`） |
| 打开文档 | 站点根绝对路径 `"/" + docPath`，例如 `/prd/design/vip/PRD.md` |
| 搜索上限 | `MAX_RESULTS = 20`；浏览器内建索引，**不是** Qdrant `chunk_id` |
| 对外 API | `app.js` / `kb.js` **不含** `"/api/kb"` |
| 默认打开 | 文档索引进入时若无当前路径 → `prd/INDEX.md` |

代码锚点：`site/feature-interaction/{index.html,app.js,data.js,kb.js,ui-icons.js,workbench.css}`，`site/core-docs/prd/llm-manifest.json`（源码清单），`site/scripts/build_site.py`（生成浏览器清单）。

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

**打开**：`fetch` 站点根 Markdown，页内渲染。支持 hash / 标题滚动。功能 PRD 通过发布时生成的 `/prd/design/<id>/history/index.json` 的 `files` 列表打开旧版，禁止依赖目录列表；changelog 标非现行。

历史 JSON 格式为 `{ "files": ["prd/design/<id>/history/<文件名>.md", ...] }`，不带前导斜线。阅读器只接受当前功能历史目录的直接 Markdown 文件，拒绝越界路径、隐藏名和其他后缀，并去重；空数组显示无旧版，格式错误或加载失败显示原因。切换正文后，迟到的历史响应不能覆盖当前页面。

文档和旧版目录请求各自校验请求序号，迟到响应不能覆盖新页面；清空/替换搜索词后，旧检索结果不得重新出现。文档内相对链接改写为站点根路径。浏览器 manifest 的 `published_paths` 限定可跳转的产品文档；工作区、工程文档、未发布归档等链接移除跳转并显示“未发布”，本地原文引用不删。原文定位优先 hash，失效时可用标题回退；检索词优先在对应章节高亮。用户开始滚动或选择新目标后，不再执行旧定位的延迟重试。后台章节的「查看关系」必须进入客户端 ↔ 后台视图并选中对应节点。

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
| `site/feature-interaction/tests/kb-navigation.test.cjs` | 旧文档失败、同路径响应乱序、清空搜索期间索引完成、历史 JSON 越界过滤/迟到响应、未发布链接 |
| `site/kb-api/tests/test_publication.py` | 发布清单、浏览器 manifest 投影、历史 JSON、私有文件排除、生成失败保留旧产物、拒绝越界与符号链接 |
| `site/docs/design/h5-kb/steps-verified.md` | L1/L2 完成标志与 AC11 |

阅读器的请求时序由 Node 测试覆盖；改阅读器时仍需用浏览器验证列表、PRD、搜索高亮、目录定位、关系回跳和小屏抽屉。外部索引服务隔离属于既有验收项，本次结构增量未重测停服场景。

## 8. 核心文档与受控发布

### 8.1 唯一源与路径映射

`site/core-docs/` 是网站业务文档的分类父目录，当前分类为 `prd/`。原根 `prd/` 已一次性迁移，不保留副本、软链接或双向同步；今后只维护 `site/core-docs/prd/`。各功能 `PRD.md` 仍是产品规则权威，brief 是派生检索说明。网站工程需求与实现契约仍归 `site/docs/`。

| 用途 | 路径口径 |
|---|---|
| 仓库物理位置 / 源码 manifest / brief 的 `source` | 以仓库根为基准，`site/core-docs/prd/...` |
| API 文档根 | `CORE_DOCS_ROOT`，本机默认 `site/core-docs`，Compose 挂载为 `/core-docs`；不指向 `prd` 子目录 |
| 浏览器 manifest / 知识块 / 既有问答引用 | 稳定逻辑路径 `prd/...`，不跟随物理迁移加上 `site/core-docs/` |
| 浏览器请求 | `/prd/...` |
| 生成产物 | `site/release/www/prd/...`，不是第二份权威，不人工编辑或反向覆盖源文档 |

仓库层和产品层的机器路由不等于 Web 发布清单。新增 Markdown 分类与 `prd/` 并列，但本轮扫描器与发布器仅处理 PRD；新增分类须另行明确扫描与发布策略，不能因在 `core-docs` 下就自动公开。

### 8.2 发布选择与清单

发布入口为 `site/scripts/build_site.py`，输出 `site/release/www`。只选择以下文件，不整目录复制仓库、`site` 或 `core-docs`：

| 来源 | 选择规则 / 输出 |
|---|---|
| `site/docker/publish-files.json` 的 `static_files` | 逐文件的仓库源路径 → Web 相对路径；新增页面、脚本、CSS 必须显式登记 |
| 产品 manifest 的 `scan_roots` | 只接受 `site/core-docs/prd/` 下的大写总览 Markdown、`inbox/INDEX.md` 及 `design/<id>/PRD.md`；不得用它开放其他目录 |
| 已登记功能的配套文档 | `brief/current.md`、`changelog.md` 必须存在并发布 |
| 已登记功能的图片 | `images/` 下递归选择 `.png/.jpeg/.jpg/.gif/.webp`，不复制其他后缀 |
| 已登记功能的历史 | `history/*.md` 直接文件，以及生成的 `history/index.json`；不发布历史目录中的任意附件或子目录 |
| 浏览器 manifest | 生成 `/prd/llm-manifest.json`：`scan_roots` 和 `documents[].path` 去掉物理前缀 `site/core-docs/`，移除 `exclude_roots`，增加全部输出文件的 `published_paths`；`documents[].path` 必须指向已选文件 |

明确保留的非 PRD 页面也须服从逐文件清单：运营后台原型的五个文件映射为 `/admin-skin-demo/...`；`reviews/referral/summary/index.html` 与 `reviews/getnew/summary/index.html` 保留原 URL。它们不是整棵工作区或复盘目录的开放授权，也不成为问答语料。其他工作区、工程文档、归档、inbox 条目、测试、后端源码、配置和证书包不默认发布。

所选源文件须存在且位于仓库内；发布器拒绝绝对路径、`..`、隐藏路径段、符号链接及重复复制目标。清单校验或复制失败时不替换现有 Web 目录。完整临时目录生成后才整体切换；遗留 `.www-previous` 或非发布器管理的已有目录会阻止覆盖，须先检查恢复状态。`site/release/publish-report.json` 保存文件数、功能数与 SHA-256，报告和发布器标记位于 Web 根之外。

`published_paths` 用于阅读器的本地引用提示，真正的访问边界是受控 Web 根与 Nginx。只隐藏目录列表或前端链接不能阻止猜路径取文件。未发布的本地引用按 §5 显示“未发布”；外部 URL、页内锚点保留原处理方式。

### 8.3 本地刷新与验证边界

- 在仓库根执行 `sh site/preview.sh`：先生成产物，再构建并等待 API，最后强制重建 Web 容器。生成失败时不继续刷新服务。
- 仅文档/前端更新且 API 镜像已包含迁移代码时，可用 `sh site/preview.sh --no-build`。发布器整体替换目录后，单纯重启或沿用旧 Web 容器不能代替重新创建 bind mount。
- 文档只改权威源，静态资源只改源码及逐文件清单；不通过手改 `release/www` 维护网站。数据与 TLS 命名卷沿用，目录挂载和角色边界见 [账号契约 §7](../kb-auth/contract.md#7-tls-与-compose)。
- 本地静态验证、HTTP/角色矩阵与 Chrome 页面证据见[迁移执行记录](../../design/core-docs-migration/execution/核心文档迁移开发执行记录.md)。本地已切换不代表生产已修复；上线包与回退步骤仍属未执行的步骤 6。
