---
title: "Hayyo H5 知识库 STEP 验证版"
status: "verified"
stage_result: "PASS_WITH_RISKS"
prd: "site/docs/design/h5-kb/PRD-H5知识库-v1.md"
prd_sha256: "2a7df930765a8a70138fa093cc236be2101a78c30fff0c776225db375212e8dc"
created: "2026-08-26"
source_draft: "site/docs/design/h5-kb/steps-draft.md"
audit: "site/docs/design/h5-kb/step-audit.md"
user_decisions: "UD-AC11、UD-VIEW-GRAPH、UD-HISTORY（2026-08-26）"
note: "step-doc-review review-repair 完整复审后的验证版。原文 steps-draft.md 未覆盖。业务代码仍为 NOT_STARTED。"
---

# Hayyo H5 知识库 STEP 验证版

## 来源摘要

| source_id | 路径 | 状态 | SHA-256 | 本轮核实 |
|---|---|---|---|---|
| SRC-PRD | `site/docs/design/h5-kb/PRD-H5知识库-v1.md` | `existing` | `2a7df930765a8a70138fa093cc236be2101a78c30fff0c776225db375212e8dc` | 全文阅读 v1.1 |
| SRC-H5-HTML | `site/feature-interaction/index.html` | `existing` | `11de7fe163bf1f3865a01cfc36dcc1efe40cd022362c90b8216671bfbf92a068` | 两 Tab：`data-view` = `admin` \| `client` |
| SRC-H5-APP | `site/feature-interaction/app.js` | `existing` | `282fc10aa0a03483d6b81c6664defcb4b95768ef3db80741438d6090a17665f8` | `visibleIds`、`prd-link`、切 Tab 清空选中 |
| SRC-H5-DATA | `site/feature-interaction/data.js` | `existing` | `3b21b3a5fe72cec0a250eae622acc1cb319d5338f070f255a6cb5b2107ce333c` | `FEATURE_DATA`；拉新后台现状 `#admin-referral` |
| SRC-H5-CSS | `site/feature-interaction/style.css` | `existing` | `d81e2f731f9e694dddd302f6e536db890b6713dc472ca03ee434e82c4178eb15` | `.workspace` 为 `220px 1fr 320px`；`body { overflow: hidden }` |
| SRC-MANIFEST | `prd/llm-manifest.json` | `existing` | `ed303df22fe50cd9f1167d31e890a2523d676e8fa774a240d8c97db5b5e411be` | `scan_roots` 27 条；不含 changelog |
| SRC-INDEX | `prd/INDEX.md` | `existing` | `67391d1cfbed42f39b82d116328596dedcd6d2354dd7512070b21c4f9008f595` | 默认入口；排除 history/archive/demo/垃圾桶 |
| SRC-ADMIN | `prd/design/admin/PRD.md` | `existing` | — | 锚点 `admin-rooms` 第 1204 行；`admin-referral-v130` 第 3643 行 |
| SRC-VIP | `prd/design/vip/PRD.md` | `existing` | — | 正文含「保级」；引用 17 张 `images/` |
| SRC-ROOMLIST | `prd/design/room-list/PRD.md` | `existing` | — | 标题为「房间列表官方房临时置顶」 |
| SRC-REFERRAL | `prd/design/referral/PRD.md` | `existing` | — | 正文含「补绑」；文首含后文覆盖说明 |

事实标签只用：`USER_DECISION`、`PRD`、`CONTRACT`、`REPO_BASELINE`、`RUNTIME`、`PLANNED`、`UNVERIFIED`。本轮无 `RUNTIME`。仓库根无 `package.json`（`REPO_BASELINE`）。无 Markdown 渲染依赖（`REPO_BASELINE`）。

## 输入清单

### 本期有效需求

F1–F16（L1/L2）。优先级沿用 PRD 的 P0/P1，不另造排期。F15 虽标 P1，但 F9/F10/F11/F16 依赖内存索引，STEP 依赖边以真实前置为准，不改写 PRD 优先级字段。

### 本期有效验收

AC1、AC2、AC3、AC4、AC4b、AC5、AC6、AC7、AC8、AC9、AC9b、AC10、AC11、AC12、AC13、AC14、AC15、AC16、AC16b、AC16c。

### 未编号约束（CSTR）

| ID | 摘要 | 来源 |
|---|---|---|
| CSTR-001 | H5 只展示/检索，权威仍是各功能 `PRD.md` | C5；§4.5 |
| CSTR-002 | 功能目录不重切；不把 PRD 拆成独立维护的 JSON 知识条 | C4；G3 |
| CSTR-003 | 同站点分视图；不在 SVG 上渲染长文 | C6 |
| CSTR-004 | 关系图两个视图保持可切回 | §4.2 |
| CSTR-005 | 总览只出现在知识库列表，不做成关系图节点 | §4.2；T4 |
| CSTR-006 | changelog 不进知识库首页，仅阅读器次级入口 | §4.2；F12 |
| CSTR-007 | 顶栏展示文首已有信息（功能 ID、合并版本、文档更新日） | §4.2 |
| CSTR-008 | 提示「后文覆盖同主题前文」；不按 `### V*` 只显示最后一节 | §4.2；R2；§4.5 |
| CSTR-009 | 文首「更新」日是入库日；不做上线/下线硬字段 | §4.2；§4.5 |
| CSTR-010 | 不提交搜索索引文件；不把生成脚本写成必用路径 | C12；T1 |
| CSTR-011 | 关系图顶栏继续只搜节点名/ID；正文检索只在知识库 | §4.3；AC16b |
| CSTR-012 | 搜索最多 20 条，超出提示收窄 | §4.3；AC16c |
| CSTR-013 | 静态根为仓库根；`file://` 无服务直开不作为本期能力 | §4.5；§9.1 |
| CSTR-014 | Markdown 可本地 vendor 或等价；不强制框架、不强制 npm 构建 | T1；T4 |
| CSTR-015 | 从节点打开文档时保留图上选中；现有切关系图 Tab 清空选中不应用到该路径 | T1；F2 |
| CSTR-016 | 渲染 md 时禁止执行文档内脚本 | T6；E5 |
| CSTR-017 | 默认可读范围与 `scan_roots` 一致：三份总览 + 24 份当前 `PRD.md` | §6.1；SRC-MANIFEST |
| CSTR-018 | `data.js` 不复制正文、不加总览节点；仅改拉新后台锚点 | T4；C11 |
| CSTR-019 | `prd/design/*/PRD.md` 本期默认零改动；不改 `llm-manifest.json` 权威列表 | T4 |
| CSTR-020 | 无账号、不按角色切换界面 | §3 |
| CSTR-021 | L1 长文整文件滚动，不分页 | E3；AC6 |
| CSTR-022 | 回滚去掉知识库/阅读器代码，不靠删 `PRD.md`；`data.js` 锚点随 H5 回滚还原 | T5 |
| CSTR-023 | L1/L2 无必须日志 | T6 |
| CSTR-024 | 本期无模型密钥 | T6 |
| CSTR-025 | 本产品默认内网/本机，不当公开站点 | T6 |

### 决策

C1–C12 均已确认。C1 为 PRD 写法，无开发 STEP。C7/C8 约束 L1→L2 依赖。

### 用户补充决定（`USER_DECISION`，2026-08-26）

| ID | 决定 | 落点 |
|---|---|---|
| UD-AC11 | 搜索「官方房置顶」通过条件：最终打开 `prd/design/room-list/PRD.md`；该文档标题或正文含「官方房临时置顶」即视为命中，不要求连续子串「官方房置顶」。只打开 INDEX 不算通过。不得改权威 `room-list/PRD.md` 凑字。 | STEP-013、STEP-014 |
| UD-VIEW-GRAPH | 正在阅读 INDEX / VERSIONS / PROJECT_OVERVIEW，或从列表打开且无 `#锚点` 的 `admin/PRD.md` 时，「查看关系」可切回关系图，不选中任何节点、不新增节点。能对应 `data.js` 功能 ID 的文档仍按 AC16 选中。 | STEP-018 |
| UD-HISTORY | 「查看旧版逻辑」进入该功能 `history/` 后，在阅读器列出该目录下文件，点哪个打开哪个。未点入口前不请求 `history/`。 | STEP-011 |

### 排除项 / 本期不做

| ID | 项 | 来源 |
|---|---|---|
| OUT-1 | 把 H5 或 `data.js` 写成新权威 | §4.5 |
| OUT-2 | 为 H5 重切功能目录 / 拆 JSON 知识条 | §4.5；C4 |
| OUT-3 | 玩家帮助中心 / 运营 CMS | §4.5 |
| OUT-4 | 在线编辑 PRD、评论、权限账号 | §4.5 |
| OUT-5 | 用检索或问答结果自动改写或合并 PRD | §4.5 |
| OUT-6 | 修复文档内部规则冲突 | §4.5 |
| OUT-7 | `file://` 无服务直开 | §4.5 |
| OUT-8 | 本期 L3 问答（F17–F24、AC17–AC21、R6、E7–E9、附录 A） | §4.4；G6 |
| OUT-9 | 自动只渲染最后一个版本节 | §4.5 |
| OUT-10 | 把真实上线/下线时间做成硬标签 | §4.5 |
| OUT-11 | 提交 `search-index.json`（v1 已废止） | C12；§10 |
| OUT-12 | 新增关系图节点/边 | C11 |
| OUT-13 | 编造性能秒级门槛 | §8 开首 |
| OUT-14 | 建议补充的手工查询词（财富值、水果机、门票、YallaPay、封禁）作正式门槛 | §8.2 |
| OUT-15 | 把本 H5 当公开站点发布 | T6；CSTR-025 |

