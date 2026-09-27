---
title: "知识问答 · 反馈与对话样式 STEP 验证版"
status: "verified"
stage_result: "PASS_WITH_RISKS"
prd: "site/docs/design/kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md"
prd_sha256: "1923bb41a8520401cd34eab9fc36f4050a194a7185d91d157b360eaae4c4fc59"
source_draft: "site/docs/design/kb-qa-feedback/steps-draft.md"
source_draft_sha256: "6d034a290a0d1c055a2a1d2dfb0b52f2a228d29e6240b76f72d81d44d1e8c947"
audit: "site/docs/design/kb-qa-feedback/step-audit.md"
created: "2026-09-17"
note: "step-doc-review 第一轮 review-repair 后的验证版。草稿未覆盖。仍含非阻断风险；不自动开始开发。"
---

# 知识问答 · 反馈与对话样式 STEP 验证版

> **现行权威**：[`PRD-知识问答-反馈与对话样式-v2.md`](PRD-知识问答-反馈与对话样式-v2.md)（status=已确认）。  
> **独立增量**：不替代 [`../kb-qa/PRD-知识问答-v3.md`](../kb-qa/PRD-知识问答-v3.md)。检索 / 改写 / 切块 / 日志存法 B / 热度聚合公式以现网为准，本期不改。  
> **v1 已过期**：`history/PRD-知识问答-反馈与对话样式-v1.md` 不是实施依据，本轮未读。  
> **草稿**（未覆盖）：[`steps-draft.md`](steps-draft.md)。  
> 宿主为现网第四 Tab 知识问答。实现状态：未实施。  
> 本文件经九维复审，仍含非阻断风险；不宣布开发已开始。

## 来源摘要

事实标签只用：`USER_DECISION`、`PRD`、`CONTRACT`、`REPO_BASELINE`、`RUNTIME`、`PLANNED`、`UNVERIFIED`。本轮无 `RUNTIME`。

| source_id | 路径 | 状态 | SHA-256 | 本轮核实 |
|---|---|---|---|---|
| SRC-PRD | `site/docs/design/kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md` | `existing` | `1923bb41a8520401cd34eab9fc36f4050a194a7185d91d157b360eaae4c4fc59` | 全文；status=已确认；确认点 1–16；req-confirm RQ-01～RQ-04；无产品待确认 |
| SRC-QA-JS | `site/feature-interaction/qa.js` | `existing` | `44019a5630e3534c3184229a22039144cdef12c8a4c5c2cda886519085fcf1aa` | `messageHtml` 仅「复制回答」；`send` 生成 `round_id` 未挂消息；`emptyHtml` 无 chip；`lockGuard` / `copyText` / `openRounds` / `openHeatmap` |
| SRC-QA-CSS | `site/feature-interaction/qa.css` | `existing` | `5fa4d5c8fb0378ff3fc64eb5610258cd16356474efb9ac770470175a9daffb7d` | `.qa-row` `max-width: 760px`；`.qa-composer-box` `max-width: 840px`；文件头写「无过程栏、无 chips」 |
| SRC-H5-HTML | `site/feature-interaction/index.html` | `existing` | `b871e5e250ca4a2002baf9a8805aedd942a67ceafa34c345c2e04a8d9e6a5d97` | 四 Tab；`#qaWorkspace` 左列表+右对话；`#qaInput`/`#qaSend` 并排；顶栏配置/重建/明细/热度 |
| SRC-SQL | `site/kb-api/sql/init.sql` | `existing` | `30a109d3535addf442eeb662299c3f005d9be35d2e199a22b7aa4686ca14e4a4` | `qa_rounds` 无反馈列；`CREATE TABLE IF NOT EXISTS` |
| SRC-LOGS | `site/kb-api/app/logs.py` | `existing` | `ae799f5e26be9c7b8c88edd9d0cec5ae8f7668f798c822fdf1bfe63d11d1f9c0` | `update_round` allowed 无 feedback；`heatmap()` 返回 `{items, unclassified}`，`items` 按 count 降序 |
| SRC-API | `site/kb-api/app/main.py` | `existing` | `8d6e16437cce1f641d6a47fc3b74a55619a25225dad6a3e7f1531e17c96090a2` | 现有 `POST /api/kb/ask`、`GET /api/kb/heatmap`、`GET /api/kb/rounds`、`GET /api/kb/rounds/{round_id}`；无反馈写入路由 |
| SRC-ALIAS | `site/kb-api/app/aliases.py` | `existing` | `295ea661338fd6b61181c6ec64cf6da5eabd3af9b6fb47c6de519b2b41682088` | `load_aliases()` 合并 `feature_aliases.json` 与 `EXTRA_ALIASES` 后去重；本轮只读 |
| SRC-ALIAS-JSON | `site/kb-api/feature_aliases.json` | `existing` | `afaaa4d1f71d0559a2fdacfd8e6ddcfac055da6f1abbd9a6552bc16fff11fb84` | `vip` 含「用户VIP」；`yallapay` 含「链接支付」 |
| SRC-CONTRACT | `site/kb-api/tests/test_site_contract.py` | `existing` | `7eb3ec9a0787e65ba765306cb52f84631288a71cc7fc6432ecc30367c91d34ee` | `test_fourth_tab_and_no_chips_or_process` 断言 `index.html` 无 `data-suggest` / `qa-chip`，无 `#qaProcess` |
| SRC-HEAT-TEST | `site/kb-api/tests/test_retrieve_ops.py` | `existing` | `f8d5153c40cae2dd10e9b7fc0d467d15e063d87199d8fa7bc058f0032511daa7` | `test_heatmap_c34` 覆盖进生成 `feature_id` 计数；`unclassified` 不进 `items` |
| SRC-COMPOSE | `site/docker-compose.yml` | `existing` | `e932cada76d72f86ae61393531e9e94bd738dd6479a5d147508d480c52044ef7` | MySQL 卷 `kb-mysql-data`；`init.sql` 仅挂 `/docker-entrypoint-initdb.d/` |
| SRC-NGINX | `site/docker/nginx.conf` | `existing` | `61e81c8bfb90bfe4a2a53e6399a934340df383cda9e9d803b30b9f8141ceb1e2` | `location /api/kb/` 反代 kb-api |
| SRC-PYTEST | `site/kb-api/pytest.ini` | `existing` | `b160d82f7811555051f8966d8e02750a985227c1d022208c784e606946f2eada` | `testpaths = tests` |
| SRC-SETTINGS | `site/kb-api/app/settings.py` | `existing` | `4e60c7cf89ab6bafe61ccc23cdfe24ac73d05dfc1486a887014ab4077d395658` | `SYSTEM_PROMPT` / `REWRITE_PROMPT` 现网；本期不改 |
| SRC-PIPELINE | `site/kb-api/app/pipeline.py` | `existing` | `055f87be7bd5d9d4e702e03e7a5b51f7963948d760aa3b1e68fc886811e7f767` | 改写/检索/重排/生成；本期不改 |
| SRC-V3 | `site/docs/design/kb-qa/PRD-知识问答-v3.md` | `existing` | `d6253434437f47a3120bd7d3b6b326b7dd72fe9e0bcf3f58278d64789a59c537` | **不改正文**。C32/AC21「无建议问法 chips」由本文 C22 覆盖现网验收 |
| SRC-QA-STEPS | `site/docs/design/kb-qa/Hayyo-知识问答-STEP-验证版.md` | `existing` | `308746426b2faab65e12336782ebdce9ab40842df3f81f3c97fbf45980ae48fa` | STEP-004 原 AC21 无 chips；本期改契约测试，不改该验证版正文除非另开 |

**发现门（不填具体值、不宣称已决定）：**

- 反馈写入路由：采用 PRD 实施说明拟 `POST /api/kb/rounds/{round_id}/feedback`；现网无此路由（`PLANNED`）。
- C20 显示名如何从 `load_aliases()` 接到空状态渲染：现网 `GET /api/kb/heatmap` 只返回 `feature_id`；按已核实项目约定确定接线，不得改别名数据、不得改热度公式。
- 已有 MySQL 卷补列的触发点：PRD 写「启动补列或手工 ALTER」，具体挂在 lifespan 或运维步骤按项目约定确定。
- 本机 pytest 解释器路径：`pytest.ini` 已核实；执行记录曾用 `site/kb-api/.venv/bin/python -m pytest site/kb-api/tests`，本轮未核实 `.venv` 仍在。

启动命令（compose 文件头，`REPO_BASELINE`）：在 `site/` 执行 `docker compose up -d`；或仓库根 `docker compose -f site/docker-compose.yml up -d`。

## 对象比较约定

比较同一输入快照。PRD 未要求顺序时不增加顺序断言。热度 `items` 现网已按 count 降序；空状态「前 4 个 `feature_id`」指该已排序数组的前 `min(4, n)` 个身份，不是另定排序规则。

