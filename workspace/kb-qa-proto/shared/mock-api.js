/**
 * 知识问答原型假接口：改写、混合召回、重排、流式回答、重建、配置、健康检查。
 * 不连接外网；延迟只为演示阶段感，不是验收数字。
 */
(function () {
  const DATA = () => window.KbQaMockData;

  function delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function chunkOf(id) {
    return DATA().CHUNKS[id];
  }

  function cloneChunk(id) {
    const c = chunkOf(id);
    return c ? Object.assign({}, c) : null;
  }

  function domainOfIntent(intent) {
    if (intent.indexOf("vip") === 0) return "vip";
    if (intent === "admin-referral") return "admin";
    if (intent === "merchant-transfer") return "merchant";
    if (intent === "conflict") return "referral";
    return "other";
  }

  function detectIntent(text) {
    const t = String(text || "");
    if (/VIP\s*11|保级线|具体是多少|财富值表|等级所需/.test(t)) return "vip-numbers";
    if (/奖励组|拉新后台|后台字段/.test(t)) return "admin-referral";
    if (/币商|转账|最低/.test(t) && !/退款/.test(t)) return "merchant-transfer";
    if (/已领取|已发放|终态/.test(t)) return "conflict";
    if (/退款/.test(t)) return "vip-refund";
    if (/保级|财富值|金币/.test(t)) return "vip-wealth";
    return "unknown";
  }

  function lastDomain(history) {
    if (!history || !history.length) return "";
    for (let i = history.length - 1; i >= 0; i -= 1) {
      const turn = history[i];
      if (turn && turn.intent) return domainOfIntent(turn.intent);
    }
    return "";
  }

  function rewriteQuery(original, intent) {
    if (intent === "vip-refund" && /那|呢|还|怎么/.test(original)) {
      return "VIP 保级体系中退款如何扣除财富值，以及因退款导致降级时如何处理";
    }
    if (intent === "vip-wealth") return "VIP 保级扣减的是财富值还是金币，财富值与金币如何换算";
    if (intent === "vip-numbers") return "VIP11 以及各等级保级线、所需财富值的具体数字表";
    if (intent === "admin-referral") return "拉新后台奖励组有哪些字段、类型和商品 ID 规则";
    if (intent === "merchant-transfer") return "币商从代理账户转账给用户的最低金额与限制";
    if (intent === "conflict") return "拉新用户端奖励记录终态是已领取还是已发放";
    return original;
  }

  function chunksForIntent(intent, scenario) {
    if (scenario === "empty_result") return [];
    if (scenario === "conflict" || intent === "conflict") {
      return ["referral.logic-reward-record", "demo.conflict-old", "admin.referral"].map(cloneChunk).filter(Boolean);
    }
    if (intent === "vip-wealth") return ["vip.logic-wealth", "vip.logic-cycle"].map(cloneChunk);
    if (intent === "vip-refund") return ["vip.logic-cycle", "vip.logic-wealth"].map(cloneChunk);
    if (intent === "vip-numbers") return ["vip.logic-wealth", "vip.logic-cycle"].map(cloneChunk);
    if (intent === "admin-referral") return ["admin.referral", "referral.logic-reward-record"].map(cloneChunk);
    if (intent === "merchant-transfer") return ["merchant.logic-transfer"].map(cloneChunk);
    return [];
  }

  function mergePrev(chunks, prevChunks, sameTopic, n) {
    const map = {};
    (chunks || []).concat(sameTopic ? (prevChunks || []) : []).forEach((c) => {
      if (c && c.chunk_id && !map[c.chunk_id]) map[c.chunk_id] = c;
    });
    return Object.keys(map).map((k) => map[k]).slice(0, n);
  }

  function buildAnswer(intent, chunks) {
    if (!chunks.length) {
      return {
        refused: true,
        conflict: false,
        body: "文档未写。当前重排后没有可依据的块。请改问法，或打开文档索引阅读 brief / PRD。"
      };
    }
    if (intent === "vip-numbers") {
      return {
        refused: true,
        conflict: false,
        body: "文档未写。VIP 各等级所需财富值 / 保级线数字，brief 写明「原文未写入本功能 PRD，本文不编造」，召回块里也没有这张数字表。下面是相关候选，请打开原文核对，不要把本回答当合同。"
      };
    }
    if (intent === "conflict" || (chunks.some((c) => c.demoOnly) && chunks.some((c) => c.chunk_id === "admin.referral" || c.chunk_id === "referral.logic-reward-record"))) {
      return {
        refused: false,
        conflict: true,
        body: "召回块对「拉新奖励终态」表述互斥，这里并列摘录，不选边。\n\n- 正式 brief：C 端与后台订单终态均为「已发放」，不再用「已领取」。用户端不展示审核中、待领取。\n- 演示冲突块：用户端奖励终态仍展示「已领取」，未审完也可看成已领取。\n\n请点出处读原文。后文覆盖前文仍由人判断；问答层不能当需求合同。"
      };
    }
    if (intent === "vip-wealth") {
      return {
        refused: false,
        conflict: false,
        body: "保级计量的是财富值，不是直接扣金币。VIP 是基于付费贡献的保级身份，计量单位为财富值。商店充值、币商以及补单类加币按 200 金币 = 1 财富值计入。其它得金币方式不加财富值；后台扣币不减财富值。保级：到期未达下一档、但达到本级保级财富值时，财富值重置为本级初始，保持本级特权。"
      };
    }
    if (intent === "vip-refund") {
      return {
        refused: false,
        conflict: false,
        body: "退款按 200 退款金币 = 3 财富值扣除。若因退款导致降级：保持退款后的财富值，不把充值财富值补回上一周期初始；发放上一档特权并回收当前气泡、框、座驾；开新周期。这与到期保级（财富重置为本级初始）不是同一条路径。"
      };
    }
    if (intent === "admin-referral") {
      return {
        refused: false,
        conflict: false,
        body: "拉新后台有两套奖励组：通用奖励组、新用户奖励组。列表按生成时间倒序；配置组名称支持连贯字符搜索；有进行中活动占用则不可删。组内类型：礼物、VIP、道具（头像框、座驾、房间背景）、宝石。V1.4.0 改为填商品 ID，名称只读（后台展示，非前端、不开放编辑）。出处在 admin brief 的拉新后台页。"
      };
    }
    if (intent === "merchant-transfer") {
      return {
        refused: false,
        conflict: false,
        body: "币商转账从代理账户扣可交易金币，转入用户钱包后不可再交易。最低金额 10,000（服务端可配）；小于最低时转账按钮不点亮，toast「每次最少转账10000金额哦~」。账户冻结或退款欠平台期间限制给用户转账。"
      };
    }
    return {
      refused: true,
      conflict: false,
      body: "文档未写所问事实。已列出本轮候选块，请打开文档索引。"
    };
  }

  async function health(scenario) {
    await delay(80);
    if (scenario === "no_key") {
      return {
        ok: false,
        code: "E1",
        qdrant: true,
        indexed: true,
        dashscopeKey: false,
        deepseekKey: false,
        message: "未配置 API Key（DASHSCOPE_API_KEY / DEEPSEEK_API_KEY）。本轮不调用外网模型。文档索引仍可打开。"
      };
    }
    if (scenario === "empty_index") {
      return {
        ok: false,
        code: "E2",
        qdrant: false,
        indexed: false,
        dashscopeKey: true,
        deepseekKey: true,
        message: "索引未就绪：Qdrant 不可用或点数为 0。可点「重建索引」。文档索引关键词检索仍可用。"
      };
    }
    return {
      ok: true,
      code: "ok",
      qdrant: true,
      indexed: true,
      dashscopeKey: true,
      deepseekKey: true,
      message: "索引就绪 · Key 已配置"
    };
  }

  async function rewrite(original, history, scenario, config) {
    await delay(420);
    if (scenario === "rewrite_fail") {
      const err = new Error("REWRITE_FAIL");
      err.code = "E7";
      throw err;
    }
    const intent = detectIntent(original);
    const query = rewriteQuery(original, intent);
    const prev = lastDomain(history);
    const cur = domainOfIntent(intent);
    const sameTopic = !prev || (cur !== "other" && prev === cur);
    return {
      query: query,
      same_topic: sameTopic,
      intent: intent,
      historyUsed: Math.min((history || []).length, (config && config.historyTurns) || 5)
    };
  }

  async function retrieveAndRerank(input) {
    await delay(520);
    const n = Math.max(1, Number(input.config && input.config.rerankN) || 8);
    const k = Math.max(n, Number(input.config && input.config.recallK) || 64);
    let chunks = chunksForIntent(input.intent, input.scenario);
    chunks = mergePrev(chunks, input.prevChunks, input.sameTopic, n);
    const recalled = Math.min(k, Math.max(chunks.length, chunks.length ? 12 : 0));
    return {
      recalled: recalled,
      chunks: chunks.slice(0, n)
    };
  }

  async function* streamText(text, options) {
    const opts = options || {};
    const interruptAt = opts.interrupt ? Math.max(12, Math.floor(String(text).length * 0.38)) : null;
    let acc = "";
    const src = String(text);
    const step = 3;
    for (let i = 0; i < src.length; i += step) {
      await delay(22);
      acc += src.slice(i, i + step);
      yield acc;
      if (interruptAt != null && acc.length >= interruptAt) {
        const err = new Error("STREAM_INTERRUPT");
        err.code = "E4";
        err.partial = acc;
        throw err;
      }
    }
  }

  async function reindex() {
    await delay(700);
    return JSON.parse(JSON.stringify(DATA().REINDEX_RESULT));
  }

  window.KbQaMockApi = {
    delay: delay,
    detectIntent: detectIntent,
    health: health,
    rewrite: rewrite,
    retrieveAndRerank: retrieveAndRerank,
    buildAnswer: buildAnswer,
    streamText: streamText,
    reindex: reindex
  };
})();
