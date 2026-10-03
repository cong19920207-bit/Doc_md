/* 管理站壳。按工作区排页面，勾选权限只决定哪一块出现。
   查看、编辑、发布分别鉴权，测试结果由服务端执行。不套用演示皮肤，不跟随 H5 主题。 */
(function () {
  const API = "/api/kb";
  const AREAS = [
    { id: "overview", label: "总览" },
    { id: "qa", label: "问答" },
    { id: "issues", label: "问题" },
    { id: "config", label: "配置" },
    { id: "knowledge", label: "知识与记忆" },
    { id: "debug", label: "调试" },
    { id: "status", label: "运行状态" },
    { id: "audit", label: "操作记录" },
    { id: "access", label: "访问管理" }
  ];

  const els = {
    nav: document.getElementById("adminNav"),
    main: document.getElementById("adminMain"),
    user: document.getElementById("adminUser"),
    healthBtn: document.getElementById("healthToggle"),
    healthRule: document.getElementById("healthRule"),
    healthPop: document.getElementById("healthPop")
  };
  const state = {
    me: null,
    area: "overview",
    health: null,
    qaSeg: "rounds",
    qaId: "",
    qaQ: "",
    roundFilters: { op_type: "", route: "", attention: "" },
    qaItems: [],
    qaDetailHeld: false,
    configDirty: false,
    configTab: "runtime",
    knowledgeTab: "sources",
    overviewReturn: null,
    /* 全部轮次：服务端分页缓存。返回列表保留筛选与已加载页，刷新才重新取。 */
    qaList: null,
    /* 按会话（A05）：服务端筛选与分页缓存、详情与各回合正在查看的版本 */
    convList: null,
    convFilters: { q: "", account: "", visibility: "", cleared: "", state: "" },
    convDetail: null,
    purgeAsk: "",
    convVerPick: {},
    /* 反馈（A16）：服务端筛选与分页缓存，默认被踩 */
    fbList: null,
    fbFilters: { value: "down", account: "" },
    /* 运行概览（A15）：时间范围天数 */
    ovDays: 7,
    /* 诊断（A18）：异常列表与当前选中 */
    diagItems: [],
    diagSel: "",
    issueId: "",
    audit: null,
    accessTab: "accounts",
    reindexHtml: "",
    notice: null
  };

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /* 列表里去掉微秒，避免时间折成两行。详情仍用接口原值。 */
  function shortTime(value) {
    return String(value || "").replace(/\.\d+$/, "");
  }

  function hasPerm(name) {
    if (!state.me) return false;
    if (state.me.is_super) return true;
    return (state.me.permissions || []).indexOf(name) >= 0;
  }

  /* 旧「配置」已停用：配置现值与 Prompt 正文分别按查看权限显示。 */
  function canSeeConfig() {
    return hasPerm("配置查看") || hasPerm("Prompt查看");
  }

  function accountName(row) {
    var n = String((row && row.username) || "").trim();
    return n || "—";
  }

  function feedbackLabel(row) {
    if (row.feedback === "up") return "赞";
    if (row.feedback === "down") return "踩";
    return "未评价";
  }

  function feedbackTone(row) {
    if (row.feedback === "up") return "ok";
    if (row.feedback === "down") return "danger";
    return "muted";
  }

  /* 只翻译已经写入库的状态字，不新增结果类型。 */
  function statusLabel(status) {
    if (status === "success") return "成功";
    if (status === "gen_fail" || status === "interrupted") return "失败";
    if (status === "refuse") return "拒绝";
    if (status === "empty") return "无结果";
    return status || "—";
  }

  function statusTone(status) {
    if (status === "success") return "ok";
    if (status === "refuse" || status === "empty") return "warn";
    return "danger";
  }

  function badge(label, tone) {
    return '<span class="kb-badge is-' + tone + '">' + escapeHtml(label) + "</span>";
  }

  function dot(tone) {
    return '<i class="kb-dot is-' + tone + '"></i>';
  }

  async function api(path, opts) {
    const res = await fetch(API + path, Object.assign({ credentials: "same-origin" }, opts || {}));
    const data = await res.json().catch(function () { return {}; });
    if (!res.ok) {
      const err = new Error(data.message || ("HTTP " + res.status));
      err.status = res.status;
      err.code = data.code || "";
      throw err;
    }
    return data;
  }

  /* ---------- 列表骨架（G-ADM-E01）：服务端分页、六态、时区 ---------- */
  const DEFAULT_TZ = "Asia/Shanghai";

  /* 服务端时间按 UTC 存，页面按接口给的显示时区换算，并标明时区。 */
  function fmtTime(value, tz) {
    const raw = String(value || "").trim();
    if (!raw) return "";
    const iso = raw.replace(" ", "T").replace(/(\.\d{3})\d*$/, "$1") + (/[zZ]|[+-]\d\d:?\d\d$/.test(raw) ? "" : "Z");
    const d = new Date(iso);
    if (isNaN(d.getTime())) return shortTime(raw);
    try {
      const parts = new Intl.DateTimeFormat("zh-CN", {
        timeZone: tz || DEFAULT_TZ, hour12: false,
        year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit"
      }).formatToParts(d);
      const get = function (t) { return (parts.filter(function (p) { return p.type === t; })[0] || {}).value || ""; };
      return get("year") + "-" + get("month") + "-" + get("day") + " " + get("hour") + ":" + get("minute") + ":" + get("second");
    } catch (e) {
      return shortTime(raw);
    }
  }

  function listTz() {
    return (state.qaList && state.qaList.meta && state.qaList.meta.tz) || DEFAULT_TZ;
  }

  function tzNote(data) {
    const tz = (data && data.tz) || DEFAULT_TZ;
    const field = (data && data.time_field) || "";
    return '<p class="kb-muted kb-list-note">时间：' + escapeHtml(field ? field + " · " : "") + escapeHtml(tz) + "</p>";
  }

  /* 六态：loading / ok / empty / forbidden / error / partial。报错绝不显示成「暂无记录」。 */
  function listState(kind, text) {
    if (kind === "loading") return '<p class="kb-muted kb-list-state" data-list-state="loading">' + escapeHtml(text || "加载中…") + "</p>";
    if (kind === "forbidden") return '<p class="kb-err kb-list-state" data-list-state="forbidden">' + escapeHtml(text || "没有权限查看。") + "</p>";
    if (kind === "error") return '<p class="kb-err kb-list-state" data-list-state="error">' + escapeHtml("加载失败：" + (text || "服务异常")) + "</p>";
    if (kind === "partial") return '<p class="kb-warn kb-list-state" data-list-state="partial">' + escapeHtml(text || "结果不完整。") + "</p>";
    return '<p class="kb-empty kb-list-state" data-list-state="empty">' + escapeHtml(text || "暂无记录。") + "</p>";
  }

  function listError(e) {
    return listState(e && e.status === 403 ? "forbidden" : "error", e && e.status === 403 ? "" : (e && e.message));
  }

  function coverageNote(data) {
    const cov = data && data.coverage;
    return cov && cov.complete === false ? listState("partial", cov.note || "结果不完整。") : "";
  }

  function qs(params) {
    const out = [];
    Object.keys(params).forEach(function (k) {
      const v = params[k];
      if (v === "" || v == null) return;
      out.push(encodeURIComponent(k) + "=" + encodeURIComponent(v));
    });
    return out.length ? "?" + out.join("&") : "";
  }

  function visibleAreas() {
    return AREAS.filter(function (a) { return areaVisible(a.id); });
  }

  function areaVisible(id) {
    if (id === "overview") return overviewParts().length > 0;
    if (id === "qa") return hasPerm("问答明细") || hasPerm("反馈汇总") || hasPerm("对话审计");
    if (id === "issues") return hasPerm("问题处理");
    if (id === "config") return canSeeConfig();
    if (id === "knowledge") return hasPerm("重建") || hasPerm("知识源查看");
    if (id === "status") return hasPerm("健康");
    if (id === "debug") return hasPerm("Prompt调试") && hasPerm("Prompt查看") && hasPerm("配置查看");
    if (id === "audit") return hasPerm("操作审计");
    if (id === "access") return !!(state.me && state.me.is_super);
    return false;
  }

  function overviewParts() {
    const parts = [];
    if (hasPerm("问答明细") || hasPerm("反馈汇总")) parts.push("pending");
    if (hasPerm("功能热度")) parts.push("heat");
    if (hasPerm("操作审计")) parts.push("ops");
    if (hasPerm("数据概览")) parts.push("stats");
    return parts;
  }

  function qaSegs() {
    const segs = [];
    if (hasPerm("问答明细")) segs.push({ id: "rounds", label: "全部轮次" });
    if (hasPerm("反馈汇总")) segs.push({ id: "down", label: "反馈" });
    if (hasPerm("对话审计")) segs.push({ id: "convs", label: "按会话" });
    return segs;
  }

  function renderNav() {
    const areas = visibleAreas();
    if (!areas.some(function (a) { return a.id === state.area; })) {
      state.area = areas.length ? areas[0].id : "";
    }
    const icons = {overview:'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',qa:'M4 4h16v12H9l-5 4z M8 8h8 M8 12h5',issues:'M12 3l10 18H2z M12 9v5 M12 17v1',index:'M12 3l9 5-9 5-9-5z M3 12l9 5 9-5 M3 17l9 5 9-5',debug:'M8 3h8 M10 3v6l-7 11h18L14 9V3 M7 15h10',audit:'M5 3h14v18H5z M9 7h6 M9 11h6 M9 15h4',access:'M16 8a4 4 0 1 1-8 0 4 4 0 0 1 8 0 M4 21v-2a8 8 0 0 1 16 0v2'};
    icons.knowledge = icons.index;
    icons.config = 'M4 6h16 M4 12h16 M4 18h16 M8 3v6 M16 9v6 M10 15v6';
    icons.status = 'M3 12h4l3-8 4 16 3-8h4';
    els.nav.innerHTML = areas.map(function (a) {
      return '<button type="button" data-area="' + a.id + '"' +
        (a.id === state.area ? ' class="active" aria-current="page"' : "") + '><svg class="kb-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="' + icons[a.id] + '"/></svg>' + escapeHtml(a.label) + "</button>";
    }).join("");
  }

  function pageHead(title, desc, extra) {
    return '<header class="kb-page-head"><div><h2>' + escapeHtml(title) + "</h2>" +
      (desc ? "<p>" + escapeHtml(desc) + "</p>" : "") +
      "</div>" + (extra || "") + "</header>" +
      '<p id="kbMsg" class="kb-msg"></p>';
  }

  function setMsg(text, isErr) {
    const node = document.getElementById("kbMsg");
    if (!node) return;
    node.textContent = text || "";
    node.className = isErr ? "kb-msg is-err" : "kb-msg";
  }

  function takeNotice() {
    if (!state.notice) return;
    setMsg(state.notice.text, state.notice.err);
    state.notice = null;
  }

  function empty(text) {
    return '<p class="kb-empty">' + escapeHtml(text) + "</p>";
  }

  async function showArea() {
    const area = state.area;
    els.main.classList.toggle("is-fit", state.area === "qa");
    try {
      if (state.area === "overview") await pageOverview();
      else if (state.area === "qa") await pageQa();
      else if (state.area === "issues") await pageIssues();
      else if (state.area === "config") await pageConfig();
      else if (state.area === "knowledge") await pageKnowledge();
      else if (state.area === "status") await pageStatus();
      else if (state.area === "debug") await pageDebug();
      else if (state.area === "audit") await pageAudits();
      else if (state.area === "access") await pageAccess();
      else els.main.innerHTML = empty("没有可显示的页面。");
    } catch (e) {
      if (state.area !== area) return;
      els.main.innerHTML = pageHead("无法打开", "") + '<p class="kb-err">' + escapeHtml(e.message) + "</p>";
    }
  }

  function gotoArea(id) {
    if (!areaVisible(id)) return false;
    if (state.configDirty && !window.confirm("配置还没保存，离开后这次修改会丢掉。")) return false;
    if (!allowRoleLeave()) return false;
    state.configDirty = false;
    if (id === "qa" && state.area !== "overview" && state.area !== "qa") state.overviewReturn = null;
    state.area = id;
    renderNav();
    showArea();
    return true;
  }

  function pageTabs(items, selected, attr) {
    return '<div class="kb-subnav" aria-label="页面分组">' + items.map(function (item) {
      return '<button type="button" data-' + attr + '="' + item.id + '" aria-pressed="' + (item.id === selected) + '" class="' +
        (item.id === selected ? 'active' : '') + '">' + escapeHtml(item.label) + '</button>';
    }).join('') + '</div>';
  }

  function openOverviewQa(seg, id, attention, feedbackValue) {
    state.overviewReturn = { main: els.main.scrollTop, window: window.scrollY };
    state.qaSeg = seg;
    state.qaId = id || "";
    state.qaQ = "";
    state.qaDetailHeld = false;
    state.roundFilters = { op_type: "", route: "", attention: attention ? "1" : "" };
    state.qaList = null;
    state.fbList = null;
    state.fbFilters = { value: feedbackValue || "down", account: "", handled: "" };
    gotoArea("qa");
  }

  /* ---------- 顶栏健康：仅「健康」勾选。接口仍是原来的匿名 /health ---------- */
  function keyTone(value) {
    return value === "已配置" ? "ok" : "warn";
  }

  function renderHealthDots() {
    if (!hasPerm("健康")) {
      els.healthBtn.hidden = true;
      els.healthRule.hidden = true;
      els.healthPop.hidden = true;
      return;
    }
    const data = state.health || {};
    const keysWarn = keyTone(data.key_dashscope) !== "ok" || keyTone(data.key_deepseek) !== "ok";
    els.healthBtn.hidden = false;
    els.healthRule.hidden = false;
    els.healthBtn.innerHTML =
      '<span class="kb-health-item">' + dot(data.index_ready ? "ok" : "danger") + "索引</span>" +
      '<span class="kb-health-item">' + dot(data.qdrant_ready ? "ok" : "danger") + "Qdrant</span>" +
      '<span class="kb-health-item">' + dot(keysWarn ? "warn" : "ok") + "密钥</span>";
    const yesNo = function (v) { return v ? "是" : "否"; };
    const rows = [
      ["索引就绪", yesNo(data.index_ready)],
      ["Qdrant", yesNo(data.qdrant_ready)],
      ["配置", yesNo(data.config_ready)],
      ["DashScope Key", data.key_dashscope || "未配置"],
      ["DeepSeek Key", data.key_deepseek || "未配置"],
      ["块数", String(data.chunk_count == null ? 0 : data.chunk_count)]
    ];
    if (data.startup_error) rows.push(["启动错误", String(data.startup_error)]);
    els.healthPop.innerHTML = '<div class="kb-card-h">健康</div>' + rows.map(function (r) {
      return '<div class="kb-kv"><b>' + escapeHtml(r[0]) + "</b><span>" + escapeHtml(r[1]) + "</span></div>";
    }).join("");
  }

  async function loadHealth() {
    if (!hasPerm("健康")) return;
    const data = await fetch(API + "/health", { credentials: "same-origin" }).then(function (r) { return r.json(); });
    state.health = data;
    renderHealthDots();
  }

  function healthCards(data) {
    const yesNo = function (v) { return v ? "是" : "否"; };
    const card = function (label, value, tone) {
      return '<article class="kb-card kb-stat"><em>' + escapeHtml(label) + "</em><strong>" +
        (tone ? dot(tone) : "") + escapeHtml(value) + "</strong></article>";
    };
    const extra = [
      ["DashScope Key", data.key_dashscope || "未配置"],
      ["DeepSeek Key", data.key_deepseek || "未配置"]
    ];
    if (data.startup_error) extra.push(["启动错误", String(data.startup_error)]);
    return '<div class="kb-stats">' +
      card("索引就绪", yesNo(data.index_ready), data.index_ready ? "ok" : "danger") +
      card("Qdrant", yesNo(data.qdrant_ready), data.qdrant_ready ? "ok" : "danger") +
      card("配置", yesNo(data.config_ready), data.config_ready ? "ok" : "danger") +
      card("块数", String(data.chunk_count == null ? 0 : data.chunk_count), "") +
      "</div>" +
      '<section class="kb-card kb-pad" style="margin-top:12px">' + extra.map(function (r) {
        return '<div class="kb-kv"><b>' + escapeHtml(r[0]) + "</b><span>" + escapeHtml(r[1]) + "</span></div>";
      }).join("") + "</section>";
  }

  /* ---------- 总览 ---------- */
  async function pageOverview() {
    const parts = overviewParts();
    els.main.innerHTML = pageHead("总览", "查看需关注的问答、运行统计与最近操作。") +
      '<div id="ovBody"><p class="kb-muted">加载中…</p></div>';
    const body = document.getElementById("ovBody");
    const jobs = {};
    if (hasPerm("反馈汇总")) jobs.down = api("/admin/feedback-summary");
    /* 待处理由服务端筛选（非成功或被踩），不再先取 200 行在页面里过滤。 */
    if (hasPerm("问答明细")) jobs.rounds = api("/rounds" + qs({ pending: 1, page_size: 8 }));
    if (hasPerm("功能热度")) jobs.heat = api("/admin/heatmap");
    if (hasPerm("操作审计")) jobs.ops = api("/admin/audits" + qs({ page_size: 5 }));
    if (hasPerm("数据概览")) jobs.stats = api("/admin/overview" + qs({ since: ovSince(state.ovDays), domain: state.ovDomain || "prod" }));
    const keys = Object.keys(jobs);
    const settled = await Promise.all(keys.map(function (k) {
      return jobs[k].then(function (v) { return { ok: true, v: v }; }, function (e) { return { ok: false, e: e }; });
    }));
    const got = {};
    settled.forEach(function (item, i) { got[keys[i]] = item; });
    if (!body.isConnected) return;
    body.innerHTML = renderOverview(got, parts);
    els.main.querySelectorAll("[data-goto]").forEach(function (btn) {
      btn.onclick = function () { gotoArea(btn.getAttribute("data-goto")); };
    });
    els.main.querySelectorAll("[data-open-round]").forEach(function (btn) {
      btn.onclick = function () {
        const seg = btn.getAttribute("data-open-seg");
        const target = seg === "down" && hasPerm("反馈汇总") ? "down" : hasPerm("问答明细") ? "rounds" : "down";
        openOverviewQa(target, btn.getAttribute("data-open-round"), target === "rounds");
      };
    });
    const all = document.getElementById("ovAttentionAll");
    if (all) all.onclick = function () { openOverviewQa(hasPerm("问答明细") ? "rounds" : "down", "", true); };
    bindStats();
    if (state.restoreOverview) {
      const pos = state.restoreOverview;
      state.restoreOverview = null;
      requestAnimationFrame(function () {
        if (state.area !== "overview") return;
        els.main.scrollTop = pos.main;
        window.scrollTo(0, pos.window);
      });
    }
  }

  function renderOverview(got, parts) {
    const top = [];
    if (parts.indexOf("pending") >= 0) top.push(renderPending(got));
    if (parts.indexOf("ops") >= 0) top.push(renderOps(got.ops));
    let html = '<div class="kb-overview">';
    if (top.length) {
      html += '<div class="kb-overview-top' + (top.length === 1 ? " is-one" : "") + '">' + top.join("") + "</div>";
    }
    if (parts.indexOf("stats") >= 0) html += renderStats(got.stats);
    if (parts.indexOf("heat") >= 0) html += renderHeat(got.heat);
    html += "</div>";
    return html;
  }

  /* ---------- 运行概览（A15）：只读聚合；每个数字带口径，未知单列，分母为 0 显示不适用 ---------- */
  const OV_DAYS = [7, 30, 92];

  function ovSince(days) {
    const n = Number(days) || 7;
    const d = new Date(Date.now() - (n - 1) * 86400000);
    try {
      return new Intl.DateTimeFormat("en-CA", { timeZone: DEFAULT_TZ, year: "numeric", month: "2-digit", day: "2-digit" }).format(d);
    } catch (e) {
      return d.toISOString().slice(0, 10);
    }
  }

  function ovValue(m) {
    const v = m.value;
    if (m.status === "not_connected" || v == null) return "未接入";
    if (typeof v === "number") return String(v);
    if (v && v.display != null) return v.display + "（" + v.numerator + " / " + v.denominator + "）";
    if (m.key === "duration") {
      return v.samples ? "均值 " + v.mean_ms + " · P50 " + v.p50_ms + " · P95 " + v.p95_ms + "（样本 " + v.samples + "）" : "无样本";
    }
    const keys = Object.keys(v || {});
    return keys.length ? keys.map(function (k) { return k + " " + v[k]; }).join("、") : "0";
  }

  function ovPairs(items) {
    return '<dl class="kb-ov-pairs">' + items.map(function (item) {
      return '<div><dt>' + escapeHtml(item[0]) + '</dt><dd>' +
        escapeHtml(item[1] == null ? "未知" : item[1]) + '</dd></div>';
    }).join("") + '</dl>';
  }

  function ovBreakdown(m) {
    const v = m.value;
    if (m.status === "not_connected" || !v || typeof v !== "object" || v.display != null) return "";
    if (m.key === "duration") {
      return v.samples ? ovPairs([
        ["均值（毫秒）", v.mean_ms], ["P50（毫秒）", v.p50_ms],
        ["P95（毫秒）", v.p95_ms], ["样本（次）", v.samples]
      ]) : "";
    }
    const labels = m.key === "test_status"
      ? { queued: "排队中", running: "运行中", done: "已完成", failed: "失败", interrupted: "已中断" } : {};
    const keys = Object.keys(v);
    return keys.length ? ovPairs(keys.map(function (k) {
      return [k === "null" ? "未知" : labels[k] || k, v[k]];
    })) : "";
  }

  function ovExtras(m) {
    const labels = {
      unknown: "未知", rejected: "被拒请求", not_called: "未调用", unrecorded: "未记录",
      running: "运行中", pending_retry: "待补写", pending: "保存中", not_applicable: "未发生保存",
      up: "赞", down: "踩", unrated: "未评价"
    };
    const bits = [];
    Object.keys(labels).forEach(function (k) {
      if (m[k] != null && typeof m[k] !== "object") bits.push(labels[k] + " " + m[k]);
    });
    return bits.length ? '<div class="kb-ov-extras">' + bits.map(function (bit) {
      return '<span>' + escapeHtml(bit) + '</span>';
    }).join("") + '</div>' : "";
  }

  function ovMetricRow(m) {
    const drill = m.key.indexOf("feedback") === 0 && hasPerm("反馈汇总")
      ? ' <button type="button" class="kb-link" data-ov-drill="feedback">看反馈</button>' : "";
    const extra = ovExtras(m);
    const breakdown = ovBreakdown(m);
    const ratio = m.value && m.value.display != null ? m.value : null;
    const value = breakdown || '<div class="kb-ov-val"><span>' + escapeHtml(ratio ? ratio.display : ovValue(m)) + '</span>' +
      (ratio ? '<small>' + escapeHtml(ratio.numerator + " / " + ratio.denominator) + '</small>' : "") + '</div>';
    return '<div class="kb-ov-row' + (breakdown ? ' is-breakdown' : '') + '"><div class="kb-ov-title"><strong>' +
      escapeHtml(m.label) + '</strong><span class="kb-ov-unit">单位：' + escapeHtml(m.unit) + '</span>' + drill + '</div>' +
      value + extra + '<p class="kb-muted kb-ov-rule">' + escapeHtml(m.rule) + '</p></div>';
  }

  function ovHeatHtml(h, tz) {
    const rows = (h.items || []).slice(0, 8).map(function (r) {
      return '<div class="kb-kv"><b>' + escapeHtml(r.feature_id) + "</b><span>" + escapeHtml(String(r.count)) + "</span></div>";
    }).join("") || empty("范围内没有符合资格的执行。");
    const cov = h.coverage || {};
    const legacy = h.legacy || {};
    return '<div class="kb-ov-sec"><h3>功能热度（新口径）</h3>' +
      (cov.complete === false ? listState("partial", cov.note) : "") + rows +
      ovPairs([["未归类", h.unclassified], ["资格未知", h.unknown_qualification], ["生成集未采集", h.unknown_c_gen],
        ["扫描 / 上限", cov.scanned + " / " + cov.limit]]) +
      (cov.window_start ? '<p class="kb-muted">实际窗口：' + escapeHtml(fmtTime(cov.window_start, tz)) + " ～ " + escapeHtml(fmtTime(cov.window_end, tz)) + '</p>' : "") +
      '<p class="kb-muted">' + escapeHtml(h.rule || "") + "</p>" +
      '<p class="kb-muted">' + escapeHtml(legacy.note || "") + "：" + escapeHtml(String(legacy.rows || 0)) + " 条" +
      ((legacy.items || []).length ? "，" + escapeHtml(legacy.items.slice(0, 5).map(function (r) { return r.feature_id + " " + r.count; }).join("、")) : "") + "</p></div>";
  }

  function renderStats(pack) {
    const days = state.ovDays || 7;
    const pick = '<select class="kb-select" id="ovDays" title="时间范围" aria-label="时间范围">' + OV_DAYS.map(function (d) {
      return '<option value="' + d + '"' + (d === days ? " selected" : "") + ">近 " + d + " 天</option>";
    }).join("") + "</select>";
    const head = '<section class="kb-card kb-ov"><div class="kb-card-h"><span>运行概览</span>' +
      '<div class="kb-ov-controls"><span class="kb-segs">' + ['prod','test'].map(function (domain) { return '<button type="button" data-ov-domain="' + domain + '" class="' + ((state.ovDomain || 'prod') === domain ? 'active' : '') + '">' + (domain === 'prod' ? '生产' : '测试') + '</button>'; }).join('') + '</span>' +
      pick + "</div></div>";
    if (!pack || !pack.ok) return head + '<div class="kb-card-b">' + listError(pack && pack.e) + "</div></section>";
    const d = pack.v;
    const tz = d.tz || DEFAULT_TZ;
    const rng = d.range || {};
    const meta = [["统计范围", rng.since + ' ～ ' + rng.until],
      ["时间口径", (d.domain === 'test' ? '按测试受理时间' : '按执行开始时间') + ' · ' + tz]];
    if (d.domain !== 'test') meta.push(["数据截止", fmtTime(d.data_cutoff, tz)], ["查询方式", "实时查询、不缓存"]);
    const note = d.domain === 'test' ? d.note || '' : (d.legacy_note || '') + '：' + String(d.legacy_rows || 0) + ' 条';
    const decl = '<dl class="kb-ov-meta">' + meta.map(function (item) {
      return '<div><dt>' + escapeHtml(item[0]) + '</dt><dd>' + escapeHtml(item[1]) + '</dd></div>';
    }).join('') + '</dl><p class="kb-muted kb-ov-note">' + escapeHtml(note) + '</p>';
    const secs = (d.sections || []).map(function (s) {
      return '<div class="kb-ov-sec"><h3>' + escapeHtml(s.label) + "</h3>" +
        (s.note ? '<p class="kb-muted">' + escapeHtml(s.note) + "</p>" : "") +
        '<div class="kb-ov-metrics">' + s.metrics.map(ovMetricRow).join("") + "</div></div>";
    }).join("");
    return head + '<div class="kb-card-b">' + decl + secs + (d.domain !== "test" && d.heat ? ovHeatHtml(d.heat, tz) : "") + "</div></section>";
  }

  function bindStats() {
    els.main.querySelectorAll("[data-ov-domain]").forEach(function (btn) { btn.onclick=function () { state.ovDomain=btn.dataset.ovDomain; pageOverview(); }; });
    const sel = document.getElementById("ovDays");
    if (sel) {
      sel.onchange = function () {
        state.ovDays = Number(sel.value) || 7;
        pageOverview();
      };
    }
    els.main.querySelectorAll("[data-ov-drill]").forEach(function (btn) {
      btn.onclick = function () {
        openOverviewQa("down", "", false, "all");
      };
    });
  }

  function renderPending(got) {
    const items = [];
    const seen = {};
    let more = false;
    let tz = DEFAULT_TZ;
    if (got.rounds && got.rounds.ok) {
      tz = got.rounds.v.tz || tz;
      more = !!got.rounds.v.has_more;
      (got.rounds.v.items || []).forEach(function (r) {
        seen[r.round_id] = true;
        const down = r.feedback === "down" && r.status === "success";
        items.push({
          id: r.round_id,
          time: r.created_at || "",
          query: r.original_query || "",
          badge: down ? "踩" : statusLabel(r.status),
          tone: down ? "danger" : statusTone(r.status),
          seg: down ? "down" : ""
        });
      });
    } else if (got.down && got.down.ok) {
      /* 只有反馈汇总权限时，沿用被踩列表 */
      (got.down.v.down || []).forEach(function (r) {
        if (seen[r.round_id]) return;
        items.push({ id: r.round_id, time: r.created_at || "", query: r.original_query || "", badge: "踩", tone: "danger", seg: "down" });
      });
    }
    const failed = (got.rounds && !got.rounds.ok && got.rounds.e) || (!got.rounds && got.down && !got.down.ok && got.down.e);
    const rows = items.slice(0, 8).map(function (r) {
      return '<button type="button" class="kb-qa-row" data-open-round="' + escapeHtml(r.id) + '"' +
        (r.seg ? ' data-open-seg="' + escapeHtml(r.seg) + '"' : "") + ">" +
        '<span class="kb-qa-meta"><span class="kb-mono">' + escapeHtml(fmtTime(r.time, tz)) + "</span>" +
        badge(r.badge, r.tone) + "</span>" +
        '<span class="kb-qa-line"><span class="kb-ellipsis">' + escapeHtml(r.query) + "</span></span></button>";
    }).join("");
    const count = Math.min(items.length, 8) + (more ? "+" : "");
    let bodyHtml;
    if (failed) bodyHtml = listError(failed);
    else bodyHtml = rows || listState("empty", "没有需关注的问答。");
    return '<section class="kb-card kb-pane"><div class="kb-card-h"><span>需关注 <span class="kb-count">' +
      escapeHtml(count) + '</span></span><button type="button" class="kb-link" id="ovAttentionAll">查看全部</button></div>' +
      '<p class="kb-list-note kb-muted">' + (hasPerm("问答明细") ? '非成功执行或被踩的回答' : '被踩的回答') +
      '；问题处理进度见关联问题。</p><div class="kb-card-b">' + bodyHtml + "</div></section>";
  }

  function renderHeat(pack) {
    if (!pack || !pack.ok) {
      return '<section class="kb-card kb-heat"><div class="kb-card-h">功能热度</div>' +
        '<p class="kb-err" style="padding:12px 16px">' + escapeHtml(pack && pack.e ? pack.e.message : "无法加载") + "</p></section>";
    }
    const data = pack.v;
    const items = (data.items || []).slice();
    if (Number(data.unclassified || 0) > 0) items.push({ display_name: "未归类", count: data.unclassified });
    items.sort(function (a, b) { return (Number(b.count) || 0) - (Number(a.count) || 0); });
    const top = items.slice(0, 8);
    let max = 1;
    top.forEach(function (r) { max = Math.max(max, Number(r.count) || 0); });
    const rows = top.map(function (r) {
      const count = Number(r.count) || 0;
      const width = Math.max(0, Math.round((count / max) * 100));
      return '<div class="kb-tr" style="grid-template-columns:120px minmax(0,1fr) 48px"><span class="kb-ellipsis">' +
        escapeHtml(r.display_name || r.feature_id) + '</span><div class="kb-bar"><span style="width:' +
        width + '%"></span></div><span class="kb-mono">' + escapeHtml(String(count)) + "</span></div>";
    }).join("");
    const hint = items.length > 8 ? '<span class="kb-count">前 8</span>' : "";
    return '<section class="kb-card kb-heat"><div class="kb-card-h"><span>功能热度</span>' + hint +
      '</div><div class="kb-card-b">' + (rows || empty("暂无热度。")) + "</div></section>";
  }

  function renderOps(pack) {
    const head = '<section class="kb-card kb-pane"><div class="kb-card-h"><span>最近操作</span>' +
      '<button type="button" class="kb-link" data-goto="audit">进入记录</button></div><div class="kb-card-b">';
    if (!pack || !pack.ok) {
      return head + listError(pack && pack.e) + "</div></section>";
    }
    const tz = pack.v.tz || DEFAULT_TZ;
    const rows = (pack.v.items || []).slice(0, 5).map(function (r) {
      const what = [r.action, r.object].filter(Boolean).join(" · ");
      return '<div class="kb-qa-row"><span class="kb-qa-meta"><span class="kb-mono">' + escapeHtml(fmtTime(r.created_at, tz)) +
        '</span><span class="kb-who">' + escapeHtml(accountName({ username: r.actor_username })) + "</span></span>" +
        '<span class="kb-qa-line"><span class="kb-ellipsis">' + escapeHtml(what) + "</span></span></div>";
    }).join("");
    return head + (rows || empty("还没有操作记录。")) + "</div></section>";
  }

  /* ---------- 问答：明细 / 被踩 / 会话，左列表右详情 ---------- */
  async function pageQa() {
    const segs = qaSegs();
    if (!segs.some(function (s) { return s.id === state.qaSeg; })) {
      state.qaSeg = segs.length ? segs[0].id : "";
    }
    state.qaDetailHeld = false;
    const tools = '<div class="kb-tools"><div class="kb-segs">' + segs.map(function (s) {
      return '<button type="button" data-seg="' + s.id + '"' + (s.id === state.qaSeg ? ' class="active"' : "") + ">" +
        escapeHtml(s.label) + "</button>";
    }).join("") + '</div><input id="qaSearch" class="kb-search" placeholder="' +
      (state.qaSeg === "rounds" ? "搜索原句（回车查询）"
        : state.qaSeg === "convs" ? "搜索标题或消息（回车查询）"
          : state.qaSeg === "down" ? "账号（回车查询）" : "搜索原句或账号") + '" value="' +
      escapeHtml(state.qaSeg === "convs" ? state.convFilters.q : state.qaSeg === "down" ? state.fbFilters.account : state.qaQ) + '">' +
      (state.qaSeg === "convs" ? convFiltersHtml() : "") +
      (state.qaSeg === "down" ? fbFiltersHtml() : "") +
      (state.qaSeg === "rounds" ? roundFiltersHtml() : "") +
      '<button type="button" class="kb-btn" id="qaRefresh">刷新</button></div>';
    els.main.innerHTML = pageHead("问答", "按执行、反馈或会话查看详情。", state.overviewReturn ? '<button type="button" class="kb-btn" id="qaBackOverview">← 返回总览</button>' : "") + tools +
      '<div class="kb-fit"><div class="kb-split"><div id="qaList" class="kb-card"></div><div id="qaDetail" class="kb-card"></div></div></div>';
    const listView = document.getElementById("qaList");
    const back = document.getElementById("qaBackOverview");
    if (back) back.onclick = function () {
      state.restoreOverview = state.overviewReturn;
      state.overviewReturn = null;
      gotoArea("overview");
    };
    els.main.querySelectorAll("[data-seg]").forEach(function (btn) {
      btn.onclick = function () {
        state.qaSeg = btn.getAttribute("data-seg");
        state.qaId = "";
        state.qaQ = "";
        pageQa();
      };
    });
    const search = document.getElementById("qaSearch");
    if (state.qaSeg === "rounds") {
      /* 全部轮次在服务端检索：回车才查，避免每个字都打接口 */
      search.onkeydown = function (ev) {
        if (ev.key !== "Enter") return;
        state.qaQ = ev.target.value;
        state.qaList = null;
        state.qaId = "";
        pageQa();
      };
      document.getElementById("qaRefresh").onclick = function () {
        state.qaList = null;
        pageQa();
      };
      bindRoundFilters();
    } else if (state.qaSeg === "convs") {
      /* 会话按标题与消息正文在服务端检索：回车才查 */
      search.onkeydown = function (ev) {
        if (ev.key !== "Enter") return;
        state.convFilters.q = ev.target.value.trim();
        state.qaId = "";
        pageQa();
      };
      document.getElementById("qaRefresh").onclick = function () {
        state.convList = null;
        pageQa();
      };
      bindConvFilters();
    } else if (state.qaSeg === "down") {
      /* 反馈在服务端按账号与反馈值筛选：回车才查 */
      search.onkeydown = function (ev) {
        if (ev.key !== "Enter") return;
        state.fbFilters.account = ev.target.value.trim();
        state.qaId = "";
        pageQa();
      };
      document.getElementById("qaRefresh").onclick = function () {
        state.fbList = null;
        pageQa();
      };
      bindFbFilters();
    } else {
      search.oninput = function (ev) {
        state.qaQ = ev.target.value;
        paintQaList();
      };
    }
    try {
      if (state.qaSeg === "rounds") {
        const key = String(state.qaQ || "").trim();
        if (!state.qaList || state.qaList.key !== roundListKey(key)) {
          document.getElementById("qaList").innerHTML = listState("loading");
          const data = await api("/rounds" + qs(roundParams({ q: key, page_size: 50 })));
          if (!listView.isConnected) return;
          state.qaList = { key: roundListKey(key), items: data.items || [], next: data.next_cursor, more: !!data.has_more, meta: data, err: null };
        }
        state.qaItems = state.qaList.items;
      } else if (state.qaSeg === "down") {
        if (!state.fbList) document.getElementById("qaList").innerHTML = listState("loading");
        const feedbackList = await loadFbList();
        if (!listView.isConnected) return;
        state.qaItems = feedbackList.items;
      } else if (state.qaSeg === "convs") {
        if (!state.convList) document.getElementById("qaList").innerHTML = listState("loading");
        const conversationList = await loadConvList();
        if (!listView.isConnected) return;
        state.qaItems = conversationList.items;
      } else {
        state.qaItems = [];
      }
    } catch (e) {
      if (!listView.isConnected) return;
      state.qaItems = [];
      state.qaList = null;
      state.convList = null;
      state.fbList = null;
      document.getElementById("qaList").innerHTML = listError(e);
      document.getElementById("qaDetail").innerHTML = empty("无法打开详情。");
      return;
    }
    if (!state.qaId && state.qaItems.length) state.qaId = itemId(state.qaItems[0]);
    paintQaList({ keepDetail: true });
    paintQaDetail();
  }

  function itemId(row) {
    if (!row) return "";
    return String(row.round_id || row.exec_id || row.id || "");
  }

  function filteredQa() {
    const q = String(state.qaQ || "").trim().toLowerCase();
    /* 全部轮次、反馈与按会话已由服务端筛选，不再在页面里二次过滤 */
    if (!q || state.qaSeg === "rounds" || state.qaSeg === "convs" || state.qaSeg === "down") return state.qaItems;
    return state.qaItems.filter(function (r) {
      const hay = [r.original_query, r.title, accountName(r), itemId(r)].join(" ").toLowerCase();
      return hay.indexOf(q) >= 0;
    });
  }

  function paintQaList(opts) {
    const box = document.getElementById("qaList");
    if (!box) return;
    const items = filteredQa();
    const convPaged = state.qaSeg === "convs" && state.convList;
    const fbPaged = state.qaSeg === "down" && state.fbList;
    const pagedList = (state.qaSeg === "rounds" && state.qaList) || convPaged || fbPaged || null;
    const paged = Boolean(pagedList);
    const tz = paged ? (pagedList.meta.tz || DEFAULT_TZ) : DEFAULT_TZ;
    const head = paged ? tzNote(pagedList.meta) + coverageNote(pagedList.meta) : "";
    const tail = paged && pagedList.more
      ? '<div class="kb-pad"><button type="button" class="kb-btn" id="qaMore">加载更多</button></div>' : "";
    const searched = state.qaSeg === "convs"
      ? Object.keys(state.convFilters).some(function (k) { return state.convFilters[k]; })
      : state.qaSeg === "down" ? state.fbFilters.account : state.qaQ;
    if (!items.length) {
      box.innerHTML = head + listState("empty", searched ? "没有匹配的记录。" : "暂无记录。");
    } else {
      box.innerHTML = head + items.map(function (r) {
      const id = itemId(r);
      const picked = id === state.qaId ? " kb-pick" : "";
      if (convPaged) return convRowHtml(r, picked, tz);
      if (fbPaged) return fbRowHtml(r, picked, tz);
      let line = "";
      let mark = "";
      if (state.qaSeg === "convs") {
        line = escapeHtml(r.title || "—");
      } else if (state.qaSeg === "down") {
        line = escapeHtml(r.original_query || "");
        mark = badge("踩", "danger");
      } else {
        line = escapeHtml(r.original_query || "");
        mark = roundListMark(r);
      }
      const when = (paged ? fmtTime(r.created_at, tz) : shortTime(r.created_at)) || (state.qaSeg === "convs" ? id : "");
      return '<button type="button" class="kb-qa-row' + picked + '" data-pick="' + escapeHtml(id) + '">' +
        '<span class="kb-qa-meta"><span class="kb-mono kb-ellipsis">' + escapeHtml(when) + "</span>" +
        '<span class="kb-who">' + escapeHtml(accountName(r)) + "</span></span>" +
        '<span class="kb-qa-line"><span class="kb-ellipsis">' + line + "</span>" + mark + "</span></button>";
    }).join("") + tail;
      const moreBtn = document.getElementById("qaMore");
      if (moreBtn) moreBtn.onclick = convPaged ? loadMoreConvs : fbPaged ? loadMoreFb : loadMoreRounds;
      box.querySelectorAll("[data-pick]").forEach(function (btn) {
        btn.onclick = function () {
          state.qaId = btn.getAttribute("data-pick");
          state.qaDetailHeld = false;
          paintQaList({ keepDetail: true });
          paintQaDetail();
        };
      });
    }
    if (opts && opts.keepDetail) return;
    const detail = document.getElementById("qaDetail");
    if (!detail) return;
    const visible = items.some(function (r) { return itemId(r) === state.qaId; });
    if (!visible) {
      state.qaDetailHeld = true;
      detail.innerHTML = empty("选一条记录查看。");
      return;
    }
    if (state.qaDetailHeld) {
      state.qaDetailHeld = false;
      paintQaDetail();
    }
  }

  async function loadMoreRounds() {
    const list = state.qaList;
    if (!list || !list.next) return;
    const btn = document.getElementById("qaMore");
    if (btn) btn.disabled = true;
    try {
      const data = await api("/rounds" + qs(roundParams({ q: state.qaQ, page_size: 50, cursor: list.next })));
      if (state.qaList !== list) return;
      list.items = list.items.concat(data.items || []);
      list.next = data.next_cursor;
      list.more = !!data.has_more;
      state.qaItems = list.items;
      paintQaList({ keepDetail: true });
    } catch (e) {
      if (btn) {
        btn.disabled = false;
        btn.insertAdjacentHTML("afterend", listError(e));
      }
    }
  }

  async function paintQaDetail() {
    const box = document.getElementById("qaDetail");
    if (!box) return;
    const row = state.qaItems.filter(function (r) { return itemId(r) === state.qaId; })[0];
    if (row && state.qaSeg === "convs") {
      await paintConvDetail(box, row.id);
      return;
    }
    /* 反馈详情走反馈接口（按被评价版本），从总览跳来的 id 不在当前页也能打开 */
    if (state.qaSeg === "down" && state.qaId) {
      await paintFbDetail(box, state.qaId);
      return;
    }
    /* 不在当前列表里时，有问答明细仍按 id 取详情。搜索把详情收起后，过期请求不再写回。 */
    if (!row && !(state.qaId && state.qaSeg !== "convs" && hasPerm("问答明细"))) {
      box.innerHTML = empty("选一条记录查看。");
      return;
    }
    box.innerHTML = '<div class="kb-pad"><p class="kb-muted">加载详情…</p></div>';
    try {
      const full = await api("/rounds/" + encodeURIComponent(state.qaId));
      if (!box.isConnected) return;
      if (state.qaId !== itemId(full) && state.qaId !== full.round_id) return;
      if (state.qaDetailHeld) return;
      box.innerHTML = detailFromRow(full, false);
      bindContextButtons(box, full.round_id);
      if (hasPerm('问答明细') && hasPerm('Prompt调试') && hasPerm('Prompt查看') && hasPerm('配置查看') && full.user_msg_id) {
        box.insertAdjacentHTML('beforeend','<div class="kb-pad"><button class="kb-btn" type="button" id="qaBringToDebug">带入调试</button><p class="kb-muted">仅带入本次执行的提问与回答，进入调试后再确认输入并开始。</p></div>');
        box.querySelector('#qaBringToDebug').onclick = function () {
          state.debugSource = {exec_id:full.round_id,conv_id:full.conv_id,input:full.original_query || '',message_ids:[full.user_msg_id,full.assistant_msg_id].filter(Boolean)};
          state.area='debug'; state.debugRunId=''; renderNav(); showArea();
        };
      }
    } catch (e) {
      box.innerHTML = '<p class="kb-err" style="padding:16px">' + escapeHtml(e.message) + "</p>";
    }
  }

  function roundParams(extra) {
    return Object.assign({
      op_type: state.roundFilters.op_type,
      route: state.roundFilters.route,
      pending: state.roundFilters.attention || ""
    }, extra || {});
  }

  function roundListKey(q) {
    return [q, state.roundFilters.op_type, state.roundFilters.route, state.roundFilters.attention].join("\n");
  }

  function roundFiltersHtml() {
    const op = state.roundFilters.op_type;
    const route = state.roundFilters.route;
    const opOpts = [["", "全部发起"], ["send", "发送"], ["refresh", "刷新"]];
    const routeOpts = [["", "全部 Route"], ["knowledge_query", "知识查询"], ["conversation_task", "对话任务"],
      ["ack", "确认"], ["smalltalk", "闲聊"], ["out_of_scope", "越界"], ["unclear", "不清楚"]];
    function opts(list, cur) {
      return list.map(function (o) {
        return '<option value="' + o[0] + '"' + (o[0] === cur ? " selected" : "") + ">" + o[1] + "</option>";
      }).join("");
    }
    return '<select class="kb-select" id="roundScope" title="关注范围">' + opts([["", "全部执行"], ["1", "需关注：非成功或被踩"]], state.roundFilters.attention || "") + '</select>' +
      '<select class="kb-select" id="roundOp" title="发起方式">' + opts(opOpts, op) + "</select>" +
      '<select class="kb-select" id="roundRoute" title="Route">' + opts(routeOpts, route) + "</select>";
  }

  function bindRoundFilters() {
    ["roundScope", "roundOp", "roundRoute"].forEach(function (id) {
      const el = document.getElementById(id);
      if (!el) return;
      el.onchange = function () {
        state.roundFilters.op_type = document.getElementById("roundOp").value;
        state.roundFilters.route = document.getElementById("roundRoute").value;
        state.roundFilters.attention = document.getElementById("roundScope").value;
        state.qaList = null;
        state.qaId = "";
        pageQa();
      };
    });
  }

  function roundListMark(r) {
    if (r.exec_state === "failed") return badge("执行失败", "danger");
    if (r.msg_save === "failed") return badge("未保存", "danger");
    if (r.check_status === "fail" || r.check_status === "error") return badge("检查未通过", "warn");
    const tone = r.status === "success" ? feedbackTone(r) : statusTone(r.status);
    const label = r.status === "success" ? feedbackLabel(r) : statusLabel(r.status);
    const op = r.op_type === "refresh" ? badge("刷新", "muted") : r.op_type === "send" ? badge("发送", "muted") : "";
    return op + " " + badge(label, tone);
  }

  function detailFromRow(row, brief) {
    const head = '<div class="kb-pad"><p class="kb-mono" style="color:var(--accent)">' + escapeHtml(row.round_id || "") +
      "</p><p class=\"kb-muted\">" + escapeHtml(accountName(row)) + " · " +
      escapeHtml(row.created_at ? fmtTime(row.created_at, listTz()) + "（" + listTz() + "）" : "") +
      "</p><p>" + roundListMark(row) + " " + badge(feedbackLabel(row), feedbackTone(row)) + "</p>";
    if (brief || !row.view || !row.view.groups) {
      const blocks = brief
        ? block("原句", row.original_query || "")
        : block("原句", row.original_query || "") + block("改写句", row.rewrite_query || "") + block("回答", row.answer || "");
      return head + blocks + "</div>";
    }
    let body = "";
    if (row.view.legacy) body += '<p class="kb-muted">旧版未记录的字段保持空白说明，不按当前配置回填。</p>';
    (row.view.statuses || []).forEach(function (s) {
      body += badge(s.label + " " + s.text, "muted") + " ";
    });
    (row.view.groups || []).forEach(function (g) {
      const items = (g.items || []).map(function (it) {
        return "<p><strong>" + escapeHtml(it.label) + "</strong><br>" + escapeHtml(it.text).replace(/\n/g, "<br>") + "</p>";
      }).join("");
      body += '<div class="kb-block"><h3>' + escapeHtml(g.title) + "</h3>" + items + "</div>";
    });
    const ids = ((row.snapshot || {}).l1_msg_ids || []).reduce(function (acc, pair) {
      (pair || []).forEach(function (id) { if (id) acc.push(id); });
      return acc;
    }, []);
    if (ids.length) {
      body += '<div class="kb-block"><h3>历史正文</h3>' + ids.map(function (id) {
        return '<button type="button" class="kb-btn" data-ctx-msg="' + escapeHtml(id) + '">展开 ' +
          escapeHtml(id) + "</button> ";
      }).join("") + '<div id="ctxBody"></div></div>';
    }
    return head + body + "</div>";
  }

  function bindContextButtons(box, roundId) {
    box.querySelectorAll("[data-ctx-msg]").forEach(function (btn) {
      btn.onclick = async function () {
        const slot = document.getElementById("ctxBody");
        const mid = btn.getAttribute("data-ctx-msg");
        if (!slot) return;
        slot.innerHTML = '<p class="kb-muted">读取中…</p>';
        try {
          const data = await api("/rounds/" + encodeURIComponent(roundId) + "/context/" + encodeURIComponent(mid));
          if (state.qaId !== roundId) return;
          slot.innerHTML = '<pre class="kb-pre">' + escapeHtml((data.message && data.message.content) || "") + "</pre>";
        } catch (e) {
          slot.innerHTML = '<p class="kb-err">' + escapeHtml(e.message || "没有权限查看历史正文") + "</p>";
        }
      };
    });
  }

  function block(title, text) {
    return '<div class="kb-block"><h3>' + escapeHtml(title) + '</h3><pre class="kb-pre">' + escapeHtml(text) + "</pre></div>";
  }

  /* ---------- 反馈（A16）：按回答版本只读查看用户赞踩，本节不发任何写请求 ---------- */
  function fbParams(extra) {
    return Object.assign({ value: state.fbFilters.value, account: state.fbFilters.account, handled:state.fbFilters.handled || "", page_size: 50 }, extra || {});
  }

  async function loadFbList() {
    const params = fbParams();
    const key = JSON.stringify(params);
    if (state.fbList && state.fbList.key === key) return state.fbList;
    const data = await api("/admin/feedback" + qs(params));
    state.fbList = { key: key, items: data.items || [], next: data.next_cursor, more: !!data.has_more, meta: data };
    return state.fbList;
  }

  async function loadMoreFb() {
    const list = state.fbList;
    if (!list || !list.next) return;
    const btn = document.getElementById("qaMore");
    if (btn) btn.disabled = true;
    try {
      const data = await api("/admin/feedback" + qs(fbParams({ cursor: list.next })));
      if (state.fbList !== list) return;
      list.items = list.items.concat(data.items || []);
      list.next = data.next_cursor;
      list.more = !!data.has_more;
      state.qaItems = list.items;
      paintQaList({ keepDetail: true });
    } catch (e) {
      if (btn) {
        btn.disabled = false;
        btn.insertAdjacentHTML("afterend", listError(e));
      }
    }
  }

  function fbFiltersHtml() {
    return '<select class="kb-select" id="fbValue" title="反馈值">' + [['down','被踩'],['up','被赞'],['all','全部有反馈']].map(function (o) { return '<option value="' + o[0] + '"' + (o[0] === state.fbFilters.value ? ' selected' : '') + '>' + o[1] + '</option>'; }).join('') + '</select><select class="kb-select" id="fbHandled" title="问题处理状态">' + [['','全部处理状态'],['no','未关联问题'],['open','未处理'],['doing','处理中'],['closed','已关闭']].map(function (o) { return '<option value="' + o[0] + '"' + (o[0] === (state.fbFilters.handled || '') ? ' selected' : '') + '>' + o[1] + '</option>'; }).join('') + '</select>';
  }

  function bindFbFilters() {
    [['fbValue','value'],['fbHandled','handled']].forEach(function (item) { const sel=document.getElementById(item[0]); if (sel) sel.onchange=function () { state.fbFilters[item[1]]=sel.value; state.qaId=''; pageQa(); }; });
  }

  function fbVersionBadge(r) {
    if (r.legacy) return badge("旧版轮次", "muted");
    if (r.version_no == null) return badge("版本不可确定", "muted");
    return badge("v" + r.version_no + (r.is_current ? "（当前）" : "（旧版）"), r.is_current ? "ok" : "warn");
  }

  function fbRowHtml(r, picked, tz) {
    return '<button type="button" class="kb-qa-row' + picked + '" data-pick="' + escapeHtml(r.exec_id) + '">' +
      '<span class="kb-qa-meta"><span class="kb-mono kb-ellipsis">' + escapeHtml(fmtTime(r.feedback_at, tz)) + "</span>" +
      '<span class="kb-who">' + escapeHtml(accountName(r)) + "</span></span>" +
      '<span class="kb-qa-line"><span class="kb-ellipsis">' + escapeHtml(r.original_query || r.excerpt || "") + "</span>" +
      badge(feedbackLabel(r), feedbackTone(r)) + " " + fbVersionBadge(r) + (r.issue_status ? ' ' + badge('问题 · ' + r.issue_status,'muted') : '') + "</span></button>";
  }

  async function paintFbDetail(box, id) {
    box.innerHTML = '<div class="kb-pad"><p class="kb-muted">加载详情…</p></div>';
    try {
      const d = await api("/admin/feedback/" + encodeURIComponent(id));
      if (state.qaId !== id || state.qaSeg !== "down") return;
      const tz = d.tz || DEFAULT_TZ;
      const execLink = hasPerm("问答明细")
        ? '<button type="button" class="kb-link kb-mono" data-fb-exec="' + escapeHtml(d.exec_id) + '">' + escapeHtml(d.exec_id) + "</button>"
        : escapeHtml(d.exec_id);
      const convLink = d.conv_id && hasPerm("对话审计")
        ? '<button type="button" class="kb-link kb-mono" data-fb-conv="' + escapeHtml(d.conv_id) + '">' + escapeHtml(d.conv_id) + "</button>"
        : escapeHtml(d.conv_id || "—");
      let notes = "";
      if (d.legacy_note) notes += listState("partial", d.legacy_note);
      if (d.stale_note) notes += listState("partial", d.stale_note);
      box.innerHTML = '<div class="kb-pad">' +
        "<p>" + badge(feedbackLabel(d), feedbackTone(d)) + " " + fbVersionBadge(d) + "</p>" + notes +
        kv("反馈时间", escapeHtml(d.feedback_at ? fmtTime(d.feedback_at, tz) : "—")) +
        kv("账号", escapeHtml(accountName(d))) +
        kv("对应执行", execLink) +
        kv("会话", convLink) +
        kv("逻辑回合", escapeHtml(d.logical_round_id || "—")) +
        kv("Route", escapeHtml(d.route || "未记录")) +
        kv("回复生成时间", escapeHtml(d.reply_created_at ? fmtTime(d.reply_created_at, tz) : "—")) +
        kv("问题处理", hasPerm("问题处理")
          ? '<button type="button" class="kb-btn" id="kb-fb-issue">记为问题</button>'
          : escapeHtml("无问题处理权限")) +
        block("问题", d.question || "") +
        block("被评价的回答", d.rated_content || "") +
        '<p class="kb-muted kb-list-note">只读：管理员不能创建、撤销或更正用户评价。时间：' + escapeHtml(tz) + "</p></div>";
      box.querySelectorAll("[data-fb-exec]").forEach(function (btn) {
        btn.onclick = function () {
          state.qaSeg = "rounds";
          state.qaId = btn.getAttribute("data-fb-exec");
          state.qaQ = "";
          pageQa();
        };
      });
      box.querySelectorAll("[data-fb-conv]").forEach(function (btn) {
        btn.onclick = function () {
          state.qaSeg = "convs";
          state.convFilters = { q: "", account: "", visibility: "", cleared: "", state: "" };
          state.convList = null;
          state.qaId = btn.getAttribute("data-fb-conv");
          pageQa();
        };
      });
      const issueBtn = box.querySelector("#kb-fb-issue");
      if (issueBtn) bindFeedbackIssue(issueBtn, d);
    } catch (e) {
      box.innerHTML = '<p class="kb-err" style="padding:16px">' + escapeHtml(e.message) + "</p>";
    }
  }

  /* ---------- 会话（A05）：查阅只读。实际删除是超管单独按钮，不走用户删除 ---------- */
  const CONV_STATE_LABEL = { idle: "可继续", busy: "执行忙碌", blocked: "消息保存阻塞", inaccessible: "不可访问" };
  const CONV_STATE_TONE = { idle: "ok", busy: "warn", blocked: "danger", inaccessible: "muted" };
  const COMPLETENESS_LABEL = { complete: "完整", partial: "中断片段", error_notice: "技术错误提示" };

  function convStateBadge(inter) {
    const st = inter && inter.state;
    return badge(CONV_STATE_LABEL[st] || "未知", CONV_STATE_TONE[st] || "muted");
  }

  function convParams(extra) {
    const f = state.convFilters;
    return Object.assign({
      q: f.q, account: f.account, visibility: f.visibility, cleared: f.cleared, state: f.state, page_size: 50
    }, extra || {});
  }

  async function loadConvList() {
    const params = convParams();
    const key = JSON.stringify(params);
    if (state.convList && state.convList.key === key) return state.convList;
    const data = await api("/admin/conversations" + qs(params));
    state.convList = { key: key, items: data.items || [], next: data.next_cursor, more: !!data.has_more, meta: data };
    return state.convList;
  }

  async function loadMoreConvs() {
    const list = state.convList;
    if (!list || !list.next) return;
    const btn = document.getElementById("qaMore");
    if (btn) btn.disabled = true;
    try {
      const data = await api("/admin/conversations" + qs(convParams({ cursor: list.next })));
      if (state.convList !== list) return;
      list.items = list.items.concat(data.items || []);
      list.next = data.next_cursor;
      list.more = !!data.has_more;
      state.qaItems = list.items;
      paintQaList({ keepDetail: true });
    } catch (e) {
      if (btn) {
        btn.disabled = false;
        btn.insertAdjacentHTML("afterend", listError(e));
      }
    }
  }

  function convSelect(name, label, options) {
    const cur = state.convFilters[name] || "";
    return '<select class="kb-select" data-conv-filter="' + name + '" title="' + escapeHtml(label) + '">' +
      '<option value="">' + escapeHtml(label) + "：全部</option>" +
      options.map(function (o) {
        return '<option value="' + o[0] + '"' + (o[0] === cur ? " selected" : "") + ">" + escapeHtml(o[1]) + "</option>";
      }).join("") + "</select>";
  }

  function convFiltersHtml() {
    return '<input id="convAccount" class="kb-search kb-search-sm" placeholder="账号（回车）" value="' +
      escapeHtml(state.convFilters.account) + '">' +
      convSelect("visibility", "可见性", [["visible", "用户可见"], ["hidden", "用户侧已移除"]]) +
      convSelect("cleared", "清空", [["yes", "发生过清空"], ["no", "未清空"]]) +
      convSelect("state", "交互状态", [["idle", "可继续"], ["busy", "执行忙碌"], ["blocked", "消息保存阻塞"], ["inaccessible", "不可访问"]]);
  }

  function bindConvFilters() {
    els.main.querySelectorAll("[data-conv-filter]").forEach(function (sel) {
      sel.onchange = function () {
        state.convFilters[sel.getAttribute("data-conv-filter")] = sel.value;
        state.qaId = "";
        pageQa();
      };
    });
    const acc = document.getElementById("convAccount");
    if (acc) {
      acc.onkeydown = function (ev) {
        if (ev.key !== "Enter") return;
        state.convFilters.account = ev.target.value.trim();
        state.qaId = "";
        pageQa();
      };
    }
  }

  function convRowHtml(r, picked, tz) {
    const marks = [];
    if (r.visibility === "hidden") marks.push(badge("用户侧已移除", "muted"));
    if (r.cleared) marks.push(badge("清空 " + (r.clear_count || 1) + " 次", "warn"));
    if (r.legacy) marks.push(badge("旧会话", "muted"));
    if (r.interaction && r.interaction.state && r.interaction.state !== "idle") marks.push(convStateBadge(r.interaction));
    const hit = (r.hits || [])[0];
    const hitLine = hit
      ? '<span class="kb-qa-line kb-muted"><span class="kb-ellipsis">' +
        escapeHtml((hit.role === "user" ? "问" : "答 v" + (hit.version_no || "?")) + "：" + hit.excerpt) + "</span></span>"
      : "";
    return '<button type="button" class="kb-qa-row' + picked + '" data-pick="' + escapeHtml(r.id) + '">' +
      '<span class="kb-qa-meta"><span class="kb-mono kb-ellipsis">' + escapeHtml(fmtTime(r.updated_at, tz)) + "</span>" +
      '<span class="kb-who">' + escapeHtml(accountName(r)) + "</span></span>" +
      '<span class="kb-qa-line"><span class="kb-ellipsis">' + escapeHtml(r.title || "—") + "</span>" + marks.join(" ") + "</span>" +
      hitLine + "</button>";
  }

  async function paintConvDetail(box, id) {
    box.innerHTML = '<div class="kb-pad"><p class="kb-muted">加载详情…</p></div>';
    try {
      const d = await api("/admin/conversations/" + encodeURIComponent(id));
      if (state.qaId !== id || state.qaSeg !== "convs") return;
      state.convDetail = d;
      state.convVerPick = {};
      state.purgeAsk = "";
      renderConvDetail(box);
    } catch (e) {
      box.innerHTML = '<p class="kb-err" style="padding:16px">' + escapeHtml(e.message) + "</p>";
    }
  }

  function kv(label, value) {
    return '<div class="kb-kv"><b>' + escapeHtml(label) + "</b><span>" + value + "</span></div>";
  }

  function convVersionHtml(g, v, tz) {
    const execBtn = v.exec_id && hasPerm("问答明细")
      ? '<button type="button" class="kb-link kb-mono" data-conv-exec="' + escapeHtml(v.exec_id) + '">' + escapeHtml(v.exec_id) + "</button>"
      : '<span class="kb-mono">' + escapeHtml(v.exec_id || "—") + "</span>";
    const fb = v.exec_known ? feedbackLabel(v) : "反馈未知";
    return '<div class="kb-conv-ver">' +
      '<p class="kb-muted">v' + escapeHtml(String(v.version_no || "?")) + " · " +
      (v.is_current ? badge("当前采用", "ok") : badge("旧版本", "muted")) + " " +
      badge(COMPLETENESS_LABEL[v.completeness] || v.completeness, v.completeness === "complete" ? "ok" : "warn") + " " +
      badge(fb, v.exec_known ? feedbackTone(v) : "muted") +
      " · 执行 " + execBtn + " · " + escapeHtml(fmtTime(v.created_at, tz)) + "</p>" +
      '<pre class="kb-pre">' + escapeHtml(v.content) + "</pre></div>";
  }

  function convRoundHtml(g, tz) {
    const vs = g.versions || [];
    const pickId = state.convVerPick[g.round_id] || g.current_msg_id || (vs.length ? vs[vs.length - 1].msg_id : "");
    const shown = vs.filter(function (v) { return v.msg_id === pickId; })[0];
    const tabs = vs.length > 1
      ? '<div class="kb-segs kb-conv-tabs">' + vs.map(function (v) {
          return '<button type="button" data-conv-ver="' + escapeHtml(g.round_id) + '" data-msg="' + escapeHtml(v.msg_id) + '"' +
            (v.msg_id === pickId ? ' class="active"' : "") + ">v" + escapeHtml(String(v.version_no || "?")) +
            (v.is_current ? "（当前）" : "") + "</button>";
        }).join("") + "</div>"
      : "";
    let refs = "";
    if (g.refs_old_versions && g.refs_old_versions.length) {
      refs = '<p class="kb-muted">本回合当时引用的旧版本：' + g.refs_old_versions.map(function (r) {
        return "v" + escapeHtml(String(r.version_no || "?")) + "（" + escapeHtml(r.round_id) + "）";
      }).join("、") + "</p>";
    } else if (g.user && !g.refs_known) {
      refs = '<p class="kb-muted">当时引用的版本：不可确定</p>';
    }
    const user = g.user
      ? '<p class="kb-muted">问 · <span class="kb-mono">' + escapeHtml(g.user.msg_id) + "</span> · " +
        escapeHtml(fmtTime(g.user.created_at, tz)) + '</p><pre class="kb-pre">' + escapeHtml(g.user.content) + "</pre>"
      : '<p class="kb-muted">本回合没有 User 记录</p>';
    return '<div class="kb-conv-round"><p class="kb-muted kb-mono">回合 ' + escapeHtml(g.round_id) + "</p>" +
      user + refs + tabs + (shown ? convVersionHtml(g, shown, tz) : '<p class="kb-muted">没有已保存的回答</p>') + "</div>";
  }

  function renderConvDetail(box) {
    const d = state.convDetail;
    if (!d) return;
    const tz = d.tz || DEFAULT_TZ;
    const inter = d.interaction || {};
    const stateText = convStateBadge(inter) +
      (inter.busy ? ' <span class="kb-mono">' + escapeHtml(inter.running_exec_id || "") + "</span>" : "") +
      (inter.save_blocked ? ' <span class="kb-mono">' + escapeHtml(inter.blocked_exec_id || "") + "</span>" : "");
    const head = '<div class="kb-pad">' +
      '<p class="kb-mono" style="color:var(--accent)">' + escapeHtml(d.id) + "</p>" +
      "<h3 style=\"margin:4px 0 8px;font-size:16px\">" + escapeHtml(d.title || "—") + "</h3>" +
      kv("账号", escapeHtml(accountName(d)) + ' <span class="kb-mono">' + escapeHtml(d.account_id || "") + "</span>") +
      kv("创建时间", escapeHtml(fmtTime(d.created_at, tz))) +
      kv("最近消息时间", escapeHtml(d.last_message_at ? fmtTime(d.last_message_at, tz) : "—")) +
      kv("逻辑回合数", escapeHtml(d.round_count == null ? "不可确定" : String(d.round_count))) +
      kv("用户侧可见性", d.visibility === "hidden" ? badge("用户侧已移除（仅管理查阅）", "muted") : badge("用户可见", "ok")) +
      kv("清空", escapeHtml(d.clear_count ? d.clear_count + " 次，最近 " + fmtTime(d.last_clear_at, tz) : "未发生")) +
      kv("当前交互状态", stateText) +
      '<p class="kb-muted kb-list-note">只读查阅：不改原话、不代评价、不改默认版本、不处理忙碌或阻塞。时间：' + escapeHtml(tz) + "</p>" +
      purgeBar(d) + "</div>";
    let body = "";
    if (d.legacy_note) {
      body += '<div class="kb-pad">' + listState("partial", d.legacy_note) +
        (d.payload_messages || []).map(function (m) {
          return '<p class="kb-muted">' + escapeHtml(m.role === "user" ? "问" : "答") + '</p><pre class="kb-pre">' + escapeHtml(m.text) + "</pre>";
        }).join("") + "</div>";
    }
    const clears = d.clears || [];
    const rounds = d.rounds || [];
    for (let i = 0; i <= clears.length; i += 1) {
      const part = rounds.filter(function (g) { return g.segment === i; });
      let label = "";
      if (i < clears.length) {
        label = "以下为第 " + (i + 1) + " 次清空前保留记录，仅管理查阅（清空于 " + fmtTime(clears[i].created_at, tz) + "）";
      } else if (clears.length) {
        label = "以下为最后一次清空之后，用户当前可见范围";
      }
      if (!part.length && !label) continue;
      body += '<div class="kb-pad kb-conv-seg">' + (label ? '<p class="kb-conv-divider">' + escapeHtml(label) + "</p>" : "") +
        (part.length ? part.map(function (g) { return convRoundHtml(g, tz); }).join("") : '<p class="kb-muted">这一段没有消息</p>') + "</div>";
    }
    if (!rounds.length && !d.legacy_note) body += '<div class="kb-pad">' + empty("这个会话还没有消息。") + "</div>";
    box.innerHTML = head + body;
    box.querySelectorAll("[data-conv-ver]").forEach(function (btn) {
      btn.onclick = function () {
        state.convVerPick[btn.getAttribute("data-conv-ver")] = btn.getAttribute("data-msg");
        renderConvDetail(box);
      };
    });
    box.querySelectorAll("[data-conv-exec]").forEach(function (btn) {
      btn.onclick = function () {
        state.qaSeg = "rounds";
        state.qaId = btn.getAttribute("data-conv-exec");
        state.qaQ = "";
        pageQa();
      };
    });
    bindPurge(box, d);
  }

  /* ---------- 实际删除（A06）：仅超管，二次确认；用户删除仍只隐藏 ---------- */
  function purgeBar(d) {
    if (!(state.me && state.me.is_super)) return "";
    if (state.purgeAsk === d.id) {
      return '<div class="kb-pad" style="padding-top:0"><p class="kb-muted">将删除本会话的消息、版本、执行记录和记忆索引，不可恢复。备份不在这次删除范围内。</p>' +
        '<p id="kb-purge-err" class="kb-err" hidden></p>' +
        '<button type="button" class="kb-btn danger" id="kb-purge-go">确认删除</button> ' +
        '<button type="button" class="kb-btn" id="kb-purge-cancel">取消</button></div>';
    }
    return '<div class="kb-pad" style="padding-top:0"><button type="button" class="kb-btn" id="kb-purge-ask">实际删除</button></div>';
  }

  function bindPurge(box, d) {
    const ask = box.querySelector("#kb-purge-ask");
    if (ask) ask.onclick = function () { state.purgeAsk = d.id; renderConvDetail(box); };
    const cancel = box.querySelector("#kb-purge-cancel");
    if (cancel) cancel.onclick = function () { state.purgeAsk = ""; renderConvDetail(box); };
    const go = box.querySelector("#kb-purge-go");
    if (!go) return;
    go.onclick = async function () {
      go.disabled = true;
      const err = box.querySelector("#kb-purge-err");
      try {
        const op = await api("/admin/conversations/" + encodeURIComponent(d.id) + "/purge", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ confirm: d.id })
        });
        state.convDetail = null;
        state.purgeAsk = "";
        box.innerHTML = '<div class="kb-pad"><p>已删除。操作号 <span class="kb-mono">' + escapeHtml(op.id) +
          "</span>。备份不在这次删除范围内。</p></div>";
      } catch (e) {
        go.disabled = false;
        if (err) {
          err.hidden = false;
          err.textContent = e.message || "删除失败";
        }
      }
    };
  }

  /* ---------- 诊断（A18）：只观察、定位、跳转；唯一的写动作是「标记已查看」，不改任何业务状态 ---------- */
  const DIAG_STATUS = {
    ok: ["正常", "ok"], degraded: ["有异常", "warn"], down: ["不可用", "danger"],
    limited: ["观察受限", "warn"], unknown: ["未知", "muted"], not_connected: ["未接入", "muted"]
  };
  const DIAG_TYPE_LABEL = {
    user_save_fail: "User 保存失败",
    assistant_save_fail: "Assistant 首次保存失败",
    assistant_save_blocked: "Assistant 补写仍失败（会话保存阻塞）",
    retry_save_fail: "用户重试保存失败",
    runtime_insert_fail: "Runtime 写入失败",
    runtime_update_fail: "Runtime 不完整",
    audit_write_fail: "审计写入失败",
    retrieve_error: "知识检索异常",
    model_error: "模型调用异常"
  };

  function diagStatusBadge(st) {
    const s = DIAG_STATUS[st] || DIAG_STATUS.unknown;
    return badge(s[0], s[1]);
  }

  function diagSectionHtml() {
    return '<section class="kb-card kb-diag"><div class="kb-card-h"><span>健康与异常</span>' +
      '<button type="button" class="kb-link" id="diagReload">刷新快照</button></div>' +
      '<div id="diagSnap" class="kb-pad"><p class="kb-muted">加载中…</p></div>' +
      '<div class="kb-split kb-diag-split"><div id="diagList" class="kb-card"></div><div id="diagDetail" class="kb-card"></div></div></section>';
  }

  function diagCardHtml(it, tz) {
    const rows = [];
    if (it.db_ping != null) rows.push(kv("数据库 ping", escapeHtml(it.db_ping ? "可连通" : "失败")));
    if (it.qdrant_ready != null) rows.push(kv("Qdrant / 索引", escapeHtml((it.qdrant_ready ? "可达" : "不可达") + " / " + (it.index_ready ? "就绪" : "未就绪") + " · " + it.chunk_count + " 块")));
    if (it.keys) rows.push(kv("Key 配置", escapeHtml("DashScope " + it.keys.dashscope + " · DeepSeek " + it.keys.deepseek)));
    if (it.recent) {
      rows.push(kv("近 " + it.recent.window_hours + " 小时异常", escapeHtml(String(it.recent.total) +
        (it.recent.last_at ? "，最近 " + fmtTime(it.recent.last_at, tz) : ""))));
    }
    if (it.integrity) {
      rows.push(kv("审计失败计数", escapeHtml("读取 " + it.integrity.read_audit_failures + " · 结果 " +
        it.integrity.result_audit_failures + " · 阻断 " + it.integrity.blocked_high_risk)));
    }
    return '<div class="kb-diag-card"><p><strong>' + escapeHtml(it.label) + "</strong> " + diagStatusBadge(it.status) + "</p>" +
      rows.join("") + (it.impact ? '<p class="kb-muted">' + escapeHtml(it.impact) + "</p>" : "") +
      '<p class="kb-muted">' + escapeHtml(it.note || "") + "</p></div>";
  }

  async function paintDiag() {
    const snap = document.getElementById("diagSnap");
    if (!snap) return;
    const reload = document.getElementById("diagReload");
    if (reload) reload.onclick = function () { state.diagSel = ""; paintDiag(); };
    try {
      const d = await api("/admin/diagnostics");
      if (!snap.isConnected) return;
      const tz = d.tz || DEFAULT_TZ;
      snap.innerHTML = (d.observation && d.observation.limited ? listState("partial", "诊断记录写入或读取失败，观察受限；无记录不等于零失败。") : "") +
        '<div class="kb-diag-grid">' + (d.items || []).map(function (it) { return diagCardHtml(it, tz); }).join("") + "</div>" +
        '<p class="kb-muted kb-list-note">检查于 ' + escapeHtml(fmtTime(d.checked_at, tz)) + "（" + escapeHtml(tz) +
        "）。打开本页只做数据库与 Qdrant 连通检查，不调用模型、不重建索引。</p>";
    } catch (e) {
      snap.innerHTML = listError(e);
    }
    if (snap.isConnected) await paintDiagList();
  }

  async function paintDiagList() {
    const box = document.getElementById("diagList");
    if (!box) return;
    box.innerHTML = listState("loading");
    try {
      const data = await api("/admin/diag-events" + qs({ page_size: 50 }));
      if (!box.isConnected) return;
      const tz = data.tz || DEFAULT_TZ;
      const items = data.items || [];
      state.diagItems = items;
      if (!state.diagSel && items.length) state.diagSel = items[0].id;
      box.innerHTML = tzNote(data) + coverageNote(data) + (items.length ? items.map(function (e) {
        return '<button type="button" class="kb-qa-row' + (e.id === state.diagSel ? " kb-pick" : "") + '" data-diag="' + escapeHtml(e.id) + '">' +
          '<span class="kb-qa-meta"><span class="kb-mono">' + escapeHtml(fmtTime(e.ts, tz)) + "</span>" +
          '<span class="kb-who">' + escapeHtml(e.module_label || e.module || "") + "</span></span>" +
          '<span class="kb-qa-line"><span class="kb-ellipsis">' + escapeHtml(DIAG_TYPE_LABEL[e.type] || e.type) + "</span>" +
          (e.acked ? badge("已查看", "muted") : badge("未查看", "warn")) + "</span></button>";
      }).join("") : listState("empty", "还没有观察到异常。"));
      box.querySelectorAll("[data-diag]").forEach(function (btn) {
        btn.onclick = function () {
          state.diagSel = btn.getAttribute("data-diag");
          paintDiagList();
        };
      });
    } catch (e) {
      box.innerHTML = listError(e);
    }
    await paintDiagDetail();
  }

  async function paintDiagDetail() {
    const box = document.getElementById("diagDetail");
    if (!box) return;
    const id = state.diagSel;
    if (!id) {
      box.innerHTML = empty("选一条异常查看。");
      return;
    }
    box.innerHTML = '<div class="kb-pad"><p class="kb-muted">加载详情…</p></div>';
    try {
      const d = await api("/admin/diag-events/" + encodeURIComponent(id));
      if (!box.isConnected || state.diagSel !== id) return;
      const tz = d.tz || DEFAULT_TZ;
      const cur = d.current || {};
      const rows = [
        kv("类型", escapeHtml(DIAG_TYPE_LABEL[d.type] || d.type)),
        kv("模块", escapeHtml(d.module_label || d.module || "")),
        kv("错误码", escapeHtml(d.code || "—")),
        kv("观察时间", escapeHtml(fmtTime(d.ts, tz)))
      ];
      if (d.conv_id) {
        rows.push(kv("会话", hasPerm("对话审计")
          ? '<button type="button" class="kb-link kb-mono" data-diag-conv="' + escapeHtml(d.conv_id) + '">' + escapeHtml(d.conv_id) + "</button>"
          : escapeHtml(d.conv_id)));
        const ci = cur.conversation;
        rows.push(kv("会话当前状态", ci ? convStateBadge(ci) : escapeHtml("未知/待核对")));
      }
      if (d.exec_id) {
        rows.push(kv("执行", hasPerm("问答明细")
          ? '<button type="button" class="kb-link kb-mono" data-diag-exec="' + escapeHtml(d.exec_id) + '">' + escapeHtml(d.exec_id) + "</button>"
          : escapeHtml(d.exec_id)));
        const ex = cur.exec;
        rows.push(kv("执行当前保存状态", escapeHtml(ex ? ("消息 " + (ex.msg_save || "未知") + " · Runtime " + (ex.runtime_save || "未知")) : "未知/待核对")));
      }
      if (d.retries_note) rows.push(kv("后端已做的补写", escapeHtml(d.retries_note)));
      rows.push(kv("关联问题", hasPerm("问题处理")
        ? '<button type="button" class="kb-btn" id="kb-diag-issue">记为问题</button>'
        : escapeHtml("无问题处理权限")));
      rows.push(kv("查看记录", escapeHtml(d.acks.length ? d.acks.map(function (a) {
        return (a.actor_username || a.actor_id || "—") + " · " + fmtTime(a.ts, tz);
      }).join("；") : "还没人查看")));
      box.innerHTML = '<div class="kb-pad">' + rows.join("") +
        '<p class="kb-muted kb-list-note">' + escapeHtml(d.note || "") + "</p>" +
        '<div class="kb-actions"><button type="button" class="kb-btn" id="diagAck">标记已查看</button></div></div>';
      document.getElementById("diagAck").onclick = async function (ev) {
        ev.target.disabled = true;
        try {
          await api("/admin/diag-events/" + encodeURIComponent(id) + "/ack", { method: "POST" });
          setMsg("已记录查看；会话阻塞与执行状态不变");
          paintDiagList();
        } catch (e) {
          ev.target.disabled = false;
          setMsg(e.message, true);
        }
      };
      box.querySelectorAll("[data-diag-conv]").forEach(function (btn) {
        btn.onclick = function () {
          state.qaSeg = "convs";
          state.convFilters = { q: "", account: "", visibility: "", cleared: "", state: "" };
          state.convList = null;
          state.qaId = btn.getAttribute("data-diag-conv");
          gotoArea("qa");
        };
      });
      box.querySelectorAll("[data-diag-exec]").forEach(function (btn) {
        btn.onclick = function () {
          state.qaSeg = "rounds";
          state.qaId = btn.getAttribute("data-diag-exec");
          state.qaQ = "";
          gotoArea("qa");
        };
      });
      const diagIssue = document.getElementById("kb-diag-issue");
      if (diagIssue) {
        diagIssue.onclick = async function () {
          diagIssue.disabled = true;
          try {
            const row = await api("/admin/issues", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                title: ("异常 " + String(d.code || d.id || "")).slice(0, 80),
                source_type: "diag",
                source_id: d.id || "",
                conv_id: d.conv_id || "",
                category: "other"
              })
            });
            state.issueId = row.id;
            gotoArea("issues");
          } catch (e) {
            diagIssue.disabled = false;
            setMsg(e.message, true);
          }
        };
      }
    } catch (e) {
      box.innerHTML = '<p class="kb-err" style="padding:16px">' + escapeHtml(e.message) + "</p>";
    }
  }

  /* ---------- 配置、知识与记忆、运行状态：按工作区分别加载 ---------- */
  async function pageConfig() {
    els.main.innerHTML = pageHead("配置", "编辑草稿，完成测试后审阅发布。") + '<div id="indexBody"><p class="kb-muted">加载中…</p></div>';
    const body = document.getElementById("indexBody");
    try {
      const cfg = await api('/config');
      if (!body.isConnected) return;
      state.configView = cfg;
      body.innerHTML = configColumns(cfg);
      bindConfig();
    } catch (e) {
      if (body.isConnected) body.innerHTML = listError(e);
    }
  }

  async function pageKnowledge() {
    const tabs = [];
    if (hasPerm("知识源查看")) {
      tabs.push({id:"sources", label:"知识来源"}, {id:"memory", label:"对话记忆"});
    }
    if (hasPerm("知识源查看") || hasPerm("重建")) tabs.push({id:"tasks", label:"索引任务"});
    if (!tabs.some(function (t) { return t.id === state.knowledgeTab; })) state.knowledgeTab = tabs[0].id;
    els.main.innerHTML = pageHead("知识与记忆", "查看知识来源、对话记忆覆盖和索引任务。") +
      pageTabs(tabs, state.knowledgeTab, "knowledge-tab") + '<div id="knowledgeBody"></div>';
    els.main.querySelectorAll('[data-knowledge-tab]').forEach(function (btn) {
      btn.onclick = function () { state.knowledgeTab = btn.dataset.knowledgeTab; pageKnowledge(); };
    });
    const body = document.getElementById("knowledgeBody");
    if (state.knowledgeTab === "sources") {
      body.innerHTML = '<div id="kbSources"></div>';
      await paintSources();
    } else if (state.knowledgeTab === "memory") {
      body.innerHTML = '<div id="kbMemory"></div>';
      await paintMemory();
    } else {
      body.innerHTML = (hasPerm("重建") ? reindexBar() : "") + '<div id="kbIndexTasks"></div>';
      bindReindex();
      await paintIndexTasks();
    }
  }

  async function pageStatus() {
    els.main.innerHTML = pageHead("运行状态", "查看依赖健康与异常记录，定位关联会话和执行。") + diagSectionHtml();
    await paintDiag();
  }

  function isLongField(key) {
    return String(key).toLowerCase().indexOf("prompt") >= 0;
  }

  /* 接口键仍是英文，页面上用原来的中文名。提交时 name 不变。 */
  function fieldLabel(key) {
    const map = {
      recall_k: "召回 K",
      rerank_n: "重排 n",
      history_turns: "历史轮数",
      temperature: "temperature",
      system_prompt: "系统 Prompt",
      rewrite_prompt: "改写 Prompt",
      history_recovery: '历史恢复', recall_budget: '追溯预算', test_budget: '隔离测试预算',
      pools: '固定话术', prompts: 'Prompt 职责'
    };
    return map[key] || key;
  }

  function readonlyRows(ro) {
    const rows = [];
    Object.keys(ro || {}).forEach(function (k) {
      const val = ro[k];
      if (val && typeof val === "object" && !Array.isArray(val)) {
        Object.keys(val).forEach(function (sk) {
          rows.push([k + " · " + sk, String(val[sk])]);
        });
      } else if (Array.isArray(val)) {
        rows.push([k, val.join("、")]);
      } else {
        rows.push([k, String(val == null ? "" : val)]);
      }
    });
    return rows;
  }

  function configColumns(cfg) {
    const edit = cfg.editable || {};
    const visible = cfg.visible || {};
    const wr = cfg.draft || cfg.writable || {};
    const params = Object.keys(wr).filter(function (k) { return !isLongField(k) && k !== 'history_turns'; }).map(function (k) {
      return '<label class="kb-field"><span>' + escapeHtml(fieldLabel(k)) + '</span><input type="number" step="' + (k === "temperature" ? "0.1" : "1") + '" name="' + k + '" value="' + escapeHtml(wr[k]) + '"' + (edit.config ? '' : ' readonly data-cfg-ro') + '></label>';
    }).join("");
    const locked = edit.config ? '' : ' readonly data-cfg-ro';
    function budgetFields(prefix, values, labels) {
      return '<div class="kb-form-grid">' + Object.keys(labels).map(function (k) {
        return '<label class="kb-field"><span>' + labels[k] + '</span><input type="number" min="1" name="' + prefix + k + '" value="' + escapeHtml(values[k] == null ? '' : values[k]) + '"' + locked + '></label>';
      }).join('') + '</div>';
    }
    const runtime = visible.config ? '<section class="kb-card kb-pad"><div class="kb-section-head"><h3>运行参数</h3>' + badge(edit.config ? '可编辑' : '只读', 'muted') + '</div><div class="kb-form-grid">' + params + '</div>' +
      '<p class="kb-muted">当前上下文固定最多 10 个完整回合 / 5000 tokens；旧历史轮数配置已停用。</p><label class="kb-check"><input type="checkbox" name="history_recovery"' + (cfg.history_recovery === false ? '' : ' checked') + (edit.config ? '' : ' disabled') + '>允许恢复更早历史</label><p class="kb-muted">停用后保留当前上下文；空白循环预算不能启用追溯。</p>' +
      budgetFields('budget_', cfg.recall_budget || {}, {calls:'追溯调用次数',steps:'追溯步骤上限',parallel:'最大并行数',tokens:'历史 token 上限'}) +
      '<h4>隔离测试预算</h4>' + budgetFields('test_', cfg.test_budget || {}, {calls:'模型/工具调用上限',steps:'步骤上限',tokens:'估算 token 上限',timeout_seconds:'总截止（秒）'}) + '</section>' : '';
    const pools = visible.config ? '<section class="kb-card kb-pad"><div class="kb-section-head"><h3>固定话术</h3><span class="kb-muted">不调用模型</span></div><p class="kb-muted">每行一条，1| 启用，0| 停用。两个话术池独立使用。</p>' +
      '<label class="kb-field"><span>确认话术池</span><textarea name="ack_pool"' + locked + '>' + escapeHtml(poolText(cfg.pools && cfg.pools.ack)) + '</textarea></label>' +
      '<label class="kb-field"><span>范围话术池</span><textarea name="scope_pool"' + locked + '>' + escapeHtml(poolText(cfg.pools && cfg.pools.scope)) + '</textarea></label><div><button class="kb-btn" type="button" id="phrasePreviewBtn">预览将发出的原文</button></div><pre id="phrasePreview" class="kb-pre" hidden></pre></section>' : '';
    const slots = visible.prompt ? '<section class="kb-card kb-pad"><div class="kb-section-head"><h3>Prompt 职责</h3><span class="kb-muted">展开编辑 · 保存不调用模型</span></div>' + (cfg.prompts || []).map(function (slot) {
      return '<details class="kb-slot"><summary><span>' + escapeHtml(slot.title) + '</span>' + badge(slot.connected ? '已接入' : '未接入', slot.connected ? 'ok' : 'muted') + '</summary>' +
        (slot.connected ? '<label class="kb-field"><span>正文 · ' + escapeHtml(slot.id) + '</span><textarea data-slot="' + escapeHtml(slot.id) + '"' + (edit.prompt ? '' : ' readonly') + '>' + escapeHtml(slot.text) + '</textarea></label>' : '<p class="kb-muted">完整 Generate 职责配置尚未接入。现有回答链路仍使用系统 Prompt，可在下方编辑。</p><label class="kb-field"><span>回答系统 Prompt · 现有链路</span><textarea name="system_prompt"' + (edit.prompt ? '' : ' readonly') + '>' + escapeHtml(wr.system_prompt) + '</textarea></label>') + '</details>';
    }).join('') + '</section>' : '';
    const ro = readonlyRows(cfg.readonly || {}).map(function (r) { return '<div class="kb-kv"><b>' + escapeHtml(r[0]) + '</b><span>' + escapeHtml(r[1]) + '</span></div>'; }).join('');
    const rules = (cfg.fixed_rules || []).map(function (r) { return '<div class="kb-kv"><b>' + escapeHtml(r.title) + '</b><span>' + escapeHtml(r.value) + '</span></div>'; }).join('');
    const canSave = edit.config || edit.prompt;
    const canPublish = hasPerm('配置发布') && visible.config && visible.prompt;
    const history = (cfg.history || []).slice().reverse().map(function (r) {
      return '<div class="kb-version"><span class="kb-mono">' + escapeHtml(r.id) + '</span><p class="kb-muted">' + escapeHtml(r.reason || '未记录说明') + '</p>' +
        (edit.config && edit.prompt ? '<button type="button" class="kb-btn" data-restore="' + escapeHtml(r.id) + '">准备回退草稿</button>' : '') + '</div>';
    }).join('');
    const tabs = [];
    if (visible.config) tabs.push({id:'runtime',label:'运行参数'});
    if (visible.prompt || visible.config) tabs.push({id:'prompts',label:visible.prompt && visible.config ? 'Prompt 与话术' : visible.prompt ? 'Prompt' : '固定话术'});
    tabs.push({id:'versions',label:'版本与发布'});
    if (!tabs.some(function (t) { return t.id === state.configTab; })) state.configTab = tabs[0].id;
    return '<form id="cfgForm" class="kb-config-workspace" data-rev="' + cfg.draft_rev + '"><div class="kb-config-status"><div><span class="kb-eyebrow">CONFIGURATION</span><h3>' + (cfg.draft ? '草稿待发布' : '当前生效配置') + '</h3><p class="kb-muted">生效包 <span class="kb-mono">' + escapeHtml(cfg.package_id) + '</span> · 草稿修订 ' + cfg.draft_rev + '</p></div>' +
      '<div class="kb-actions">' + (canSave ? '<button class="kb-btn primary" type="submit">保存草稿</button>' : '') + (canPublish ? '<button class="kb-btn" type="button" id="cfgPublish">审阅发布</button>' : '') +
      (cfg.draft && edit.config && edit.prompt ? '<button class="kb-btn" type="button" id="cfgDiscard">丢弃草稿</button>' : '') + '</div></div>' +
      pageTabs(tabs, state.configTab, 'config-tab') +
      (visible.config ? '<div data-config-panel="runtime" class="kb-config-layout">' + runtime + '<aside class="kb-config-aside"><section class="kb-card kb-pad"><h3>系统约束</h3><p class="kb-muted">固定规则与当前环境。</p>' + ro + rules + '<p class="kb-muted">' + escapeHtml(cfg.key_note) + '</p></section></aside></div>' : '') +
      '<div data-config-panel="prompts" class="kb-config-editor">' + slots + pools + '</div>' +
      '<div data-config-panel="versions" class="kb-config-editor"><section class="kb-card kb-pad"><h3>版本历史</h3><p class="kb-muted">历史包先恢复为草稿，通过测试后再发布为新版本。</p>' +
      (history || empty('暂无历史发布。')) + '</section><div id="cfgReview" class="kb-review" hidden></div></div></form>';
  }

  function poolText(items) {
    return (items || []).map(function (x) {
      return (x.enabled === false ? "0" : "1") + "|" + (x.text || "");
    }).join("\n");
  }

  function parsePool(text) {
    return String(text || "").split("\n").filter(function (line) { return line.trim(); }).map(function (line) {
      var bar = line.indexOf("|");
      var on = bar < 0 || line.slice(0, bar) !== "0";
      return { text: bar < 0 ? line : line.slice(bar + 1), enabled: on };
    });
  }

  /* Prompt 按全文撑开，避免框内再出一条滚动。 */
  function fitPrompt(node) {
    node.style.minHeight = "0px";
    node.style.height = "1px";
    var full = node.scrollHeight;
    node.style.minHeight = "";
    node.style.height = full + "px";
  }

  function setConfigTab(tab) {
    state.configTab = tab;
    const form = document.getElementById('cfgForm');
    if (!form) return;
    form.querySelectorAll('[data-config-panel]').forEach(function (panel) { panel.hidden = panel.dataset.configPanel !== tab; });
    form.querySelectorAll('[data-config-tab]').forEach(function (btn) {
      const selected = btn.dataset.configTab === tab;
      btn.classList.toggle('active', selected);
      btn.setAttribute('aria-pressed', String(selected));
    });
  }

  function bindConfig() {
    const form = document.getElementById('cfgForm');
    if (!form) return;
    async function refreshAfterChange(message) {
      if (form.isConnected) {
        state.configDirty = false;
        await pageConfig();
      }
      setMsg(message);
    }
    setConfigTab(state.configTab);
    form.querySelectorAll('[data-config-tab]').forEach(function (btn) { btn.onclick = function () { setConfigTab(btn.dataset.configTab); }; });
    form.addEventListener('invalid', function (event) {
      const panel = event.target.closest('[data-config-panel]');
      if (panel) setConfigTab(panel.dataset.configPanel);
    }, true);
    form.addEventListener('input', function (event) { if (event.target.name !== 'publish_reason') state.configDirty = true; });
    const preview = document.getElementById('phrasePreviewBtn');
    if (preview) preview.onclick = function () {
      const items = parsePool(form.querySelector('[name=ack_pool]').value).filter(function (x) { return x.enabled && x.text.trim(); });
      const out = document.getElementById('phrasePreview'); out.hidden = false;
      out.textContent = items.length ? items[0].text : '确认话术池没有可发出的原文';
    };
    form.onsubmit = async function (ev) {
      ev.preventDefault();
      const body = {rev: Number(form.dataset.rev)};
      const view = state.configView;
      form.querySelectorAll('[name]').forEach(function (node) {
        if (node.readOnly || node.disabled || node.name === 'publish_reason') return;
        if (node.name.indexOf('budget_') === 0 || node.name.indexOf('test_') === 0) return;
        if (node.name === 'ack_pool' || node.name === 'scope_pool') body[node.name] = parsePool(node.value);
        else if (node.name === 'history_recovery') body[node.name] = node.checked;
        else body[node.name] = node.type === 'number' ? Number(node.value) : node.value;
      });
      if (view.editable.config) {
        ['budget_', 'test_'].forEach(function (prefix) {
          const values = {};
          form.querySelectorAll('[name^="' + prefix + '"]').forEach(function (n) { values[n.name.slice(prefix.length)] = n.value.trim() ? Number(n.value) : ''; });
          body[prefix === 'budget_' ? 'recall_budget' : 'test_budget'] = values;
        });
      }
      const prompts = {};
      form.querySelectorAll('[data-slot]').forEach(function (n) { if (!n.readOnly) prompts[n.dataset.slot] = n.value; });
      if (Object.keys(prompts).length) body.prompts = prompts;
      const submit = form.querySelector('[type=submit]');
      if (submit) submit.disabled = true;
      try {
        await api('/config', {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
        await refreshAfterChange('已存成草稿，发布后才会生效');
      } catch (e) { setMsg(e.message + '，未保存', true); }
      if (submit) submit.disabled = false;
    };
    const pub = document.getElementById('cfgPublish');
    if (pub) pub.onclick = function () {
      if (state.configDirty) { setMsg('页面有未保存修改，请先保存草稿再审阅', true); return; }
      const cfg = state.configView;
      if (!cfg.draft) { setMsg('没有可发布的草稿', true); return; }
      const published = Object.assign({},cfg.published || {},{prompts:Object.fromEntries((cfg.published_prompts || []).filter(function (s) { return s.connected; }).map(function (s) { return [s.id,s.text]; }))});
      const proposed = Object.assign({}, cfg.draft, {pools:cfg.pools,prompts: Object.fromEntries((cfg.prompts || []).filter(function (s) { return s.connected; }).map(function (s) { return [s.id,s.text]; })),history_recovery:cfg.history_recovery,recall_budget:cfg.recall_budget,test_budget:cfg.test_budget});
      const changes = Object.keys(proposed).filter(function (key) { return JSON.stringify(published[key]) !== JSON.stringify(proposed[key]); });
      const panel = document.getElementById('cfgReview'); panel.hidden = false;
      setConfigTab('versions');
      panel.innerHTML = '<section class="kb-card kb-pad"><h3>审阅草稿 · 修订 ' + cfg.draft_rev + '</h3><p class="kb-muted">只发布当前已审阅修订。他人保存新草稿后，本次提交会被拒绝。</p>' + changes.map(function (key) {
        return '<details class="kb-slot"><summary>' + escapeHtml(fieldLabel(key)) + '</summary><div class="kb-diff"><div><h4>当前生效</h4><pre class="kb-pre">' + escapeHtml(JSON.stringify(published[key],null,2)) + '</pre></div><div><h4>待发布</h4><pre class="kb-pre">' + escapeHtml(JSON.stringify(proposed[key],null,2)) + '</pre></div></div></details>';
      }).join('') + '<p class="kb-warn">发布前必须完成此修订的关键用例；非关键未覆盖项会返回风险提示。</p><label class="kb-field"><span>发布说明</span><textarea name="publish_reason" id="cfgReason" placeholder="说明修改原因与已验证范围" aria-required="true"></textarea></label><div class="kb-actions"><button type="button" class="kb-btn primary" id="cfgConfirmPublish">确认发布此修订</button><button type="button" class="kb-btn" id="cfgCancelPublish">取消</button></div><div id="cfgPubResult"></div></section>';
      panel.scrollIntoView({behavior:'smooth',block:'start'});
      document.getElementById('cfgCancelPublish').onclick = function () { panel.hidden = true; };
      const opId = state.publishOperation && state.publishOperation.rev === cfg.draft_rev ? state.publishOperation.id : 'ui-' + crypto.randomUUID();
      state.publishOperation = {id:opId,rev:cfg.draft_rev};
      document.getElementById('cfgConfirmPublish').onclick = async function (ev) {
        const reason = document.getElementById('cfgReason').value.trim();
        if (!reason) { setMsg('请填写发布说明', true); return; }
        ev.target.disabled = true;
        try {
          const result = await api('/config/publish', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rev:cfg.draft_rev,op_id:opId,reason:reason})});
          if (state.publishOperation && state.publishOperation.id === opId) state.publishOperation = null;
          await refreshAfterChange('已发布，新接受的提问使用这一版。' + (result.warnings || []).join('；'));
        } catch (e) {
          try { const done = await api('/config/ops/' + encodeURIComponent(opId)); if (done.status === 'done' && done.operation === 'publish' && done.source_rev === cfg.draft_rev) { if (state.publishOperation && state.publishOperation.id === opId) state.publishOperation = null; await refreshAfterChange('已核实发布成功：' + done.package_id); return; } } catch (_) { /* 未确认的操作保留同一编号供重试 */ }
          setMsg(e.message + ' · 操作号 ' + opId, true); ev.target.disabled = false;
        }
      };
    };
    const discard = document.getElementById('cfgDiscard');
    if (discard) discard.onclick = async function () {
      try { await api('/config/discard', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rev:Number(form.dataset.rev)})}); await refreshAfterChange('草稿已丢弃，生效包未变更'); } catch (e) { setMsg(e.message,true); }
    };
    form.querySelectorAll('[data-restore]').forEach(function (btn) { btn.onclick = async function () {
      if (state.configDirty) { setMsg('请先保存或丢弃页面修改',true); return; }
      try { await api('/config/restore-draft', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({package_id:btn.dataset.restore,rev:Number(form.dataset.rev)})}); await refreshAfterChange('历史整包已准备为草稿，请测试并审阅后发布'); } catch (e) { setMsg(e.message,true); }
    }; });
  }

  /* ---------- 调试（A11）：隔离测试，不写生产消息 ---------- */
  async function pageDebug() {
    els.main.innerHTML = pageHead('调试', '选择精确修订与合法输入，运行单职责或同版编排。结果只进入独立测试域。') + '<div id="dbgBody">' + listState('loading') + '</div>';
    let cfg, cases;
    try { [cfg,cases] = await Promise.all([api('/config'),api('/admin/test-cases')]); } catch (e) { document.getElementById('dbgBody').innerHTML = listError(e); return; }
    if (state.area !== 'debug') return;
    const slots = (cfg.prompts || []).filter(function (s) { return s.connected; });
    document.getElementById('dbgBody').innerHTML = '<div class="kb-debug-layout"><section class="kb-card kb-pad"><div class="kb-section-head"><h3>测试输入</h3>' + badge('修订 ' + cfg.draft_rev,'muted') + '</div><form id="dbgForm" class="kb-pad" style="padding:0">' +
      '<div class="kb-form-grid"><label class="kb-field"><span>执行模式</span><select name="mode"><option value="slot">单职责测试</option><option value="chain">整链路测试</option></select></label><label class="kb-field"><span>职责槽位</span><select name="slot">' + slots.map(function (s) { return '<option value="' + s.id + '">' + escapeHtml(s.title) + '</option>'; }).join('') + '</select></label></div>' +
      '<label class="kb-field"><span>已保存用例</span><select name="case_id"><option value="">手工输入</option>' + (cases.items || []).map(function (c) { return '<option value="' + escapeHtml(c.id) + '">' + (c.critical ? '必测 · ' : '') + escapeHtml(c.title) + '</option>'; }).join('') + '</select></label><label class="kb-field"><span>输入正文</span><textarea name="input" placeholder="输入要验证的问题或职责材料" required></textarea></label>' +
      '<details class="kb-slot"><summary>知识材料与调用方式</summary><div class="kb-pad"><label class="kb-field"><span>合成材料，每段之间空一行</span><textarea name="materials" placeholder="测试材料不进入正式知识库"></textarea></label>' + ((hasPerm('知识问答') || hasPerm('知识源查看')) ? '<label class="kb-check"><input type="checkbox" name="real_knowledge">读取真实受控知识（使用模型/工具额度）</label>' : '') + '<label class="kb-check"><input type="checkbox" name="simulate">标记为模拟依赖测试（不能作为发布通过证据）</label></div></details>' +
      (hasPerm('对话审计') ? '<details class="kb-slot"><summary>选取真实对话快照</summary><div class="kb-pad"><label class="kb-field"><span>会话编号</span><input name="conv_id" placeholder="仅带入勾选的消息"></label><button class="kb-btn" type="button" id="dbgLoadSource">读取并选择消息</button><div id="dbgMessages"></div></div></details>' : '') +
      '<p class="kb-muted">预算：最多 ' + (cfg.test_budget || {}).calls + ' 次调用，' + (cfg.test_budget || {}).timeout_seconds + ' 秒。打开和保存不调用模型，点击开始才执行。</p><button class="kb-btn primary" type="submit">开始测试</button></form></section><section class="kb-card kb-pad kb-debug-result"><div class="kb-section-head"><h3>执行结果</h3><span id="dbgStatus"></span></div><div id="dbgOut">' + empty('选择输入后开始测试。可从下方记录恢复查看。') + '</div></section></div>' +
      (hasPerm('配置发布') ? '<details class="kb-slot kb-debug-record"><summary>建立发布必测用例</summary><form id="dbgCase" class="kb-pad"><div class="kb-form-grid"><label class="kb-field"><span>用例名称</span><input name="title" required></label><label class="kb-field"><span>预期 Route</span><select name="route"><option value="ack">ack · 确认</option><option value="knowledge_query">knowledge_query · 知识问答</option><option value="out_of_scope">out_of_scope · 越界</option><option value="unclear">unclear · 澄清</option><option value="smalltalk">smalltalk · 闲聊</option><option value="conversation_task">conversation_task · 对话任务</option></select></label></div><label class="kb-field"><span>固定输入</span><textarea name="input" required></textarea></label><div class="kb-form-grid"><label class="kb-field"><span>用例模式</span><select name="mode"><option value="slot">单职责</option><option value="chain">整链路</option></select></label><label class="kb-field"><span>职责 ID</span><input name="slot" value="router" placeholder="router / task_prep / rewriter…"></label></div><label class="kb-field"><span>必要断言 JSON（可选，覆盖预期 Route）</span><textarea name="assertions" placeholder="{&quot;schema_ok&quot;:true}"></textarea></label><label class="kb-check"><input name="critical" type="checkbox" checked>关键必测</label><button class="kb-btn" type="submit">保存用例</button><p class="kb-muted">预期由实际输出验证。已有用例不能通过同编号覆盖来降低门禁。</p></form></details>' : '') +
      '<section class="kb-card kb-debug-record"><div class="kb-card-h">测试记录<div class="kb-actions"><button class="kb-btn" id="dbgCompare" type="button">对比所选两次</button><button class="kb-btn" id="dbgRefresh" type="button">刷新记录</button></div></div><div id="dbgRuns"></div><div id="dbgComparison" class="kb-pad" hidden></div></section>';
    const form = document.getElementById('dbgForm');
    const source = state.debugSource;
    if (source) {
      form.elements.input.value=source.input;
      if (form.elements.conv_id) form.elements.conv_id.disabled=true;
      form.insertAdjacentHTML('afterbegin','<div class="kb-block"><h3>带入执行 ' + escapeHtml(source.exec_id) + '</h3><p class="kb-muted">仅复制本次执行关联消息；不包含整段历史。请勾选需要的正文。</p>' + source.message_ids.map(function (id) { return '<label class="kb-check"><input type="checkbox" data-message="' + escapeHtml(id) + '" checked>' + escapeHtml(id) + '</label>'; }).join('') + '<button class="kb-btn" id="dbgClearSource" type="button">改用手工输入</button></div>');
      document.getElementById('dbgClearSource').onclick=function () { state.debugSource=null; pageDebug(); };
    }
    form.elements.mode.onchange = function () { form.elements.slot.disabled = form.elements.mode.value === 'chain'; };
    form.elements.case_id.onchange = function () { const item = (cases.items || []).find(function (c) { return c.id === form.elements.case_id.value; }); if (item) { form.elements.input.value=item.input; form.elements.mode.value=item.mode; form.elements.slot.value=item.slot; } form.elements.mode.onchange(); form.elements.input.readOnly=!!item; };
    const load = document.getElementById('dbgLoadSource');
    if (load && source) load.disabled=true;
    if (load) load.onclick = async function () {
      const box = document.getElementById('dbgMessages'); box.innerHTML=listState('loading');
      try {
        const detail = await api('/admin/conversations/' + encodeURIComponent(form.elements.conv_id.value));
        const messages = [];
        (detail.rounds || []).forEach(function (r) { if (r.user) messages.push(Object.assign({role:'User'},r.user)); (r.versions || []).forEach(function (v) { messages.push(Object.assign({role:'Assistant · v' + v.version_no},v)); }); });
        box.innerHTML = messages.map(function (m) { return '<label class="kb-source-pick"><input type="checkbox" data-message="' + escapeHtml(m.msg_id) + '"><div><strong>' + escapeHtml(m.role) + '</strong><p>' + escapeHtml(m.content) + '</p></div></label>'; }).join('') || empty('没有可选择的消息。');
      } catch (e) { box.innerHTML=listError(e); }
    };
    form.onsubmit = async function (ev) {
      ev.preventDefault(); const data = new FormData(form); const btn = form.querySelector('[type=submit]'); btn.disabled=true;
      try {
        const row = await api('/admin/test-runs', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({input:data.get('input'),mode:data.get('mode'),slot:data.get('slot') || 'router',case_id:data.get('case_id'),exec_id:source ? source.exec_id : '',conv_id:source ? source.conv_id : data.get('conv_id') || '',message_ids:Array.from(form.querySelectorAll('[data-message]:checked')).map(function (n) { return n.dataset.message; }),simulate_tool:!!data.get('simulate'),real_knowledge:!!data.get('real_knowledge'),materials:String(data.get('materials') || '').split(/\n\s*\n/).filter(Boolean).map(function (text) { return {content:text}; }),rev:cfg.draft_rev})});
        state.debugRunId=row.id; await showTestRun(row.id); await debugRecords();
      } catch (e) { setMsg(e.message,true); } finally { btn.disabled=false; }
    };
    const caseForm=document.getElementById('dbgCase');
    if (caseForm) caseForm.onsubmit=async function (ev) { ev.preventDefault(); const data=new FormData(caseForm); try { await api('/admin/test-cases',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:data.get('title'),input:data.get('input'),mode:data.get('mode'),slot:data.get('slot') || 'router',critical:!!data.get('critical'),assertions:data.get('assertions').trim() ? JSON.parse(data.get('assertions')) : {route:data.get('route')}})}); await pageDebug(); setMsg('用例已保存，请选择后运行'); } catch (e) { setMsg(e.message,true); } };
    document.getElementById('dbgRefresh').onclick=debugRecords;
    document.getElementById('dbgCompare').onclick=async function () {
      const ids=Array.from(document.querySelectorAll('[data-compare]:checked')).map(function (n) { return n.dataset.compare; });
      if (ids.length !== 2) { setMsg('请选择两条测试记录',true); return; }
      try { const result=await api('/admin/test-runs/compare' + qs({a:ids[0],b:ids[1]})); const box=document.getElementById('dbgComparison'); box.hidden=false; box.innerHTML='<p>' + (result.same_input ? '相同输入' : '输入不同') + ' · ' + (result.same_source ? '相同来源快照' : '来源内容已变化') + ' · ' + (result.same_time_base ? '相同时间基准' : '时间基准不同') + '</p><div class="kb-diff"><div><h4>' + escapeHtml(result.left.id) + '</h4><pre class="kb-pre">' + escapeHtml(result.left.output || result.left.error) + '</pre></div><div><h4>' + escapeHtml(result.right.id) + '</h4><pre class="kb-pre">' + escapeHtml(result.right.output || result.right.error) + '</pre></div></div>'; } catch (e) { setMsg(e.message,true); }
    };
    await debugRecords(); if (state.debugRunId) await showTestRun(state.debugRunId);
  }

  async function showTestRun(id) {
    if (state.area !== 'debug') return;
    const out=document.getElementById('dbgOut'); if (!out) return;
    try {
      const row=await api('/admin/test-runs/' + encodeURIComponent(id));
      document.getElementById('dbgStatus').innerHTML=badge(row.status,row.status === 'done' ? 'ok' : row.status === 'failed' ? 'danger' : 'muted');
      out.innerHTML='<p class="kb-mono">' + escapeHtml(row.id) + ' · 修订 ' + row.against_rev + (row.stale ? ' · 针对旧修订' : '') + '</p><div class="kb-form-grid"><div>' + kv('结构校验', row.schema_ok == null ? '未完成' : row.schema_ok ? '通过' : '未通过') + kv('业务解决', row.biz_resolved == null ? '未判定' : row.biz_resolved ? '已回答' : '未回答') + '</div><div>' + kv('发布断言',row.case_id ? row.passed ? '符合预期' : '未达到预期' : '未关联用例') + kv('调用 / 耗时',(row.usage || {}).calls == null ? '执行中' : row.usage.calls + ' 次 / ' + row.elapsed_ms + ' ms') + '</div></div><pre class="kb-pre">' + escapeHtml(row.note || row.error || row.output || '测试已受理，服务端继续执行…') + '</pre><p class="kb-muted">' + escapeHtml((row.limitations || []).join('；')) + '</p><details class="kb-slot"><summary>步骤、渲染输入与可用用量</summary><pre class="kb-pre">' + escapeHtml(JSON.stringify({events:row.events,rendered:row.rendered,usage:row.usage},null,2)) + '</pre></details>';
      if (row.status === 'queued' || row.status === 'running') setTimeout(function () { if (state.area === 'debug' && state.debugRunId === id) showTestRun(id); },1500);
    } catch (e) { out.innerHTML=listError(e); }
  }

  async function debugRecords(cursor) {
    const box=document.getElementById('dbgRuns'); if (!box) return;
    try {
      const data=await api('/admin/test-runs' + qs({cursor:typeof cursor === 'string' ? cursor : ''}));
      const html=(data.items || []).map(function (r) { return '<div class="kb-debug-run"><input type="checkbox" aria-label="选择对比" data-compare="' + escapeHtml(r.id) + '"><button type="button" class="kb-pick-btn" data-run="' + escapeHtml(r.id) + '"><strong>' + escapeHtml(r.slot) + ' · ' + escapeHtml(r.mode) + '</strong><p class="kb-mono">' + escapeHtml(r.id) + '</p></button>' + badge(r.status,r.status === 'done' ? 'ok' : 'muted') + '<span class="kb-muted">修订 ' + r.against_rev + '</span></div>'; }).join('');
      if (typeof cursor === 'string' && cursor) box.querySelector('[data-runs-more]').remove();
      else box.innerHTML='';
      box.insertAdjacentHTML('beforeend',html || empty('暂无测试记录。'));
      if (data.has_more) box.insertAdjacentHTML('beforeend','<div class="kb-pad"><button class="kb-btn" data-runs-more="' + escapeHtml(data.next_cursor) + '">加载更多</button></div>');
      box.querySelectorAll('[data-run]').forEach(function (btn) { btn.onclick=function () { state.debugRunId=btn.dataset.run; showTestRun(btn.dataset.run); }; });
      const more=box.querySelector('[data-runs-more]'); if (more) more.onclick=function () { debugRecords(more.dataset.runsMore); };
    } catch (e) { box.innerHTML=listError(e); }
  }

  function reindexBar() {
    return '<section class="kb-card kb-rebuild"><div><strong>重建</strong><p class="kb-muted">按内容 hash 增量对账。打开本页不会自动执行。</p></div>' +
      '<button class="kb-btn primary" type="button" id="reindexGo">开始重建</button></section>' +
      '<div id="reindexOut" style="margin-top:12px">' + (state.reindexHtml || "") + "</div>";
  }

  function renderReindexResult(data) {
    const rows = (data.changed || []).concat(data.failed || []);
    const table = rows.length
      ? '<div class="kb-card kb-table-wrap"><table class="kb-table"><thead><tr><th>path</th><th>chunk_id</th><th>action</th><th>旧 hash</th><th>新 hash</th><th>失败</th></tr></thead><tbody>' +
        rows.map(function (r) {
          return "<tr><td>" + escapeHtml(r.path) + "</td><td>" + escapeHtml(r.chunk_id) + "</td><td>" +
            escapeHtml(r.action) + "</td><td>" + escapeHtml(r.old_hash || "") + "</td><td>" +
            escapeHtml(r.new_hash || "") + "</td><td>" + escapeHtml(r.reason || "") + "</td></tr>";
        }).join("") + "</tbody></table></div>"
      : empty("无变更。");
    return "<p class=\"kb-muted\">扫描 " + escapeHtml(String(data.scanned || 0)) + " 块，库内 " +
      escapeHtml(String(data.chunk_count || 0)) + " 点。</p>" + table;
  }

  function bindReindex() {
    const btn = document.getElementById("reindexGo");
    if (!btn) return;
    btn.onclick = async function () {
      const out = document.getElementById("reindexOut");
      btn.disabled = true;
      out.innerHTML = '<p class="kb-muted">正在重建…</p>';
      try {
        const data = await api("/reindex", { method: "POST" });
        state.reindexHtml = renderReindexResult(data);
        out.innerHTML = state.reindexHtml;
        await paintIndexTasks();
      } catch (e) {
        state.reindexHtml = '<p class="kb-err">' + escapeHtml(e.message) + "</p>";
        out.innerHTML = state.reindexHtml;
      }
      btn.disabled = false;
    };
  }

  async function paintSources(cursor) {
    const box=document.getElementById('kbSources'); if (!box) return;
    if (!cursor) box.innerHTML='<section class="kb-card"><div class="kb-card-h">知识来源<span class="kb-muted">受控来源 · 只读</span></div><div class="kb-table-wrap"><table class="kb-table"><thead><tr><th>来源 / 切片</th><th>功能</th><th>正文范围</th><th>正文 hash</th><th>状态</th></tr></thead><tbody id="kbSourceRows"></tbody></table></div><div id="kbSourceMore" class="kb-pad"></div><div id="kbSourceDetail" class="kb-pad" hidden></div></section>';
    try {
      const data=await api('/admin/knowledge-sources' + qs({cursor:cursor || ''}));
      const rows=box.querySelector('#kbSourceRows');
      rows.insertAdjacentHTML('beforeend',(data.items || []).map(function (r) { return '<tr><td><button type="button" class="kb-link" data-source="' + escapeHtml(r.chunk_id) + '" data-path="' + escapeHtml(r.path) + '">' + escapeHtml(r.chunk_id) + '</button><p class="kb-mono">' + escapeHtml(r.path) + '</p></td><td>' + escapeHtml(r.feature_id || '未提供') + '</td><td>' + escapeHtml(r.integrity) + '</td><td><span class="kb-mono" title="正文 hash，不表示业务版本">' + escapeHtml(r.content_hash || '未提供') + '</span></td><td>' + escapeHtml(r.readable) + '</td></tr>'; }).join(''));
      box.querySelector('#kbSourceMore').innerHTML=data.has_more ? '<button type="button" class="kb-btn" id="kbSourceNext">加载更多来源</button>' : '<p class="kb-muted">' + escapeHtml(data.note || '已加载全部受控来源。') + '</p>';
      const next=box.querySelector('#kbSourceNext'); if (next) next.onclick=function () { next.disabled=true; paintSources(data.next_cursor); };
      rows.querySelectorAll('[data-source]').forEach(function (btn) { btn.onclick=async function () {
        const detail=box.querySelector('#kbSourceDetail'); detail.hidden=false; detail.innerHTML=listState('loading');
        try { const r=await api('/admin/knowledge-sources/detail' + qs({path:btn.dataset.path,chunk_id:btn.dataset.source})); detail.innerHTML='<h3>' + escapeHtml(r.heading || r.chunk_id) + '</h3>' + kv('来源',escapeHtml(r.path)) + kv('当前正文 hash',escapeHtml(r.content_hash)) + kv('索引 hash',escapeHtml(r.indexed_hash || '未知/未索引')) + kv('索引一致性',r.index_consistent == null ? '未知' : r.index_consistent ? '一致' : '已变化') + '<p class="kb-muted">' + escapeHtml(r.integrity_note) + '</p><pre class="kb-pre">' + escapeHtml(r.content) + '</pre>'; } catch (e) { detail.innerHTML=listError(e); }
      }; });
    } catch (e) { box.querySelector('#kbSourceMore').innerHTML=listError(e); }
  }

  async function paintIndexTasks(cursor) {
    const box=document.getElementById('kbIndexTasks'); if (!box) return;
    if (!cursor) box.innerHTML='<section class="kb-card"><div class="kb-card-h">索引任务历史<button class="kb-btn" type="button" id="kbTaskRefresh">刷新</button></div><div class="kb-table-wrap"><table class="kb-table"><thead><tr><th>任务 / 范围</th><th>类型</th><th>状态</th><th>扫描 / 变更 / 失败</th><th>时间</th></tr></thead><tbody id="kbTaskRows"></tbody></table></div><div id="kbTaskMore" class="kb-pad"></div><div id="kbTaskDetail" class="kb-pad" hidden></div></section>';
    box.querySelector('#kbTaskRefresh').onclick=function () { paintIndexTasks(); };
    try {
      const data=await api('/admin/index-tasks' + qs({cursor:cursor || ''}));
      const rows=box.querySelector('#kbTaskRows');
      rows.insertAdjacentHTML('beforeend',(data.items || []).map(function (r) { return '<tr><td><button type="button" class="kb-link" data-task="' + escapeHtml(r.id) + '">' + escapeHtml(r.id) + '</button><p class="kb-mono">' + escapeHtml(r.scope) + '</p></td><td>' + (r.group === 'memory' ? 'Memory 回填' : '知识重建') + '</td><td>' + badge(r.status,r.status === 'done' ? 'ok' : r.status === 'failed' ? 'danger' : 'warn') + '</td><td>' + r.scanned + ' / ' + r.changed + ' / ' + r.failed + '</td><td class="kb-mono">' + escapeHtml(fmtTime(r.created_at,data.tz)) + '</td></tr>'; }).join(''));
      box.querySelector('#kbTaskMore').innerHTML=data.has_more ? '<button type="button" class="kb-btn" id="kbTaskNext">加载更多任务</button>' : '<p class="kb-muted">' + ((data.items || []).length ? '任务记录已加载。' : '暂无任务。打开页面不会发起重建。') + '</p>';
      const next=box.querySelector('#kbTaskNext'); if (next) next.onclick=function () { next.disabled=true; paintIndexTasks(data.next_cursor); };
      rows.querySelectorAll('[data-task]').forEach(function (btn) { btn.onclick=async function () {
        const detail=box.querySelector('#kbTaskDetail'); detail.hidden=false; detail.innerHTML=listState('loading');
        try { const r=await api('/admin/index-tasks/' + encodeURIComponent(btn.dataset.task)); detail.innerHTML='<h3>任务 ' + escapeHtml(r.id) + '</h3>' + kv('完整性',escapeHtml(r.integrity)) + kv('父任务',escapeHtml(r.parent_id || '无')) + kv('错误',escapeHtml(r.error || '无')) + '<pre class="kb-pre">' + escapeHtml(JSON.stringify(r.detail || {},null,2)) + '</pre>' + (hasPerm('重建') && r.status !== 'running' && r.status !== 'done' ? '<button type="button" class="kb-btn" id="kbTaskRetry">重试此任务</button>' : ''); const retry=detail.querySelector('#kbTaskRetry'); if (retry) retry.onclick=async function () { retry.disabled=true; try { await api('/admin/index-tasks/' + encodeURIComponent(r.id) + '/retry',{method:'POST'}); await paintIndexTasks(); setMsg('重试已完成，保留原任务历史'); } catch (e) { setMsg(e.message,true); retry.disabled=false; } }; } catch (e) { detail.innerHTML=listError(e); }
      }; });
    } catch (e) { box.querySelector('#kbTaskMore').innerHTML=listError(e); }
  }

  async function paintMemory() {
    const box = document.getElementById("kbMemory");
    if (!box) return;
    box.innerHTML = '<section class="kb-card"><div class="kb-card-h">对话记忆覆盖</div><div class="kb-card-b">' +
      '<form id="kbMemCov"><input class="kb-input" name="conv_id" placeholder="会话编号"> ' +
      '<button class="kb-btn" type="submit">查看覆盖</button>' +
      (hasPerm("重建") ? ' <button class="kb-btn" type="button" id="kbMemFill">回填这个会话</button>' : "") +
      "</form><div id=\"kbMemOut\"></div></div></section>";
    const out = box.querySelector("#kbMemOut");
    box.querySelector("#kbMemCov").onsubmit = async function (ev) {
      ev.preventDefault();
      const id = new FormData(ev.target).get("conv_id");
      try {
        const cov = await api("/admin/memory-coverage?conv_id=" + encodeURIComponent(id));
        const holes = (cov.holes || []).map(function (h) { return h.join("–"); }).join("，");
        out.innerHTML = "<p>" + badge(cov.state_label || cov.state, cov.state === "normal" ? "ok" : "warn") +
          " " + escapeHtml(cov.quality || "") + "</p>" +
          "<p class=\"kb-muted\">" + escapeHtml(cov.quality_note || cov.note || "") + "</p>" +
          "<p>空洞：" + escapeHtml(holes || "无") + "</p>" +
          "<p>积压：" + escapeHtml(cov.backlog == null ? "未知" : String(cov.backlog)) + "</p>";
      } catch (e) {
        out.innerHTML = '<p class="kb-err">' + escapeHtml(e.message) + "</p>";
      }
    };
    const fill = box.querySelector("#kbMemFill");
    if (fill) {
      fill.onclick = async function () {
        const id = box.querySelector("input[name=conv_id]").value;
        try {
          const res = await api("/admin/memory-backfill", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ conv_id: id })
          });
          out.innerHTML = "<p>" + escapeHtml(res.note || "已提交") + "</p>";
        } catch (e) {
          out.innerHTML = '<p class="kb-err">' + escapeHtml(e.message) + "</p>";
        }
      };
    }
  }

  /* ---------- 操作记录：摘要列表与按需详情 ---------- */
  const AUDIT_ACTIONS = {
    login_success:'登录成功', login_fail:'登录失败', logout:'退出登录',
    create_account:'创建账号', enable_account:'启用账号', disable_account:'禁用账号', change_role:'修改账号角色',
    create_role:'创建角色', change_role_perms:'修改角色权限', unlock:'登录解锁',
    config_update:'保存配置草稿', config_publish:'发布配置', config_rollback:'回退配置',
    tls_upload:'保存证书', tls_enable:'启用 HTTPS', tls_disable:'关闭 HTTPS',
    purge_conversation:'实际删除会话', issue_create:'创建问题', issue_update:'更新问题', issue_note:'追加问题记录'
  };

  function openDrawer(title, content) {
    const old = document.getElementById('kbDrawer');
    if (old) old.remove();
    const dialog = document.createElement('dialog');
    dialog.id = 'kbDrawer';
    dialog.className = 'kb-drawer';
    dialog.setAttribute('aria-labelledby', 'kbDrawerTitle');
    dialog.innerHTML = '<div class="kb-drawer-head"><h3 id="kbDrawerTitle">' + escapeHtml(title) +
      '</h3><button class="kb-btn" type="button" id="kbDrawerClose">关闭</button></div><div class="kb-drawer-body">' + content + '</div>';
    document.body.appendChild(dialog);
    dialog.querySelector('#kbDrawerClose').onclick = function () { dialog.close(); };
    dialog.addEventListener('close', function () { dialog.remove(); });
    dialog.showModal();
    return dialog;
  }

  function auditFields(value, prefix) {
    const rows = [];
    Object.keys(value || {}).forEach(function (key) {
      const item = value[key], label = prefix ? prefix + ' / ' + key : key;
      if (item && typeof item === 'object' && !Array.isArray(item)) rows.push(auditFields(item, label));
      else rows.push('<div><dt>' + escapeHtml(label) + '</dt><dd>' + escapeHtml(item == null ? '未记录' :
        Array.isArray(item) ? item.map(function (v) { return typeof v === 'object' ? JSON.stringify(v) : String(v); }).join('、') : String(item)) + '</dd></div>');
    });
    return rows.join('');
  }

  async function pageAudits() {
    const f = (state.audit && state.audit.filters) || {};
    const resultOpts = [["", "全部结果"], ["success", "成功"], ["failed", "失败"], ["accepted", "待核对"], ["legacy", "旧记录"]];
    const field = function (name, label, placeholder) { return '<label class="kb-field"><span>' + label + '</span><input name="' + name + '" value="' + escapeHtml(f[name] || '') + '" placeholder="' + placeholder + '"' + (name === 'action' ? ' list="auditActions"' : '') + '></label>'; };
    const advanced = ['object','object_type','op_id'].some(function (key) { return f[key]; });
    const tools = '<form id="auditFilter" class="kb-card kb-pad kb-audit-filter"><div class="kb-filter-row">' +
      field('actor','操作者','输入账号') + field('action','动作','选择或输入动作代码') +
      '<datalist id="auditActions">' + Object.keys(AUDIT_ACTIONS).map(function (key) { return '<option value="' + key + '">' + AUDIT_ACTIONS[key] + '</option>'; }).join('') + '</datalist>' +
      '<label class="kb-field"><span>结果</span><select name="result">' + resultOpts.map(function (o) {
        return '<option value="' + o[0] + '"' + (o[0] === (f.result || '') ? ' selected' : '') + '>' + o[1] + '</option>';
      }).join('') + '</select></label><div class="kb-actions"><button class="kb-btn primary" type="submit">筛选</button><button class="kb-btn" type="button" id="auditReset">重置</button></div></div>' +
      '<details class="kb-filter-more"' + (advanced ? ' open' : '') + '><summary>按对象与操作号查找</summary><div class="kb-filter-row">' +
      field('object','对象标识','账号 / 会话 / 版本等标识') + field('object_type','对象类型','如 account、config') + field('op_id','操作号','输入关联操作号') + '</div></details></form>';
    els.main.innerHTML = pageHead('操作记录', '查询谁在何时对什么做了操作，展开查看结果与关联字段。', '<button type="button" class="kb-btn" id="auditRefresh">刷新记录</button>') +
      tools + '<div id="auditBody">' + listState('loading') + '</div>';
    const body = document.getElementById('auditBody');
    document.getElementById('auditFilter').onsubmit = function (ev) {
      ev.preventDefault();
      const data = new FormData(ev.target), filters = {};
      ['action','actor','result','object','object_type','op_id'].forEach(function (key) { filters[key] = String(data.get(key) || '').trim(); });
      state.audit = {filters:filters};
      pageAudits();
    };
    document.getElementById('auditReset').onclick = function () { state.audit = null; pageAudits(); };
    document.getElementById('auditRefresh').onclick = function () { state.audit = {filters:f}; pageAudits(); };
    if (!state.audit || !state.audit.items) {
      const requestState = {filters:f}; state.audit = requestState;
      try {
        const data = await api('/admin/audits' + qs(Object.assign({},f,{page_size:50})));
        if (!body.isConnected || state.audit !== requestState) return;
        state.audit = {filters:f,items:data.items || [],next:data.next_cursor,more:!!data.has_more,meta:data};
      } catch (e) { if (body.isConnected) body.innerHTML = listError(e); return; }
    }
    paintAudits();
  }

  function auditResult(r) {
    if (r.legacy) return badge('旧记录', 'muted');
    if (r.pending_check) return badge('待核对', 'warn');
    if (r.result === 'success') return badge('成功', 'ok');
    if (r.result === 'failed') return badge('失败', 'danger');
    return badge(r.result || '未知', 'muted');
  }

  function paintAudits() {
    const a = state.audit, box = document.getElementById('auditBody');
    if (!box || !a) return;
    const tz = (a.meta && a.meta.tz) || DEFAULT_TZ;
    const integ = (a.meta && a.meta.integrity) || {};
    const warn = (integ.read_audit_failures || integ.result_audit_failures || integ.blocked_high_risk)
      ? listState('partial', '审计完整性待核对：读取留痕失败 ' + (integ.read_audit_failures || 0) + ' 次，结果写入失败 ' +
        (integ.result_audit_failures || 0) + ' 次，因审计不可用拒绝 ' + (integ.blocked_high_risk || 0) + ' 次（本进程启动以来）。') : '';
    const rows = a.items.map(function (r, i) {
      return '<tr><td class="kb-audit-time">' + escapeHtml(fmtTime(r.created_at,tz)) + '</td><td>' + escapeHtml(r.actor_username || '未记录') +
        '</td><td><button class="kb-link" type="button" data-audit-detail="' + i + '">' + escapeHtml(AUDIT_ACTIONS[r.action] || r.action || '未知动作') +
        '</button></td><td><span class="kb-audit-object" title="' + escapeHtml(r.object || '') + '">' + escapeHtml(r.object || '—') +
        '</span><span class="kb-muted">' + escapeHtml(r.object_type || '') + '</span></td><td>' + auditResult(r) + '</td></tr>';
    }).join('');
    box.innerHTML = warn + '<section class="kb-card"><div class="kb-card-h"><span>操作列表</span><span class="kb-muted">已加载 ' + a.items.length +
      ' 条' + (a.more ? ' · 还有更多' : '') + '</span></div>' + tzNote(a.meta) + coverageNote(a.meta) +
      (rows ? '<div class="kb-table-wrap"><table class="kb-table kb-audit-table"><thead><tr><th>时间</th><th>操作者</th><th>动作 / 详情</th><th>对象</th><th>结果</th></tr></thead><tbody>' + rows + '</tbody></table></div>' : listState('empty','没有符合条件的操作记录。')) +
      (a.more ? '<div class="kb-pad"><button type="button" class="kb-btn" id="auditMore">加载更多</button></div>' : '') + '</section>';
    box.querySelectorAll('[data-audit-detail]').forEach(function (btn) {
      btn.onclick = function () {
        const r = a.items[Number(btn.dataset.auditDetail)];
        const fields = [['时间',fmtTime(r.created_at,tz) + '（' + tz + '）'],['操作者',r.actor_username],['动作代码',r.action],['对象类型',r.object_type],['对象',r.object],['操作号',r.op_id],['错误码',r.error_code],['来源 IP',r.ip],['记录编号',r.id]];
        const detail = auditFields(r.detail || {}, '');
        openDrawer('操作详情', '<div class="kb-detail-status">' + auditResult(r) + '</div><dl class="kb-detail-fields">' + fields.map(function (f) {
          return '<div><dt>' + escapeHtml(f[0]) + '</dt><dd>' + escapeHtml(f[1] == null || f[1] === '' ? '未记录' : f[1]) + '</dd></div>';
        }).join('') + '</dl><h4>附加字段</h4>' + (detail ? '<dl class="kb-detail-fields">' + detail + '</dl>' : empty('没有附加字段。')) +
          '<details class="kb-slot"><summary>原始字段</summary><pre class="kb-pre">' + escapeHtml(JSON.stringify(r,null,2)) + '</pre></details>');
      };
    });
    const btn = document.getElementById('auditMore');
    if (btn) btn.onclick = async function () {
      btn.disabled = true;
      try {
        const data = await api('/admin/audits' + qs(Object.assign({},a.filters,{page_size:50,cursor:a.next})));
        if (!box.isConnected || state.audit !== a) return;
        a.items = a.items.concat(data.items || []); a.next = data.next_cursor; a.more = !!data.has_more;
        paintAudits();
      } catch (e) { if (btn.isConnected) { btn.disabled = false; btn.insertAdjacentHTML('afterend',listError(e)); } }
    };
  }

  /* ---------- 访问：账号 / 角色 / 解锁；证书单独 ---------- */
  async function pageAccess() {
    if (!(state.me && state.me.is_super)) {
      els.main.innerHTML = empty("没有权限");
      return;
    }
    const tabs = [
      { id: "accounts", label: "账号" },
      { id: "roles", label: "角色" },
      { id: "unlock", label: "登录解锁" },
      { id: "tls", label: "证书", quiet: true }
    ];
    els.main.innerHTML = pageHead("访问管理", "管理账号身份、角色权限与登录状态。") +
      '<div class="kb-tabs">' + tabs.map(function (t) {
        const cls = (t.id === state.accessTab ? "active" : "") + (t.quiet ? " quiet" : "");
        const before = t.quiet ? '<span class="spacer"></span><span class="kb-sys">系统</span>' : "";
        return before + '<button type="button" data-tab="' + t.id + '" class="' + cls + '">' + escapeHtml(t.label) + "</button>";
      }).join("") + '</div><div id="accessBody"><p class="kb-muted">加载中…</p></div>';
    els.main.querySelectorAll("[data-tab]").forEach(function (btn) {
      btn.onclick = function () {
        if (!allowRoleLeave()) return;
        state.accessTab = btn.getAttribute("data-tab");
        pageAccess();
      };
    });
    if (state.accessTab === "accounts") await paneAccounts();
    else if (state.accessTab === "roles") await paneRoles();
    else if (state.accessTab === "unlock") paneUnlock();
    else await paneTls();
    takeNotice();
  }

  async function paneAccounts() {
    const box = document.getElementById('accessBody');
    if (!box) return;
    const cache = state.accessAcc || {q:''};
    try {
      const packs = await Promise.all([api('/admin/roles'),api('/admin/accounts' + qs({q:cache.q,page_size:50}))]);
      if (!box.isConnected || state.accessTab !== 'accounts') return;
      const data = packs[1], roles = packs[0].items || [];
      state.accessAcc = {q:cache.q,items:data.items || [],next:data.next_cursor,more:!!data.has_more,total:data.total};
      box.innerHTML = '<section class="kb-card"><div class="kb-card-h"><div>账号列表 <span class="kb-muted" id="accTotal"></span></div><button class="kb-btn primary" id="accCreate" type="button">新建账号</button></div>' +
        '<form id="accFilter" class="kb-tools kb-pad"><label class="kb-field"><span>用户名</span><input name="q" placeholder="输入用户名筛选" value="' + escapeHtml(cache.q) + '"></label><button class="kb-btn" type="submit">筛选</button><button class="kb-btn" type="button" id="accReset">重置</button></form>' +
        '<div class="kb-table-wrap"><table class="kb-table kb-account-table"><thead><tr><th>账号</th><th>角色</th><th>状态</th><th>管理</th></tr></thead><tbody id="accRows"></tbody></table></div><div id="accMore"></div></section>';
      paintAccounts(roles);
      document.getElementById('accCreate').onclick = function () { openAccountEditor(null,roles); };
      document.getElementById('accFilter').onsubmit = function (ev) { ev.preventDefault(); state.accessAcc={q:ev.target.elements.q.value.trim()}; paneAccounts(); };
      document.getElementById('accReset').onclick = function () { state.accessAcc={q:''}; paneAccounts(); };
    } catch (e) { if (box.isConnected) box.innerHTML = listError(e); }
  }

  function paintAccounts(roles) {
    const acc = state.accessAcc, tbody = document.getElementById('accRows');
    if (!tbody) return;
    tbody.innerHTML = acc.items.map(function (a) {
      return '<tr><td><strong>' + escapeHtml(a.username) + '</strong></td><td>' + escapeHtml(a.role_name || '未分配') + '</td><td>' + badge(a.enabled ? '启用' : '禁用',a.enabled ? 'ok' : 'danger') +
        '</td><td><button class="kb-link" type="button" data-account-edit="' + escapeHtml(a.id) + '">查看 / 编辑</button></td></tr>';
    }).join('') || '<tr><td colspan="4">' + listState('empty',acc.q ? '没有匹配的账号。' : '暂无账号。') + '</td></tr>';
    document.getElementById('accTotal').textContent = acc.total == null ? '' : '共 ' + acc.total + ' 个';
    document.getElementById('accMore').innerHTML = acc.more ? '<div class="kb-pad"><button type="button" class="kb-btn" id="accMoreBtn">加载更多</button></div>' : '';
    tbody.querySelectorAll('[data-account-edit]').forEach(function (btn) {
      btn.onclick = function () { openAccountEditor(acc.items.find(function (a) { return a.id === btn.dataset.accountEdit; }), roles); };
    });
    const more = document.getElementById('accMoreBtn');
    if (more) more.onclick = async function () {
      more.disabled = true;
      try {
        const data = await api('/admin/accounts' + qs({q:acc.q,page_size:50,cursor:acc.next}));
        if (!tbody.isConnected || state.accessAcc !== acc) return;
        acc.items = acc.items.concat(data.items || []); acc.next=data.next_cursor; acc.more=!!data.has_more;
        paintAccounts(roles);
      } catch (e) { if (more.isConnected) { more.disabled=false; more.insertAdjacentHTML('afterend',listError(e)); } }
    };
  }

  function openAccountEditor(account, roles) {
    const options = roles.map(function (r) { return '<option value="' + escapeHtml(r.id) + '"' + (account && account.role_id === r.id ? ' selected' : '') + '>' + escapeHtml(r.name) + '</option>'; }).join('');
    const dialog = openDrawer(account ? '管理账号 · ' + account.username : '新建账号',
      '<form id="accountForm" class="kb-stack">' + (account ? '<div class="kb-detail-status">' + badge(account.enabled ? '账号已启用' : '账号已禁用',account.enabled ? 'ok':'danger') + '</div>' :
        '<label class="kb-field"><span>用户名</span><input name="username" autocomplete="off" required></label><label class="kb-field"><span>初始密码</span><input name="password" type="password" autocomplete="new-password" required></label>') +
      '<label class="kb-field"><span>角色</span><select name="role_id" required>' + (account ? '' : '<option value="" disabled selected>请选择角色</option>') + options + '</select></label>' +
      '<p class="kb-muted">' + (account ? '修改角色后，该账号的下一次请求按新权限校验。' : '账号继承所选角色的权限。') + '</p><p id="accountError" class="kb-err" hidden></p>' +
      '<div class="kb-actions"><button class="kb-btn primary" type="submit">' + (account ? '保存角色' : '创建账号') + '</button></div></form>' +
      (account ? '<section class="kb-access-state"><h4>账号状态</h4><p class="kb-muted">' + (account.enabled ? '禁用后，该账号不能继续使用当前登录会话。' : '启用后，该账号可以重新登录。') + '</p><button class="kb-btn' + (account.enabled ? ' danger' : '') + '" id="accountToggle" type="button">' + (account.enabled ? '禁用此账号' : '启用此账号') + '</button></section>' : ''));
    const form = dialog.querySelector('#accountForm'), error = dialog.querySelector('#accountError');
    const fail = function (e) { error.hidden=false; error.textContent=e.message; };
    form.onsubmit = async function (ev) {
      ev.preventDefault();
      const roleId = form.elements.role_id.value, submit = form.querySelector('[type=submit]');
      if (account) {
        if (roleId === account.role_id) { fail({message:'角色没有变化'}); return; }
        const role = roles.find(function (r) { return r.id === roleId; });
        if (!window.confirm('把「' + account.username + '」的角色从「' + account.role_name + '」改为「' + role.name + '」？新权限对下一次请求立即生效。')) return;
      }
      submit.disabled=true;
      try {
        await api('/admin/accounts' + (account ? '/' + encodeURIComponent(account.id) : ''), {method:account ? 'PATCH' : 'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(account ? {role_id:roleId} : {username:form.elements.username.value,password:form.elements.password.value,role_id:roleId})});
        dialog.close(); await paneAccounts(); setMsg(account ? '已修改账号角色' : '已创建账号');
      } catch (e) { fail(e); submit.disabled=false; }
    };
    const toggle = dialog.querySelector('#accountToggle');
    if (toggle) toggle.onclick = async function () {
      toggle.disabled=true;
      try {
        await api('/admin/accounts/' + encodeURIComponent(account.id),{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:!account.enabled})});
        dialog.close(); await paneAccounts(); setMsg(account.enabled ? '已禁用账号' : '已启用账号');
      } catch (e) { fail(e); toggle.disabled=false; }
    };
  }

  function permissionGroups(permissions, selected, pending, readonly) {
    const groups = [
      ['工作台与问答',['进管理模块','知识问答','问答明细','对话审计','反馈汇总','问题处理']],
      ['统计与观察',['数据概览','功能热度','健康','操作审计']],
      ['配置与 Prompt',['配置查看','配置编辑','Prompt查看','Prompt编辑','Prompt调试','配置发布']],
      ['知识维护',['知识源查看','重建']],
      ['其他',[]]
    ];
    permissions.forEach(function (p) { if (!groups.some(function (g) { return g[1].indexOf(p) >= 0; })) groups[groups.length-1][1].push(p); });
    return '<div class="kb-permission-groups">' + groups.map(function (g) {
      const items = g[1].filter(function (p) { return permissions.indexOf(p) >= 0; });
      if (!items.length) return '';
      return '<fieldset><legend>' + g[0] + '</legend><div>' + items.map(function (p) {
        return '<label class="kb-check"><input type="checkbox" value="' + escapeHtml(p) + '"' + (selected.indexOf(p) >= 0 ? ' checked' : '') + (readonly ? ' disabled' : '') + '><span>' + escapeHtml(p) +
          (pending.indexOf(p) >= 0 ? ' <small class="kb-muted">未接入</small>' : '') + '</span></label>';
      }).join('') + '</div></fieldset>';
    }).join('') + '</div>';
  }

  function allowRoleLeave() {
    if (state.roleDirty && !window.confirm('角色权限还没保存，离开后这次修改会丢掉。')) return false;
    state.roleDirty = false;
    return true;
  }

  async function paneRoles() {
    const box = document.getElementById('accessBody');
    if (!box) return;
    const data = await api('/admin/roles');
    if (!box.isConnected || state.accessTab !== 'roles') return;
    const pending = data.pending || [], roles = data.items || [], permissions = data.checkboxes || [];
    box.innerHTML = '<div id="roleMigration"></div><div class="kb-role-layout"><section class="kb-card"><div class="kb-card-h"><span>角色 <span class="kb-muted">' + roles.length + '</span></span><button class="kb-btn" id="roleCreate" type="button">新建角色</button></div>' +
      '<div class="kb-role-list">' + roles.map(function (r) {
        return '<button class="kb-qa-row" type="button" data-role-pick="' + escapeHtml(r.id) + '"><span class="kb-qa-line"><strong>' + escapeHtml(r.name) + '</strong>' +
          badge(r.is_super ? '超管' : r.is_preset ? '系统' : '自定义','muted') + '</span><span class="kb-muted">' + (r.account_count || 0) + ' 个账号 · ' +
          (r.is_super ? '全部权限' : (r.permissions || []).length + ' 项权限') + '</span></button>';
      }).join('') + '</div></section><div id="roleEdit"></div></div>';
    function selectRole(role) {
      if (!allowRoleLeave()) return;
      state.roleId = role.id;
      box.querySelectorAll('[data-role-pick]').forEach(function (btn) { btn.classList.toggle('kb-pick', btn.dataset.rolePick === role.id); });
      if (role.is_super) {
        document.getElementById('roleEdit').innerHTML = '<section class="kb-card kb-pad"><div class="kb-section-head"><h3>' + escapeHtml(role.name) + '</h3>' + badge('内置全权限','muted') +
          '</div><p class="kb-muted">关联 ' + (role.account_count || 0) + ' 个账号。内置超管权限不可编辑。</p>' + permissionGroups(permissions,permissions,pending,true) + '</section>';
      } else openRoleEditor(role,permissions,pending);
      if (window.innerWidth <= 980) document.getElementById('roleEdit').scrollIntoView({block:'start'});
    }
    box.querySelectorAll('[data-role-pick]').forEach(function (btn) { btn.onclick = function () { selectRole(roles.find(function (r) { return r.id === btn.dataset.rolePick; })); }; });
    const selected = roles.find(function (r) { return r.id === state.roleId; }) || roles[0];
    if (selected) selectRole(selected);
    document.getElementById('roleCreate').onclick = function () {
      if (!allowRoleLeave()) return;
      if (selected) selectRole(roles.find(function (r) { return r.id === state.roleId; }) || selected);
      const dialog = openDrawer('新建角色','<form id="createRole" class="kb-stack"><label class="kb-field"><span>角色名称</span><input name="name" required></label>' +
        permissionGroups(permissions,[],pending,false) + '<p id="createRoleError" class="kb-err" hidden></p><div class="kb-actions"><button class="kb-btn primary" type="submit">创建角色</button></div></form>');
      dialog.querySelector('#createRole').onsubmit = async function (ev) {
        ev.preventDefault();
        const form = ev.target, button = form.querySelector('[type=submit]'); button.disabled=true;
        try {
          const row = await api('/admin/roles',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:form.elements.name.value,permissions:Array.from(form.querySelectorAll('input[type=checkbox]:checked')).map(function (n) { return n.value; })})});
          state.roleId=row.id; dialog.close(); await paneRoles(); setMsg('已创建角色');
        } catch (e) { button.disabled=false; const error=form.querySelector('#createRoleError'); error.hidden=false; error.textContent=e.message; }
      };
    };
    const report = document.getElementById('roleMigration');
    try {
      const migration = await api('/admin/perm-migration');
      if (report.isConnected) report.innerHTML = migrationReport(migration);
    } catch (e) { if (report.isConnected) report.innerHTML = listError(e); }
  }

  /* 编辑自定义角色：先预览前后差异与影响账号数，再二次确认提交。 */
  function openRoleEditor(role, checkboxes, pending) {
    const box = document.getElementById("roleEdit");
    const before = (role.permissions || []).slice().sort();
    state.roleDirty = false;
    box.innerHTML = '<form id="roleEditForm" class="kb-card kb-pad"><div class="kb-section-head"><h3>' + escapeHtml(role.name) + '</h3>' + badge(role.is_preset ? '系统角色' : '自定义角色','muted') + '</div>' +
      '<p class="kb-muted">关联 ' + (role.account_count || 0) + ' 个账号。先预览权限差异，再确认修改。</p>' +
      ((role.retired_permissions || []).length ? '<p class="kb-warn">已停用权限：' + escapeHtml(role.retired_permissions.join('、')) + '</p>' : '') +
      permissionGroups(checkboxes,before,pending,false) + '<div id="roleDiff"></div><div class="kb-actions"><button class="kb-btn" type="button" id="rolePreview">预览变更</button>' +
      '<button class="kb-btn primary" type="submit" id="roleSave" disabled>确认修改</button><button class="kb-btn" type="button" id="roleCancel">撤销修改</button></div></form>';
    const form = document.getElementById("roleEditForm");
    let pendingPerms = null;
    function picked() {
      return Array.prototype.slice.call(form.querySelectorAll("input[type=checkbox]:checked")).map(function (n) { return n.value; }).sort();
    }
    form.addEventListener("change", function () {
      pendingPerms = null;
      state.roleDirty = JSON.stringify(picked()) !== JSON.stringify(before);
      document.getElementById("roleSave").disabled = true;
      document.getElementById("roleDiff").innerHTML = "";
    });
    document.getElementById("rolePreview").onclick = function () {
      const after = picked();
      const added = after.filter(function (p) { return before.indexOf(p) < 0; });
      const removed = before.filter(function (p) { return after.indexOf(p) < 0; });
      if (!added.length && !removed.length) {
        document.getElementById("roleDiff").innerHTML = listState("empty", "没有变化。");
        return;
      }
      pendingPerms = after;
      document.getElementById("roleDiff").innerHTML = '<div class="kb-block">' +
        (added.length ? "<p>新增：" + escapeHtml(added.join("、")) + "</p>" : "") +
        (removed.length ? "<p>移除：" + escapeHtml(removed.join("、")) + "</p>" : "") +
        '<p class="kb-muted">影响 ' + escapeHtml(String(role.account_count || 0)) + " 个账号；保存后这些账号的下一次请求立即按新权限校验。</p></div>";
      document.getElementById("roleSave").disabled = false;
    };
    document.getElementById("roleCancel").onclick = function () { openRoleEditor(role, checkboxes, pending); };
    form.onsubmit = async function (ev) {
      ev.preventDefault();
      if (!pendingPerms) return;
      if (!window.confirm("确认修改角色「" + role.name + "」的权限？影响 " + (role.account_count || 0) + " 个账号。")) return;
      const btn = document.getElementById("roleSave");
      btn.disabled = true;
      try {
        await api("/admin/roles/" + encodeURIComponent(role.id) + "/permissions", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ permissions: pendingPerms })
        });
        if (form.isConnected) {
          state.roleDirty = false;
          pageAccess();
        }
        setMsg("已修改角色权限");
      } catch (e) {
        btn.disabled = false;
        setMsg(e.message, true);
      }
    };
  }

  /* 权限拆分迁移：旧「配置」不再生效，新权限不自动附加，由超管逐个分配。 */
  function migrationReport(data) {
    const items = (data && data.items) || [];
    if (!items.length) return "";
    const rows = items.map(function (r) {
      return "<tr><td>" + escapeHtml(r.role_name) + "</td><td>" + escapeHtml((r.retired || []).join("、")) +
        "</td><td>" + escapeHtml((r.was || []).join("；")) + "</td><td>" + escapeHtml((r.now || []).join("；")) +
        "</td><td>" + escapeHtml(String(r.account_count || 0)) + "</td></tr>";
    }).join("");
    return '<section class="kb-card kb-pad" style="margin-bottom:12px"><strong>权限变更影响</strong>' +
      '<p class="kb-muted">以下角色持有已停用的旧权限，原能力已失效；新权限不会自动附加，请在角色中重新勾选。</p>' +
      '<div class="kb-table-wrap"><table class="kb-table"><thead><tr><th>角色</th><th>停用权限</th><th>原能力</th><th>现在</th><th>账号数</th></tr></thead><tbody>' +
      rows + "</tbody></table></div></section>";
  }

  function paneUnlock() {
    document.getElementById("accessBody").innerHTML =
      '<form id="unlockForm" class="kb-card kb-pad" style="max-width:420px"><strong>解锁</strong>' +
        '<p class="kb-muted">只解除登录失败锁定，不影响问答会话的执行或保存状态。</p>' +
        '<label class="kb-field"><span>用户名</span><input name="username" required></label>' +
        '<div id="lockState"></div>' +
        '<div class="kb-actions"><button class="kb-btn" type="button" id="lockCheck">查看锁定状态</button>' +
        '<button class="kb-btn primary" type="submit">清除失败次数</button></div></form>';
    document.getElementById("lockCheck").onclick = async function () {
      const form = document.getElementById("unlockForm");
      const out = document.getElementById("lockState");
      const name = form.username.value.trim();
      if (!name) {
        setMsg("请先输入用户名", true);
        return;
      }
      out.innerHTML = listState("loading");
      try {
        const st = await api("/admin/login-lock" + qs({ username: name }));
        out.innerHTML = '<div class="kb-kv"><b>账号</b><span>' + escapeHtml(st.exists ? "存在" : "不存在") + "</span></div>" +
          '<div class="kb-kv"><b>状态</b><span>' + (st.locked ? badge("已锁定", "danger") : badge("未锁定", "ok")) + "</span></div>" +
          (st.locked_until ? '<div class="kb-kv"><b>锁定至</b><span>' + escapeHtml(fmtTime(st.locked_until, DEFAULT_TZ) + "（" + DEFAULT_TZ + "）") + "</span></div>" : "") +
          '<div class="kb-kv"><b>连续失败</b><span>' + escapeHtml(String(st.fail_count || 0)) + " 次</span></div>";
      } catch (e) {
        out.innerHTML = listError(e);
      }
    };
    document.getElementById("unlockForm").onsubmit = async function (ev) {
      ev.preventDefault();
      try {
        await api("/admin/unlock", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: ev.target.username.value })
        });
        setMsg("已解锁，可立即登录");
      } catch (e) {
        setMsg(e.message, true);
      }
    };
  }

  /* ---------- 证书：上传只保存，启用失败如实显示；私钥不回显 ---------- */
  async function paneTls() {
    const box = document.getElementById("accessBody");
    const st = await api("/admin/tls");
    if (!box || !box.isConnected || state.accessTab !== "tls") return;
    const extra = [];
    if (st.pending) extra.push(badge("已保存，待启用", "warn"));
    if (st.last_enable_error) {
      extra.push('<span class="kb-err">最近一次启用失败：' + escapeHtml(st.last_enable_error) +
        (st.last_enable_error_at ? "（" + escapeHtml(st.last_enable_error_at) + " UTC）" : "") + "</span>");
    }
    box.innerHTML =
      '<section class="kb-card kb-pad" style="max-width:720px"><strong>证书</strong><p class="kb-muted">当前：' +
      (st.enabled ? "已启用（本机非 80/443 不强制跳转）" : "HTTP") + "；已保存证书 " + (st.has_cert ? "是" : "否") + "</p>" +
      (extra.length ? "<p>" + extra.join(" ") + "</p>" : "") +
      (st.port_note ? '<p class="kb-muted">' + escapeHtml(st.port_note) + "</p>" : "") +
      '<form id="tlsForm"><label class="kb-field"><span>证书 PEM</span><textarea name="cert_pem" rows="8"></textarea></label>' +
      '<label class="kb-field"><span>私钥 PEM</span><textarea name="key_pem" rows="8"></textarea></label>' +
      '<button class="kb-btn" type="submit">只保存</button></form>' +
      '<div class="kb-actions"><button class="kb-btn primary" type="button" id="tlsEnable">启用 HTTPS</button>' +
      '<button class="kb-btn danger" type="button" id="tlsDisable">关闭回 HTTP</button></div></section>';
    document.getElementById("tlsForm").onsubmit = async function (ev) {
      ev.preventDefault();
      try {
        await api("/admin/tls", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ cert_pem: ev.target.cert_pem.value, key_pem: ev.target.key_pem.value })
        });
        setMsg("已保存，尚未启用");
      } catch (e) {
        setMsg(e.message, true);
      }
    };
    document.getElementById("tlsEnable").onclick = async function () {
      try {
        await api("/admin/tls/enable", { method: "POST" });
        state.notice = { text: "已启用", err: false };
        pageAccess();
      } catch (e) {
        /* 启用失败：重画状态，页面显示仍为 HTTP 与失败原因 */
        state.notice = { text: "启用失败，对外仍为 HTTP：" + e.message, err: true };
        pageAccess();
      }
    };
    document.getElementById("tlsDisable").onclick = async function () {
      try {
        await api("/admin/tls/disable", { method: "POST" });
        state.notice = { text: "已关闭，对外仍为 HTTP", err: false };
        pageAccess();
      } catch (e) {
        setMsg(e.message, true);
      }
    };
  }

  /* ---------- 问题（A17）：只改人工记录，不改赞踩、不改回答 ---------- */
  function bindFeedbackIssue(btn, d) {
    btn.onclick = async function () {
      btn.disabled = true;
      try {
        const row = await api("/admin/issues", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: ("反馈 " + String(d.exec_id || "")).slice(0, 80),
            source_type: "feedback",
            source_id: d.exec_id || "",
            conv_id: d.conv_id || "",
            category: "other"
          })
        });
        state.issueId = row.id;
        gotoArea("issues");
      } catch (e) {
        btn.disabled = false;
        setMsg(e.message, true);
      }
    };
  }

  const ISSUE_CATS = [
    ["route", "路由"], ["context", "语境"], ["retrieve", "检索"], ["source", "来源"],
    ["generate", "生成/检查"], ["save", "保存"], ["perm", "权限"], ["ux", "体验"], ["other", "其他/未确定"]
  ];

  async function pageIssues() {
    els.main.innerHTML=pageHead('问题','跟踪人工复查、处理与复测结论。发布不会自动关闭问题。');
    const box=document.createElement('div'); box.className='kb-issue-workspace'; els.main.appendChild(box);
    const opts=ISSUE_CATS.map(function (c) { return '<option value="' + c[0] + '">' + escapeHtml(c[1]) + '</option>'; }).join('');
    box.innerHTML='<section class="kb-card kb-pad"><h3>新建问题</h3><form id="kbIssueNew" class="kb-tools"><input class="kb-input" name="title" maxlength="80" placeholder="标题（人工摘要）" required><select class="kb-select" name="category">' + opts + '</select><button class="kb-btn primary" type="submit">新建</button></form></section><div class="kb-split kb-issue-split"><section class="kb-card kb-pane"><div class="kb-card-h">问题列表<select class="kb-select" id="kbIssueFilter"><option value="">全部状态</option><option value="open">未处理</option><option value="doing">处理中</option><option value="closed">已关闭</option></select></div><div class="kb-card-b" id="kbIssueRows"></div></section><section class="kb-card" id="kbIssueDetail">' + empty('选择问题，查看处理记录。') + '</section></div>';
    const list=box.querySelector('#kbIssueRows'); let next='';
    async function load(cursor) {
      if (!cursor) list.innerHTML=listState('loading');
      try {
        const data=await api('/admin/issues' + qs({status:box.querySelector('#kbIssueFilter').value,cursor:cursor || ''}));
        if (!cursor) list.innerHTML=''; else { const old=list.querySelector('[data-issue-more]'); if (old) old.remove(); }
        list.insertAdjacentHTML('beforeend',(data.items || []).map(function (r) { return '<button type="button" class="kb-qa-row" data-issue="' + escapeHtml(r.id) + '"><span class="kb-qa-line"><span class="kb-ellipsis">' + escapeHtml(r.title) + '</span>' + badge(r.status_label,r.status === 'closed' ? 'muted' : 'ok') + '</span><span class="kb-muted">' + escapeHtml(r.category_label) + (r.source_deleted ? ' · 来源已删除' : '') + '</span></button>'; }).join('') || empty('没有匹配的问题记录。'));
        next=data.next_cursor;
        if (data.has_more) list.insertAdjacentHTML('beforeend','<div class="kb-pad" data-issue-more><button class="kb-btn" type="button" id="kbIssueMore">加载更多</button></div>');
        const more=box.querySelector('#kbIssueMore'); if (more) more.onclick=function () { more.disabled=true; load(next); };
      } catch (e) { if (!cursor) list.innerHTML=listError(e); else list.insertAdjacentHTML('beforeend',listError(e)); }
    }
    list.onclick=function (ev) { const btn=ev.target.closest('[data-issue]'); if (!btn) return; state.issueId=btn.dataset.issue; list.querySelectorAll('.kb-pick').forEach(function (n) { n.classList.remove('kb-pick'); }); btn.classList.add('kb-pick'); paintIssue(box.querySelector('#kbIssueDetail'),state.issueId); };
    box.querySelector('#kbIssueFilter').onchange=function () { load(); };
    box.querySelector('#kbIssueNew').onsubmit=async function (ev) { ev.preventDefault(); const data=new FormData(ev.target); try { const row=await api('/admin/issues',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:data.get('title'),category:data.get('category')})}); state.issueId=row.id; await load(); paintIssue(box.querySelector('#kbIssueDetail'),row.id); ev.target.reset(); } catch (e) { setMsg(e.message,true); } };
    await load(); if (state.issueId) paintIssue(box.querySelector('#kbIssueDetail'),state.issueId);
  }

  async function paintIssue(box, id) {
    if (!box) return;
    let d;
    try {
      d = await api("/admin/issues/" + encodeURIComponent(id));
    } catch (e) {
      box.innerHTML = '<p class="kb-err" style="padding:16px">' + escapeHtml(e.message) + "</p>";
      return;
    }
    const notes = (d.notes || []).map(function (n) {
      return "<p>" + escapeHtml(n.body) + ' <span class="kb-muted">' + escapeHtml(n.created_at || "") + "</span></p>";
    }).join("") || '<p class="kb-muted">还没有处理记录</p>';
    box.innerHTML = '<div class="kb-pad">' +
      "<h3>" + escapeHtml(d.title) + "</h3>" +
      "<p>" + badge(d.status_label, d.status === "closed" ? "muted" : "ok") + " " +
      (d.source_note ? badge(d.source_note, "warn") : "") + "</p>" +
      kv("分类", escapeHtml(d.category_label)) +
      kv("处理人", escapeHtml(d.assignee_username || d.assignee_id || "—")) +
      kv("来源", escapeHtml((d.source_type || "—") + (d.source_id ? " " + d.source_id : ""))) +
      kv("现象", escapeHtml(d.symptom || "—")) +
      (d.close_reason_label ? kv("关闭结论", escapeHtml(d.close_reason_label + "：" + (d.close_basis || ""))) : "") +
      "<h4>处理记录</h4>" + notes +
      '<form id="kbIssueNote"><input class="kb-input" name="text" maxlength="500" placeholder="追加记录"> ' +
      '<button class="kb-btn" type="submit">追加</button></form>' +
      '<form id="kbIssueClose"><select name="status">' +
      '<option value="doing">处理中</option><option value="open">未处理</option><option value="closed">已关闭</option></select> ' +
      '<select name="close_reason"><option value="not_defect">复核非缺陷</option><option value="external">资料待补/外部处理</option>' +
      '<option value="unrepro">无法复现</option><option value="verified">已验证修复</option></select> ' +
      '<input class="kb-input" name="basis" placeholder="依据或重开原因"> ' +
      '<label><input type="checkbox" name="retested"> 已复测</label> ' +
      '<button class="kb-btn" type="submit">保存状态</button></form></div>';
    box.querySelector("#kbIssueNote").onsubmit = async function (ev) {
      ev.preventDefault();
      try {
        await api("/admin/issues/" + encodeURIComponent(id) + "/notes", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: new FormData(ev.target).get("text") })
        });
        paintIssue(box, id);
      } catch (e) {
        setMsg(e.message, true);
      }
    };
    box.querySelector("#kbIssueClose").onsubmit = async function (ev) {
      ev.preventDefault();
      const fd = new FormData(ev.target);
      const status = fd.get("status");
      const payload = { status: status };
      if (status === "closed") {
        payload.close_reason = fd.get("close_reason");
        payload.close_basis = fd.get("basis");
        payload.retested = !!fd.get("retested");
      } else if (d.status === "closed") {
        payload.reopen_reason = fd.get("basis");
      }
      try {
        await api("/admin/issues/" + encodeURIComponent(id), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        paintIssue(box, id);
      } catch (e) {
        setMsg(e.message, true);
      }
    };
  }

  window.addEventListener("beforeunload", function (e) {
    if (!state.configDirty && !state.roleDirty) return;
    e.preventDefault();
    e.returnValue = "";
  });

  els.nav.addEventListener("click", function (ev) {
    const btn = ev.target.closest("[data-area]");
    if (!btn) return;
    const id = btn.getAttribute("data-area");
    if (id === state.area) return;
    if (gotoArea(id)) state.overviewReturn = null;
  });

  els.healthBtn.addEventListener("click", function () {
    els.healthPop.hidden = !els.healthPop.hidden;
  });

  document.addEventListener("click", function (ev) {
    if (els.healthPop.hidden) return;
    if (els.healthPop.contains(ev.target) || els.healthBtn.contains(ev.target)) return;
    els.healthPop.hidden = true;
  });

  async function boot() {
    try {
      state.me = await api("/auth/me");
    } catch (e) {
      if (e.status === 401) {
        window.location.replace("/login/?next=" + encodeURIComponent("/kb-admin/"));
        return;
      }
      els.main.innerHTML = '<p class="kb-err">没有权限</p>';
      return;
    }
    if (!hasPerm("进管理模块")) {
      els.main.innerHTML = '<p class="kb-err">没有权限</p>';
      return;
    }
    els.user.textContent = state.me.username || "";
    renderNav();
    loadHealth().catch(function () { /* 健康灯失败不挡住工作区 */ });
    showArea();
  }

  boot();
})();