| 符号 | 定义 | 来源 |
|---|---|---|
| `MAIN_TAB_NODES` | `header .tabs .tab` 按钮集合（与现网四 Tab 同一选择器）。比较键为按钮可见文案多重集，不得用 `role=tab`（仅父级 `role="tablist"`） | SRC-H5-HTML 第 17–21 行；AC13 |
| `MAIN_TABS` | 文案多重集 {「客户端 ↔ 后台」,「客户端交叉」,「文档索引」,「知识问答」} | 同上 |
| `FEEDBACK_UI` | 界面三态：未评价 / 赞 / 踩 | C4、C6 |
| `FEEDBACK_DB` | 库内枚举：空 / `up` / `down`（界面契约仍是 `FEEDBACK_UI`） | C19 实施说明；`PLANNED` |
| `ACTION_KEYS` | 操作条键类型多重集。投影：复制=现网按钮文案「复制回答」；赞、踩、刷新=对应键。全集 `{复制, 赞, 踩, 刷新}` | C1；F1 |
| `BIND_FIELDS` | `{round_id, logWritten, query, historySnapshot, lastChunksSnapshot}` | PRD T2；§6.2 |
| `CHIP_FIXED` | 常驻 4 条：短标题→发送全文，见下表。比较键为 4 个 `(短标题, 全文)` 元组多重集 | C15；A7 |
| `HEAT_TMPL(name)` | 「{name} 有哪些现行规则？」 | C16 |
| `C20(fid)` | `load_aliases()` 合并去重列表中第一条含汉字的别名；若无汉字则 `feature_aliases.json` 该 id 第一项；若仍无则 `feature_id` | C20 |
| `ITEMS4` | 同一空状态请求得到的 `heatmap.items` 中前 `min(4, items.length)` 个元素的 `feature_id` 序列（沿用现网已排序数组的前段身份） | §6.2 |
| `CHIP_HEAT` | 文案多重集 `{ HEAT_TMPL(C20(fid)) \| fid ∈ ITEMS4 }`；`items.length=0` 或 heatmap 非 2xx 时为空集 | AC8；E5；E6 |
| `CONTENT_COL` | 消息、chips、输入同一居中栏；最大约 768px；更宽锁定；更窄随 `.qa-main` 收缩，左右约 24px | C8 |
| `COL_PAIR` | 同一快照下：内容柱主列（有消息时为消息列；空状态时为欢迎+chips 所在列）与输入卡片的所用宽度相等，且二者在 `.qa-main` 内水平居中。不把门禁写成硬像素 768 | AC9；F5 |
| `ASK_BODY` | 现网 `POST /api/kb/ask` JSON：`conversation_id`、`round_id`、`query`、`history`、`last_chunks` | SRC-QA-JS `send`；SRC-API `_ask_events` |
| `UNWRITTEN_HINTS` | 可见提示文本须匹配下列 PRD 已写句子之一（允许整句或以其为全文；禁止另造第三套产品文案）：「本轮日志未写入，反馈不会进明细」；「不会进明细」；「未写入明细」 | §6.2；E1；E2；AC7 |
| `TOP_ACTIONS` | `#qaTopActions` 内仍存在 `data-qa-config`、`data-qa-rounds`、`data-qa-heatmap`、`data-qa-reindex`；它们不是 `.tabs .tab` | C7；CSTR-002；AC13 |

**常驻 4 chip（`CHIP_FIXED`）**

| 短标题 | 发送全文 |
|---|---|
| 链接支付权益 | 币商用链接支付帮朋友充金币：付款人能拿 VIP 积分和拉新返利吗？收货人呢？这笔算不算收货人的首充？会不会进充值任务进度？ |
| 代充三套账 | 币商给用户转了 20000 金币。这笔会进 Billionaires 充值榜吗？算不算用户首充？会不会给用户加 VIP 财富值？ |
| Game Center | 非 VIP 在语聊房 Game Center 点 Bounty Racing 会怎样？如果这个房间同时开着 Ludo，我关掉数值游戏弹窗后，休闲游戏还在吗？Lord of Olympus 有 VIP 限制吗？ |
| 保级对照 | VIP 保级扣的是财富值还是金币？200 金币等于多少财富值？退款怎么扣？ |

C20 抽样（本轮用 `load_aliases()` 合并列表核过，与 PRD 补充句一致）：`vip`→用户VIP；`yallapay`→链接支付。

## 输入清单

### 本期有效需求

F1–F9。优先级沿用 PRD 的 P0，不另造排期。

### 本期有效验收

AC1–AC13。补充句（C23 `lastChunks`、C20 抽样）随对应 STEP 验证，不新编号。

### 未编号约束（CSTR）

| ID | 摘要 | 来源 |
|---|---|---|
| CSTR-001 | 不改切块、两库检索、重排、改写/生成 Prompt、热度聚合公式 | §4.2 |
| CSTR-002 | 不改左侧会话列表结构、四个主 Tab、顶栏配置/重建/明细/热度入口形态 | C7、§4.2、AC13 |
| CSTR-003 | 无登录；反馈一轮一个值；现网仍发送 `user_id: null` | §3；SRC-QA-JS `send` |
| CSTR-004 | 刷新时不在新旧 round 之间建父子关联字段 | §4.2 |
| CSTR-005 | 不把「那退款呢」做成空状态 chip | §4.2 |
| CSTR-006 | 不把本增量写进 `prd/design/*/PRD.md`；不修订 v3 正文 | §4.2；C22 |
| CSTR-007 | 不做截图中的「链接」「更多」键 | C1、§4.2 |
| CSTR-008 | 空状态欢迎标题与 brief 说明沿用现网 `emptyHtml` | C21 |
| CSTR-009 | 「无过程栏」仍以 v3 为准；现网不得出现 `#qaProcess` | C22 |
| CSTR-010 | 复制成功 toast 为现网「已复制回答」 | F1；`copyText` |
| CSTR-011 | 顶栏热度页仍展示 `feature_id`，不改其形态 | C16、C20 |
| CSTR-012 | `CREATE TABLE IF NOT EXISTS` 不会给已有库加列；实施必须补列 | §9.1；T5；T7 |
| CSTR-013 | `state.busy` 时复制/赞/踩对已完成的其它气泡可用 | C18 |
| CSTR-014 | Enter 发送、Shift+Enter 换行不变 | C9 |
| CSTR-015 | 阶段文案与出处折叠保留，放入新内容柱 | C17 |
| CSTR-016 | 刷新复用现网 `POST /api/kb/ask` 全链路，不新开生成公式 | C3；A3 |
| CSTR-017 | 存储键仍为 `hayyo-kb-qa-conversations-v1`；pending 仍不落盘 | T2；`CONV_KEY` |
| CSTR-018 | 浏览器刷新页面仍走 v3 AC18；本增量只把「刷新键」补进 busy 锁 | C18 |
| CSTR-019 | 无灰度开关；本机 compose | T5 |
| CSTR-020 | 不编造日志保留天数 | T6「用户未给，不编造」 |

### 决策

| C1–C18、C20、C22、C23 均已确认。C19 为实施说明（库内 `up`/`down`/空）。C21 为可查事实（沿用 `emptyHtml`）。req-confirm RQ-01～RQ-04 已写入 C18/C20/C23/C22，不另开需求号。

PRD E1 表内「验收编号」写成 AC6，与 E1/AC7 正文不符。覆盖以 AC6、AC7、E1 各自正文为准：E1 行为由 STEP-004 / AC7 验证；不修改 PRD 文件。

### 排除项 / 本期不做

| ID | 项 | 来源 |
|---|---|---|
| OUT-1 | 「链接」「更多」键 | §4.2；C1 |
| OUT-2 | 改左侧会话列表结构、四个主 Tab、顶栏入口形态 | §4.2；C7 |
| OUT-3 | 改切块、两库检索、重排、改写/生成 Prompt、热度聚合公式 | §4.2 |
| OUT-4 | 登录、按人计票、赞踩筛选明细 | §4.2 |
| OUT-5 | 刷新时建父子 round 关联字段 | §4.2 |
| OUT-6 | 把「那退款呢」做成空状态 chip | §4.2 |
| OUT-7 | 把本增量写进 `prd/design/*/PRD.md` | §4.2 |
| OUT-8 | 修订 `PRD-知识问答-v3.md` 正文 | §4.2；C22 |
| OUT-9 | 改 `SYSTEM_PROMPT` / `REWRITE_PROMPT` | A3 |
| OUT-10 | 改顶栏热度页展示（仍 `feature_id`） | C16 |
| OUT-11 | 因踩而改写知识库或 Prompt | A2 |
| OUT-12 | 另建反馈审计表 | T6 |
| OUT-13 | 编造日志保留天数 | T6；CSTR-020 |

### 技术债（PRD T7，本期要做掉的不新编号）

| 项 | 处置 |
|---|---|
| 消息未绑 `round_id` | STEP-001 做掉 |
| init.sql 非迁移 / 已有卷无新列 | STEP-003 做掉 |
| 无登录反馈 | 接受；CSTR-003；不另开 STEP |
| v3 仍写「无 chips」 | 接受；C22；STEP-011 只改现网测试 |

## 功能清单

本期只实施：回答效果采集（复制 / 赞 / 踩 / 刷新）、反馈落库与明细回放、右侧 Grok 式内容柱 / 输入卡片 / 消息排版、空状态 4+最多 4 chips。不实施检索公式、登录、v3 文档修订。

## STEP 总览

| STEP | 标题 | 需求 | 验收 | 前置 | 优先级（PRD 原值） |
|---|---|---|---|---|---|
| STEP-001 | 发送消息绑定 round_id 与刷新快照 | F2、F3（子条款） | —（为 AC3/AC6/AC7 供输入） | 无 | P0 |
| STEP-002 | 操作条出现规则与复制 | F1、F9（可见性） | AC1、AC4 | 无 | P0 |
| STEP-003 | 反馈落库列、补列与写入接口 | F2、F4（写路径） | —（为 AC6/AC7 供接口） | 无 | P0 |
| STEP-004 | 赞踩三态与写库失败降级 | F2 | AC2、AC7 | STEP-001、STEP-002、STEP-003 | P0 |
| STEP-005 | 问答明细展示反馈 | F4 | AC6 | STEP-003、STEP-004 | P0 |
| STEP-006 | 刷新原地重生成 | F3、F9（行为） | AC3、AC5、AC12 | STEP-001、STEP-002 | P0 |
| STEP-007 | 右侧居中内容柱 | F5 | AC9（栏宽）、AC10 | 无 | P0 |
| STEP-008 | Grok 式输入卡片 | F5、F6 | AC9（输入同栏） | STEP-007 | P0 |
| STEP-009 | 消息排版 | F7 | AC11 | STEP-002、STEP-007 | P0 |
| STEP-010 | 空状态建议搜索 | F5、F8 | AC8 | STEP-007、STEP-008 | P0 |
| STEP-011 | 左栏顶栏不变与契约测试覆盖 | C7、C22 | AC13 | STEP-002、STEP-007、STEP-008、STEP-009、STEP-010 | P0 |