### 技术债（PRD T7，本期不实施、不新编号）

T7 六条均为 PRD 明示技术债。不分配新的 `TD-*`（PRD 未给 TD 编号）。不另开修复 STEP。

| PRD T7 项 | 处置 | 落点 |
|---|---|---|
| PRD 仍是 Word 表结构 | 本期接受；L1 原样渲染，不当功能失败 | STEP-003；E5 |
| 版本叠写 | 本期接受；顶栏提示；检索结果带版本标题 | STEP-005、STEP-013 |
| `infra` 为跨模块桶 | 当普通功能打开；不在 H5 重切 | STEP-002；CSTR-002 |
| 详情链到裸 md | 本期按 L1 实施站内打开 | STEP-007 |
| 无结构化上线/下线时间 | 本期不做硬字段 | STEP-005；CSTR-009 |
| 图上缺部分 admin 文内锚点 | 不补全量节点；目录与文内链接到达 | STEP-009、STEP-010、STEP-015；OUT-12 |

## 功能清单

本期只实施 L1 阅读器 + L2 文档站。L3 不进入任何 STEP 的开发任务。

## STEP 总览

| STEP | 标题 | 需求 | 验收 | 前置 | 优先级（PRD 原值） |
|---|---|---|---|---|---|
| STEP-001 | 知识库第三视图入口 | F1、C6、C9 | AC1 | 无 | P0 |
| STEP-002 | 默认可读文档列表 | F1、CSTR-005/006/017 | AC1 | STEP-001 | P0 |
| STEP-003 | Markdown 页内渲染 | F3、CSTR-014/016/021 | AC1、AC2、AC3、AC6 | STEP-001、STEP-002 | P0 |
| STEP-004 | 按文档加载图片 | F6 | AC3、AC8 | STEP-003 | P1 |
| STEP-005 | 文首元数据与覆盖提示 | R2、R5、CSTR-007/008/009 | —（无独立 AC，完成标志按 §4.2 可观察） | STEP-003 | P0 范围 |
| STEP-006 | 失败与启动说明 | F7 | AC7 | STEP-001 | P0 |
| STEP-007 | 从节点打开文档并保留选中 | F2、CSTR-015 | AC2、AC4 | STEP-001、STEP-003、STEP-006 | P0 |
| STEP-008 | 拉新后台锚点改写 | F2、C11 | AC4b | STEP-007 | P0 |
| STEP-009 | 本文目录 | F4 | AC5 | STEP-003 | P0 |
| STEP-010 | 站内文档跳转 | F5 | AC9 | STEP-003、STEP-007 | P1 |
| STEP-011 | 旧版逻辑显式入口 | F8、C10、UD-HISTORY | AC9b | STEP-003 | P0 |
| STEP-012 | 内存搜索索引 | F11、F15、C12 | AC13 | STEP-002 | P1（检索前置） |
| STEP-013 | 知识库关键词检索 | F9、CSTR-011/012、UD-AC11 | AC10、AC11、AC12、AC16b、AC16c | STEP-012 | P0 |
| STEP-014 | 结果定位与高亮 | F10、UD-AC11 | AC10、AC11 | STEP-013、STEP-007 | P0 |
| STEP-015 | 后台按章节命中 | F16 | —（无独立 AC；完成标志用 admin 已有锚点） | STEP-013、STEP-014 | P0 |
| STEP-016 | changelog / 发版入口 | F12 | AC14 | STEP-003、STEP-007 | P1 |
| STEP-017 | 当前文档图集 | F13 | AC15 | STEP-003、STEP-004 | P1 |
| STEP-018 | 文档与关系图互跳 | F14、UD-VIEW-GRAPH | AC16 | STEP-001、STEP-007 | P1 |

## 需求映射

| ID | 映射 STEP | 映射方式 |
|---|---|---|
| F1 | STEP-001、STEP-002、STEP-003 | Tab + 列表 + 从列表打开阅读 |
| F2 | STEP-007、STEP-008 | 直接：打开路径；C11 锚点 |
| F3 | STEP-003、STEP-004 | 标题/表格/列表/链接在 STEP-003；图片请求在 STEP-004 |
| F4 | STEP-009 | 直接 |
| F5 | STEP-010 | 直接 |
| F6 | STEP-004 | 直接 |
| F7 | STEP-006 | 直接 |
| F8 | STEP-011 | 直接 |
| F9 | STEP-013 | 直接 |
| F10 | STEP-014 | 直接 |
| F11 | STEP-012 | 直接（建索引时排除） |
| F12 | STEP-016 | 直接 |
| F13 | STEP-017 | 直接 |
| F14 | STEP-018 | 直接 |
| UD-AC11 | STEP-013、STEP-014 | 用户决定 |
| UD-VIEW-GRAPH | STEP-018 | 用户决定 |
| UD-HISTORY | STEP-011 | 用户决定 |
| F15 | STEP-012 | 直接 |
| F16 | STEP-015 | 直接 |
| C1 | （无开发 STEP） | PRD 已按 L1/L2/L3 成文 |
| C2–C5、CSTR-001/002 | 全部阅读/检索 STEP 的「不做」 | 约束 |
| C6、C9 | STEP-001 | 直接 |
| C7、C8 | 依赖边 STEP-001…011 → STEP-012…018 | 顺序 |
| C10 | STEP-011 | 直接 |
| C11 | STEP-008 | 直接 |
| C12 | STEP-012 | 直接 |
| CSTR-023、CSTR-024、CSTR-025 | 全部 STEP 的「不做」 | 无必须日志；无模型密钥；不当公开站点 |
| R1 | 全部阅读 STEP 的「不做」 | 约束 |
| R2 | STEP-005、STEP-013 | 提示；结果带版本标题 |
| R3 | STEP-002、STEP-012 | 默认排除 |
| R4 | STEP-012 | 索引非权威 |
| R5 | STEP-005 | 版本非导航主轴 |
| R6 | 无 | OUT-8 |
| G1 | CSTR-001 | 分层浏览，H5 非权威 |
| G2 | 本文 L1/L2 STEP 范围；L3 为 OUT-8 | 改动范围成文 |
| G3 | CSTR-002 | 功能目录不重切 |
| G4 | STEP-003、STEP-007 | 本期目标 |
| G5 | STEP-013、STEP-014 | 本期目标 |
| G6 | 无 | OUT-8 |
| E1、E2 | STEP-006 | 直接 |
| E3 | STEP-003、STEP-009 | 长文滚动 + 目录 |
| E4 | STEP-004 | 裂图 |
| E5 | STEP-003 | 有限 HTML、禁脚本 |
| E6 | STEP-013 | 结果带版本标题 |
| E10 | STEP-012 | 部分 fetch 失败 |

## 验收映射

| AC | 映射 STEP | 对象比较方法 |
|---|---|---|
| AC1 | STEP-001、STEP-002、STEP-003 | 列表项路径集合 = `scan_roots` 的 27 条路径（比较路径字符串，不比数量）；点击列表某一路径后打开的文档身份等于该项路径 |
| AC2 | STEP-003、STEP-007 | 打开文档身份为 `prd/design/referral/PRD.md`；可见的是渲染后的标题/段落，不是 md 源码墙 |
| AC3 | STEP-003、STEP-004 | 文档身份 `prd/design/vip/PRD.md`；文中 `images/v1.0.0-vip-*.png` 请求 URL 相对该文档；表格节点可见 |
| AC4 | STEP-007 | 文档身份 `prd/design/admin/PRD.md`；视口内出现 `id="admin-rooms"` 或其后标题「管理房间」 |
| AC4b | STEP-008 | 文档身份同上；视口内出现 `id="admin-referral-v130"`；`data.js` 中该节点 `prd` 字段以 `#admin-referral-v130` 结尾 |
| AC5 | STEP-009 | 点击目录项后，对应标题元素进入视口 |
| AC6 | STEP-003 | `admin/PRD.md` 全文可连续滚动到文末；不设秒级门槛 |
| AC7 | STEP-006 | 失败态同时包含：原因说明、失败路径原文、仓库根启动示例；页面不是无正文的空白 |
| AC8 | STEP-004 | 打开 `user-level` 时，网络请求 URL 集合不含 `casual-game/images` |
| AC9 | STEP-010 | 点击的是 `referral/PRD.md` 内指向 `admin/PRD.md` 的相对链接；仍在阅读器内打开，目标文档身份为 `admin/PRD.md` |
| AC9b | STEP-011 | 未点击前请求 URL 不含该功能 `history/`；点击入口后列表路径集合 = 该功能 `history/` 目录下现有文件路径（比路径多重集）；再点其中一项则打开路径等于该项 |
| AC10 | STEP-013、STEP-014 | 打开文档路径为 `prd/design/vip/PRD.md`；可见块文本含「保级」 |
| AC11 | STEP-013、STEP-014 | 查询「官方房置顶」的结果中含路径 `prd/design/room-list/PRD.md`（该文档标题或正文含「官方房临时置顶」即命中）；点击后打开路径为该文件。只打开 INDEX 不通过 |
| AC12 | STEP-013、STEP-012 | 打开文档路径为 `prd/design/referral/PRD.md`；结果列表每条路径都不含 `/history/`、不以 `changelog.md` 结尾 |
| AC13 | STEP-012 | 索引路径集合是 `scan_roots` 的子集；与 `history`、`prd/archive`、`demo`、`changelog.md`、`docs/` 的交集为空 |
| AC14 | STEP-016 | 打开的文件身份为该功能 `changelog.md`；界面有「非当前规则」标记 |
| AC15 | STEP-017 | `vip`：点击缩略图后原文对应 `![](images/...)` 位置进入视口；`room-list`：无图片文件时图集为空态，不是假缩略图 |
| AC16 | STEP-018 | 当前文档为 `merchant/PRD.md` 时，关系图 `state.selectedId === "merchant"` |
| UD-VIEW-GRAPH | STEP-018 | 总览或无锚点 admin 全文「查看关系」后 `selectedId === null`，且 `data.js` 节点 id 集合不变 |
| AC16b | STEP-013 | 关系图顶栏输入后，不出现文档命中列表；过滤仍只基于节点 `name`/`id`/`admin`/`kind` |
| AC16c | STEP-013 | 命中条数 > 20 时，可见结果条数 = 20，且 20 条路径都属于本次命中集合；同时出现收窄提示 |

