# -*- coding: utf-8 -*-
"""运行时配置。端口/前缀/目录按实施发现门写入。"""
from __future__ import annotations

import os
from pathlib import Path


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


REPO_ROOT = Path(env("REPO_ROOT", "/repo")).resolve()
DATA_DIR = Path(env("DATA_DIR", "/data")).resolve()
CONFIG_PATH = DATA_DIR / "kb-config.json"
ALIASES_PATH = Path(env("ALIASES_PATH", "/app/feature_aliases.json"))

QDRANT_URL = env("QDRANT_URL", "http://qdrant:6333")
MYSQL_HOST = env("MYSQL_HOST", "mysql")
MYSQL_PORT = int(env("MYSQL_PORT", "3306") or "3306")
MYSQL_USER = env("MYSQL_USER", "hayyo")
MYSQL_PASSWORD = env("MYSQL_PASSWORD", "hayyo_kb_local")
MYSQL_DATABASE = env("MYSQL_DATABASE", "hayyo_kb")

# 空库引导超管：仅账号表为空时创建一次，不因重启改口令。
KB_BOOTSTRAP_USER = env("KB_BOOTSTRAP_USER", "admin")
KB_BOOTSTRAP_PASSWORD = env("KB_BOOTSTRAP_PASSWORD")
AUTH_COOKIE_NAME = env("KB_AUTH_COOKIE_NAME", "hayyo_kb_sid")
AUTH_SESSION_SECONDS = 7 * 24 * 3600
AUTH_LOCK_FAILS = 5
AUTH_LOCK_SECONDS = 15 * 60
PBKDF2_ITERATIONS = int(env("KB_PBKDF2_ITERATIONS", "210000") or "210000")

DASHSCOPE_API_KEY = env("DASHSCOPE_API_KEY")
DEEPSEEK_API_KEY = env("DEEPSEEK_API_KEY")
DASHSCOPE_BASE = env("DASHSCOPE_BASE", "https://dashscope.aliyuncs.com")
DEEPSEEK_BASE = env("DEEPSEEK_BASE", "https://api.deepseek.com")

COLLECTION_CLIENT = "hayyo-client"
COLLECTION_ADMIN = "hayyo-admin"
EMBED_MODEL = "text-embedding-v4"
EMBED_DIM = 1024
EMBED_TOKEN_LIMIT = 8192
RERANK_MODEL = "qwen3.7-text-rerank"
LLM_MODEL = "deepseek-flash"
THINKING = "关闭"

DEFAULT_K = 64
DEFAULT_N = 8
DEFAULT_HISTORY = 5
DEFAULT_TEMPERATURE = 0.2

# 已落盘的旧默认文案；加载配置时若完全相等则迁到现行 Prompt。
LEGACY_SYSTEM_PROMPT = (
    "只根据提供的文档块回答 Hayyo 规则问题，并给出出处。"
    "不得添加未进入本轮生成集的块中的数字、状态、接口、字段。"
    "冲突则并列摘录、不选边，不得把其中一条标为唯一现行。"
    "证据不足或文档未写具体数字时声明「文档未写」。"
    "某点名功能在本轮生成集中无块时，必须声明该功能文档未写，不得用其它功能块编该功能规则。"
    "回答不是需求合同，权威仍是各功能 PRD.md。"
)
LEGACY_SYSTEM_PROMPT_V2 = (
    "只根据提供的文档块回答 Hayyo 规则问题，并给出出处。"
    "不得添加未进入本轮生成集的块中的数字、状态、接口、字段。"
    "冲突则并列摘录、不选边，不得把其中一条标为唯一现行。"
    "先回答用户本轮问到的点；能从生成集摘录则摘录，不要先整轮宣判文档未写。"
    "生成集已写「本版不做」「不编造」「原文未写入」时，原句引用，这是已写明的范围，不得改口为文档未写。"
    "仅当用户所问事实在本轮生成集中找不到时，才声明该点「文档未写」。"
    "未问到的缺表、缺数字不要为了四个字再附一句文档未写。"
    "某点名功能在本轮生成集中无块时，必须声明该功能文档未写，不得用其它功能块编该功能规则。"
    "回答不是需求合同，权威仍是各功能 PRD.md。"
)
LEGACY_REWRITE_PROMPT = (
    "把用户本轮原句改写成可检索的独立问句，并判断是否与上一轮同一主题。"
    "保留功能 ID、字段名、数字原样。已独立则原样返回。"
    "禁止在改写时发明功能 ID、版本号或数值。"
    "named_feature_ids 只能从给定的已有功能 ID 列表中选择，可为空数组。"
    "只输出 JSON："
    '{"rewrite_query":"...","same_topic":true,"named_feature_ids":[]}'
)
LEGACY_SYSTEM_PROMPTS = (LEGACY_SYSTEM_PROMPT, LEGACY_SYSTEM_PROMPT_V2)
LEGACY_REWRITE_PROMPTS = (LEGACY_REWRITE_PROMPT,)