依赖未满足时停止当前 STEP。编号顺序不表示依赖。

## 需求映射

| ID | 映射 STEP | 映射方式 |
|---|---|---|
| F1 | STEP-002 | 直接：复制正文 + toast；操作条键类型集含复制/赞/踩/刷新 |
| F2 | STEP-001、STEP-003、STEP-004、STEP-006 | 子条款：绑字段；写库；三态 UI；刷新后消息 `round_id` 换新 |
| F3 | STEP-001、STEP-006 | 子条款：快照；原地刷新与新 round |
| F4 | STEP-003、STEP-005 | 写路径 + 明细展示 |
| F5 | STEP-007、STEP-008、STEP-010 | 可分割：消息栏、输入同栏、chips 同栏 |
| F6 | STEP-008 | 直接 |
| F7 | STEP-009 | 直接 |
| F8 | STEP-010 | 直接 |
| F9 | STEP-002、STEP-006 | 可见性（只刷新）+ 重跑行为 |
| C1 | STEP-002 | 只做四键 |
| C2、C3、C18、C23 | STEP-006 | 刷新形态 / 流水线 / busy / lastChunks |
| C4 | STEP-004 | 三态 |
| C5 | STEP-002 | 哪些气泡出键 |
| C6 | STEP-004、STEP-005 | 明细与写库失败 |
| C7 | STEP-007、STEP-011 | UI 范围；左栏顶栏回归 |
| C8 | STEP-007 | 栏宽 |
| C9 | STEP-008 | 输入卡片 |
| C10 | STEP-009 | 消息样式 |
| C11 | STEP-008、STEP-010 | 空状态输入钉底；欢迎在中 |
| C12–C16、C20、C21 | STEP-010 | 空状态 chips |
| C17 | STEP-007、STEP-009 | 阶段文案入柱；出处折叠入柱 |
| C22 | STEP-010、STEP-011 | 覆盖口径与契约测试 |
| C19 | STEP-003、STEP-004 | 实施说明：库内枚举 |
| RQ-01 | STEP-006 | 已写入 C18 |
| RQ-02 | STEP-010 | 已写入 C20 |
| RQ-03 | STEP-006 | 已写入 C23 |
| RQ-04 | STEP-010、STEP-011 | 已写入 C22 |
| E1、E2、E8 | STEP-004 | 反馈异常（E1 正文对齐 AC7） |
| E3、E4、E7 | STEP-006 | 刷新异常 |
| E5、E6 | STEP-010 | 热度空/失败 |
| G1 | STEP-002～005 | 采集好坏 |
| G2 | STEP-006 | 同一问句换理解 |
| G3 | STEP-007～009 | 可扫描对话区 |
| G4 | STEP-010 | 空状态起问 |
| A7 | STEP-010 | 常驻 4 句 `original_query` = 全文 |

## 验收映射

| AC | 映射 STEP | 对象比较方法 |
|---|---|---|
| AC1 | STEP-002 | 剪贴板文本 = 该条 `m.text`。该条 `ACTION_KEYS` = `{复制, 赞, 踩, 刷新}`。本 STEP 只验键身份与复制；赞踩/刷新行为分属 004/006 |
| AC2 | STEP-004 | 同一消息 `id` 上 `FEEDBACK_UI` 依次为赞、踩、未评价 |
| AC3 | STEP-006 | 刷新前后：用户消息 `id` 多重集相等。被刷新消息客户端 `id` 不变。明细 `round_id` 集合 = 刷新前集合 ∪ {新 `round_id`}。新行 `original_query` = 该条首次 `query`。该条流式重画 |
| AC4 | STEP-002 | 该纯错误条 `ACTION_KEYS` = `{刷新}` |
| AC5 | STEP-006 | `state.busy=true` 时点刷新：可见 toast 全文=「生成中…」；同一时刻 in-flight `POST /api/kb/ask` 次数保持 1；本轮 SSE 不被 abort。点发送：现网 `send()` 在 busy 时直接 return，不新增用户消息 `id` |
| AC6 | STEP-005 | 以已赞的那条消息的 `round_id` 为键：`GET /api/kb/rounds/{round_id}` 投影的界面反馈=赞，且出现在「回答或错误态」块之后。列表中 `round_id` 相同的那一行反馈列=赞 |
| AC7 | STEP-004 | 浏览器该消息 `FEEDBACK_UI`=赞。明细 `round_id` 集合不含该消息的 `round_id`（无该轮）。可见提示 ∈ `UNWRITTEN_HINTS` |
| AC8 | STEP-010 | 空会话：欢迎文案沿用现网 `emptyHtml` 标题与 brief 说明（C21）。常驻 chip 的 `(短标题, 点击发出的 query)` 多重集 = `CHIP_FIXED`。对 `CHIP_FIXED` 每一对：点击短标题后本轮 `ASK_BODY.query` 与写入明细的 `original_query` 均 = 该对全文。`CHIP_HEAT` 文案多重集按上表定义。chips 与消息、输入满足 `COL_PAIR`/`CONTENT_COL`（F5 子条款） |
| AC9 | STEP-007、STEP-008 | 宽窗口同一快照：`COL_PAIR` 成立；所用宽度不拉满 `.qa-main` |
| AC10 | STEP-007 | 缩小 `.qa-main` 后内容柱所用宽度 < `.qa-main` 所用宽度；左右留白约 24px（不贴死），不另设硬像素门 |
| AC11 | STEP-009 | 用户句在 `CONTENT_COL` 内靠右的圆角块。回答计算边框为无厚边框（相对现网 `.qa-bubble` 的 `1px solid` 边框去掉）且占满 `CONTENT_COL`。出处折叠与 `ACTION_KEYS`（有正文时全集，纯错误时 `{刷新}`）在该回答下方 |
| AC12 | STEP-006 | 取刷新成功且 `logWritten` 为真的新轮 `c_gen` 中出现的某一 `feature_id`。打开热度页前后快照：该 `feature_id` 的 `count_after = count_before + 1`；若刷新前 `items` 无该 id，则 `count_after = 1`。不改 `heatmap()` 公式 |
| AC13 | STEP-011 | `MAIN_TAB_NODES` 可见文案多重集 = `MAIN_TABS`。左栏新建/切换/删除/清空仍可用（现网 `data-qa-new` / `data-conv` / `data-del` / `data-qa-clear`）。`TOP_ACTIONS` 仍在 `#qaTopActions`，不是新 `.tab` |

---

## 完整 STEP 提示词

### [STEP-001] 发送消息绑定 round_id 与刷新快照

**阶段状态**：`verified`

**目标**：每次走现网发送路径时，把 `round_id`、`logWritten`、原文 `query` 以及该轮第一次发送的 `history` / `last_chunks` 快照写到对应回答或错误消息上，供赞踩与刷新使用。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F2 | 写库成功则更新该 `round_id` 的反馈 | `PRD` |
| 需求 ID | F3 | query 与首次快照按 C3 | `PRD` |
| 约束 | C3、C6、C23 | 快照绑在消息上；无 `round_id` 的旧消息走 E1 同类 | `PRD` |
| 技术债 | T7 | 消息未绑 `round_id`，本期写入消息 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| 无 | 现网 `send()` 已能 `POST /api/kb/ask` | SRC-QA-JS `send` 第 405 行起 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `send` | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 405–566 行 | 在现有发送上挂字段，不改 ask 公式 |
| `roundId` 局部变量 | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 433–436 行 | 现已生成并写入请求体，未写回消息 |
| `log_written` | `existing` | `REPO_BASELINE` | SRC-API `done`/`error`；SRC-QA-JS 第 514、519 行 | 现只 `setBanner`，未存消息 |
| `sanitizeConv` / `persist` | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 56–68、115–136 行 | 消息对象额外字段会随 JSON 保留；pending 仍过滤 |
| `CONV_KEY` | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 7 行 | 不改键名（CSTR-017） |
| 消息字段 `round_id`、`logWritten`、`query`、`historySnapshot`、`lastChunksSnapshot` | `planned` | `PRD` T2 / 6.2 | 不适用 | 名称来自 PRD 实施表与主流程，不另造业务字段 |

**输入**：

- 现网 `send()`：生成 `round_id`、组装 `history`（最近用户句最多 5 条）、`last_chunks: conv.lastChunks`。
- SSE `done` / `error` / `log` 上的 `log_written`。

**输出**：

- 完成后的 assistant / 拒答 / 纯错误消息带有：`round_id`、`logWritten`、`query`（用户原句）、`historySnapshot`、`lastChunksSnapshot`（均为该轮首次发送时的请求体值）。
- 多次刷新不得改这份快照（本 STEP 只负责首次写入；改快照的禁令由 STEP-006 遵守）。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| `query` | 该轮用户原句 | C3 |
| `history` / `last_chunks` 快照 | 该轮第一次发送时的值；同一条多次刷新都用这一份 | C3 |
| `logWritten` | 本轮日志是否写入；为假时赞踩不请求接口 | C6；§6.2 |
| 无 `round_id` 的旧本地消息 | 赞踩走 E1 同类；刷新无快照走 E4 | C6；§7 末段 |