---

## 完整 STEP 提示词

### [STEP-001] 知识库第三视图入口

**阶段状态**：`verified`

**目标**：顶栏增加第三 Tab「知识库」，能离开关系图画布进入该视图；两个关系图视图仍可切回。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F1 | 顶栏增加第三 Tab「知识库」 | `PRD` |
| 需求 ID | C6、C9 | 同站点分视图；第三视图「知识库」；不在 SVG 上渲染长文 | `PRD` |
| 验收 ID | AC1 | 打开知识库 Tab，能看到文档列表或从当前节点进入阅读 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| 无 | 现有两 Tab 与 `app.js` 视图状态 | 打开 `/feature-interaction/` 可见「客户端 ↔ 后台」「客户端交叉」 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `site/feature-interaction/index.html` `.tabs` | `existing` | `REPO_BASELINE` | SRC-H5-HTML / 第 16–19 行 | 增加第三 Tab |
| `data-view` = `admin` \| `client` | `existing` | `REPO_BASELINE` | SRC-H5-HTML / 第 17–18 行 | 现有视图值，知识库需新增值 |
| `app.js` 切 Tab 清空 `selectedId` 并复位镜头 | `existing` | `REPO_BASELINE` | SRC-H5-APP / 第 398–410 行 | 本 STEP 保持两关系图 Tab 现有行为 |
| 知识库 Tab 与阅读器 DOM | `planned` | `PLANNED` | 不适用 | 本期新增 |
| Markdown 库名/文件名 | `planned` | `PLANNED` | 不适用 | 不在本 STEP 选定 |

**输入**：

- 现有 `index.html` 顶栏两 Tab、`app.js` 的 `state.view`。

**输出**：

- 第三 Tab「知识库」可点；`data-view` 能切到知识库视图；画布不用于渲染长文；两关系图 Tab 仍可切回。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 知识库视图名称 | 「知识库」 | F1、C9 |
| 关系图视图 | 「客户端 ↔ 后台」「客户端交叉」保持可切回 | CSTR-004 |
| 长文位置 | 不在 SVG 上渲染 | C6 |

**开发任务**：

1. 在顶栏 `.tabs` 增加第三按钮，文案为「知识库」。
2. 切换到该视图时离开关系图画布阅读区；不在 `#graph` SVG 内渲染正文。
3. 切回 `admin` / `client` 时关系图仍可用。两关系图 Tab 之间切换仍按现有逻辑清空选中并复位镜头。

**不在本 STEP 范围内**：

- 文档列表内容身份（STEP-002）。
- Markdown 渲染、检索、从节点打开（后续 STEP）。
- 修改 `data.js` 节点/边。OUT-1～OUT-14、L3。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 本地 HTTP 指向仓库根，打开知识库 Tab | 离开关系图画布；出现知识库视图（列表或阅读区容器） | AC1 |
| 正常 | 从知识库切回「客户端 ↔ 后台」再切「客户端交叉」 | 两关系图视图可切回，SVG 仍渲染节点 | CSTR-004 |
| 边界 | 知识库视图下查看 `#graph` | 长文不在 SVG 内 | C6 |

**完成标志**：

- [ ] 顶栏存在且仅新增文案为「知识库」的第三 Tab
- [ ] 切到知识库后主阅读区不在 SVG 内
- [ ] 两关系图 Tab 可切回且现有清空选中行为仍适用于这两 Tab
- [ ] 未改 `prd/design/*/PRD.md` 与 `llm-manifest.json`

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-002] 默认可读文档列表

**阶段状态**：`verified`

**目标**：知识库列表展示且仅展示 `scan_roots` 中的 27 份默认可读文档；总览不进关系图；changelog 不进首页。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F1 | 能离开关系图画布阅读正文 | `PRD` |
| 验收 ID | AC1 | 能看到文档列表（各功能/后台 PRD.md + INDEX / VERSIONS / PROJECT_OVERVIEW） | `PRD` |
| 约束 | CSTR-005/006/017 | 总览只在列表；changelog 不进首页；范围与 `scan_roots` 一致 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | 知识库视图容器 | 第三 Tab 可进入知识库 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `prd/llm-manifest.json` `scan_roots` | `existing` | `REPO_BASELINE` | SRC-MANIFEST / 第 3–31 行 | 列表身份正列表 |
| `FEATURE_DATA.features` / `adminNodes` | `existing` | `REPO_BASELINE` | SRC-H5-DATA | 确认不把总览加成节点 |

**输入**：

- `scan_roots` 27 条路径；STEP-001 的知识库视图。

**输出**：

- 知识库首页列表项的路径集合与 `scan_roots` 一致。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 默认可读范围 | 三份总览 + 24 份当前 `PRD.md`，与 `scan_roots` 一致 | CSTR-017 |
| 总览 | `prd/INDEX.md`、`prd/VERSIONS.md`、`prd/PROJECT_OVERVIEW.md` 只出现在知识库列表 | CSTR-005 |
| 首页排除 changelog | changelog 不进知识库首页 | CSTR-006 |

**开发任务**：

1. 在知识库视图列出 `scan_roots` 每条路径对应的可打开项。
2. 比较列表身份时用路径字符串集合，不得只数 27 条。
3. 不把三份总览写入 `data.js` 节点。changelog 不出现在该列表。

**不在本 STEP 范围内**：

- 打开后的渲染（STEP-003）。检索索引（STEP-012）。改 manifest。OUT-*。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 打开知识库 Tab | 列表路径集合等于 `scan_roots` 27 条，含 INDEX、VERSIONS、PROJECT_OVERVIEW 与 24 份 PRD | AC1 |
| 异常 | 检查列表 | 无 `changelog.md`、无 `history/` | CSTR-006；R3 |
| 边界 | 检查 `data.js` | 无 INDEX/VERSIONS/PROJECT_OVERVIEW 节点 | CSTR-005 |

**完成标志**：

- [ ] 列表路径集合与 `scan_roots` 逐条一致
- [ ] changelog 不在首页列表
- [ ] `data.js` 未增加总览节点

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-003] Markdown 页内渲染

**阶段状态**：`verified`

**目标**：拉取成功的 Markdown 在页内渲染为标题、表格、列表、链接；长文整页滚动；有限展示 HTML 残留且不执行脚本。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F3 | 渲染标题、表格、列表、链接、图片 | `PRD` |
| 验收 ID | AC1 | 从列表进入阅读时，打开的文档身份等于列表项路径 | `PRD` |
| 验收 ID | AC2 | 渲染 `referral/PRD.md`，不是下载/源码墙 | `PRD` |
| 验收 ID | AC3 | 打开 vip，正文表格可见 | `PRD` |
| 验收 ID | AC6 | admin 长文可完整滚动；不要求秒级性能门槛 | `PRD` |
| 约束 | CSTR-014/016/021 | vendor 或等价；禁脚本；不分页 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | 阅读器 DOM 容器 | 知识库视图存在可挂载正文的区域 |
| STEP-002 | 默认可读列表项及其路径 | 列表路径集合已等于 `scan_roots` |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| 仓库根 `package.json` | `existing`（确认不存在） | `REPO_BASELINE` | 仓库根无该文件 | 不强制 npm 构建 |
| Markdown 渲染实现 | `planned` | `PLANNED` | 不适用 | 本地 vendor 或等价；本 STEP 不预填库名 |
| `prd/design/referral/PRD.md` | `existing` | `REPO_BASELINE` | SRC-REFERRAL | AC2 样例 |
| `prd/design/vip/PRD.md` | `existing` | `REPO_BASELINE` | SRC-VIP | AC3 表格 |
| `prd/design/admin/PRD.md` | `existing` | `REPO_BASELINE` | SRC-ADMIN | AC6 长文 |
| `style.css` `body { overflow: hidden }` | `existing` | `REPO_BASELINE` | SRC-H5-CSS / 第 26–31 行 | 阅读区需可滚动，不得让正文被 body 裁切后无法滚动 |