SYSTEM_PROMPT = (
    "只根据提供的文档块回答 Hayyo 规则问题。"
    "不得添加未进入本轮生成集的块中的数字、状态、接口、字段。"
    "冲突则并列摘录、不选边，不得把其中一条标为唯一现行。"
    "先回答用户本轮问到的点；能从生成集摘录则摘录，不要先整轮宣判文档未写。"
    "生成集已写「本版不做」「不编造」「原文未写入」时，原句引用，这是已写明的范围，不得改口为文档未写。"
    "仅当用户所问事实在本轮生成集中找不到时，才声明该点「文档未写」。"
    "未问到的缺表、缺数字不要为了四个字再附一句文档未写。"
    "某点名功能在本轮生成集中无块时，必须声明该功能文档未写，不得用其它功能块编该功能规则。"
    "出处写块的 chunk_id（如 vip.logic-pretty），不要用 [1][2] 这类阿拉伯数字序号。"
    "按每块的 feature_id 与标题归属引用；同一块里多套数字必须分说"
    "（VIP 身份档、靓号档、用户经验等级），禁止把一块里的数字接到另一套名称上。"
    "一句多问须分段作答；交叉组合在块中没有写明则声明该组合文档未写，不得把多份规则相乘合成新门槛。"
    "用户问句中的数字只用于定位问题，不能当成生成集里新出现的规则数字。"
    "回答不是需求合同，权威仍是各功能 PRD.md。"
)

REWRITE_PROMPT = (
    "把用户本轮原句改写成可检索的独立问句，并判断是否与上一轮同一主题。"
    "独立问句：保留功能 ID、字段名、数字与专名原样；语句已完整时不要改数字，可补入口语对应的功能名便于检索。"
    "named_feature_ids：根据问句里出现的产品能力，从已有功能 ID 中列出所有相关项；"
    "一句多问、多个专名必须拆到多个 ID，宁多勿漏。不要因为问句已经独立完整就省略点名。"
    "必须对照用户消息中的「口语→功能 ID」表。"
    "易混项：链接支付 / YallaPay → yallapay（不是钱包充值 recharge）；"
    "体验券 / 膨胀券 → coupon，并通常同时点 vip；"
    "Bounty Racing / 水果机 / Game Center 数值游戏 → room-game；"
    "Ludo 等休闲三款 → casual-game；Billionaires / 充值榜 → ranking；"
    "代理转账 / 币商代充 → merchant；充值任务进度 → checkin-task。"
    "「等级」可能同时对应 user-level（平台经验等级）、vip（付费身份档）、"
    "mall 或 vip 块中的靓号档，问到几套就点几个。"
    "禁止发明表中没有的功能 ID、版本号或数值。"
    "named_feature_ids 只能从给定的已有功能 ID 列表中选择，可为空数组。"
    "只输出 JSON："
    '{"rewrite_query":"...","same_topic":true,"named_feature_ids":[]}'
)