**开发任务**：

1. 在现有 `send()` 成功创建 pending / 最终消息时写入上述字段；`round_id` 仍传给 `POST /api/kb/ask`。
2. 从 SSE `done`/`error`/`log` 把 `log_written` 落到 `logWritten`；现网 banner「本轮日志未写入」保留。
3. 确认 `sanitizeConv` 不剥掉这些字段；存储键不变；pending 仍不落盘。

**不在本 STEP 范围内**：

- 赞踩 UI、反馈接口、刷新请求、内容柱、chips。
- 改 `pipeline.py`、Prompt、热度公式。
- 为旧消息补造快照（E4 属 STEP-006）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 发送一句并完成 | 该非 pending 回答消息的字段集合 ⊇ `BIND_FIELDS`；`round_id` = 当次 `ASK_BODY.round_id`；`query` = 该轮用户句；`historySnapshot`/`lastChunksSnapshot` = 当次请求的 `history`/`last_chunks` | F3 子条款 |
| 正常 | `done.log_written === false` | 该条 `logWritten` 为假；banner 仍为现网「本轮日志未写入」 | C6 |
| 边界 | 刷新页面后读 `CONV_KEY` | 非 pending 消息仍带 `BIND_FIELDS` | CSTR-017 |

**完成标志**：

- [ ] 新发送非 pending 回答/错误消息满足上表 `BIND_FIELDS` 比较
- [ ] 未改变其它 STEP 的范围或来源需求
- [ ] 新发现的路径、符号已更新状态
- [ ] 进度已按本文件进度区块回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-002] 操作条出现规则与复制

**阶段状态**：`verified`

**目标**：按 C5 在回答下展示复制 / 赞 / 踩 / 刷新四键（或纯错误只刷新）；复制仍把该回答正文写入剪贴板并 toast「已复制回答」。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F1 | 有完整回答正文时点复制；toast「已复制回答」 | `PRD` |
| 需求 ID | F9 | 纯错误 / 失败提示只显示刷新，不显示赞踩 | `PRD` |
| 验收 ID | AC1 | 剪贴板为该回答正文；赞踩刷新仍在 | `PRD` |
| 验收 ID | AC4 | 纯错误提示只有刷新，无赞踩复制 | `PRD` |
| 决策 | C1、C5 | 只做四键；有正文（含拒答但仍有文本）出四键 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| 无 | 现网 `messageHtml` 已能在有正文的 assistant 上出「复制回答」 | SRC-QA-JS 第 202–216、793–798 行 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `messageHtml` | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 179–230 行 | 现仅 assistant+text 出复制；system 错误无键 |
| `copyText` | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 581–582 行 | toast「已复制回答」 |
| 操作条四键 DOM | `planned` | `PLANNED` | 不适用 | 内部 class/data-* 按项目约定，禁止「链接」「更多」 |
| `event === "refuse"` 写成 `role: "system"` | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 488–496 行 | 出现规则以 C5「有完整回答正文」为准，不以当前 role 字符串为准 |

**输入**：

- 现网气泡类型：用户句、pending、assistant 正文、拒答文本、system 错误。

**输出**：

- 操作条出现规则与下表一致；复制行为保持现网。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 有完整回答正文的 assistant（含仍给出文本的拒答） | 复制、赞/踩、刷新都要 | C5 |
| 纯错误 / 失败提示 | 不要复制、不要赞/踩、要刷新 | C5、F9、AC4 |
| 生成中 pending | 四键都不要 | C5 |
| 用户问句 | 四键都不要 | C5 |
| 操作条键集合 | 只做复制、赞、踩、刷新 | C1 |
| 复制 toast | 「已复制回答」 | F1；CSTR-010 |

**开发任务**：

1. 按上表改 `messageHtml`（或等价渲染）：出处折叠仍在（CSTR-015）；四键在回答下方。
2. 保留 `copyText` 现网文案与复制正文语义。
3. 本 STEP 交付 `ACTION_KEYS` 可见性。赞踩写库属 STEP-004，刷新 SSE 属 STEP-006；点赞踩刷新在那两 STEP 完成前可以无业务副作用，但 AC1/AC4 只验键类型集，不把行为算进本 STEP 完成。
4. `state.busy` 时，对已完成的其它气泡，复制仍可用（CSTR-013 的复制侧）。

**不在本 STEP 范围内**：

- 赞踩写库、刷新 SSE、明细列、内容柱、chips。
- OUT-1「链接」「更多」。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 有完整回答，点复制 | 剪贴板=该条 `m.text`；toast 全文=「已复制回答」；该条 `ACTION_KEYS`=`{复制, 赞, 踩, 刷新}` | AC1 |
| 异常 | 纯错误提示（如改写失败文案） | 该条 `ACTION_KEYS`=`{刷新}` | AC4 |
| 边界 | pending 生成中 | 该条 `ACTION_KEYS`=∅ | C5 |
| 边界 | 拒答但仍有文本 | 该条 `ACTION_KEYS`=`{复制, 赞, 踩, 刷新}` | C5 |
| 边界 | `state.busy` 时点另一条已完成回答的复制 | 剪贴板更新为该条正文；本轮 ask 不中断 | CSTR-013 |

**完成标志**：

- [ ] AC1、AC4 的 `ACTION_KEYS` 与剪贴板比较通过
- [ ] 未改变其它 STEP 的范围或来源需求
- [ ] 新发现的路径、符号已更新状态
- [ ] 进度已回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-003] 反馈落库列、补列与写入接口

**阶段状态**：`verified`

**目标**：`qa_rounds` 能保存一轮一个反馈值；已有数据卷能补列；写库成功的 round 可被后续明细读取。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F2 | 写库成功则更新该 `round_id` 的反馈 | `PRD` |
| 需求 ID | F4 | 详情/列表能读到反馈 | `PRD` |
| 实施说明 | C19、T2、T3 | 库内空/`up`/`down`；拟增 `feedback`、`feedback_at`；拟 `POST /api/kb/rounds/{round_id}/feedback` | `PRD` |
| 技术债 | T7 / CSTR-012 | 已有卷需 ALTER | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| 无 | 现网 `qa_rounds` 与 `GET /api/kb/rounds/{round_id}` | SRC-SQL；SRC-API 第 149–154 行 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `qa_rounds` 建表 | `existing` | `REPO_BASELINE` | SRC-SQL / 第 7–28 行 | 无反馈列 |
| `LogStore.update_round` allowed | `existing` | `REPO_BASELINE` | SRC-LOGS / 第 92–95 行 | 现不允许 feedback |
| `LogStore.insert_running` 列清单 | `existing` | `REPO_BASELINE` | SRC-LOGS / 第 55–58 行 | 插入时反馈可空 |
| `get_round` / `list_rounds` | `existing` | `REPO_BASELINE` | SRC-API / 第 139–154 行；SRC-LOGS `SELECT *` | 加列后自然投影 |
| 反馈列与写入路由 | `planned` | `PRD` 实施说明 | 不适用 | 路径用 PRD T3 拟议 `POST /api/kb/rounds/{round_id}/feedback`；现网无此路由是基线缺口。不得改 ask 写入语义；404 无此轮 |
| 启动补列 | `planned` | `PRD` T5 | 不适用 | 按项目约定挂启动或文档说明手工 ALTER |

**输入**：

- 现网一行一轮的 `qa_rounds`。
- PRD 实施说明：界面赞/踩/未评价 ↔ 库内 `up`/`down`/空。

**输出**：

- 能把某 `round_id` 的反馈更新为 `up`/`down`/空，并带 `feedback_at`（可空，随反馈更新）。
- 新数据卷：`init.sql` 含新列。已有卷：补列后接口可用。
- round 不存在时接口失败（E2 的服务端侧）。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 一轮一个值 | 后写覆盖；无「谁评的」 | C4；CSTR-003；E8 |
| 库内枚举 | 空 / `up` / `down` | C19 |
| 界面文案 | 赞 / 踩 / 未评价 | C6；C19（不改变界面契约） |
| 无此轮 | 接口失败 | T3；E2 |

**开发任务**：

1. 新列写入 `init.sql`；`update_round`（或专用更新）允许反馈字段。
2. 为已有卷提供启动补列或等价 ALTER（CSTR-012）。
3. 增加写入接口：采用 PRD T3 拟议 `POST /api/kb/rounds/{round_id}/feedback`（`PLANNED`，不是现网已有契约）；失败按 T3（404 无此轮）。
4. 不改 `heatmap()` 公式，不改 ask 插入/更新的其它 allowed 字段语义。
5. 不编造日志保留天数（CSTR-020）。

**不在本 STEP 范围内**：

- 浏览器三态 UI（STEP-004）。
- 明细 DOM（STEP-005）。
- 按人去重、筛选（OUT-4）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 已存在 round，写入 `up` | `GET /api/kb/rounds/{id}` 可读出对应反馈 | F4 写路径 |
| 正常 | 再写入空 | 反馈回到未评价 | C4 |
| 异常 | 不存在的 `round_id` | 接口失败，不静默当成功 | E2 |
| 边界 | 新卷走 `init.sql` | 表含反馈列 | CSTR-012 |

**完成标志**：

- [ ] 对已知 `round_id` 写入 `up` 后 `GET /api/kb/rounds/{id}` 的反馈投影可读回；再写入空后投影为未评价
- [ ] 不存在的 `round_id` 接口失败
- [ ] 新卷 `init.sql` 含反馈列；已有卷经补列后同样可读写
- [ ] 未改变其它 STEP 的范围或来源需求
- [ ] 新发现的路径、符号已更新状态
- [ ] 进度已回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-004] 赞踩三态与写库失败降级