**输入**：

- 已 fetch 的 Markdown 文本；阅读器容器。

**输出**：

- 页内可见标题、表格、列表、链接；不是源码页；admin 全文可滚到文末。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 渲染对象 | 标题、表格、列表、链接、图片（图片请求见 STEP-004） | F3 |
| 有限 HTML | md 含 Word 残留 `<br>` 等可展示；禁止执行脚本 | E5；CSTR-016 |
| 长文 | L1 整文件进入页面滚动，不分页 | E3；CSTR-021 |
| 不自动只显示最后版本节 | 不按 `### V*` 隐藏旧节 | CSTR-008；OUT-9 |

**开发任务**：

1. 在阅读器容器渲染 Markdown。实现方式按 CSTR-014：本地 vendor 或等价，不强制框架、不强制 npm 构建；库名本 STEP 不预填。
2. 标题、表格、列表、链接可见。脚本（含文档内事件处理）不得执行。
3. 阅读区可滚动完整 admin 正文。不按版本节过滤。
4. 点击知识库列表某一项时，按该项路径 fetch 并在本阅读器渲染；打开后的文档身份必须等于该项路径字符串。

**不在本 STEP 范围内**：

- 图片懒加载与裂图（STEP-004）。目录（STEP-009）。失败文案（STEP-006）。L3。指定某个 npm 包名。采集日志（CSTR-023）。引入模型密钥（CSTR-024）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 点击列表中路径为 `prd/design/referral/PRD.md` 的项 | 打开的文档身份等于该路径；页面不是 md 源码墙 | AC1、AC2 |
| 正常 | 打开 vip | 表格可见 | AC3 |
| 边界 | 打开 admin 全文并滚动 | 可滚到文末；不设 3 秒门槛 | AC6 |
| 异常 | md 含 `<br>` | 有限展示；不执行 `<script>` | E5 |

**完成标志**：

- [ ] AC1：从列表打开的文档路径与列表项路径为同一字符串
- [ ] AC2/AC3/AC6 按上表对象比较通过
- [ ] 无 npm 构建作为必用路径；未执行文档内脚本
- [ ] 未隐藏非最后的 `### V*` 节

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-004] 按文档加载图片

**阶段状态**：`verified`

**目标**：只请求当前打开文档所引用的 `images/`；裂图占位且不中断正文；不预加载其他功能图库。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F3 | 渲染对象含图片（请求范围由 F6 约束） | `PRD` |
| 需求 ID | F6 | 只请求该文档引用的 `images/` | `PRD` |
| 验收 ID | AC3 | vip 文中 `images/` 图能显示 | `PRD` |
| 验收 ID | AC8 | 打开 user-level 不请求 casual-game/images | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-003 | 渲染后的图片节点 | 打开文档后 DOM 中有 img 或等价 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `prd/design/vip/images/` 17 个 png | `existing` | `REPO_BASELINE` | 本轮 `ls` 17 个文件 | AC3 |
| `prd/design/vip/PRD.md` 中 `![](images/v1.0.0-vip-*.png)` | `existing` | `REPO_BASELINE` | SRC-VIP | 相对路径 |
| `prd/design/user-level/images/` | `existing` | `REPO_BASELINE` | 本轮 `ls` 存在文件 | AC8 对照 |
| `prd/design/casual-game/images/` | `existing` | `REPO_BASELINE` | 本轮存在 | AC8 禁止请求 |

**输入**：

- 当前文档路径与文内相对图片路径。

**输出**：

- 仅当前文档引用图的 HTTP 请求；vip 图可见；裂图不打断正文。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 加载范围 | 图按当前打开文档的相对路径加载，不预加载全部功能图片 | §4.2；F6 |
| 裂图 | 占位，不中断正文 | E4 |

**开发任务**：

1. 将 md 相对图片路径解析为相对当前文档的 URL，经仓库根静态服务获取。
2. 打开某功能时不请求其他功能 `images/`。
3. 缺失图片显示占位，正文其余部分仍可读。

**不在本 STEP 范围内**：

- 图集入口（STEP-017）。预打包全部图片。改 PRD 图片文件。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 打开 vip | 文中 `images/` 图能显示 | AC3 |
| 正常 | 打开 user-level，观察请求 | URL 集合不含 `casual-game/images` | AC8 |
| 异常 | 图片文件缺失 | 占位；正文其余仍可见 | E4 |

**完成标志**：

- [ ] AC3 图片可见（文档身份 vip）
- [ ] AC8 请求集合不含 `casual-game/images`
- [ ] 裂图不替换整页为空白

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-005] 文首元数据与覆盖提示

**阶段状态**：`verified`

**目标**：顶栏展示文首已有的功能 ID、合并版本、文档更新日；提示后文覆盖同主题前文；不把更新日当成上线日，不做上线/下线硬字段。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 约束 | CSTR-007/008/009 | 顶栏展示文首已有信息；提示后文覆盖；更新日为入库日 | `PRD` |
| 规则 | R2、R5 | 整篇渲染并提示；版本号只做文首标注，不作为目录或 Tab | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-003 | 已打开并渲染的文档 | 阅读器有正文 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `prd/design/referral/PRD.md` 文首 | `existing` | `REPO_BASELINE` | SRC-REFERRAL / 第 1–3、17 行 | 功能 ID、合并版本、更新日、后文覆盖句 |

**输入**：

- 当前文档文首已有文本（如功能 ID、合并版本、更新行）。

**输出**：

- 阅读器顶栏可见上述已有字段；可见「后文覆盖同主题前文」类提示；无上线/下线硬标签；无版本 Tab。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 顶栏字段 | 功能 ID、合并版本、文档更新日（仅文首已有） | CSTR-007 |
| 覆盖提示 | 「后文覆盖同主题前文」 | CSTR-008；R2 |
| 更新日含义 | 文档入库日，本期不当成功能上线日 | CSTR-009 |
| 版本 | 只做文首标注，不作为目录或 Tab | R5 |

**开发任务**：

1. 从文首已有信息展示功能 ID、合并版本、文档更新日；文首没有的字段不编造。
2. 展示后文覆盖提示。
3. 不新增上线/下线硬字段，不增加版本导航 Tab。

**不在本 STEP 范围内**：

- 只显示最后 `### V*` 节（禁止，OUT-9）。改权威 PRD 文首。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 打开 referral | 顶栏可见功能 ID `referral`、合并版本原文、更新日；有后文覆盖提示 | CSTR-007/008 |
| 边界 | 检查界面 | 无上线/下线硬标签；无版本 Tab | CSTR-009；R5 |

**完成标志**：

- [ ] 顶栏三项均来自文首已有文本，无编造字段
- [ ] 覆盖提示可见
- [ ] 无上线/下线硬字段、无版本 Tab

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-006] 失败与启动说明

**阶段状态**：`verified`

**目标**：未起服务、路径 404、fetch 失败时给出原因、路径和仓库根启动示例，不留下空白假页面。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F7 | 明确失败文案，保留路径，并给出仓库根启动示例 | `PRD` |
| 验收 ID | AC7 | 有失败说明、路径和启动示例，页面不是静默空白 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | 阅读器可发起打开 | 知识库或打开入口存在 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| 启动示例 `python3 -m http.server` | `existing`（PRD 原文） | `PRD` | SRC-PRD / §6.2 | 示例命令，不是唯一允许的服务器 |
| 静态根为仓库根 | `existing`（PRD） | `PRD` | CSTR-013 | fetch `../prd/design/...` |

**输入**：

- fetch 失败原因（`file://`/CORS、404、其他网络失败）；尝试打开的路径。

**输出**：

- 同一失败界面含：原因、路径原文、仓库根启动示例；无假正文。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| E1 | `file://` 或跨源导致 fetch 失败：说明需在仓库根起静态服务，并给出示例命令 | E1 |
| E2 | `prd` 路径失效：停止渲染，提示路径无效，保留路径 | E2 |
| 启动示例 | `python3 -m http.server`（不是唯一允许的服务器） | §6.2 |

**开发任务**：

1. fetch 失败时不渲染假正文。
2. 展示失败原因、所请求路径、仓库根启动示例。
3. 404 时保留节点详情中的路径（若从节点打开）。

**不在本 STEP 范围内**：

- 让 `file://` 可直开（OUT-7）。编造超时秒数。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 异常 | 故意不启动服务或改坏路径后打开文档 | 失败说明 + 路径原文 + 启动示例；非静默空白 | AC7 |
| 异常 | `file://` 打开 | 不渲染假正文；提示需 HTTP | E1 |

