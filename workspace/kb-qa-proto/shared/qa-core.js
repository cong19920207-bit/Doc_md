/**
 * 知识问答原型会话状态机。
 * 多对话存在 localStorage，刷新可恢复；配置另存 volume 模拟键。
 */
(function () {
  const CFG_KEY = "hayyo-kb-qa-proto-config-v1";
  const SCN_KEY = "hayyo-kb-qa-proto-scenario";
  const CONV_KEY = "hayyo-kb-qa-proto-conversations-v1";
  const MAX_CONVS = 40;

  function uid(prefix) {
    return prefix + "-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 7);
  }

  function loadConfig() {
    const base = Object.assign({}, window.KbQaMockData.DEFAULT_CONFIG);
    try {
      const raw = localStorage.getItem(CFG_KEY);
      if (!raw) return base;
      const parsed = JSON.parse(raw);
      ["recallK", "rerankN", "historyTurns", "temperature", "systemPrompt", "rewritePrompt"].forEach((k) => {
        if (parsed[k] !== undefined && parsed[k] !== null && parsed[k] !== "") base[k] = parsed[k];
      });
    } catch (e) { /* 缺文件或坏 JSON 用 PRD 默认值 */ }
    return base;
  }

  function saveConfig(cfg) {
    localStorage.setItem(CFG_KEY, JSON.stringify(cfg));
  }

  function titleFromText(text) {
    const t = String(text || "").replace(/\s+/g, " ").trim();
    if (!t) return "新对话";
    return t.length > 18 ? t.slice(0, 18) + "…" : t;
  }

  function emptyConv() {
    return {
      id: uid("c"),
      title: "新对话",
      titleLocked: false,
      messages: [],
      lastChunks: [],
      lastIntent: "",
      lastRewrite: null,
      lastSameTopic: null,
      lastOriginal: "",
      lastRecalled: 0,
      lastRoundChunks: [],
      citationsOpen: {},
      updatedAt: Date.now()
    };
  }

  function sanitizeConv(raw) {
    const c = emptyConv();
    if (!raw || typeof raw !== "object") return c;
    c.id = String(raw.id || c.id);
    c.title = String(raw.title || "新对话");
    c.titleLocked = Boolean(raw.titleLocked);
    c.messages = Array.isArray(raw.messages)
      ? raw.messages.filter((m) => m && m.role && !m.pending)
      : [];
    c.lastChunks = Array.isArray(raw.lastChunks) ? raw.lastChunks : [];
    c.lastIntent = raw.lastIntent || "";
    c.lastRewrite = raw.lastRewrite || null;
    c.lastSameTopic = raw.lastSameTopic == null ? null : Boolean(raw.lastSameTopic);
    c.lastOriginal = raw.lastOriginal || "";
    c.lastRecalled = Number(raw.lastRecalled) || 0;
    c.lastRoundChunks = Array.isArray(raw.lastRoundChunks) ? raw.lastRoundChunks : [];
    c.citationsOpen = raw.citationsOpen && typeof raw.citationsOpen === "object" ? raw.citationsOpen : {};
    c.updatedAt = Number(raw.updatedAt) || Date.now();
    return c;
  }

  function loadStore() {
    try {
      const raw = localStorage.getItem(CONV_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      const list = (parsed.conversations || []).map(sanitizeConv);
      if (!list.length) return null;
      let activeId = parsed.activeId;
      if (!list.some((c) => c.id === activeId)) activeId = list[0].id;
      return { conversations: list, activeId: activeId };
    } catch (e) {
      return null;
    }
  }

  function create(onChange) {
    const stored = loadStore();
    const first = stored ? stored.conversations : [emptyConv()];
    const state = {
      conversations: first,
      activeId: stored ? stored.activeId : first[0].id,
      busy: false,
      stage: "",
      scenario: sessionStorage.getItem(SCN_KEY) || "normal",
      config: loadConfig(),
      health: null
    };

    function active() {
      return state.conversations.find((c) => c.id === state.activeId) || state.conversations[0];
    }

    function persist() {
      const conv = active();
      while (state.conversations.length > MAX_CONVS) {
        const oldest = state.conversations
          .filter((c) => c.id !== conv.id)
          .sort((a, b) => (a.updatedAt || 0) - (b.updatedAt || 0))[0];
        if (!oldest) break;
        state.conversations = state.conversations.filter((c) => c.id !== oldest.id);
      }
      const payload = {
        activeId: state.activeId,
        conversations: state.conversations.map((c) => ({
          id: c.id,
          title: c.title,
          titleLocked: c.titleLocked,
          messages: (c.messages || []).filter((m) => !m.pending),
          lastChunks: c.lastChunks,
          lastIntent: c.lastIntent,
          lastRewrite: c.lastRewrite,
          lastSameTopic: c.lastSameTopic,
          lastOriginal: c.lastOriginal,
          lastRecalled: c.lastRecalled,
          lastRoundChunks: c.lastRoundChunks,
          citationsOpen: c.citationsOpen,
          updatedAt: c.updatedAt
        }))
      };
      try {
        localStorage.setItem(CONV_KEY, JSON.stringify(payload));
      } catch (e) { /* 配额满时忽略，本轮内存仍可用 */ }
    }

    function emit(shouldPersist) {
      if (shouldPersist) persist();
      if (onChange) onChange(snapshot());
    }

    function snapshot() {
      const conv = active();
      const list = state.conversations.slice().sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0));
      return {
        conversations: list.map((c) => ({
          id: c.id,
          title: c.title,
          updatedAt: c.updatedAt,
          empty: !(c.messages && c.messages.length)
        })),
        activeId: conv.id,
        messages: conv.messages.slice(),
        lastChunks: conv.lastChunks.slice(),
        lastIntent: conv.lastIntent,
        lastRewrite: conv.lastRewrite,
        lastSameTopic: conv.lastSameTopic,
        lastOriginal: conv.lastOriginal,
        lastRecalled: conv.lastRecalled,
        lastRoundChunks: conv.lastRoundChunks.slice(),
        citationsOpen: Object.assign({}, conv.citationsOpen),
        stage: state.stage,
        busy: state.busy,
        scenario: state.scenario,
        config: Object.assign({}, state.config),
        health: state.health
      };
    }

    function recentHistory(conv) {
      const turns = [];
      conv.messages.forEach((m) => {
        if (m.role === "user") turns.push({ role: "user", text: m.text, intent: m.intent || "" });
      });
      const keep = Number(state.config.historyTurns) || 5;
      return turns.slice(-keep);
    }

    function beginPending(conv) {
      const id = uid("a");
      conv.messages.push({
        id: id,
        role: "assistant",
        pending: true,
        stage: "rewrite",
        text: "",
        citations: [],
        refused: false,
        conflict: false
      });
      return id;
    }

    function patchPending(conv, id, patch) {
      const m = conv.messages.find((x) => x.id === id);
      if (m) Object.assign(m, patch);
    }

    function dropPending(conv, id) {
      conv.messages = conv.messages.filter((m) => m.id !== id);
    }

    function setScenario(id) {
      state.scenario = id;
      sessionStorage.setItem(SCN_KEY, id);
      emit(false);
    }

    function setConfig(partial) {
      state.config = Object.assign({}, state.config, partial);
      saveConfig(state.config);
      emit(false);
    }

    function resetConfig() {
      state.config = Object.assign({}, window.KbQaMockData.DEFAULT_CONFIG);
      saveConfig(state.config);
      emit(false);
    }

    function touch(conv) {
      conv.updatedAt = Date.now();
    }

    function clear() {
      if (state.busy) return false;
      const conv = active();
      conv.messages = [];
      conv.lastChunks = [];
      conv.lastIntent = "";
      conv.lastRewrite = null;
      conv.lastSameTopic = null;
      conv.lastOriginal = "";
      conv.lastRecalled = 0;
      conv.lastRoundChunks = [];
      conv.citationsOpen = {};
      conv.title = "新对话";
      conv.titleLocked = false;
      touch(conv);
      emit(true);
      return true;
    }

    function createConversation() {
      if (state.busy) return false;
      const conv = emptyConv();
      state.conversations.unshift(conv);
      state.activeId = conv.id;
      emit(true);
      return true;
    }

    function switchConversation(id) {
      if (state.busy) return false;
      if (!state.conversations.some((c) => c.id === id)) return false;
      state.activeId = id;
      emit(true);
      return true;
    }

    function deleteConversation(id) {
      if (state.busy) return false;
      const remain = state.conversations.filter((c) => c.id !== id);
      if (!remain.length) {
        const conv = emptyConv();
        state.conversations = [conv];
        state.activeId = conv.id;
        emit(true);
        return true;
      }
      state.conversations = remain;
      if (state.activeId === id) {
        remain.sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0));
        state.activeId = remain[0].id;
      }
      emit(true);
      return true;
    }

    function toggleCitations(id) {
      const conv = active();
      conv.citationsOpen[id] = !conv.citationsOpen[id];
      emit(true);
    }

    async function refreshHealth() {
      state.health = await window.KbQaMockApi.health(state.scenario);
      emit(false);
      return state.health;
    }

    async function send(raw) {
      const text = String(raw || "").trim();
      if (!text || state.busy) return;
      const api = window.KbQaMockApi;
      const conv = active();
      const historyForRewrite = recentHistory(conv);
      state.busy = true;
      conv.lastOriginal = text;
      if (!conv.titleLocked) {
        conv.title = titleFromText(text);
        conv.titleLocked = true;
      }
      touch(conv);

      const userId = uid("u");
      conv.messages.push({ id: userId, role: "user", text: text, intent: "" });
      const pendingId = beginPending(conv);
      emit(false);

      try {
        const healthNow = await api.health(state.scenario);
        state.health = healthNow;
        if (!healthNow.ok) {
          dropPending(conv, pendingId);
          conv.messages.push({
            id: uid("s"),
            role: "system",
            kind: "health",
            text: healthNow.message,
            citations: []
          });
          return;
        }

        state.stage = "rewrite";
        patchPending(conv, pendingId, { stage: "rewrite" });
        emit(false);

        let rw;
        try {
          rw = await api.rewrite(text, historyForRewrite, state.scenario, state.config);
        } catch (err) {
          dropPending(conv, pendingId);
          conv.messages.push({
            id: uid("s"),
            role: "system",
            kind: "rewrite_fail",
            text: "改写失败，本轮未检索、未生成。可重试。上一轮对话仍在。",
            citations: []
          });
          return;
        }

        conv.lastRewrite = rw;
        conv.lastSameTopic = rw.same_topic;
        const userMsg = conv.messages.find((m) => m.id === userId);
        if (userMsg) userMsg.intent = rw.intent;

        state.stage = "retrieve";
        patchPending(conv, pendingId, { stage: "retrieve" });
        emit(false);
        await api.delay(280);

        state.stage = "rerank";
        patchPending(conv, pendingId, { stage: "rerank" });
        emit(false);

        const retrieved = await api.retrieveAndRerank({
          intent: rw.intent,
          sameTopic: rw.same_topic,
          prevChunks: conv.lastChunks,
          scenario: state.scenario,
          config: state.config
        });
        conv.lastRoundChunks = retrieved.chunks;
        conv.lastRecalled = retrieved.recalled;

        if (!retrieved.chunks.length) {
          dropPending(conv, pendingId);
          conv.messages.push({
            id: uid("s"),
            role: "system",
            kind: "empty",
            refused: true,
            text: "文档未写。重排后 0 块，系统拒答。候选为空，请打开文档索引。",
            citations: []
          });
          conv.lastChunks = [];
          conv.lastIntent = rw.intent;
          return;
        }

        state.stage = "generate";
        patchPending(conv, pendingId, { stage: "generate" });
        emit(false);

        if (state.scenario === "gen_fail") {
          dropPending(conv, pendingId);
          const sid = uid("s");
          conv.messages.push({
            id: sid,
            role: "system",
            kind: "gen_fail",
            text: "生成失败。半段正文已丢弃，不展示完整回答。下列为本轮重排后出处，不是回答气泡。",
            citations: retrieved.chunks
          });
          conv.lastChunks = retrieved.chunks;
          conv.lastIntent = rw.intent;
          conv.citationsOpen[sid] = true;
          return;
        }

        const answer = api.buildAnswer(rw.intent, retrieved.chunks);
        try {
          for await (const part of api.streamText(answer.body, { interrupt: state.scenario === "gen_interrupt" })) {
            patchPending(conv, pendingId, { text: part, stage: "generate" });
            emit(false);
          }
        } catch (err) {
          dropPending(conv, pendingId);
          const sid = uid("s");
          conv.messages.push({
            id: sid,
            role: "system",
            kind: "gen_fail",
            text: "生成失败（流中断）。半段正文已丢弃，不展示完整回答。下列为本轮重排后出处，不是回答气泡。",
            citations: retrieved.chunks
          });
          conv.lastChunks = retrieved.chunks;
          conv.lastIntent = rw.intent;
          conv.citationsOpen[sid] = true;
          return;
        }

        patchPending(conv, pendingId, {
          pending: false,
          stage: "",
          text: answer.body,
          citations: retrieved.chunks,
          refused: answer.refused,
          conflict: answer.conflict
        });
        conv.lastChunks = retrieved.chunks;
        conv.lastIntent = rw.intent;
        conv.citationsOpen[pendingId] = false;
      } finally {
        state.busy = false;
        state.stage = "";
        touch(conv);
        emit(true);
      }
    }

    return {
      snapshot: snapshot,
      setScenario: setScenario,
      setConfig: setConfig,
      resetConfig: resetConfig,
      clear: clear,
      createConversation: createConversation,
      switchConversation: switchConversation,
      deleteConversation: deleteConversation,
      toggleCitations: toggleCitations,
      refreshHealth: refreshHealth,
      send: send,
      reindex: function () { return window.KbQaMockApi.reindex(); }
    };
  }

  window.KbQaCore = { create: create, loadConfig: loadConfig };
})();
