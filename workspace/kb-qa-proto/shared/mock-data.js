/**
 * 知识问答原型 mock 数据。
 * 摘录来自真实 brief；「演示冲突」块仅用于 AC5，不写入 prd/。
 */
(function () {
  const SYSTEM_PROMPT = "只根据提供的文档块回答 Hayyo 规则问题，并给出出处。不得添加未召回块中的数字、状态、接口、字段。冲突则并列摘录、不选边。证据不足则声明文档未写。回答不是需求合同，权威仍是各功能 PRD.md。";

  const REWRITE_PROMPT = "把用户本轮原句改写成可检索的独立问句，并判断是否与上一轮同一主题。保留功能 ID、字段名、数字原样。已独立则原样返回。禁止在改写时发明版本号或数值。只产出独立问句 + 是否同一主题。";

  const CHUNKS = {
    "vip.logic-wealth": {
      path: "prd/design/vip/brief/current.md",
      heading: "财富值与周期",
      anchor: "logic-wealth",
      chunk_id: "vip.logic-wealth",
      feature_id: "vip",
      collection: "hayyo-client",
      text: "VIP 是基于付费贡献的保级身份。计量单位为财富值。来源：商店充值、币商以及后续第三方充值得到的金币；运营后台加币且操作类型为「对掉单的用户补单」。比例 200 金币 = 1 财富值。其它得金币方式不加财富值（含非上述类型的后台加币、系统返币）。后台扣币不减财富值。达到最高等级保级线后财富值停在保级线，不再提升。每轮 30 天，自首次充值（财富值有数字）起算。结算统一每天 GMT+3 12 点。"
    },
    "vip.logic-cycle": {
      path: "prd/design/vip/brief/current.md",
      heading: "升级、保级、降级、退款",
      anchor: "logic-cycle",
      chunk_id: "vip.logic-cycle",
      feature_id: "vip",
      collection: "hayyo-client",
      text: "保级：到期未达下一档、但达到本级保级财富值。财富值重置为本级初始，保持本级特权，开新周期。退款：按 200 退款金币 = 3 财富值扣除。因退款导致降级：保持退款后的财富值，不把充值财富值补回上一周期初始；发放上一档特权并回收当前气泡、框、座驾；开新周期。"
    },
    "admin.referral": {
      path: "prd/design/admin/brief/current.md",
      heading: "拉新后台",
      anchor: "admin-referral",
      chunk_id: "admin.referral",
      feature_id: "admin",
      collection: "hayyo-admin",
      text: "C 端与后台订单终态均为「已发放」，不再用「已领取」。奖励组：通用奖励组、新用户奖励组各一套。列表按生成时间倒序；配置组名称支持连贯字符搜索。有进行中活动占用则不可删。组内类型：礼物、VIP、道具（头像框、座驾、房间背景）、宝石。V1.4.0：改为填商品 ID，名称只读（后台展示，非前端、不开放编辑）。"
    },
    "referral.logic-reward-record": {
      path: "prd/design/referral/brief/current.md",
      heading: "奖励记录",
      anchor: "logic-reward-record",
      chunk_id: "referral.logic-reward-record",
      feature_id: "referral",
      collection: "hayyo-client",
      text: "用户端状态：不展示审核中、待领取；「已领取」改为「已发放」（个人和团队）。用户端出现「已发放」，表示该笔已经审核完成并发放；未审完的不会在用户端显示成已发放。C 端与后台终态都是「已发放」。"
    },
    "merchant.logic-transfer": {
      path: "prd/design/merchant/brief/current.md",
      heading: "转账",
      anchor: "logic-transfer",
      chunk_id: "merchant.logic-transfer",
      feature_id: "merchant",
      collection: "hayyo-client",
      text: "从代理账户扣可交易金币，转入收款用户钱包金币（不可再交易）。最低金额 10,000（服务端可配）；小于最低时转账按钮不点亮，收起输入框 toast「每次最少转账10000金额哦~」。输入大于代理余额则自动改为余额。冻结中限制给用户转账。"
    },
    "demo.conflict-old": {
      path: "prd/design/referral/brief/current.md",
      heading: "范围（演示冲突摘录）",
      anchor: "scope",
      chunk_id: "demo.conflict-old",
      feature_id: "referral",
      collection: "hayyo-client",
      demoOnly: true,
      text: "【演示冲突块，非正式 brief】用户端奖励终态仍展示「已领取」。未审完的订单也可以在用户端看成已领取。"
    }
  };

  const DOCS = [
    { path: "prd/design/vip/brief/current.md", name: "VIP · 现行说明", feature_id: "vip" },
    { path: "prd/design/admin/brief/current.md", name: "运营后台 · 现行说明", feature_id: "admin" },
    { path: "prd/design/referral/brief/current.md", name: "拉新 · 现行说明", feature_id: "referral" },
    { path: "prd/design/merchant/brief/current.md", name: "币商 · 现行说明", feature_id: "merchant" }
  ];

  const SUGGESTIONS = [
    "保级扣的是财富值还是金币",
    "那退款呢",
    "VIP11 保级线具体是多少",
    "拉新后台奖励组有哪些字段",
    "币商转账最低多少",
    "拉新用户端终态是已领取还是已发放"
  ];

  const SCENARIOS = [
    { id: "normal", label: "正常" },
    { id: "no_key", label: "未配 Key" },
    { id: "empty_index", label: "索引未就绪" },
    { id: "rewrite_fail", label: "改写失败" },
    { id: "gen_fail", label: "生成失败" },
    { id: "gen_interrupt", label: "流中断" },
    { id: "empty_result", label: "强制空结果" },
    { id: "conflict", label: "演示冲突" }
  ];

  const LOCKED = {
    embeddingModel: "text-embedding-v4",
    embeddingDim: 1024,
    rerankModel: "qwen3.7-text-rerank",
    answerModel: "deepseek-flash",
    rewriteModel: "deepseek-flash",
    thinking: "disabled",
    collections: ["hayyo-client", "hayyo-admin"],
    chunkPolicy: "仅 chunk:default；两库都搜；无范围过滤",
    dashscopeKey: "已配置",
    deepseekKey: "已配置"
  };

  const DEFAULT_CONFIG = {
    recallK: 64,
    rerankN: 8,
    historyTurns: 5,
    temperature: 0.2,
    systemPrompt: SYSTEM_PROMPT,
    rewritePrompt: REWRITE_PROMPT
  };

  const REINDEX_RESULT = {
    scanned: 24,
    added: [
      {
        path: "prd/design/vip/brief/current.md",
        chunk_id: "vip.logic-cycle",
        action: "改",
        old_hash: "a1f3c8",
        new_hash: "b9e210"
      }
    ],
    created: [
      {
        path: "prd/design/admin/brief/current.md",
        chunk_id: "admin.referral",
        action: "增",
        old_hash: "",
        new_hash: "c4d771"
      }
    ],
    deleted: [
      {
        path: "prd/design/lottery/brief/current.md",
        chunk_id: "lottery.logic-old",
        action: "删",
        old_hash: "88aa01",
        new_hash: ""
      }
    ],
    failed: [
      {
        path: "prd/design/admin/brief/current.md",
        chunk_id: "admin.oversize-demo",
        reason: "超过 text-embedding-v4 上限 8192 token，该块不入库、不二次切、不截断"
      }
    ]
  };

  window.KbQaMockData = {
    CHUNKS: CHUNKS,
    DOCS: DOCS,
    SUGGESTIONS: SUGGESTIONS,
    SCENARIOS: SCENARIOS,
    LOCKED: LOCKED,
    DEFAULT_CONFIG: DEFAULT_CONFIG,
    REINDEX_RESULT: REINDEX_RESULT
  };
})();