**完成标志**：

- [ ] AC7 三项文案均出现在失败态
- [ ] 失败态无伪造的 PRD 正文

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-007] 从节点打开文档并保留选中

**阶段状态**：`verified`

**目标**：选中带 `prd` 的节点并打开时，切到知识库，按 `data.js` 的 `prd` fetch md；含锚点则滚动到该处；保留图上选中。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F2 | 切到知识库，按 `prd` 拉取；含 `#锚点` 则滚动；保留图上选中 | `PRD` |
| 验收 ID | AC2 | 打开「拉新」节点对应文档，渲染 `prd/design/referral/PRD.md` | `PRD` |
| 验收 ID | AC4 | 打开「房间管理」后台节点，落在 `#admin-rooms` 附近 | `PRD` |
| 约束 | CSTR-015 | 现有切关系图 Tab 清空选中，不应用到「从节点打开文档」 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | 知识库视图 | 第三 Tab 存在 |
| STEP-003 | 渲染器 | 能把 md 渲染进阅读器 |
| STEP-006 | 失败态 | 路径失败时有说明 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `prd-link` `target="_blank"` | `existing` | `REPO_BASELINE` | SRC-H5-APP / 第 281–283 行 | 本期改为站内打开 |
| `features[].prd` 拉新 | `existing` | `REPO_BASELINE` | SRC-H5-DATA / 第 23 行 `../prd/design/referral/PRD.md` | AC2 |
| `adminNodes` 房间管理 | `existing` | `REPO_BASELINE` | SRC-H5-DATA / 第 33 行 `#admin-rooms` | AC4 |
| `id="admin-rooms"` | `existing` | `REPO_BASELINE` | SRC-ADMIN / 第 1204 行 | 滚动手标 |
| 切 Tab 清空选中 | `existing` | `REPO_BASELINE` | SRC-H5-APP / 第 398–410 行 | 不得套用到本路径 |

**输入**：

- 当前选中节点的 `prd` 字符串（路径，可选 `#锚点`）。

**输出**：

- 知识库打开对应 md；锚点进入视口；`selectedId` 仍为该节点。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 客户端节点 | 打开对应功能 `PRD.md` | F2 |
| 后台节点 | 打开 `prd/design/admin/PRD.md` 上该节点 `prd` 所带锚点 | F2 |
| 保留选中 | 从图打开文档时切到知识库，并保留图上选中 | F2；CSTR-015 |

**开发任务**：

1. 将详情「打开 PRD」从 `target="_blank"` 改为站内打开：切知识库、fetch、渲染。
2. `prd` 含 `#` 时滚动到对应锚点。
3. 本路径不清空 `selectedId`、不复位镜头。两关系图 Tab 互切仍保持原清空行为。

**不在本 STEP 范围内**：

- 修改拉新后台锚点（STEP-008）。站内 md 链接（STEP-010）。新增节点（OUT-12）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 选中「拉新」并打开 | 文档身份 `prd/design/referral/PRD.md`；站内渲染；选中仍为 `referral` | AC2 |
| 正常 | 选中「房间管理」并打开 | 文档身份 `admin/PRD.md`；`id="admin-rooms"` 或其后「管理房间」在视口附近 | AC4 |
| 边界 | 从节点打开后检查 `selectedId` | 仍为打开前节点，镜头未按切 Tab 逻辑复位 | CSTR-015 |

**完成标志**：

- [ ] AC2、AC4 按文档身份与锚点比较通过
- [ ] 从节点打开后选中保留
- [ ] 关系图两 Tab 互切仍清空选中

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-008] 拉新后台锚点改写

**阶段状态**：`verified`

**目标**：将「拉新后台」节点 `prd` 改为 `#admin-referral-v130`；不新增节点/边。打开该节点落到该锚点。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | C11、F2 | 不新增节点/边；现有「拉新后台」的 `prd` 改为 `#admin-referral-v130` | `PRD` |
| 验收 ID | AC4b | 打开「拉新后台」落到 `#admin-referral-v130` 附近 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-007 | 从节点打开与锚点滚动 | AC4 已能落到 `#admin-rooms` |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `admin-referral` 现状 `prd` | `existing` | `REPO_BASELINE` | SRC-H5-DATA / 第 44 行 `#admin-referral` | 本期唯一改动点 |
| `id="admin-referral-v130"` | `existing` | `REPO_BASELINE` | SRC-ADMIN / 第 3643 行 | 目标锚点 |
| `id="admin-referral"` | `existing` | `REPO_BASELINE` | SRC-ADMIN / 第 2874 行 | 不得再作为该节点默认打开目标 |

**输入**：

- 现有 `admin-referral` 节点对象。

**输出**：

- 该节点 `prd` 以 `#admin-referral-v130` 结尾；打开后该锚点在视口附近。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 拉新后台打开目标 | `#admin-referral-v130` | C11 |
| 节点集合 | 不新增节点/边 | C11；OUT-12 |

**开发任务**：

1. 只改 `data.js` 中「拉新后台」的 `prd` 锚点为 `#admin-referral-v130`。
2. 不新增、不删除其他节点或边。
3. 验证打开后落到 V1.3.0 拉新后台锚点。

**不在本 STEP 范围内**：

- 改 `admin/PRD.md` 正文（CSTR-019）。补全其他缺失 admin 锚点节点（T7，另立项）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 打开「拉新后台」 | `data.js` 该条 `prd` 以 `#admin-referral-v130` 结尾；视口内出现该 id | AC4b |
| 边界 | diff `data.js` | 仅该锚点字符串变化（允许空白）；节点/边数量与 id 集合不变 | C11 |

**完成标志**：

- [ ] AC4b 文档身份 + 锚点 id 比较通过
- [ ] 节点与边的 id 集合与改前一致

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-009] 本文目录

**阶段状态**：`verified`

**目标**：由文档 `h1–h3` 生成可点击目录，点击后滚动到对应标题。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F4 | 文档含 `h1–h3` 时生成可点击目录 | `PRD` |
| 验收 ID | AC5 | 点击目录项，滚动到对应标题 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-003 | 已渲染标题 | DOM 中有 h1–h3 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| 渲染后的标题节点 | `planned` | `PLANNED` | 不适用 | 目录数据来源 |
| admin 长文 | `existing` | `REPO_BASELINE` | SRC-ADMIN | E3 目录可用 |

**输入**：

- 当前渲染文档中的 `h1–h3` 文本与顺序。

**输出**：

- 可点击目录；点击后对应标题进入视口。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 目录级别 | `h1–h3` | F4 |
| 版本非目录主轴 | 版本号不作为目录或 Tab | R5 |

**开发任务**：

1. 根据已渲染 `h1–h3` 生成目录。
2. 点击目录项滚动到同一文档中对应标题（比较标题文本或稳定标题 id，不只比目录条数）。
3. 不为版本号另做目录轴。

**不在本 STEP 范围内**：

- 检索结果目录（STEP-014）。把目录做成关系图。PRD 风险里「目录收 h2/h3」是缓解建议，不是另一套级别；实现仍以 F4 的 h1–h3 为准。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 文档已渲染，点击某一目录项 | 对应标题元素进入视口；目录项文本与该标题文本一致 | AC5 |
| 边界 | 打开 admin | 目录可用，长文仍可滚动 | E3；AC6 |

**完成标志**：

- [ ] AC5：所点目录项与滚到的标题为同一标题对象
- [ ] 目录来源为 h1–h3，无版本 Tab

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-010] 站内文档跳转

**阶段状态**：`verified`

**目标**：点击指向其他 `PRD.md` 或 admin 锚点的链接时，仍在知识阅读器打开，不依赖系统默认 md 处理。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F5 | 仍在知识阅读器打开，不依赖系统默认 md 处理 | `PRD` |
| 验收 ID | AC9 | 点击相对链接，仍在阅读器打开目标 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-003 | 链接已渲染 | 正文有 a 元素 |
| STEP-007 | 打开文档 + 锚点滚动 | 阅读器能按路径+锚点打开 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `referral/PRD.md` 关联后台链接 | `existing` | `REPO_BASELINE` | SRC-REFERRAL / 第 13 行 `../admin/PRD.md#admin-referral` | AC9 样例 |

**输入**：

- 用户点击的、指向仓库内 md 的相对链接（可含锚点）。

**输出**：

- 阅读器打开目标文档或锚点；不出现浏览器源码/下载墙作为唯一结果。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 站内目标 | 其他 `PRD.md` 或 admin 锚点 | F5 |

**开发任务**：

1. 拦截阅读器内指向默认可读 md 的相对链接，走阅读器打开。
2. 含锚点则滚动到锚点。
3. 不因此改写权威文档链接文本。

**不在本 STEP 范围内**：

- 打开 `history/`（STEP-011）。外链到非仓库文档的行为 PRD 未写，本 STEP 不发明。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 已打开 referral，点击文内指向 `../admin/PRD.md#admin-referral` 的链接 | 仍在阅读器；文档身份 `prd/design/admin/PRD.md`；锚点附近可见 | AC9 |

**完成标志**：