**阶段状态**：`verified`

**目标**：有完整回答正文时可按 C4 切换未评价/赞/踩；写库成功则更新该 `round_id`；写库失败或无 `round_id` 时只留浏览器并提示不进明细。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F2 | 按 C4 切换三态；写库成功则更新该 `round_id` | `PRD` |
| 验收 ID | AC2 | 赞 → 踩 → 再点踩，依次为赞、踩、未评价 | `PRD` |
| 验收 ID | AC7 | 写库失败的一轮点赞：浏览器有选中；明细无该轮；有未写入提示 | `PRD` |
| 异常 | E1、E2、E8 | 不调用或调用失败；一轮一个值 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | 消息上的 `round_id`、`logWritten` | 新发送消息可检出字段 |
| STEP-002 | 赞/踩键可见 | 有正文的回答上有二键 |
| STEP-003 | 反馈写入接口 | 对已知 `round_id` 写入后 GET 能读回 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `copy` 点击委托 | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 793–798 行 | 同区增加赞踩委托 |
| `setBanner("本轮日志未写入")` | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 482、514、519 行 | 失败提示可复用现网日志未写入语义 |
| `state.busy` / `lockGuard` | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 320–324、294–298 行 | 赞踩对已完成其它气泡可用（CSTR-013） |
| 浏览器消息 `feedback` | `planned` | `PRD` T2 | 不适用 | 空/赞/踩 |

**输入**：

- STEP-001 字段、STEP-002 键、STEP-003 接口。
- §6.2 赞/踩流程。

**输出**：

- 单条消息的 `FEEDBACK_UI` 三态机。
- `logWritten` 为真时请求更新对应 `round_id`；为假或不存在 round 时不把明细当成功。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 三态 | 空/赞/踩互斥；点另一键覆盖；再点当前键取消回未评价 | C4 |
| 写库成功 | 请求更新对应 `round_id` | §6.2 |
| 日志未写入 | 不请求；可见提示 ∈ `UNWRITTEN_HINTS` | §6.2；E1；AC7 |
| 写库成功标志与库不一致 | 接口失败；本地态可保留；可见提示 ∈ `UNWRITTEN_HINTS`；以明细为准 | E2 |
| 无 `round_id` 旧消息 | 与 E1 同类 | C6 |
| 无登录 | 一轮一个值，后写覆盖 | E8；CSTR-003 |

**开发任务**：

1. 实现 C4 状态机与按钮选中态。
2. `logWritten` 为真才调用 STEP-003 接口；失败走 E2。
3. `state.busy` 时仍允许对已完成其它气泡赞踩（CSTR-013）；不中断本轮 ask。
4. 不按人计票、不筛选明细（OUT-4）。

**不在本 STEP 范围内**：

- 明细列表/详情 DOM（STEP-005）。
- 刷新。
- 操作条出现规则（已由 STEP-002 完成）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 有完整回答，同一消息 id 上赞 → 踩 → 再点踩 | `FEEDBACK_UI` 依次为赞、踩、未评价 | AC2 |
| 异常 | 该轮 `logWritten` 为假（或无 `round_id`）点赞 | 该消息 `FEEDBACK_UI`=赞；明细 `round_id` 集合不含该 id；可见提示 ∈ `UNWRITTEN_HINTS` | AC7 |
| 异常 | E2：接口 404/失败 | 本地 `FEEDBACK_UI` 可保留；可见提示 ∈ `UNWRITTEN_HINTS` | E2 |
| 边界 | 生成中，点另一条已完成回答的赞 | 该条 `FEEDBACK_UI` 可变为赞；本轮 ask 不中断 | CSTR-013 |

**完成标志**：

- [ ] AC2、AC7 比较键通过
- [ ] 未改变其它 STEP 的范围或来源需求
- [ ] 新发现的路径、符号已更新状态
- [ ] 进度已回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-005] 问答明细展示反馈

**阶段状态**：`verified`

**目标**：打开问答明细时，详情在「回答或错误态」之后显示反馈（未评价 / 赞 / 踩）；列表能看到该列。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F4 | 详情在回答后显示反馈；列表可加一列 | `PRD` |
| 验收 ID | AC6 | 写库成功的一轮已赞：详情反馈=赞；列表可看到该列 | `PRD` |
| 决策 | C6 | 详情增加「反馈」：未评价 / 赞 / 踩 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-003 | GET 行内含反馈字段 | 直接 GET 一轮 |
| STEP-004 | 能把写库成功的一轮标为赞 | AC2 路径已通 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `openRounds` 详情 | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 710–731 行 | 现结束于「回答或错误态」 |
| `openRounds` 列表 | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 733–746 行 | 现列：时间、结果、原句 |
| `roundProjection` | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 687–708 行 | 现不投影反馈 |
| `GET /api/kb/rounds` | `existing` | `REPO_BASELINE` | SRC-API / 第 139–146 行 | 读路径；不改筛选 |

**输入**：

- STEP-003 行数据；STEP-004 写入的赞。

**输出**：

- 详情在「回答或错误态」后出现反馈文案（`FEEDBACK_UI`）。
- 列表可见反馈列。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 详情反馈位置 | 在「回答或错误态」之后 | C6；AC6 |
| 展示值 | 未评价 / 赞 / 踩 | C6 |
| 列表 | 增加可见列；用 `round_id` 定位行后读反馈 | F4；AC6 |
| 写库失败 | 明细无该轮 | AC7（本 STEP 不重复实现写入，只保证无行时不编造反馈） |

**开发任务**：

1. `roundProjection`（或等价）带出反馈并映射为界面文案。
2. 详情块追加「反馈」。
3. 列表增加可见列。
4. 不增加赞踩筛选（OUT-4）；不改顶栏入口形态（CSTR-002）。

**不在本 STEP 范围内**：

- 改热度页（OUT-10）。
- 写入接口（STEP-003）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 写库成功且消息 `round_id=R` 已赞，打开详情 `R` | 「回答或错误态」之后的反馈投影=赞 | AC6 |
| 正常 | 同上打开列表 | 列表中 `round_id=R` 的那一行反馈列=赞 | AC6 |
| 边界 | 已写入且未评价的 `round_id=R` | 详情与该列表行反馈=未评价 | C6 |

**完成标志**：

- [ ] AC6 按 `round_id` 比较通过
- [ ] 未改变其它 STEP 的范围或来源需求
- [ ] 新发现的路径、符号已更新状态
- [ ] 进度已回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-006] 刷新原地重生成

**阶段状态**：`verified`

**目标**：点刷新不新增用户消息 `id`；该条客户端 `id` 不变并进入生成中；用新 `round_id` 走现网 `POST /api/kb/ask` 全链路；对话只换这一条；明细 `round_id` 集合增加新 id、旧 id 仍在；该条消息 `round_id` 换成新 id、快照不变；busy 时拒绝并 toast「生成中…」。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F2 | 写库成功则更新**该条当前** `round_id` 的反馈；刷新后当前 id 为新轮 | `PRD` |
| 需求 ID | F3 | 原地替换；新 `round_id` 全链路；query 与首次快照按 C3；刷新后该条 `round_id` 换新 | `PRD` |
| 需求 ID | F9 | 纯错误条刷新按 F3 重跑该问句 | `PRD` |
| 验收 ID | AC3 | 用户气泡不增加；流式重画；明细 +1；`original_query` 与首次相同 | `PRD` |
| 验收 ID | AC5 | 生成未结束点刷新或发送被拒绝；本轮不中断 | `PRD` |
| 验收 ID | AC12 | 新轮按现网规则计入热度，同一功能可再 +1 | `PRD` |
| 决策 | C2、C3、C18、C23 | 形态/流水线/锁/lastChunks | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-001 | 快照与 `round_id` 在消息上 | 新消息可检出 |
| STEP-002 | 刷新键在回答与纯错误条上 | AC4 可见性已过 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `send` / `readSSE` | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 380–566 行 | 刷新抽共用 SSE，不新开公式 |
| `POST /api/kb/ask` `_ask_events` | `existing` | `REPO_BASELINE` | SRC-API / 第 176 行起、第 378 行 | 每 `round_id` 插入一行 running |
| `state.busy` / `send` 开头 | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 407 行 | 发送 busy 时直接 return |
| `lockGuard` toast | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 320–323 行 | 现文案「生成中，不能…」；刷新改用 C18「生成中…」 |
| `conv.lastChunks` | `existing` | `REPO_BASELINE` | SRC-QA-JS `emptyConv` 第 50 行；`send` 第 512 行 | C23 更新规则 |
| `heatmap()` | `existing` | `REPO_BASELINE` | SRC-LOGS / 第 162–180 行 | 不改公式；新轮进生成则 +1 |
| `pipeline.py` | `existing` | `REPO_BASELINE` | SRC-PIPELINE | 禁止修改（CSTR-001） |

**输入**：

- 消息上的 `query`、`historySnapshot`、`lastChunksSnapshot`（无快照走 E4）。
- 现网 ask SSE。

**输出**：

- 刷新行为符合 §6.2 刷新流程与 C2/C3/C18/C23。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 对话形态 | 原地替换当前回答，不新增用户气泡；旧轮次只留在明细 | C2 |
| 流水线 | 整轮重跑改写→检索→重排→生成；问句用原文；history/last_chunks 用首次快照；热度按新轮 +1 | C3 |
| 生成中刷新 | `state.busy` 拒绝；toast「生成中…」；不发起第二路、不中断本轮 | C18；E3；AC5 |
| 无快照 | 问句取相邻用户句；`last_chunks` 用空数组 | E4 |
| 刷新失败 | 该条变为现网错误提示；只留刷新 | E7；F9 |
| `conv.lastChunks` | 只刷新当前最后一条且成功时才换成新的进生成块；刷新历史中间条不改 | C23 |
| 禁止 | 把正在刷新的这句再当追问塞进 history；不建父子关联 | C3；CSTR-004 |

