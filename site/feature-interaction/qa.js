/**
 * 正式知识问答工作区：多会话、流式回答、出处跳转、配置/重建/明细/热度。
 * 无过程栏。空状态允许建议 chips（C22）。
 */
(function () {
  const API = "/api/kb";
  const CONV_KEY = "hayyo-kb-qa-conversations-v1";
  const MAX_CONVS = 40;
  const STAGE_LABEL = {
    rewrite: "改写中…",
    retrieve: "检索中…",
    rerank: "重排中…",
    generate: "生成中…"
  };
  const UNWRITTEN_HINT = "本轮日志未写入，反馈不会进明细";
  const CHIP_FIXED = [
    {
      title: "币商用链接支付帮朋友充金币：付款人能拿 VIP 积分和拉新返利吗？收货人呢？这笔算不算收货人的首充？会不会进充值任务进度？",
      query: "币商用链接支付帮朋友充金币：付款人能拿 VIP 积分和拉新返利吗？收货人呢？这笔算不算收货人的首充？会不会进充值任务进度？"
    },
    {
      title: "币商给用户转了 20000 金币。这笔会进 Billionaires 充值榜吗？算不算用户首充？会不会给用户加 VIP 财富值？",
      query: "币商给用户转了 20000 金币。这笔会进 Billionaires 充值榜吗？算不算用户首充？会不会给用户加 VIP 财富值？"
    },
    {
      title: "非 VIP 在语聊房 Game Center 点 Bounty Racing 会怎样？如果这个房间同时开着 Ludo，我关掉数值游戏弹窗后，休闲游戏还在吗？Lord of Olympus 有 VIP 限制吗？",
      query: "非 VIP 在语聊房 Game Center 点 Bounty Racing 会怎样？如果这个房间同时开着 Ludo，我关掉数值游戏弹窗后，休闲游戏还在吗？Lord of Olympus 有 VIP 限制吗？"
    },
    {
      title: "VIP 保级扣的是财富值还是金币？200 金币等于多少财富值？退款怎么扣？",
      query: "VIP 保级扣的是财富值还是金币？200 金币等于多少财富值？退款怎么扣？"
    }
  ];

  function uid(prefix) {
    return prefix + "-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
  }

  function truncate18(text) {
    const t = String(text || "").replace(/\s+/g, " ").trim();
    if (!t) return "新对话";
    return t.length > 18 ? t.slice(0, 18) : t;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function toast(text) {
    const old = document.querySelector(".toast");
    if (old) old.remove();
    const el = document.createElement("div");
    el.className = "toast";
    el.textContent = text;
    document.body.appendChild(el);
    setTimeout(function () { el.remove(); }, 1800);
  }

  function emptyConv() {
    return {
      id: uid("c"),
      title: "新对话",
      titleLocked: false,
      messages: [],
      lastChunks: [],
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
      ? raw.messages.filter(function (m) { return m && m.role && !m.pending; })
      : [];
    c.lastChunks = Array.isArray(raw.lastChunks) ? raw.lastChunks : [];
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
      if (!list.some(function (c) { return c.id === activeId; })) activeId = list[0].id;
      return { conversations: list, activeId: activeId };
    } catch (e) {
      return null;
    }
  }

  // 启动先不读 localStorage：已登录必须以云端为准，避免把本机旧对话画给当前账号
  const state = {
    conversations: [emptyConv()],
    activeId: null,
    busy: false,
    stage: "",
    persistError: false,
    health: null,
    overlay: null,
    me: null
  };
  if (!state.activeId) state.activeId = state.conversations[0].id;

  const els = {
    list: document.getElementById("qaConvList"),
    messages: document.getElementById("qaMessages"),
    input: document.getElementById("qaInput"),
    send: document.getElementById("qaSend"),
    stage: document.getElementById("qaStage"),
    banner: document.getElementById("qaBanner"),
    health: document.getElementById("qaHealth"),
    overlay: document.getElementById("qaOverlay"),
    workspace: document.getElementById("qaWorkspace"),
    citePane: document.getElementById("qaCitePane"),
    citePaneBody: document.getElementById("qaCitePaneBody"),
    citePaneTitle: document.getElementById("qaCitePaneTitle"),
    newBtn: document.querySelector("[data-qa-new]"),
    clearBtn: document.querySelector("[data-qa-clear]"),
    account: document.getElementById("qaAccount"),
    accountBtn: document.getElementById("qaAccountBtn"),
    accountName: document.getElementById("qaAccountName"),
    accountMenu: document.getElementById("qaAccountMenu")
  };

  const heatChipCache = { items: null, loading: false };

  function hasPerm(name) {
    if (!state.me) return false;
    if (state.me.is_super) return true;
    return (state.me.permissions || []).indexOf(name) >= 0;
  }

  function setAccountOpen(open) {
    if (!els.account) return;
    var shown = Boolean(open) && Boolean(state.me);
    els.account.classList.toggle("open", shown);
    if (els.accountBtn) {
      els.accountBtn.setAttribute("aria-expanded", shown ? "true" : "false");
    }
  }

  function renderAccount() {
    if (!els.account || !els.accountBtn || !els.accountMenu) return;
    els.account.hidden = !state.me;
    if (!state.me) {
      setAccountOpen(false);
      return;
    }
    if (els.accountName) els.accountName.textContent = state.me.username || "账号";
    var entry = els.accountMenu.querySelector("#qaAdminEntry");
    if (hasPerm("进管理模块")) {
      if (!entry) {
        entry = document.createElement("a");
        entry.id = "qaAdminEntry";
        entry.href = "/kb-admin/";
        entry.textContent = "进管理模块";
        els.accountMenu.appendChild(entry);
      }
    } else if (entry) {
      entry.remove();
    }
  }

  function goLogin() {
    var next = window.location.pathname + window.location.search + window.location.hash;
    window.location.replace("/login/?next=" + encodeURIComponent(next || "/feature-interaction/"));
  }

  function syncLoginWall() {
    if (!state.me) {
      goLogin();
      return;
    }
    renderAccount();
  }

  function applyLocalStore() {
    const stored = loadStore();
    if (!stored) return;
    state.conversations = stored.conversations;
    state.activeId = stored.activeId;
  }

  async function refreshMe() {
    try {
      const res = await fetch(API + "/auth/me", { credentials: "same-origin" });
      state.me = res.ok ? await res.json() : null;
    } catch (e) {
      state.me = null;
    }
    if (!state.me) {
      goLogin();
      return;
    }
    renderAccount();
    await loadCloud();
    render();
  }

  function active() {
    return state.conversations.find(function (c) { return c.id === state.activeId; }) || state.conversations[0];
  }

  async function saveCloud(conv) {
    if (!state.me || !conv || !conv.id) return;
    try {
      await fetch(API + "/conversations/" + encodeURIComponent(conv.id), {
        method: "PUT",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: conv.title,
          titleLocked: conv.titleLocked,
          messages: (conv.messages || []).filter(function (m) { return !m.pending; }),
          lastChunks: conv.lastChunks || [],
          citationsOpen: conv.citationsOpen || {}
        })
      });
    } catch (e) {}
  }

  async function loadCloud() {
    if (!state.me) return;
    try {
      const res = await fetch(API + "/conversations", { credentials: "same-origin" });
      if (!res.ok) return;
      const data = await res.json();
      let items = (data.items || []).map(sanitizeConv);
      if (!items.length) {
        const created = await fetch(API + "/conversations", {
          method: "POST",
          credentials: "same-origin",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: "新对话" })
        });
        if (created.ok) items = [sanitizeConv(await created.json())];
      }
      if (!items.length) return;
      state.conversations = items;
      if (!items.some(function (c) { return c.id === state.activeId; })) {
        state.activeId = items[0].id;
      }
    } catch (e) {}
  }

  function persist() {
    if (state.me) {
      saveCloud(active());
      return true;
    }
    const conv = active();
    while (state.conversations.length > MAX_CONVS) {
      const oldest = state.conversations
        .filter(function (c) { return c.id !== conv.id; })
        .sort(function (a, b) { return (a.updatedAt || 0) - (b.updatedAt || 0); })[0];
      if (!oldest) break;
      state.conversations = state.conversations.filter(function (c) { return c.id !== oldest.id; });
    }
    const payload = {
      activeId: state.activeId,
      conversations: state.conversations.map(function (c) {
        return {
          id: c.id,
          title: c.title,
          titleLocked: c.titleLocked,
          messages: (c.messages || []).filter(function (m) { return !m.pending; }),
          lastChunks: c.lastChunks,
          citationsOpen: c.citationsOpen,
          updatedAt: c.updatedAt
        };
      })
    };
    try {
      localStorage.setItem(CONV_KEY, JSON.stringify(payload));
      state.persistError = false;
      return true;
    } catch (e) {
      state.persistError = true;
      toast("对话未保存");
      return false;
    }
  }

  function setBanner(text) {
    if (!els.banner) return;
    if (!text) {
      els.banner.hidden = true;
      els.banner.textContent = "";
      return;
    }
    els.banner.hidden = false;
    els.banner.textContent = text;
  }

  function collectionLabel(c) {
    return c === "hayyo-admin" ? "后台库" : "客户端库";
  }

  function citeButton(c) {
    const col = '<span class="qa-tag' + (c.collection === "hayyo-admin" ? " admin" : "") + '">' +
      escapeHtml(collectionLabel(c.collection)) + "</span>";
    return (
      '<button class="qa-chunk" type="button" data-cite-path="' + escapeHtml(c.path || "") +
        '" data-cite-anchor="' + escapeHtml(c.anchor || "") +
        '" data-cite-heading="' + escapeHtml(c.heading || "") + '">' +
        col +
        '<span class="name">' + escapeHtml(c.heading || c.chunk_id || "") + "</span>" +
        '<span class="meta">' + escapeHtml(c.path || "") + " · #" + escapeHtml(c.anchor || "") +
        " · " + escapeHtml(c.chunk_id || "") + "</span>" +
      "</button>"
    );
  }

  function hasAnswerBody(m) {
    return Boolean(m && !m.pending && m.text && (m.role === "assistant" || m.refused));
  }

  // 操作条用内联 SVG，不引入图标库
  function iconSvg(kind) {
    const common = ' class="qa-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"';
    if (kind === "cite") {
      return "<svg" + common + '><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>';
    }
    if (kind === "copy") {
      return "<svg" + common + '><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
    }
    if (kind === "up") {
      return "<svg" + common + '><path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88z"/></svg>';
    }
    if (kind === "down") {
      return "<svg" + common + '><path d="M17 14V2"/><path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88z"/></svg>';
    }
    return "<svg" + common + '><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>';
  }

  function iconBtn(opts) {
    return (
      '<button class="kb-btn qa-icon-btn' + (opts.on ? " is-on" : "") +
        '" type="button" title="' + escapeHtml(opts.label) +
        '" aria-label="' + escapeHtml(opts.label) + '"' +
        (opts.on ? ' aria-pressed="true"' : "") +
        (opts.attrs || "") + ">" +
        iconSvg(opts.kind) +
        (opts.badge || "") +
      "</button>"
    );
  }

  function openCiteMsgId(conv) {
    const map = (conv && conv.citationsOpen) || {};
    const ids = Object.keys(map).filter(function (k) { return map[k]; });
    return ids.length ? ids[0] : "";
  }

  // 同一时间只打开一条回答的出处面板
  function setCiteOpen(conv, msgId, open) {
    if (!conv) return;
    if (!conv.citationsOpen || typeof conv.citationsOpen !== "object") conv.citationsOpen = {};
    if (!open) {
      if (msgId) delete conv.citationsOpen[msgId];
      return;
    }
    conv.citationsOpen = {};
    if (msgId) conv.citationsOpen[msgId] = true;
  }

  function actionBarHtml(m) {
    if (!m || m.pending || m.role === "user") return "";
    const id = escapeHtml(m.id);
    const keys = [];
    const cites = m.citations || [];
    const citeOpen = Boolean(active().citationsOpen && active().citationsOpen[m.id]);
    if (cites.length) {
      keys.push(iconBtn({
        kind: "cite",
        label: cites.length + " 条出处",
        on: citeOpen,
        attrs: ' data-toggle-cite="' + id + '"',
        badge: '<span class="qa-icon-badge">' + escapeHtml(String(cites.length)) + "</span>"
      }));
    }
    if (hasAnswerBody(m)) {
      keys.push(iconBtn({ kind: "copy", label: "复制回答", attrs: ' data-copy="' + id + '"' }));
      keys.push(iconBtn({
        kind: "up",
        label: "赞",
        on: m.feedback === "赞",
        attrs: ' data-qa-fb="up" data-msg="' + id + '"'
      }));
      keys.push(iconBtn({
        kind: "down",
        label: "踩",
        on: m.feedback === "踩",
        attrs: ' data-qa-fb="down" data-msg="' + id + '"'
      }));
      keys.push(iconBtn({ kind: "regen", label: "刷新", attrs: ' data-qa-regen="' + id + '"' }));
    } else {
      keys.push(iconBtn({ kind: "regen", label: "刷新", attrs: ' data-qa-regen="' + id + '"' }));
    }
    return '<div class="qa-actions">' + keys.join("") + "</div>";
  }

  function messageHtml(m) {
    if (m.role === "user") {
      return (
        '<div class="qa-row user">' +
          '<div class="qa-avatar">我</div>' +
          '<div class="qa-bubble"><div class="qa-body">' + escapeHtml(m.text) + "</div></div>" +
        "</div>"
      );
    }
    const flags = [];
    if (m.refused) flags.push('<span class="qa-tag warn">文档未写</span>');
    let body;
    if (m.pending && !m.text) {
      body = '<div class="qa-stage">' + escapeHtml(STAGE_LABEL[m.stage] || "处理中…") + "</div>";
    } else if (m.pending && m.text) {
      body = '<div class="qa-stage">' + escapeHtml(STAGE_LABEL[m.stage] || "生成中…") +
        '</div><div class="qa-body">' + escapeHtml(m.text) + "</div>";
    } else {
      body = '<div class="qa-body">' + escapeHtml(m.text || "") + "</div>";
    }
    const cls = ["qa-bubble"];
    if (m.role === "system") cls.push("system");
    if (m.refused) cls.push("refuse");
    return (
      '<div class="qa-row">' +
        '<div class="qa-avatar">' + (m.role === "system" ? "!" : "答") + "</div>" +
        '<div class="' + cls.join(" ") + '">' +
          (flags.length ? '<div class="qa-flags">' + flags.join("") + "</div>" : "") +
          body +
          actionBarHtml(m) +
        "</div>" +
      "</div>"
    );
  }

  function chipButton(title, query) {
    return (
      '<button class="qa-chip" type="button" data-qa-chip="' + escapeHtml(query) + '">' +
        escapeHtml(title) +
      "</button>"
    );
  }

  function emptyHtml() {
    const fixed = CHIP_FIXED.map(function (c) { return chipButton(c.title, c.query); }).join("");
    const heat = (heatChipCache.items || []).map(function (c) { return chipButton(c.title, c.query); }).join("");
    return (
      '<div class="qa-empty">' +
        "<h2>知识问答</h2>" +
        "<p>直接提问，或从下面的例子开始。按 Hayyo 现行规则作答，不是需求合同。</p>" +
        '<div class="qa-chips">' +
          '<p class="qa-chips-label">试试这些问题</p>' +
          '<div class="qa-chips-fixed">' + fixed + "</div>" +
          (heat ? '<div class="qa-chips-heat">' + heat + "</div>" : "") +
        "</div>" +
      "</div>"
    );
  }

  async function refreshHeatChips() {
    if (!state.me || !hasPerm("知识问答")) {
      heatChipCache.items = [];
      heatChipCache.loading = false;
      return;
    }
    if (heatChipCache.loading) return;
    heatChipCache.loading = true;
    try {
      const res = await fetch(API + "/heatmap", { credentials: "same-origin" });
      if (!res.ok) {
        heatChipCache.items = [];
      } else {
        const data = await res.json();
        const items = (data.items || []).slice(0, 4);
        heatChipCache.items = items.map(function (it) {
          const name = it.display_name || it.feature_id || "";
          const q = name + " 有哪些现行规则？";
          return { title: q, query: q };
        });
      }
    } catch (e) {
      heatChipCache.items = [];
    }
    heatChipCache.loading = false;
    const conv = active();
    if (els.messages && conv && !conv.messages.length) {
      els.messages.innerHTML = emptyHtml();
    }
  }

  function renderHealth() {
    if (!els.health) return;
    const h = state.health;
    const ok = h && h.qdrant_ready && h.config_ready;
    els.health.className = "health-dot" + (ok ? "" : " bad");
    let msg = "检查中…";
    if (h) {
      const keys = [];
      if (h.key_dashscope === "未配置") keys.push("DashScope");
      if (h.key_deepseek === "未配置") keys.push("DeepSeek");
      if (!h.qdrant_ready) msg = "索引未就绪";
      else if (keys.length) msg = "缺 Key：" + keys.join("/");
      else if (!h.index_ready) msg = "索引未就绪";
      else msg = "索引就绪 · Key 已配置";
    }
    els.health.innerHTML = "<i></i><span>" + escapeHtml(msg) + "</span>";
  }

  function renderList() {
    if (!els.list) return;
    const list = state.conversations.slice().sort(function (a, b) {
      return (b.updatedAt || 0) - (a.updatedAt || 0);
    });
    els.list.innerHTML = list.map(function (c) {
      return (
        '<div class="qa-conv-item' + (c.id === state.activeId ? " active" : "") + '" data-conv="' + escapeHtml(c.id) + '">' +
          '<span class="qa-conv-title">' + escapeHtml(c.title) + "</span>" +
          '<button class="qa-conv-del" type="button" data-del="' + escapeHtml(c.id) + '">删除</button>' +
        "</div>"
      );
    }).join("");
  }

  function renderMessages() {
    if (!els.messages) return;
    const conv = active();
    const stick = els.messages.scrollHeight - els.messages.scrollTop - els.messages.clientHeight < 90;
    if (!conv.messages.length) {
      els.messages.innerHTML = emptyHtml();
      if (heatChipCache.items === null) refreshHeatChips();
    } else {
      els.messages.innerHTML = conv.messages.map(messageHtml).join("");
    }
    if (stick) els.messages.scrollTop = els.messages.scrollHeight;
  }

  // 出处卡片渲染到右侧面板，不再插进气泡
  function renderCitePane() {
    const pane = els.citePane;
    const body = els.citePaneBody;
    const title = els.citePaneTitle;
    const workspace = els.workspace;
    if (!pane || !body) return;
    const conv = active();
    const openId = openCiteMsgId(conv);
    const msg = openId ? conv.messages.find(function (m) { return m.id === openId; }) : null;
    const cites = (msg && msg.citations) || [];
    if (!openId || !msg || (!cites.length && !msg.pending)) {
      pane.hidden = true;
      if (workspace) workspace.classList.remove("cite-open");
      body.innerHTML = "";
      if (title) title.textContent = "出处";
      return;
    }
    pane.hidden = false;
    if (workspace) workspace.classList.add("cite-open");
    if (title) title.textContent = cites.length ? ("出处 · " + cites.length) : "出处";
    body.innerHTML = cites.length
      ? cites.map(citeButton).join("")
      : '<p class="qa-cite-pane-hint">生成中…</p>';
  }

  // 阶段文案只显示在待生成气泡内，顶栏槽位不再重复写出
  function renderStage() {
    if (!els.stage) return;
    els.stage.hidden = true;
    els.stage.textContent = "";
  }

  function renderLock() {
    if (els.input) els.input.disabled = state.busy;
    if (els.send) els.send.disabled = state.busy;
    if (els.newBtn) els.newBtn.disabled = state.busy;
    if (els.clearBtn) els.clearBtn.disabled = state.busy;
  }

  function autosizeInput() {
    const el = els.input;
    if (!el) return;
    el.style.height = "auto";
    const next = Math.min(Math.max(el.scrollHeight, 44), 200);
    el.style.height = next + "px";
  }

  function render() {
    renderList();
    renderMessages();
    renderCitePane();
    renderStage();
    renderLock();
    renderHealth();
  }

  async function refreshHealth() {
    try {
      const res = await fetch(API + "/health");
      state.health = await res.json();
    } catch (e) {
      state.health = { qdrant_ready: false, config_ready: false, index_ready: false };
    }
    renderHealth();
    return state.health;
  }

  function lockGuard(actionName) {
    if (!state.busy) return false;
    toast("生成中，不能" + actionName);
    return true;
  }

  async function createConversation() {
    if (lockGuard("新建对话")) return false;
    if (state.me) {
      try {
        const res = await fetch(API + "/conversations", {
          method: "POST",
          credentials: "same-origin",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: "新对话" })
        });
        if (!res.ok) return false;
        const conv = sanitizeConv(await res.json());
        state.conversations.unshift(conv);
        state.activeId = conv.id;
        render();
        return true;
      } catch (e) {
        return false;
      }
    }
    const conv = emptyConv();
    state.conversations.unshift(conv);
    state.activeId = conv.id;
    persist();
    render();
    return true;
  }

  function switchConversation(id) {
    if (lockGuard("切换对话")) return false;
    if (!state.conversations.some(function (c) { return c.id === id; })) return false;
    state.activeId = id;
    persist();
    render();
    return true;
  }

  async function deleteConversation(id) {
    if (lockGuard("删除对话")) return false;
    if (state.me) {
      try {
        await fetch(API + "/conversations/" + encodeURIComponent(id), {
          method: "DELETE",
          credentials: "same-origin"
        });
      } catch (e) {}
    }
    const remain = state.conversations.filter(function (c) { return c.id !== id; });
    if (!remain.length) {
      if (state.me) {
        state.conversations = [];
        return createConversation();
      }
      const conv = emptyConv();
      state.conversations = [conv];
      state.activeId = conv.id;
      persist();
      render();
      return true;
    }
    state.conversations = remain;
    if (state.activeId === id) {
      remain.sort(function (a, b) { return (b.updatedAt || 0) - (a.updatedAt || 0); });
      state.activeId = remain[0].id;
    }
    persist();
    render();
    return true;
  }

  function clearCurrent() {
    if (lockGuard("清空当前")) return false;
    const conv = active();
    conv.messages = [];
    conv.lastChunks = [];
    conv.citationsOpen = {};
    conv.title = "新对话";
    conv.titleLocked = false;
    conv.updatedAt = Date.now();
    heatChipCache.items = null;
    persist();
    render();
    return true;
  }

  async function readSSE(res, onEvent) {
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    while (true) {
      const chunk = await reader.read();
      if (chunk.done) break;
      buf += dec.decode(chunk.value, { stream: true });
      const parts = buf.split("\n\n");
      buf = parts.pop();
      parts.forEach(function (block) {
        let event = "message";
        const dataLines = [];
        block.split("\n").forEach(function (line) {
          if (line.indexOf("event:") === 0) event = line.slice(6).trim();
          else if (line.indexOf("data:") === 0) dataLines.push(line.slice(5).trim());
        });
        if (!dataLines.length) return;
        try {
          onEvent(event, JSON.parse(dataLines.join("\n")));
        } catch (e) { /* 忽略半包 */ }
      });
    }
  }

  function adjacentUserQuery(conv, msgId) {
    const idx = conv.messages.findIndex(function (m) { return m.id === msgId; });
    if (idx < 0) return "";
    for (let i = idx - 1; i >= 0; i -= 1) {
      if (conv.messages[i].role === "user") return conv.messages[i].text || "";
    }
    return "";
  }

  async function completeAssistantRound(conv, targetId, body, opt) {
    opt = opt || {};
    const mode = opt.mode || "send";
    const freezeSnap = Boolean(opt.freezeSnap);
    let logWritten = true;

    function meta(patch) {
      const base = {
        round_id: body.round_id,
        logWritten: logWritten
      };
      if (!freezeSnap) {
        base.query = body.query;
        base.historySnapshot = body.history;
        base.lastChunksSnapshot = body.last_chunks;
      }
      return Object.assign(base, patch || {});
    }

    function patchTarget(patch) {
      const m = conv.messages.find(function (x) { return x.id === targetId; });
      if (m) Object.assign(m, meta(patch));
    }

    try {
      const res = await fetch(API + "/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify(body)
      });
      if (!res.ok || !res.body) {
        logWritten = false;
        patchTarget({
          pending: false,
          role: "system",
          kind: "ask_fail",
          text: "提问失败（" + res.status + "）。",
          citations: [],
          refused: false
        });
        return;
      }
      let acc = "";
      let lastCgen = [];
      await readSSE(res, function (event, data) {
        if (event === "stage") {
          state.stage = data.stage || "";
          patchTarget({ stage: state.stage });
          render();
        } else if (event === "token") {
          acc += data.text || "";
          patchTarget({ text: acc, stage: "generate" });
          render();
        } else if (event === "log" && data.written === false) {
          logWritten = false;
          setBanner("本轮日志未写入");
          patchTarget({});
        } else if (event === "rerank") {
          lastCgen = data.c_gen || [];
        } else if (event === "citations") {
          lastCgen = data.items || lastCgen;
        } else if (event === "refuse") {
          patchTarget({
            pending: false,
            role: "system",
            refused: true,
            stage: "",
            text: data.text || "文档未写。",
            citations: data.c_gen || []
          });
          if (mode === "send") conv.lastChunks = [];
          render();
        } else if (event === "done") {
          if (data.log_written === false) {
            logWritten = false;
            setBanner("本轮日志未写入");
          }
          if (data.status === "interrupted") {
            if (mode === "regen") {
              patchTarget({
                pending: false,
                role: "system",
                kind: "interrupted",
                stage: "",
                text: "提问失败",
                citations: [],
                refused: false
              });
            } else {
              conv.messages = conv.messages.filter(function (m) { return m.id !== targetId; });
            }
            return;
          }
          if (data.status === "empty") {
            patchTarget({ pending: false, stage: "" });
            return;
          }
          if (data.status === "success" || data.status === "refuse") {
            const cgen = data.c_gen || lastCgen;
            patchTarget({
              pending: false,
              role: "assistant",
              stage: "",
              text: data.text || acc,
              citations: cgen,
              refused: Boolean(data.refused) || data.status === "refuse"
            });
            if (mode === "send") {
              setCiteOpen(conv, targetId, false);
              conv.lastChunks = cgen;
            } else if (mode === "regen" && opt.isLast && data.status === "success") {
              conv.lastChunks = cgen;
            }
          }
        } else if (event === "error") {
          const cites = data.c_gen || [];
          if (data.log_written === false) {
            logWritten = false;
            setBanner("本轮日志未写入");
          }
          let text = data.message || "提问失败";
          let kind = data.type || "ask_fail";
          if (data.type === "rewrite_fail") {
            text = data.message || "改写失败，本轮未检索、未生成。可重试。";
          } else if (data.type === "gen_fail" || data.type === "rerank_fail" || data.type === "retrieve_fail") {
            text = data.message || "生成失败。半段正文已丢弃，不展示完整回答。";
          }
          patchTarget({
            pending: false,
            role: "system",
            kind: kind,
            stage: "",
            text: text,
            citations: cites,
            refused: false
          });
          if (cites.length) setCiteOpen(conv, targetId, true);
          if (mode === "send" && cites.length) conv.lastChunks = cites;
          render();
        }
      });
    } catch (e) {
      logWritten = false;
      patchTarget({
        pending: false,
        role: "system",
        kind: "ask_fail",
        stage: "",
        text: "提问失败，请检查 kb-api。",
        citations: [],
        refused: false
      });
    }
  }

  async function send(presetQuery) {
    if (!state.me) {
      goLogin();
      return;
    }
    const text = String(presetQuery == null ? (els.input && els.input.value || "") : presetQuery).trim();
    if (!text || state.busy) return;
    const conv = active();
    const history = conv.messages.filter(function (m) { return m.role === "user"; }).slice(-5).map(function (m) {
      return { role: "user", text: m.text };
    });
    const lastChunksSnapshot = conv.lastChunks || [];
    state.busy = true;
    setBanner("");
    if (!conv.titleLocked) {
      conv.title = truncate18(text);
      conv.titleLocked = true;
    }
    conv.updatedAt = Date.now();
    conv.messages.push({ id: uid("u"), role: "user", text: text });
    const pendingId = uid("a");
    const roundId = uid("r");
    conv.messages.push({
      id: pendingId,
      role: "assistant",
      pending: true,
      stage: "rewrite",
      text: "",
      citations: [],
      round_id: roundId,
      logWritten: true,
      query: text,
      historySnapshot: history,
      lastChunksSnapshot: lastChunksSnapshot,
      feedback: ""
    });
    if (els.input) {
      els.input.value = "";
      autosizeInput();
    }
    persist();
    render();

    const body = {
      conversation_id: conv.id,
      round_id: roundId,
      query: text,
      history: history,
      last_chunks: lastChunksSnapshot,
      user_id: null,
      owner_id: null,
      tenant_id: null,
      role: null
    };
    try {
      await completeAssistantRound(conv, pendingId, body, { mode: "send" });
    } finally {
      state.busy = false;
      state.stage = "";
      active().updatedAt = Date.now();
      persist();
      render();
    }
  }

  async function regen(id) {
    if (!state.me) {
      goLogin();
      return;
    }
    if (state.busy) {
      toast("生成中…");
      return;
    }
    const conv = active();
    const m = conv.messages.find(function (x) { return x.id === id; });
    if (!m || m.pending || m.role === "user") return;
    const hasSnap = Boolean(m.query) && Array.isArray(m.historySnapshot) && Array.isArray(m.lastChunksSnapshot);
    const query = hasSnap ? m.query : (m.query || adjacentUserQuery(conv, id));
    const historySnapshot = hasSnap ? m.historySnapshot : [];
    const lastChunksSnapshot = hasSnap ? m.lastChunksSnapshot : [];
    const isLast = Boolean(conv.messages.length && conv.messages[conv.messages.length - 1].id === id);
    const roundId = uid("r");
    state.busy = true;
    setBanner("");
    m.pending = true;
    m.stage = "rewrite";
    m.text = "";
    m.citations = [];
    m.feedback = "";
    m.refused = false;
    persist();
    render();

    const body = {
      conversation_id: conv.id,
      round_id: roundId,
      query: query,
      history: historySnapshot,
      last_chunks: lastChunksSnapshot,
      user_id: null,
      owner_id: null,
      tenant_id: null,
      role: null
    };
    try {
      await completeAssistantRound(conv, id, body, {
        mode: "regen",
        freezeSnap: true,
        isLast: isLast
      });
    } finally {
      const now = conv.messages.find(function (x) { return x.id === id; });
      if (now) {
        now.round_id = roundId;
        now.pending = false;
      }
      state.busy = false;
      state.stage = "";
      conv.updatedAt = Date.now();
      persist();
      render();
    }
  }

  async function setFeedback(id, key) {
    const conv = active();
    const m = conv.messages.find(function (x) { return x.id === id; });
    if (!hasAnswerBody(m)) return;
    const label = key === "up" ? "赞" : "踩";
    m.feedback = m.feedback === label ? "" : label;
    persist();
    render();
    if (!m.round_id || !m.logWritten) {
      toast(UNWRITTEN_HINT);
      return;
    }
    const db = m.feedback === "赞" ? "up" : (m.feedback === "踩" ? "down" : null);
    try {
      const res = await fetch(API + "/rounds/" + encodeURIComponent(m.round_id) + "/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feedback: db })
      });
      if (!res.ok) toast(UNWRITTEN_HINT);
    } catch (e) {
      toast(UNWRITTEN_HINT);
    }
  }

  function openCitation(path, anchor, heading) {
    if (!path) return;
    if (window.GraphApp && window.GraphApp.setView) {
      window.GraphApp.setView("kb", { preserveSelection: true });
    }
    if (window.KB && window.KB.openDocument) {
      window.KB.openDocument(path, {
        hash: anchor ? "#" + String(anchor).replace(/^#/, "") : "",
        headingText: heading || ""
      });
    }
  }

  function copyText(text) {
    const ok = function () { toast("已复制回答"); };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(ok).catch(function () {
        window.prompt("复制以下文本", text);
      });
    } else {
      window.prompt("复制以下文本", text);
    }
  }

  function closeOverlay() {
    state.overlay = null;
    if (els.overlay) {
      els.overlay.hidden = true;
      els.overlay.innerHTML = "";
    }
  }

  function openOverlay(html) {
    if (!els.overlay) return;
    els.overlay.hidden = false;
    els.overlay.innerHTML = '<div class="qa-overlay-card">' + html + "</div>";
  }

  async function openConfig() {
    const res = await fetch(API + "/config");
    const cfg = await res.json();
    const ro = cfg.readonly || {};
    const wr = cfg.writable || {};
    const keyStatus = ro["Key 状态"] || {};
    const roRows = [
      ["embedding 型号", ro["embedding 型号"]],
      ["embedding 维度", ro["embedding 维度"]],
      ["重排型号", ro["重排型号"]],
      ["改写/回答型号", ro["改写/回答型号"]],
      ["thinking=关闭", ro["thinking=关闭"]],
      ["Key 状态", "DashScope " + (keyStatus.DashScope || "") + " / DeepSeek " + (keyStatus.DeepSeek || "")],
      ["collection 名称", (ro["collection 名称"] || []).join(" / ")],
      ["切块口径", ro["切块口径"]]
    ].map(function (r) {
      return '<div class="cfg-row"><span>' + escapeHtml(r[0]) + "</span><b>" + escapeHtml(String(r[1] || "")) + "</b></div>";
    }).join("");
    openOverlay(
      '<div class="cfg-head"><h2>问答配置</h2><button class="kb-btn" type="button" data-close-overlay>关闭</button></div>' +
      '<div class="cfg-grid">' +
        '<div class="cfg-card"><h3>只读</h3>' + roRows + "</div>" +
        '<div class="cfg-card"><h3>可改（只对后续轮生效）</h3>' +
          '<label>召回 K</label><input id="cfgK" type="number" min="1" value="' + escapeHtml(wr.recall_k) + '">' +
          '<label>重排 n</label><input id="cfgN" type="number" min="1" value="' + escapeHtml(wr.rerank_n) + '">' +
          '<label>历史轮数</label><input id="cfgH" type="number" min="0" value="' + escapeHtml(wr.history_turns) + '">' +
          '<label>temperature</label><input id="cfgT" type="number" step="0.1" value="' + escapeHtml(wr.temperature) + '">' +
        "</div>" +
        '<div class="cfg-card wide"><label>系统 Prompt</label><textarea id="cfgSys">' + escapeHtml(wr.system_prompt || "") + "</textarea>" +
          '<label>改写 Prompt</label><textarea id="cfgRw">' + escapeHtml(wr.rewrite_prompt || "") + "</textarea>" +
          '<div class="cfg-actions"><button class="kb-btn" type="button" data-save-cfg>保存</button></div>' +
        "</div>" +
      "</div>"
    );
  }

  async function saveConfig() {
    const body = {
      recall_k: Number(document.getElementById("cfgK").value),
      rerank_n: Number(document.getElementById("cfgN").value),
      history_turns: Number(document.getElementById("cfgH").value),
      temperature: Number(document.getElementById("cfgT").value),
      system_prompt: document.getElementById("cfgSys").value,
      rewrite_prompt: document.getElementById("cfgRw").value
    };
    await fetch(API + "/config", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    toast("已保存，下一轮生效");
    closeOverlay();
  }

  async function openReindex() {
    openOverlay('<div class="cfg-head"><h2>重建索引</h2><button class="kb-btn" type="button" data-close-overlay>关闭</button></div><p>正在重建…</p>');
    const res = await fetch(API + "/reindex", { method: "POST" });
    const data = await res.json();
    await refreshHealth();
    if (!data.ok) {
      openOverlay(
        '<div class="cfg-head"><h2>重建索引</h2><button class="kb-btn" type="button" data-close-overlay>关闭</button></div>' +
        "<p>" + escapeHtml(data.message || "重建失败") + "</p>"
      );
      return;
    }
    const rows = (data.changed || []).concat(data.failed || []);
    const table = rows.length
      ? "<table class=\"reindex-table\"><thead><tr><th>path</th><th>chunk_id</th><th>action</th><th>旧 hash</th><th>新 hash</th><th>失败</th></tr></thead><tbody>" +
        rows.map(function (r) {
          return "<tr><td>" + escapeHtml(r.path) + "</td><td>" + escapeHtml(r.chunk_id) + "</td><td>" +
            escapeHtml(r.action) + "</td><td>" + escapeHtml(r.old_hash || "") + "</td><td>" +
            escapeHtml(r.new_hash || "") + "</td><td>" + escapeHtml(r.reason || "") + "</td></tr>";
        }).join("") + "</tbody></table>"
      : "<p>无变更。</p>";
    openOverlay(
      '<div class="cfg-head"><h2>重建索引</h2><button class="kb-btn" type="button" data-close-overlay>关闭</button></div>' +
      "<p>扫描 " + escapeHtml(String(data.scanned || 0)) + " 块，库内 " + escapeHtml(String(data.chunk_count || 0)) + " 点。</p>" + table
    );
  }

  function feedbackUiFromRow(row) {
    if (row.feedback === "up") return "赞";
    if (row.feedback === "down") return "踩";
    return "未评价";
  }

  function roundProjection(row) {
    const lanes = row.lanes || [];
    const cgen = row.c_gen || [];
    return {
      original_query: row.original_query || "",
      rewrite_query: row.rewrite_query || "",
      named_feature_ids: row.named_feature_ids || [],
      lanes: lanes,
      c_gen: cgen.map(function (b) {
        return {
          path: b.path,
          chunk_id: b.chunk_id,
          anchor: b.anchor,
          feature_id: b.feature_id,
          collection: b.collection,
          excerpt: b.excerpt || ""
        };
      }),
      answer: row.answer || "",
      status: row.status,
      feedback: feedbackUiFromRow(row)
    };
  }

  async function openRounds(detailId) {
    if (detailId) {
      const res = await fetch(API + "/rounds/" + encodeURIComponent(detailId));
      if (!res.ok) {
        toast("未找到该轮");
        return;
      }
      const row = await res.json();
      const proj = roundProjection(row);
      const cites = (proj.c_gen || []).map(citeButton).join("");
      openOverlay(
        '<div class="cfg-head"><h2>问答明细</h2><div><button class="kb-btn" type="button" data-open-rounds>返回列表</button> ' +
        '<button class="kb-btn" type="button" data-close-overlay>关闭</button></div></div>' +
        "<p>status = " + escapeHtml(proj.status) + "</p>" +
        "<p><b>原句</b></p><div class=\"qa-detail-pre\">" + escapeHtml(proj.original_query) + "</div>" +
        "<p><b>改写句</b></p><div class=\"qa-detail-pre\">" + escapeHtml(proj.rewrite_query) + "</div>" +
        "<p><b>named_feature_ids</b> " + escapeHtml(JSON.stringify(proj.named_feature_ids)) + "</p>" +
        "<p><b>分路</b> " + escapeHtml(JSON.stringify(proj.lanes)) + "</p>" +
        "<p><b>进生成块摘录</b></p>" + (cites || "<p>无</p>") +
        "<p><b>回答或错误态</b></p><div class=\"qa-detail-pre\">" + escapeHtml(proj.answer || proj.status) + "</div>" +
        "<p><b>反馈</b> " + escapeHtml(proj.feedback) + "</p>"
      );
      return;
    }
    const res = await fetch(API + "/rounds?limit=200");
    const data = await res.json();
    const items = data.items || [];
    const rows = items.map(function (r) {
      return "<tr><td>" + escapeHtml(r.created_at || "") + "</td><td>" + escapeHtml(r.status || "") +
        "</td><td>" + escapeHtml(r.original_query || "") + "</td><td>" + escapeHtml(feedbackUiFromRow(r)) +
        "</td><td>" +
        '<button class="kb-btn" type="button" data-round="' + escapeHtml(r.round_id) + '">打开</button></td></tr>';
    }).join("");
    openOverlay(
      '<div class="cfg-head"><h2>问答明细</h2><button class="kb-btn" type="button" data-close-overlay>关闭</button></div>' +
      (rows
        ? "<table class=\"qa-table\"><thead><tr><th>时间</th><th>结果</th><th>原句</th><th>反馈</th><th></th></tr></thead><tbody>" + rows + "</tbody></table>"
        : "<p>暂无已写入的轮次。</p>")
    );
  }

  async function openHeatmap() {
    const res = await fetch(API + "/heatmap");
    const data = await res.json();
    const items = data.items || [];
    const rows = items.map(function (r) {
      return "<tr><td>" + escapeHtml(r.feature_id) + "</td><td>" + escapeHtml(String(r.count)) + "</td></tr>";
    }).join("");
    const un = Number(data.unclassified || 0);
    openOverlay(
      '<div class="cfg-head"><h2>功能热度</h2><button class="kb-btn" type="button" data-close-overlay>关闭</button></div>' +
      "<table class=\"qa-table\"><thead><tr><th>feature_id</th><th>count</th></tr></thead><tbody>" + rows +
      (un > 0 ? "<tr><td>未归类</td><td>" + escapeHtml(String(un)) + "</td></tr>" : "") +
      "</tbody></table>"
    );
  }

  async function logoutAccount() {
    try {
      await fetch(API + "/auth/logout", { method: "POST", credentials: "same-origin" });
    } catch (e) {}
    state.me = null;
    goLogin();
  }

  function openPasswordForm() {
    openOverlay(
      '<div class="cfg-head"><h2>修改密码</h2><button class="kb-btn" type="button" data-close-overlay>关闭</button></div>' +
      '<label>原密码 <input id="qaOldPass" type="password"></label>' +
      '<label>新密码 <input id="qaNewPass" type="password"></label>' +
      '<p id="qaPassErr" class="qa-login-err" hidden></p>' +
      '<button class="kb-btn" type="button" data-save-password>保存</button>'
    );
  }

  async function savePassword() {
    const oldEl = document.getElementById("qaOldPass");
    const newEl = document.getElementById("qaNewPass");
    const err = document.getElementById("qaPassErr");
    try {
      const res = await fetch(API + "/auth/password", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          old_password: oldEl ? oldEl.value : "",
          new_password: newEl ? newEl.value : ""
        })
      });
      const data = await res.json().catch(function () { return {}; });
      if (!res.ok) {
        if (err) { err.hidden = false; err.textContent = data.message || "改密失败"; }
        return;
      }
      closeOverlay();
      state.me = null;
      goLogin();
    } catch (e) {
      if (err) { err.hidden = false; err.textContent = "改密失败"; }
    }
  }

  document.addEventListener("click", function (ev) {
    if (els.account && els.accountBtn && ev.target.closest("#qaAccountBtn")) {
      setAccountOpen(!els.account.classList.contains("open"));
      return;
    }
    if (els.account && els.account.classList.contains("open")) {
      if (!els.account.contains(ev.target)) {
        setAccountOpen(false);
      } else if (els.accountMenu && els.accountMenu.contains(ev.target)) {
        setAccountOpen(false);
      }
    }
    if (ev.target.closest("[data-qa-logout]")) { logoutAccount(); return; }
    if (ev.target.closest("[data-qa-password]")) { openPasswordForm(); return; }
    if (ev.target.closest("[data-save-password]")) { savePassword(); return; }
    const newBtn = ev.target.closest("[data-qa-new]");
    if (newBtn) { createConversation(); return; }
    const clearBtn = ev.target.closest("[data-qa-clear]");
    if (clearBtn) { clearCurrent(); return; }
    const del = ev.target.closest("[data-del]");
    if (del) { ev.stopPropagation(); deleteConversation(del.getAttribute("data-del")); return; }
    const item = ev.target.closest("[data-conv]");
    if (item && els.list && els.list.contains(item)) { switchConversation(item.getAttribute("data-conv")); return; }
    if (ev.target.closest("[data-qa-config]")) { openConfig(); return; }
    if (ev.target.closest("[data-qa-reindex]")) { openReindex(); return; }
    if (ev.target.closest("[data-qa-rounds]")) { openRounds(); return; }
    if (ev.target.closest("[data-qa-heatmap]")) { openHeatmap(); return; }
    if (ev.target.closest("[data-close-overlay]")) { closeOverlay(); return; }
    if (ev.target.closest("[data-open-rounds]")) { openRounds(); return; }
    const save = ev.target.closest("[data-save-cfg]");
    if (save) { saveConfig(); return; }
    const roundBtn = ev.target.closest("[data-round]");
    if (roundBtn) { openRounds(roundBtn.getAttribute("data-round")); return; }
    if (ev.target.closest("[data-close-cite]")) {
      const conv = active();
      setCiteOpen(conv, openCiteMsgId(conv), false);
      persist();
      render();
      return;
    }
    const toggle = ev.target.closest("[data-toggle-cite]");
    if (toggle) {
      const id = toggle.getAttribute("data-toggle-cite");
      const conv = active();
      setCiteOpen(conv, id, !Boolean(conv.citationsOpen && conv.citationsOpen[id]));
      persist();
      render();
      return;
    }
    const copy = ev.target.closest("[data-copy]");
    if (copy) {
      const id = copy.getAttribute("data-copy");
      const msg = active().messages.find(function (x) { return x.id === id; });
      if (msg) copyText(msg.text || "");
      return;
    }
    const fb = ev.target.closest("[data-qa-fb]");
    if (fb) {
      setFeedback(fb.getAttribute("data-msg"), fb.getAttribute("data-qa-fb"));
      return;
    }
    const regenBtn = ev.target.closest("[data-qa-regen]");
    if (regenBtn) {
      regen(regenBtn.getAttribute("data-qa-regen"));
      return;
    }
    const chip = ev.target.closest("[data-qa-chip]");
    if (chip) {
      send(chip.getAttribute("data-qa-chip") || "");
      return;
    }
    const cite = ev.target.closest("[data-cite-path]");
    if (cite) {
      openCitation(
        cite.getAttribute("data-cite-path"),
        cite.getAttribute("data-cite-anchor"),
        cite.getAttribute("data-cite-heading")
      );
    }
  });

  if (els.overlay) {
    els.overlay.addEventListener("click", function (ev) {
      if (ev.target === els.overlay) closeOverlay();
    });
  }
  if (els.send) els.send.addEventListener("click", function () { send(); });
  if (els.input) {
    els.input.addEventListener("input", autosizeInput);
    els.input.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter" && !ev.shiftKey) {
        ev.preventDefault();
        send();
      }
    });
    autosizeInput();
  }

  refreshHealth();
  refreshMe();

  window.HayyoQA = {
    onEnter: function () { refreshHealth(); refreshMe(); },
    closeOverlay: closeOverlay,
    getActiveId: function () { return state.activeId; },
    getConversations: function () { return state.conversations.slice(); },
    isBusy: function () { return state.busy; },
    truncate18: truncate18
  };
})();