- [ ] AC9 按目标文档路径 + 锚点比较通过
- [ ] 未用系统默认方式作为唯一打开结果

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-011] 旧版逻辑显式入口

**阶段状态**：`verified`

**目标**：默认不拉取 `history/`；仅「查看旧版逻辑」才打开该功能 `history/`。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F8、C10 | 不自动拉取 `history/`；经「查看旧版逻辑」才打开 | `PRD` |
| 验收 ID | AC9b | 打开该入口进入该功能 `history/`；未操作时不请求 history | `PRD` |
| 决定 | UD-HISTORY | 列出该目录下文件，点哪个打开哪个 | `USER_DECISION` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-003 | 功能 PRD 已打开 | 阅读器显示当前 `PRD.md` |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `prd/design/referral/history/` | `existing` | `REPO_BASELINE` | 本轮存在 V1.0.0/V1.3.1/V1.3.2 | 旧版入口目标 |
| `prd/design/user-level/history/` | `existing` | `REPO_BASELINE` | 本轮存在 | AC9b 前置文档可换成 user-level |

**输入**：

- 当前功能目录；用户是否点击「查看旧版逻辑」。

**输出**：

- 未点击时无 `history/` 请求；点击后列出该功能 `history/` 下文件路径；再点某一项则打开该文件。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 默认文档 | 当前 `PRD.md` | C10 |
| 旧版入口文案 | 「查看旧版逻辑」 | F8 |
| 旧版打开方式 | 列出该功能 `history/` 下文件，点哪个打开哪个 | UD-HISTORY |

**开发任务**：

1. 在功能阅读器提供「查看旧版逻辑」。
2. 仅点击后请求该功能 `history/`，并列出该目录下现有文件（路径集合与目录内文件一致，不编造条目）。
3. 用户点击列表中某一项后，阅读器打开该路径。默认打开路径仍是当前 `PRD.md`。不做成版本对比器或分页器。

**不在本 STEP 范围内**：

- 把 history 纳入默认检索（禁止，F11）。changelog 入口（STEP-016）。不得默认打开「第一份」或「最新一份」（已由 UD-HISTORY 排除）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 已打开 `referral` PRD，点击「查看旧版逻辑」 | 列表路径集合等于 `prd/design/referral/history/` 下现有文件；再点其中一项后打开路径等于该项 | AC9b；UD-HISTORY |
| 异常 | 打开功能后不点该入口 | 请求 URL 不含该功能 `history/` | AC9b |

**完成标志**：

- [ ] 入口文案为「查看旧版逻辑」
- [ ] 未点击前请求集合不含 `history/`
- [ ] 点击后列表路径多重集 = 该功能 `history/` 目录文件；再打开的文档路径等于所点项
- [ ] 默认文档身份仍是当前 `PRD.md`

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-012] 内存搜索索引

**阶段状态**：`verified`

**目标**：进入知识库或首次检索时 fetch 默认可读 md，在浏览器内存建索引；不入库；排除项不进索引；部分失败可降级。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F15、C12 | `fetch` 后内存建索引；会话内可缓存；不入库 | `PRD` |
| 需求 ID | F11 | 排除 `history/`、`archive/`、`demo/`、`docs/`、changelog | `PRD` |
| 验收 ID | AC13 | 扫描范围不含上述路径 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-002 | 默认可读路径集合 | 列表身份已等于 `scan_roots` |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `scan_roots` | `existing` | `REPO_BASELINE` | SRC-MANIFEST / 第 3–31 行 | 正列表 |
| `exclude_roots` | `existing` | `REPO_BASELINE` | SRC-MANIFEST / 第 32–60 行 | 对照；PRD 另排除 `docs/` 与 changelog |
| 索引文件 `search-index.json` | `planned`（确认不提交） | `PRD` | 不适用 | OUT-11 |

**输入**：

- `scan_roots` 路径列表。

**输出**：

- 仅含成功拉取的默认可读文档的内存索引；失败路径跳过并提示。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 索引时机 | 进入知识库或首次检索 | F15 |
| 权威 | 内存索引可丢可重建，不能当需求合同 | R4 |
| 排除 | `history/`、`archive/`、`demo/`、`docs/`、changelog；INDEX 口径另含 `垃圾桶/` | F11；R3 |
| 部分失败 | 已成功拉取的进入索引；失败的跳过并提示；仍可按路径打开单篇 | E10 |

**开发任务**：

1. 只 fetch `scan_roots` 中的文件建内存索引；会话内可缓存。
2. 不提交索引文件，不把生成脚本写成必用路径。
3. 索引路径集合与禁止根交集为空。单篇失败不阻断其他篇。

**不在本 STEP 范围内**：

- 检索 UI 与 20 条限制（STEP-013）。把索引写入 `data.js`。L3 向量。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 构建内存索引后导出路径集合 | 集合 ⊆ `scan_roots`；与 `**/history/**`、`prd/archive`、`demo`、`changelog.md`、`docs/` 交集为空 | AC13 |
| 异常 | 单篇 404 | 其余成功篇在索引中；有失败提示；仍可打开未失败单篇 | E10 |
| 边界 | 检查仓库 | 无新增必用 `search-index.json` 提交物 | C12 |

**完成标志**：

- [ ] AC13 用路径集合比较通过，不只数文件个数
- [ ] 无索引入库文件作为必用产物
- [ ] E10 降级可观察

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-013] 知识库关键词检索

**阶段状态**：`verified`

**目标**：仅在知识库视图按关键词检索功能名、ID、标题、正文；最多 20 条并在超出时提示收窄；关系图顶栏仍只过滤节点。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F9 | 在默认可读范围内搜功能名、ID、标题、正文；最多 20 条 | `PRD` |
| 验收 ID | AC10 | 搜索「保级」能进入 vip 相关标题或正文 | `PRD` |
| 验收 ID | AC11 | 搜索「官方房置顶」能进入 room-list | `PRD` |
| 决定 | UD-AC11 | 标题或正文含「官方房临时置顶」即命中；不要求连续子串「官方房置顶」；只打开 INDEX 不算通过 | `USER_DECISION` |
| 验收 ID | AC12 | 搜索「补绑」进入 referral 当前 PRD；默认结果不来自 changelog/history | `PRD` |
| 验收 ID | AC16b | 关系图顶栏只过滤节点，不出现文档命中列表 | `PRD` |
| 验收 ID | AC16c | 命中超过 20 条时最多展示 20 条并提示收窄 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-012 | 内存索引 | AC13 路径集合已排除归档 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `visibleIds` | `existing` | `REPO_BASELINE` | SRC-H5-APP / 第 57–79 行 | 关系图搜索字段 `name`/`id`/`admin`/`kind` |
| `#search` | `existing` | `REPO_BASELINE` | SRC-H5-HTML / 第 20 行 | 关系图顶栏，不搜正文 |
| `vip/PRD.md`「保级」 | `existing` | `REPO_BASELINE` | SRC-VIP | AC10 |
| `room-list/PRD.md` 标题「房间列表官方房临时置顶」 | `existing` | `REPO_BASELINE` | SRC-ROOMLIST / 第 21 行 | AC11 仓库事实 |
| `prd/INDEX.md`「房间列表官方房置顶」 | `existing` | `REPO_BASELINE` | SRC-INDEX / 第 31 行 | AC11 连续子串实际所在 |
| `referral/PRD.md`「补绑」 | `existing` | `REPO_BASELINE` | SRC-REFERRAL | AC12 |
| 知识库搜索框 | `planned` | `PLANNED` | 不适用 | 仅知识库视图 |

**输入**：

- 知识库关键词；或关系图顶栏关键词（对照）。

**输出**：

- 知识库文档命中列表（≤20）；关系图顶栏无文档列表。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 检索范围 | 功能名、ID、标题、正文；默认可读文档 | F9 |
| 条数 | 默认最多 20 条，超出提示收窄关键词 | CSTR-012 |
| 关系图顶栏 | 只搜节点名/ID（现有 `visibleIds` 字段），不搜正文 | CSTR-011；AC16b |
| 叠写命中 | 结果带版本标题；不自动隐藏旧节 | E6；R2 |

**开发任务**：

1. 仅在知识库视图提供正文检索。
2. 命中列表每条绑定文档路径（及标题/块定位键，供 STEP-014 使用）。超过 20 条只展示 20 条且提示收窄；展示的 20 条必须属于本次命中集合。
3. 不改变关系图 `#search` 的 `visibleIds` 过滤字段。结果带版本标题。不把 changelog/history 作为默认结果。
4. 查询「官方房置顶」时，须把 `prd/design/room-list/PRD.md` 列入命中（UD-AC11）。

**不在本 STEP 范围内**：