**开发任务**：

1. 刷新走同一把 `state.busy` 锁；toast 全文用「生成中…」（不要复用「生成中，不能…」冒充 C18）。
2. 新 `round_id` + 首次快照调用现网 ask；该条客户端 `id` 不变，改为 pending 流式重画。
3. 成功替换正文与出处；失败走现网错误条且 `ACTION_KEYS`=`{刷新}`（F9）。
4. 请求体始终用该条首次快照（`query`/`historySnapshot`/`lastChunksSnapshot` 刷新后与刷新前相等）。
5. 成功或失败落定后：该条 `round_id` 更新为本次请求的新 id；`logWritten` 取本轮 SSE；`BIND_FIELDS` 中的快照三字段不改。
6. 按 C23 更新会话级 `lastChunks`。
7. 发送在 busy 时保持现网直接 return；本轮不 abort。

**不在本 STEP 范围内**：

- 改 Prompt / pipeline / 热度公式。
- 赞踩写库（但必须让后续 004 打到新 `round_id`）。
- 内容柱样式。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 回答已结束，点刷新 | 用户消息 `id` 多重集不变；该条客户端 `id` 不变并流式重画；明细 `round_id` 集合 = 旧 ∪ {新 id}；新行 `original_query` = 该条首次 `query`；该条 `round_id` 已换成新 id，快照三字段不变 | AC3 |
| 异常 | 生成未结束点刷新 | toast 全文=「生成中…」；in-flight `POST /api/kb/ask` 次数=1；本轮 SSE 继续 | AC5 |
| 异常 | 刷新后主路径失败 | 该条为现网错误文案；`ACTION_KEYS`=`{刷新}`；`round_id` 仍为新 id | E7 |
| 边界 | 旧消息无快照 | 问句=相邻用户句；请求 `last_chunks`=[] | E4 |
| 边界 | 刷新当前最后一条成功后再追问 | 追问 `ASK_BODY.last_chunks` = 新进生成块 | C23 |
| 边界 | 刷新中间条成功后再追问 | 追问 `ASK_BODY.last_chunks` = 刷新前会话 `lastChunks` | C23 |
| 正常 | 刷新写入成功且新轮 `c_gen` 含 `feature_id=F` | 热度页 `F` 的 `count_after = count_before + 1`（或从无到 1） | AC12 |

**完成标志**：

- [ ] AC3、AC5、AC12 比较键通过
- [ ] 刷新后该条 `round_id` 为新 id 且快照未改
- [ ] 未改变其它 STEP 的范围或来源需求
- [ ] 新发现的路径、符号已更新状态
- [ ] 进度已回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-007] 右侧居中内容柱

**阶段状态**：`verified`

**目标**：右侧对话区的消息（及后续 chips、输入）共用同一条约 768px 的居中内容柱；更宽锁定，更窄随 `.qa-main` 收缩并左右约 24px。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F5 | 消息、chips、输入框同一 `max-width ≈ 768px` 居中栏 | `PRD` |
| 验收 ID | AC9 | 宽窗口：消息与输入同一条约 768px 居中栏 | `PRD` |
| 验收 ID | AC10 | 缩小 `.qa-main`：栏随宽度收缩，左右约 24px，不贴死 | `PRD` |
| 决策 | C7、C8、C17 | 只改右侧；宽度规则；阶段文案放入新内容柱 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| 无 | 现网 `.qa-main` / `.qa-row` / `.qa-composer-box` | SRC-QA-CSS |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `.qa-row` `max-width: 760px` | `existing` | `REPO_BASELINE` | SRC-QA-CSS / 第 153–158 行 | 用户靠右、与输入不同宽 |
| `.qa-composer-box` `max-width: 840px` | `existing` | `REPO_BASELINE` | SRC-QA-CSS / 第 236–241 行 | 左对齐，非同一居中栏 |
| `.qa-messages` padding `20px 22px 12px` | `existing` | `REPO_BASELINE` | SRC-QA-CSS / 第 133–138 行 | 现留白参考 |
| `.qa-conv` 左栏 | `existing` | `REPO_BASELINE` | SRC-H5-HTML / 第 77–81 行；SRC-QA-CSS `.qa-workspace` | 禁止改结构（CSTR-002） |
| 内容柱容器 | `planned` | `PLANNED` | 不适用 | 内部 class 按项目约定 |

**输入**：

- 现网右侧 `.qa-main` 布局。

**输出**：

- `CONTENT_COL` 作用于消息列；为 STEP-008/010 提供同一栏约束。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 内容柱宽度 | 最大约 768px；更宽居中锁定；更窄随 `.qa-main` 收缩，左右约 24px | C8 |
| UI 范围 | 只改右侧对话区 | C7 |

**开发任务**：

1. 把消息列纳入居中内容柱，消除「760 vs 840、一边居中一边左对齐」。
2. 宽窗口锁定；窄窗口留约 24px，不贴死。
3. 阶段槽位 `#qaStage`（及 banner 若仍属右侧对话区）放入新内容柱（C17）；不改左栏/顶栏。

**不在本 STEP 范围内**：

- 输入卡片内部结构（STEP-008）。
- 用户右块/回答去边框（STEP-009）。
- chips（STEP-010）。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 宽窗口 | `COL_PAIR` 的消息侧成立：消息列所用宽度不拉满 `.qa-main`，并与将在 008 对齐的输入栏同一套 `CONTENT_COL` | AC9 |
| 边界 | 缩小 `.qa-main` | 内容柱所用宽度随其收缩且小于 `.qa-main`；左右不贴死（约 24px） | AC10 |
| 正常 | 生成中 | `#qaStage` 位于内容柱内 | C17 |

**完成标志**：

- [ ] AC9 消息侧（与 008 共用 `COL_PAIR`）、AC10、C17 阶段文案入柱通过
- [ ] 未改变其它 STEP 的范围或来源需求
- [ ] 新发现的路径、符号已更新状态
- [ ] 进度已回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-008] Grok 式输入卡片

**阶段状态**：`verified`

**目标**：底部输入改为与内容柱等宽的圆角卡片；发送收进卡片右下；高度随内容变；Enter 发送、Shift+Enter 换行不变。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F5 | 消息、chips、输入框同一居中栏（本 STEP 负责输入同栏） | `PRD` |
| 需求 ID | F6 | 圆角卡片、轻边框/阴影，发送在卡片内右下，高度随内容变 | `PRD` |
| 验收 ID | AC9 | 消息与输入同一条约 768px 居中栏 | `PRD` |
| 决策 | C9、C11 | Grok 式卡片；空状态输入钉底与内容柱等宽 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-007 | `CONTENT_COL` 已作用于右侧 | 宽窗口消息栏约 768px 居中 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `.qa-composer` / `.qa-composer-box` | `existing` | `REPO_BASELINE` | SRC-QA-CSS / 第 231–241 行；SRC-H5-HTML / 第 86–91 行 | 现为「框+右侧发送」硬分割 |
| `#qaInput` `#qaSend` | `existing` | `REPO_BASELINE` | SRC-H5-HTML / 第 88–89 行 | 可把发送移入卡片，id 可保留 |
| Enter / Shift+Enter | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 817–822 行 | 禁止改语义（CSTR-014） |

**输入**：

- STEP-007 内容柱；现网发送快捷键。

**输出**：

- 底栏不再是「框+右侧发送」硬分割；输入与消息同一栏。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 输入框 | Grok 式圆角卡片；发送收进卡片右下；随字增高 | C9 |
| 快捷键 | Enter 发送、Shift+Enter 换行不变 | C9；CSTR-014 |
| 空状态 | 输入卡片钉在底部、与内容柱等宽 | C11 |

**开发任务**：

1. 调整 composer DOM/CSS：卡片、发送右下、随字增高。
2. 与 STEP-007 同一 `CONTENT_COL`。
3. 保持 `#qaInput`/`#qaSend` 现网事件语义（或等价绑定）。

**不在本 STEP 范围内**：

- chips。
- 消息气泡去边框。
- 改左栏。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 宽窗口 | `COL_PAIR` 成立（输入卡片所用宽度 = 消息列所用宽度，且居中） | AC9 |
| 正常 | 多行输入 | 高度随内容增加；Shift+Enter 换行、Enter 发送 | C9 |
| 边界 | 空会话 | 输入钉在底部且与内容柱等宽（`COL_PAIR`） | C11 |

**完成标志**：

- [ ] AC9 的 `COL_PAIR` 通过；CSTR-014 未回归
- [ ] 未改变其它 STEP 的范围或来源需求
- [ ] 新发现的路径、符号已更新状态
- [ ] 进度已回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-009] 消息排版

**阶段状态**：`verified`

**目标**：用户问句为栏内右侧圆角块；回答无厚边框、占满内容柱；出处与四键在回答下方。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F7 | 用户：栏内右侧圆角块。回答：无厚边框、占满栏。出处与操作条在回答下 | `PRD` |
| 验收 ID | AC11 | 同上 | `PRD` |
| 决策 | C10、C17 | 消息样式；阶段文案与出处折叠保留 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-002 | 有正文时 `ACTION_KEYS` 全集；纯错误时 `{刷新}` | AC1、AC4 |
| STEP-007 | 内容柱 | 消息已在栏内 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `.qa-row.user` `margin-left: auto` | `existing` | `REPO_BASELINE` | SRC-QA-CSS / 第 159 行 | 用户已靠右，但仍在带边框气泡内 |
| `.qa-bubble` `border: 1px solid` | `existing` | `REPO_BASELINE` | SRC-QA-CSS / 第 174–182 行 | 回答现有厚边框 |
| `citeBlock` / `data-toggle-cite` | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 202–213 行 | 出处折叠保留 |
| `#qaStage` | `existing` | `REPO_BASELINE` | SRC-H5-HTML / 第 83 行 | 阶段文案保留 |

