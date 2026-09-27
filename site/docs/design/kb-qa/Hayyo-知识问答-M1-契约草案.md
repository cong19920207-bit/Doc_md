---
title: "Hayyo-知识问答-M1-契约草案"
status: "GATE_EVIDENCE_READY"
milestone: "M1"
created: "2026-09-17"
note: "执行器提交的临时契约增量；不判定里程碑通过。正式契约路径未定。"
---

# Hayyo-知识问答-M1-契约草案

覆盖 STEP-001、002、003、004、005。权威需求仍是 PRD v3。

## 本机依赖

| 对象 | 约定 |
|---|---|
| 启动 | 在 `site/` 执行 `docker compose up -d`；仓库根则 `docker compose -f site/docker-compose.yml up -d`。仓库根无 compose 文件 |
| 服务 | `web`、`qdrant`、`mysql`、`kb-api` |
| 宿主机发布 | 全部 `127.0.0.1`：`18765→80`、`18766→3306`、`18767→6333`；`kb-api` 不发布 |
| 禁止 | 宿主机 `3306`/`3307`、`0.0.0.0` 发布 |
| 浏览器入口 | `http://127.0.0.1:18765/feature-interaction/` |

## HTTP 前缀与密钥

| 对象 | 约定 |
|---|---|
| 前缀 | `/api/kb`；浏览器只打本机 nginx |
| 反代 | `site/docker/nginx.conf` `location /api/kb/` → `http://kb-api:8080`；`proxy_buffering off` |
| Key | `DASHSCOPE_API_KEY`、`DEEPSEEK_API_KEY` 仅服务端环境变量；禁止进 git / 前端 / 健康检查明文 |
| 鉴权 | 本期中间件 pass-through |

## 健康检查 `GET /api/kb/health`

| 字段 | 语义 |
|---|---|
| `qdrant_ready` | bool |
| `config_ready` | bool |
| `key_dashscope` / `key_deepseek` | `已配置` \| `未配置` |
| `chunk_count` | 非负整数（块数口径属 008，本里程碑可出现） |
| 明文 | 响应不得含 Key 字符串 |

空 Key 提问：`POST /api/kb/ask` SSE `error.type=missing_key`，说明可读。

## 第四 Tab 与正式壳

| 对象 | 约定 |
|---|---|
| `MAIN_TABS` | 文本多重集 {「客户端 ↔ 后台」,「客户端交叉」,「文档索引」,「知识问答」}，大小 4 |
| `MAIN_TAB_NODES` | `header .tabs .tab`，用 `data-view`，不用 `role=tab` |
| 问答根 | `#qaWorkspace`；`id ≠ kbWorkspace`；不是 `#kbWorkspace` 的子节点 |
| 正式空会话 | chip=0（无 `[data-suggest]` / `.qa-chip`）；过程栏=0（无 `#qaProcess`） |
| 明细/热度 | 按钮 ∉ `MAIN_TAB_NODES` |

## 浏览器多会话

| 对象 | 约定 |
|---|---|
| 存储 | localStorage 键 `hayyo-kb-qa-conversations-v1`；最多 40 条 |
| 标题 | `truncate18` = 去空白后前 18 字，无省略号 |
| 隔离 | 不同 `conv_id` 的 `messages` `(role,text)` 多重集不相交 |
| 删除 | 列表与 localStorage 的 id 集合均不含已删 id |
| 本里程碑 | 发问只需用户气泡；不要求生成成功 |