- 高亮滚动（STEP-014）。后台优先锚点（STEP-015）。不为其他查询词另行发明模糊算法。L3。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 知识库搜索功能 ID `merchant` 或功能名「币商」 | 结果中存在路径为 `prd/design/merchant/PRD.md` 的条目 | F9 |
| 正常 | 知识库搜索「保级」 | 结果中存在路径为 `prd/design/vip/PRD.md` 的条目（打开与高亮见 STEP-014） | AC10 |
| 正常 | 知识库搜索「补绑」 | 存在路径 `prd/design/referral/PRD.md`；结果路径集合不含 `history/`、不含 `changelog.md` | AC12 |
| 正常 | 关系图顶栏输入与正文相同的词 | 只过滤节点；不出现文档命中列表 | AC16b |
| 边界 | 构造命中 > 20 | 可见结果条数 = 20，且这 20 条路径 ⊆ 命中路径集合；出现收窄提示 | AC16c |
| 边界 | 搜索「官方房置顶」 | 结果路径集合含 `prd/design/room-list/PRD.md`（依据该文档含「官方房临时置顶」）；不含「只打开 INDEX 即通过」 | AC11；UD-AC11 |

**AC11 命中规则（`USER_DECISION` UD-AC11）**：

- 查询词仍是 PRD AC11 的「官方房置顶」。
- 通过条件：结果中存在并打开 `prd/design/room-list/PRD.md`。该文档标题或正文含「官方房临时置顶」即视为命中，不要求连续子串「官方房置顶」。
- 不得把只打开 `prd/INDEX.md` 判为通过。
- 不得修改 `room-list/PRD.md` 凑子串（CSTR-019）。
- 本规则只约束本查询的验收，不把分词/模糊匹配推广为全部检索的未写算法。

**完成标志**：

- [ ] AC10/AC12 结果路径集合断言通过
- [ ] AC16b：关系图顶栏无文档命中列表；过滤字段仍为 name/id/admin/kind
- [ ] AC16c：条数=20 且为命中集合子集 + 收窄提示
- [ ] AC11 / UD-AC11：查询「官方房置顶」的结果含 `prd/design/room-list/PRD.md`

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-014] 结果定位与高亮

**阶段状态**：`verified`

**目标**：点击一条搜索结果后打开文档并滚到命中块，命中可见（高亮）。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F10 | 打开文档并滚到命中块；命中可见 | `PRD` |
| 验收 ID | AC10 | 能进入 vip 相关标题或正文 | `PRD` |
| 验收 ID | AC11 | 能进入 room-list | `PRD` |
| 决定 | UD-AC11 | 点击后打开 `prd/design/room-list/PRD.md` | `USER_DECISION` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-013 | 带路径与块键的结果项 | 点击前结果有稳定定位键 |
| STEP-007 | 打开文档能力 | 阅读器能 fetch+渲染+滚动 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `vip/PRD.md` 含「保级」的段落 | `existing` | `REPO_BASELINE` | SRC-VIP | 命中块 |
| `room-list/PRD.md` | `existing` | `REPO_BASELINE` | SRC-ROOMLIST | AC11 目标文档 |

**输入**：

- 一条结果：文档路径 + 命中块定位键（标题或段落，由 STEP-013 产出）。

**输出**：

- 打开该路径文档；命中块进入视口并高亮。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 点击结果 | 打开文档并滚到命中块；命中可见 | F10 |

**开发任务**：

1. 点击结果走阅读器打开对应路径。
2. 滚动到命中块并高亮。比较打开路径与命中块文本，不只比较「有结果」。
3. 不自动隐藏旧版本节。

**不在本 STEP 范围内**：

- 检索查询本身（STEP-013）。后台优先锚点策略（STEP-015）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 点击「保级」命中 vip 的一条结果 | 打开路径 `prd/design/vip/PRD.md`；视口内文本含「保级」且该块高亮 | AC10 |
| 正常 | 点击指向 room-list 的结果 | 打开路径 `prd/design/room-list/PRD.md` | AC11 |

**完成标志**：

- [ ] AC10：路径 + 可见文本「保级」+ 高亮块为同一命中
- [ ] AC11 / UD-AC11：打开路径为 `prd/design/room-list/PRD.md`

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-015] 后台按章节命中

**阶段状态**：`verified`

**目标**：搜索词落在 admin 时，优先落到已有锚点或标题，而不是每次从文首开始。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F16 | 优先落到已有锚点或标题，而不是每次从文首开始 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-013 | admin 文档在索引中 | 能搜到 admin |
| STEP-014 | 打开并滚动命中块 | 点击结果会滚动 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `<a id="admin-rooms">` | `existing` | `REPO_BASELINE` | SRC-ADMIN / 第 1204 行 | 已有锚点 |
| 其后标题「管理房间」 | `existing` | `REPO_BASELINE` | SRC-ADMIN / 第 1206 行 | 测试用标题原文 |

**输入**：

- 落在 admin 某已有锚点章节的搜索词；本 STEP 用文内已有标题「管理房间」。

**输出**：

- 打开 `admin/PRD.md` 时视口在对应锚点或标题附近，而不是文首。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 后台命中 | 优先落到已有锚点或标题，而不是每次从文首开始 | F16 |

**开发任务**：

1. 对 `admin/PRD.md` 命中使用已有锚点或标题作为定位键。
2. 点击该结果后滚动到该键，而不是停留在文件开头。
3. 不新增 `data.js` 节点去补全图上未画的锚点（T7 另立项）。

**不在本 STEP 范围内**：

- 关系图补节点。L3 chunk。PRD 未指定的其他排序权重。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 知识库搜索「管理房间」，点击指向 admin 该章节的结果 | 文档身份 `prd/design/admin/PRD.md`；`id="admin-rooms"` 或标题「管理房间」在视口内；文首主标题不作为该次定位目标 | F16 |
| 边界 | 同一词若也命中其他功能 | 不把非 admin 文档改写成 admin；本断言只约束 admin 那条结果 | F16 |

**完成标志**：

- [ ] admin 命中结果的定位键是已有锚点或标题，不是文首
- [ ] 点击后目标锚点/标题在视口内
- [ ] 未新增关系图节点

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-016] changelog / 发版入口

**阶段状态**：`verified`

**目标**：从阅读器打开该功能 `changelog.md` 或 `prd/VERSIONS.md`；与当前规则分开展示并标记非当前规则。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F12 | 打开该功能 changelog 或 `prd/VERSIONS.md`；标记非当前规则 | `PRD` |
| 验收 ID | AC14 | 展示该功能 `changelog.md`，并标记非当前规则 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-003 | 阅读器 | 能渲染 md |
| STEP-007 | 打开文档 | 能按路径打开 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| 24 个功能目录 `changelog.md` | `existing` | `REPO_BASELINE` | 本轮 glob 24 个文件 | AC14 |
| `prd/VERSIONS.md` | `existing` | `REPO_BASELINE` | 文首「Hayyo 产品版本记录」 | 发版入口 |
| `room-list/changelog.md` | `existing` | `REPO_BASELINE` | 文首「非默认读取」 | 样例 |

**输入**：

- 当前打开的功能；用户选择变更或发版入口。

**输出**：

- 打开对应 changelog 或 VERSIONS；界面标记非当前规则。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 变更入口 | 该功能 `changelog.md` | F12；AC14 |
| 发版入口 | `prd/VERSIONS.md` | F12 |
| 标记 | 与当前规则分开展示，并标记非当前规则 | F12 |
| 首页 | changelog 不进知识库首页 | CSTR-006 |

**开发任务**：

1. 在当前功能阅读器提供 changelog 与发版入口（次级，不进首页列表）。
2. 打开后标记非当前规则。
3. 不把 changelog 纳入默认全文索引（由 STEP-012 保证）。

**不在本 STEP 范围内**：

- 用 changelog 冒充当前规则。改 changelog 正文。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 打开有 changelog 的功能，从阅读器打开变更记录 | 文档身份为该功能 `changelog.md`；可见「非当前规则」标记 | AC14 |
| 正常 | 打开发版入口 | 文档身份 `prd/VERSIONS.md`；有非当前规则标记 | F12 |
| 边界 | 知识库首页列表 | 不含 changelog | CSTR-006 |

**完成标志**：

- [ ] AC14：路径为该功能 changelog + 非当前规则标记
- [ ] VERSIONS 入口可打开且同样标记
- [ ] 首页列表仍无 changelog

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-017] 当前文档图集

**阶段状态**：`verified`

**目标**：列出本文图片缩略图，点击回到原文位置；无图显示空态。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F13 | 列出本文图片缩略图，点击回到原文位置；无图显示空态 | `PRD` |
| 验收 ID | AC15 | 打开 vip 图集并点一张图回到原文；room-list 无图为空态 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-003 | 正文与图片标记 | 文中有 `![](images/...)` |
| STEP-004 | 图片 URL 解析 | 缩略图能请求当前文档图 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `vip/PRD.md` 17 处 `![](images/v1.0.0-vip-*.png)` | `existing` | `REPO_BASELINE` | SRC-VIP | 图集条目身份 |
| `prd/design/vip/images/` 17 文件 | `existing` | `REPO_BASELINE` | 本轮 `ls` | 文件存在 |
| `prd/design/room-list/images/` | `existing` | `REPO_BASELINE` | 目录存在且 0 文件 | 无图空态（PRD 写「无目录」，仓库为空目录，空态仍成立） |

**输入**：

- 当前文档中的图片引用列表。

**输出**：