**输入**：

- STEP-007 栏；STEP-002 的 `ACTION_KEYS`。

**输出**：

- AC11 排版（含出处与键在回答下）。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 用户问句 | 栏内右侧圆角块 | C10 |
| 回答 | 无厚边框、占满内容柱 | C10 |
| 出处与四键 | 在回答下方 | C10 |
| 保留 | 阶段文案与出处折叠 | C17 |

**开发任务**：

1. 用户句改为栏内右圆角块（可不再套回答同款厚边框）。
2. 回答去厚边框并占满栏。
3. 出处与操作条保持在回答下；不新增其它视觉项（C17）。

**不在本 STEP 范围内**：

- 四键业务行为。
- 改左栏头像策略若非 C10 所要求：C10 未要求保留/删除头像；不得借本 STEP 改左列表。头像去留若现网已有、PRD 未要求删除，则保留现网头像，避免扩大范围。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 有一问一答（完整正文） | 用户句在栏内靠右圆角块；回答无厚边框占满栏；出处与 `ACTION_KEYS`=`{复制, 赞, 踩, 刷新}` 在该回答下 | AC11 |
| 边界 | 有出处折叠 | 仍可展开/收起；折叠控件在回答下 | C17 |
| 边界 | 纯错误条 | 出处（若有）与 `ACTION_KEYS`=`{刷新}` 在该回答下 | AC11；AC4 |

**完成标志**：

- [ ] AC11 比较键通过
- [ ] 未改变其它 STEP 的范围或来源需求
- [ ] 新发现的路径、符号已更新状态
- [ ] 进度已回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-010] 空状态建议搜索

**阶段状态**：`verified`

**目标**：当前对话无消息时，中间短欢迎+说明（沿用现网文案），底部输入卡片；常驻 4 chip；heatmap `items` 有数据再追加最多 4 条模板问句；点击即按发送路径发出对应全文。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 需求 ID | F5 | chips 与消息、输入同一居中栏 | `PRD` |
| 需求 ID | F8 | 欢迎在中、输入钉底；常驻 4；有热度再追加最多 4；点击=发送 | `PRD` |
| 验收 ID | AC8 | 见验收映射 | `PRD` |
| 决策 | C12–C16、C20、C21、C22 | chips 规则与覆盖口径 | `PRD` |
| 异常 | E5、E6 | 热度空或接口失败只显示常驻 4 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-007 | 内容柱 | chips 落在同一栏 |
| STEP-008 | 输入钉底等宽 | 空状态骨架 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| `emptyHtml` | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 232–239 行 | 标题+说明；无 chip。欢迎文案沿用（C21） |
| `clearCurrent` | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 366–377 行 | 清空后 `messages` 为空，应再出 chips |
| `GET /api/kb/heatmap` `openHeatmap` | `existing` | `REPO_BASELINE` | SRC-QA-JS / 第 749–751 行；SRC-API 第 157–159 行 | 空状态只读 `items`，不改热度页 |
| `heatmap()` 排序与 unclassified | `existing` | `REPO_BASELINE` | SRC-LOGS / 第 162–180 行；SRC-HEAT-TEST | 取前 4 个 `feature_id`；未归类不占名额 |
| `load_aliases` | `existing` | `REPO_BASELINE` | SRC-ALIAS / 第 44–78 行 | C20 只读；不改 `EXTRA_ALIASES` / JSON |
| `CHIP_FIXED` 文案 | `existing` | `PRD` | SRC-PRD / §6.3 表 | 短标题与全文不得改写 |
| 空状态 chip DOM | `planned` | `PLANNED` | 不适用 | 内部命名按项目约定；C22 允许现网出现 chips |
| C20 接到前端的函数/接口 | `planned` | `UNVERIFIED` 接线 / 规则本身 `PRD` | 不适用 | 发现门：不得改别名数据 |

**输入**：

- `conv.messages.length === 0`。
- 现网 heatmap。
- `CHIP_FIXED`、C20、C16。

**输出**：

- AC8 空状态。点击 chip = 与输入框发送相同路径（A2：禁止只填不发）。
- chips 落在 `CONTENT_COL`，与输入满足 `COL_PAIR`（F5）。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| 出现条件 | 只出现在空会话（含清空后） | C12 |
| 点击 | 等于发送对应全文 | C12 |
| 常驻来源 | 高难度四题，不是 VIP/拉新四条简单句 | C13、C15 |
| 数量 | 固定 4；有排行再**增加**最多 4，不替换 | C14 |
| 热度文案 | 追加 chip 文案多重集 = `CHIP_HEAT` | C16、C20 |
| 热度取数 | `ITEMS4`；`unclassified` 不进 `items` | §6.2 |
| 欢迎正文 | 沿用现网 `emptyHtml` 标题与 brief 说明 | C21 |
| 不做 | 「那退款呢」chip | CSTR-005 |
| 覆盖 | 现网以本文为准覆盖 v3「无 chips」；不改 v3 正文 | C22 |

**C20（已确认）**：在 `load_aliases()` 合并去重后的列表中，取第一条含汉字的别名；若无汉字，取 `feature_aliases.json` 该 id 第一项；若仍无，用 `feature_id`。

**开发任务**：

1. 扩展 `emptyHtml`：保留现网欢迎文案；渲染 `CHIP_FIXED`。
2. 请求 heatmap；非 2xx 或 `items.length=0` 只保留 4 条常驻，不额外报错阻断空状态。
3. 追加热度 chip，使其文案多重集 = `CHIP_HEAT`。
4. 点击走现网 `send` 路径，全文不得截断。
5. 不改 `heatmap()`、不改顶栏热度页、不改别名表。

**不在本 STEP 范围内**：

- 改 `test_site_contract.py` 的完整 C22 覆盖（STEP-011）；本 STEP 实现行为。
- 过程栏（CSTR-009）。
- 对话中展示 chips。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 空会话 | 欢迎文案=现网 `emptyHtml` 标题与 brief 说明；输入钉底；`(短标题, query)` 多重集=`CHIP_FIXED` | AC8 |
| 正常 | 对 `CHIP_FIXED` 每一对：点短标题 | 当次 `ASK_BODY.query` 与该轮 `original_query` = 该对全文 | AC8；A7 |
| 正常 | heatmap 2xx 且 `items.length≥1` | 追加 chip 文案多重集 = `CHIP_HEAT` | AC8 |
| 异常 | heatmap 非 2xx | `CHIP_HEAT`=∅；常驻仍为 `CHIP_FIXED`；空状态可用 | E6 |
| 边界 | `items.length=0` | `CHIP_HEAT`=∅；无额外报错 | E5 |
| 边界 | 清空当前后 | 再次出现 `CHIP_FIXED` | C12 |
| 边界 | 显示名抽样（`load_aliases` 合并表） | `C20("vip")`=用户VIP；`C20("yallapay")`=链接支付 | C20 |
| 边界 | 空状态宽窗口 | chips 与输入满足 `COL_PAIR` | F5 |

**完成标志**：

- [ ] AC8 / A7 / E5 / E6 / C20 比较键通过
- [ ] 未改变其它 STEP 的范围或来源需求
- [ ] 新发现的路径、符号已更新状态
- [ ] 进度已回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

### [STEP-011] 左栏顶栏不变与契约测试覆盖

**阶段状态**：`verified`

**目标**：完成本期右侧 UI 后，左栏会话 CRUD 与四个主 Tab、顶栏配置/明细/热度入口仍在原处；现网契约测试按 C22 允许空状态 chips，仍禁止过程栏；不改 v3 正文。

**来源映射**：

| 类型 | ID | 原文短引或准确摘要 | 来源 |
|---|---|---|---|
| 验收 ID | AC13 | 仍可新建/切换/删除/清空；四个主 Tab 仍在；配置/明细/热度仍是顶栏而非新 Tab | `PRD` |
| 决策 | C7、C22 | 只改右侧；覆盖 v3 C32/AC21 的 chips 口径，不改 v3 文件 | `PRD` |
| 约束 | CSTR-002、CSTR-006、CSTR-009 | 结构与文档边界 | `PRD` |

**前置依赖**：

| STEP | 所需产物 | 验证方式 |
|---|---|---|
| STEP-002 | 右侧操作条已落地 | AC1/AC4 键类型集 |
| STEP-007 | 内容柱 | 右侧已改 |
| STEP-008 | 输入卡片 | 右侧已改 |
| STEP-009 | 消息排版 | 右侧已改 |
| STEP-010 | chips | 空状态已改 |

**参考路径与符号**：

| 路径或符号 | 状态 | 来源证据 | `source_id` / `locator` | 用途 |
|---|---|---|---|---|
| 四 Tab 按钮 | `existing` | `REPO_BASELINE` | SRC-H5-HTML / 第 17–21 行 | `MAIN_TABS` |
| `#qaTopActions` | `existing` | `REPO_BASELINE` | SRC-H5-HTML / 第 25–31 行 | 配置/重建/明细/热度 |
| `#qaConvList` / `data-qa-new` / `data-qa-clear` | `existing` | `REPO_BASELINE` | SRC-H5-HTML / 第 77–80 行 | 左栏 CRUD |
| `test_fourth_tab_and_no_chips_or_process` | `existing` | `CONTRACT` | SRC-CONTRACT / 第 9–20 行 | C22：改断言允许空状态 chips；仍禁 `#qaProcess` |
| `PRD-知识问答-v3.md` | `existing` | `PRD` | SRC-V3 | 禁止修订正文 |
| kb-qa STEP-004 AC21 原文 | `existing` | `REPO_BASELINE` | SRC-QA-STEPS / STEP-004 | 不改该验证版除非另开；现网测试以本文为准 |