- 图集条目与文内图片引用对应；点击回到该引用位置；无引用或无文件时为空态。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 图集 | 列出本文图片缩略图，点击回到原文位置 | F13 |
| 空态 | 无图显示空态 | F13；AC15 |

**开发任务**：

1. 收集当前文档图片引用，列出缩略图。
2. 点击缩略图滚动到原文对应 `![](...)` 位置。
3. 无图片引用或目录无文件时显示空态，不造假图。

**不在本 STEP 范围内**：

- 预加载其他功能图片。改图片文件。把图集做成全库画廊。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 打开 vip，打开图集，点其中一张 | 图集条目路径集合对应文内 `images/v1.0.0-vip-*.png`；点击后该引用位置进入视口 | AC15 |
| 边界 | 打开 room-list 图集 | 空态；无假缩略图 | AC15 |

**完成标志**：

- [ ] vip：缩略图集合与文内图片引用一致（比路径多重集，不只比 17）
- [ ] 点击后回到同一引用在原文中的位置
- [ ] room-list 为空态

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-018] 文档与关系图互跳

**阶段状态**：`verified`

**目标**：从功能文档回到关系图时选中对应功能 ID；从图打开文档已由 STEP-007 覆盖。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F14 | 选中对应节点或打开对应文档；两边能对上同一功能 ID | `PRD` |
| 验收 ID | AC16 | 正在阅读 merchant 时查看关系，关系图选中 `merchant` | `PRD` |
| 决定 | UD-VIEW-GRAPH | 总览或无锚点 admin 全文：切回关系图，不选中、不新增节点 | `USER_DECISION` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | 视图可切回关系图 | 两关系图 Tab 可用 |
| STEP-007 | 从图打开文档 | 反向路径已存在 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `features[].id` `merchant` | `existing` | `REPO_BASELINE` | SRC-H5-DATA / 第 16 行 | AC16 |
| `merchant.prd` | `existing` | `REPO_BASELINE` | 同条 `../prd/design/merchant/PRD.md` | 文档与 ID 对应 |

**输入**：

- 当前打开的文档路径；用户选择「查看关系」。

**输出**：

- 能对应 `features[].id` 时：切到关系图且 `selectedId` 为该功能 ID（AC16 为 `merchant`）。
- 总览或无 `#锚点` 的 admin 全文：切到关系图，`selectedId === null`，节点集合不变。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 互跳 | 从文档看关系或从图看文档；对上同一功能 ID | F14 |
| 总览 | 不做成关系图节点 | CSTR-005 |
| 无对应节点时 | 可切回关系图，不选中任何节点、不新增节点 | UD-VIEW-GRAPH |

**开发任务**：

1. 当前文档为某客户端功能 `PRD.md` 且 `data.js` 有对应 `features[].id` 时，「查看关系」切到关系图并 `selectNode(该 id)`。
2. 从图打开文档保持 STEP-007，不重复破坏选中。
3. 当前文档为 INDEX / VERSIONS / PROJECT_OVERVIEW，或从列表打开且路径不含 `#锚点` 的 `admin/PRD.md` 时：「查看关系」切回关系图，`selectedId` 置空，不新增节点。

**不在本 STEP 范围内**：

- 为总览或 admin 全文章节补全量节点（T7 另立项）。改边。把无对应节点的文档隐藏「查看关系」（与 UD-VIEW-GRAPH 不符）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 正在阅读 `prd/design/merchant/PRD.md`，查看关系 | `state.selectedId === "merchant"`；关系图可见该节点选中 | AC16 |
| 边界 | 正在阅读 INDEX（或 VERSIONS / PROJECT_OVERVIEW，或无锚点的 admin 全文），查看关系 | 切到关系图；`selectedId === null`；`data.js` 节点 id 集合与改前一致 | UD-VIEW-GRAPH |

**完成标志**：

- [ ] AC16：文档路径为 merchant PRD 且选中 id 为 `merchant`
- [ ] UD-VIEW-GRAPH：总览/无锚点 admin 全文查看关系后不选中、不新增节点

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

## 自检

- [x] F1–F16 均映射到 STEP
- [x] AC1–AC16c 均映射到 STEP，并写明对象比较方法
- [x] UD-AC11、UD-VIEW-GRAPH、UD-HISTORY 已写入对应 STEP
- [x] 未增加 PRD 中不存在的业务字段/错误码/状态机
- [x] 未使用 `[自定义]` 补造
- [x] 路径/符号标记了 `existing` / `planned` / `unverified`
- [x] `existing` 绑定了 source_id 与 locator
- [x] 未把 `PLANNED`/`UNVERIFIED` 写成已发生的线上行为；无 `RUNTIME` 声称
- [x] L3 / OUT-* / T7 另立项项无实施 STEP
- [x] AC11 已按 USER_DECISION 写成可测规则，未推广为全部检索算法

## 阶段结果

`PASS_WITH_RISKS`

非阻断风险：

1. Markdown 具体库名未定（CSTR-014），标 `PLANNED`。
2. F16 无独立 AC 编号，用 admin 已有标题「管理房间」作可观察断言。
3. STEP-005 无独立 AC，完成标志按 §4.2 可观察字段。
4. 无自动化测试命令（仓库无 `package.json`）；验收为本地 HTTP + 手工，启动示例以 PRD `python3 -m http.server` 为准。
5. PRD 写 room-list「无 images/ 目录」，仓库为空目录；空态验收仍按「无图」。

无 `RUNTIME` 证据，不声称线上已验证。

业务代码状态：`NOT_STARTED`。

## 进度

> 路径：本文件内（项目无独立进度文档约定）
> PRD 来源：`site/docs/design/h5-kb/PRD-H5知识库-v1.md` v1.1
> STEP 来源：`steps-verified.md`
> 当前阶段结果：`PASS_WITH_RISKS`

### 进度总览

| 完成数 | 总数 | 当前状态 |
|---|---|---|
| 0 | 18 | `NOT_STARTED` |

### STEP 明细

| STEP | 功能名称 | 需求 ID | 验收 ID | 前置 STEP | 状态 | 证据 |
|---|---|---|---|---|---|---|
| STEP-001 | 知识库第三视图入口 | F1、C6、C9 | AC1 | 无 | `NOT_STARTED` | — |
| STEP-002 | 默认可读文档列表 | F1 | AC1 | STEP-001 | `NOT_STARTED` | — |
| STEP-003 | Markdown 页内渲染 | F3 | AC1、AC2、AC3、AC6 | STEP-001、STEP-002 | `NOT_STARTED` | — |
| STEP-004 | 按文档加载图片 | F6 | AC3、AC8 | STEP-003 | `NOT_STARTED` | — |
| STEP-005 | 文首元数据与覆盖提示 | R2、R5 | — | STEP-003 | `NOT_STARTED` | — |
| STEP-006 | 失败与启动说明 | F7 | AC7 | STEP-001 | `NOT_STARTED` | — |
| STEP-007 | 从节点打开文档并保留选中 | F2 | AC2、AC4 | STEP-001、003、006 | `NOT_STARTED` | — |
| STEP-008 | 拉新后台锚点改写 | C11、F2 | AC4b | STEP-007 | `NOT_STARTED` | — |
| STEP-009 | 本文目录 | F4 | AC5 | STEP-003 | `NOT_STARTED` | — |
| STEP-010 | 站内文档跳转 | F5 | AC9 | STEP-003、007 | `NOT_STARTED` | — |
| STEP-011 | 旧版逻辑显式入口 | F8、C10、UD-HISTORY | AC9b | STEP-003 | `NOT_STARTED` | — |
| STEP-012 | 内存搜索索引 | F11、F15、C12 | AC13 | STEP-002 | `NOT_STARTED` | — |
| STEP-013 | 知识库关键词检索 | F9、UD-AC11 | AC10–AC12、AC16b、AC16c | STEP-012 | `NOT_STARTED` | — |
| STEP-014 | 结果定位与高亮 | F10、UD-AC11 | AC10、AC11 | STEP-013、007 | `NOT_STARTED` | — |
| STEP-015 | 后台按章节命中 | F16 | — | STEP-013、014 | `NOT_STARTED` | — |
| STEP-016 | changelog / 发版入口 | F12 | AC14 | STEP-003、007 | `NOT_STARTED` | — |
| STEP-017 | 当前文档图集 | F13 | AC15 | STEP-003、004 | `NOT_STARTED` | — |
| STEP-018 | 文档与关系图互跳 | F14、UD-VIEW-GRAPH | AC16 | STEP-001、007 | `NOT_STARTED` | — |

### 阻断与来源变化

| 日期 | STEP | 类型 | 证据或变化 | 处理结果 |
|---|---|---|---|---|
| 2026-08-26 | STEP-013 | USER_DECISION | UD-AC11：标题含「官方房临时置顶」即命中 room-list | 写入验证版；停止门取消 |
| 2026-08-26 | STEP-018 | USER_DECISION | UD-VIEW-GRAPH：总览/无锚点 admin 不选中、不新增节点 | 写入验证版 |
| 2026-08-26 | STEP-011 | USER_DECISION | UD-HISTORY：列出 history 文件再点开 | 写入验证版 |