**输入**：

- 已完成的右侧 UI 与 chips。
- 现网契约测试。

**输出**：

- AC13 成立。
- 契约测试与 C22 一致：允许空状态建议 chips；仍无过程栏；四 Tab 不变。

**业务定义**：

| 名称 | 定义 | 来源 |
|---|---|---|
| UI 改哪些区域 | 只改右侧对话区；左侧列表与顶栏结构不动 | C7 |
| 与 v3 空状态口径 | 不改 v3 正文；现网第四 Tab 空状态 chips、相关测试与 STEP 以本文为准，覆盖「无建议问法 chips」；无过程栏仍以 v3 为准 | C22 |

**开发任务**：

1. 回归左栏新建/切换/删除/清空与顶栏入口，确认未改结构。
2. 修改 `test_site_contract.py`：允许空状态 chips（C22）；仍断言无 `#qaProcess`。现网该测试只读 `index.html`（第 9–20 行）；若 chips 仅由 `qa.js` `emptyHtml` 注入，静态 HTML 可以继续不含 `qa-chip` 字符串，但必须增加对空状态渲染结果或 `qa.js` 的断言，使「允许 chips、禁止过程栏」可测。
3. 不修改 `site/docs/design/kb-qa/PRD-知识问答-v3.md`，不写入 `prd/design/*/PRD.md`。
4. `TOP_ACTIONS` 含重建入口 `data-qa-reindex`（C7；不把「重建」写进 AC13 正文）。

**不在本 STEP 范围内**：

- 再改检索或 Prompt。
- 重写 kb-qa 验证版全文。

**测试与验收**：

| 场景 | 输入/前提 | 预期结果 | 对应验收 ID |
|---|---|---|---|
| 正常 | 完成本期 UI 后操作左栏 | 新建/切换/删除/清空仍可用 | AC13 |
| 正常 | 看顶栏与 Tab | `MAIN_TAB_NODES` 文案多重集 = `MAIN_TABS`；`TOP_ACTIONS` 仍在 `#qaTopActions`，不是新 `.tab` | AC13 |
| 边界 | 契约测试 | 无 `#qaProcess`；空状态允许 chips（C22） | C22 |

**完成标志**：

- [ ] AC13 比较键通过；过程栏节点不存在
- [ ] v3 正文与 `prd/design/*/PRD.md` 未被本增量修改
- [ ] 未改变其它 STEP 的范围或来源需求
- [ ] 进度已回传

**完成回传**：

> 返回 STEP ID、完成/阻断状态、验证证据、变更文件、来源变化和下一可执行 STEP。不得自动启动下一 STEP。

---

## 进度

> 路径：本文件（专题夹无独立进度文档约定）  
> PRD 来源：`site/docs/design/kb-qa-feedback/PRD-知识问答-反馈与对话样式-v2.md`  
> STEP 来源：`steps-verified.md`（草稿 `steps-draft.md` 未覆盖）  
> 实施计划：[`实施计划.md`](实施计划.md)（2026-09-18 已确认三里程碑）  
> 执行记录：[`execution/知识问答-反馈与对话样式开发执行记录.md`](execution/知识问答-反馈与对话样式开发执行记录.md)  
> 当前阶段结果：`PASS_WITH_RISKS`

### 进度总览

| 完成数 | 总数 | 当前状态 |
|---|---|---|
| 10 | 11 | `IN_PROGRESS` |

> 2026-09-18 专题开发收口。代码已按 STEP-001～011 写入。STEP-004 保持 `IN_PROGRESS`：AC7 用户声明本地测不到，不补造失败轮、不宣称该比较键通过。不提交闸门，不宣布里程碑通过。

### STEP 明细

| STEP | 功能名称 | 需求 ID | 验收 ID | 前置 STEP | 状态 | 证据 |
|---|---|---|---|---|---|---|
| STEP-001 | 发送消息绑定 round_id 与刷新快照 | F2、F3 | — | 无 | `DONE` | CONV_KEY：回答/错误条均含 `BIND_FIELDS`；刷新后快照未改 |
| STEP-002 | 操作条出现规则与复制 | F1、F9 | AC1、AC4 | 无 | `DONE` | AC4 `{刷新}`；成功条四键。用户本机 Docker 确认复制正常（AC1） |
| STEP-003 | 反馈落库列、补列与写入接口 | F2、F4 | — | 无 | `DONE` | 已有卷两列存在；POST up/空后 GET 回读；404 `未找到该轮` |
| STEP-004 | 赞踩三态与写库失败降级 | F2 | AC2、AC7 | 001、002、003 | `IN_PROGRESS` | AC2 已过。AC7：用户 2026-09-18 声明本地测不到，收口备注，无 RUNTIME |
| STEP-005 | 问答明细展示反馈 | F4 | AC6 | 003、004 | `DONE` | 列表反馈列=赞；详情在「回答或错误态」后「反馈 赞」 |
| STEP-006 | 刷新原地重生成 | F3、F9 | AC3、AC5、AC12 | 001、002 | `DONE` | AC3 同客户端 id、新 round、原句不变；AC12 vip count +1。用户本机 Docker 确认刷新正常（AC5） |
| STEP-007 | 右侧居中内容柱 | F5 | AC9、AC10 | 无 | `DONE` | `colW=768` `mainW=1987` padding `0 24px` 不贴死 |
| STEP-008 | Grok 式输入卡片 | F5、F6 | AC9 | 007 | `DONE` | `msgW=boxW=720` |
| STEP-009 | 消息排版 | F7 | AC11 | 002、007 | `DONE` | 用户右块 `flex-end`；成功四键/错误仅刷新在下 |
| STEP-010 | 空状态建议搜索 | F5、F8 | AC8 | 007、008 | `DONE` | CHIP_FIXED 发出全文；C20 `vip→用户VIP` |
| STEP-011 | 左栏顶栏不变与契约测试覆盖 | C7、C22 | AC13 | 002、007–010 | `DONE` | 四 Tab/顶栏仍在；chips 契约通过；v3 未改 |

### 阻断与来源变化

| 日期 | STEP | 类型 | 证据或变化 | 处理结果 |
|---|---|---|---|---|
| 2026-09-18 | M1 RUNTIME | 环境 | Docker 守护进程未运行，无法 `compose up` 验 MySQL 补列与 ask SSE | 随后 Docker 已启动；用户确认复制/刷新正常 |
| 2026-09-18 | STEP-002/006 | 验证 | 自动化采不到 toast 全文 | 用户本机 Docker 确认复制、刷新正常，两 STEP 标 DONE |
| 2026-09-18 | STEP-004 | 验证 | AC7 用户声明本地测不到 | 缺口已备注；专题开发收口；004 不标 DONE；不交闸门 |

状态只使用 `NOT_STARTED`、`IN_PROGRESS`、`DONE`、`BLOCKED`。只有完成标志全部有验证证据时才能标为 `DONE`。

---

## 自检

- [x] 所有需求和验收均映射到 STEP（F1–F9；AC1–AC13）
- [x] 每个 STEP 的需求 ID、验收 ID、依赖和范围明确（001/003 无独立 AC，只承担可分割子条款，已标明）
- [x] 未增加 PRD 中不存在的业务语义
- [x] 未使用 `[自定义]` 补造业务字段或值
- [x] 所有路径和符号标记 `existing`、`planned` 或 `unverified`
- [x] `existing` 引用均绑定实际来源 ID 与定位符
- [x] 关键 `unverified` 未被表述为可执行事实（C20 接线为发现门）
- [x] 草稿原文未覆盖；本文件为验证版，仍含非阻断风险
- [x] 阶段只返回五种结果之一并在本阶段停止

## 非阻断风险

1. 已有 MySQL 卷不会因改 `init.sql` 自动加列；反馈依赖启动补列或手工 ALTER（PRD §9.1 / T7）。  
2. 写入路由现网不存在；本文件采用 PRD T3 拟议 `POST /api/kb/rounds/{round_id}/feedback`，属 `PLANNED`。  
3. C20 规则已确认，但 `heatmap` 只返回 `feature_id`，显示名如何接到 `qa.js` 现网无唯一接口。  
4. 现网 `refuse` 事件把拒答写成 `role: "system"`；C5 以「有完整回答正文」为准，实施不得被当前 role 字段带偏。  
5. v3 AC21 / `test_fourth_tab_and_no_chips_or_process` 与本期 C22 字面冲突；处理方式是改现网测试、不改 v3 正文。  
6. 本轮无 `RUNTIME`，不描述线上已验证。  
7. 刷新 toast 必须用 C18「生成中…」，不得用现网 `lockGuard` 的「生成中，不能…」冒充。  
8. C8/AC9/AC10「约 768px / 约 24px」不设硬像素门；可测的是 `COL_PAIR` 与不贴死。  
9. PRD E1 验收编号写成 AC6，与 E1/AC7 正文不一致；覆盖以各条正文为准，不改 PRD。  
10. 本机 pytest 解释器路径未在本轮核实 `.venv`。

## 阶段结果

`PASS_WITH_RISKS`

本文件是 `steps-verified.md`。不得自动开始写业务代码，不得生成里程碑计划（除非另调对应 Skill）。
