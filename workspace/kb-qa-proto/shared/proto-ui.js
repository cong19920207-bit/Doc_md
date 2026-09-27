/**
 * 知识问答原型界面：Tab、对话、出处跳转、配置、重建、文档索引阅读器。
 * layout = "a" 抽屉配置 + 折叠调试；layout = "b" 右侧过程栏 + 整页配置。
 */
(function () {
  const STAGE_LABEL = {
    rewrite: "改写中…",
    retrieve: "检索中…",
    rerank: "重排中…",
    generate: "生成中…"
  };

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function collectionLabel(c) {
    return c === "hayyo-admin" ? "后台库" : "客户端库";
  }

  function isTextField(el) {
    if (!el || !el.tagName) return false;
    const tag = el.tagName.toLowerCase();
    if (tag === "textarea" || tag === "select") return true;
    if (tag === "input") {
      const t = (el.type || "text").toLowerCase();
      return t !== "button" && t !== "checkbox" && t !== "radio" && t !== "submit";
    }
    return el.isContentEditable;
  }

  function toast(text) {
    const old = document.querySelector(".toast");
    if (old) old.remove();
    const el = document.createElement("div");
    el.className = "toast";
    el.textContent = text;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 1600);
  }

  function copyText(text) {
    const ok = () => toast("已复制回答");
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(ok).catch(() => {
        window.prompt("复制以下文本", text);
      });
    } else {
      window.prompt("复制以下文本", text);
    }
  }

  function citeButton(c) {
    const demo = c.demoOnly ? '<span class="qa-tag demo">演示冲突</span>' : "";
    const col = '<span class="qa-tag' + (c.collection === "hayyo-admin" ? " admin" : "") + '">' + escapeHtml(collectionLabel(c.collection)) + "</span>";
    return (
      '<button class="qa-chunk" type="button" data-cite="' + escapeHtml(c.chunk_id) + '">' +
        demo + col +
        '<span class="name">' + escapeHtml(c.heading) + "</span>" +
        '<span class="meta">' + escapeHtml(c.path) + " · #" + escapeHtml(c.anchor) + " · " + escapeHtml(c.chunk_id) + "</span>" +
      "</button>"
    );
  }

  function processHtml(snap) {
    const rw = snap.lastRewrite;
    const topic = snap.lastSameTopic == null ? "—" : (snap.lastSameTopic ? "是（可并入上轮块）" : "否（不携带上轮块）");
    const chunks = snap.lastRoundChunks || [];
    const chunkHtml = chunks.length
      ? chunks.map(citeButton).join("")
      : '<div class="val">发送问题后展示本轮重排块</div>';
    return (
      "<h2>本轮过程</h2>" +
      '<div class="qa-kv">' +
        "<div><b>阶段</b><div class=\"val\">" + escapeHtml(STAGE_LABEL[snap.stage] || (snap.busy ? "处理中…" : "空闲")) + "</div></div>" +
        "<div><b>本轮原句</b><div class=\"val\">" + escapeHtml(snap.lastOriginal || "—") + "</div></div>" +
        "<div><b>改写句</b><div class=\"val\">" + escapeHtml((rw && rw.query) || "—") + "</div></div>" +
        "<div><b>是否同一主题</b><div class=\"val\">" + escapeHtml(topic) + "</div></div>" +
        "<div><b>检索查询</b><div class=\"val\">" + escapeHtml(snap.lastOriginal ? (snap.lastOriginal + " + " + ((rw && rw.query) || "")) : "—") + "</div></div>" +
        "<div><b>召回 / 重排</b><div class=\"val\">mock 合并后 " + escapeHtml(String(snap.lastRecalled || 0)) + " 条（K=" + escapeHtml(String(snap.config.recallK)) + "），进生成 " + escapeHtml(String(chunks.length)) + " 块（n=" + escapeHtml(String(snap.config.rerankN)) + "）</div></div>" +
        "<div><b>重排 Top 块</b>" + chunkHtml + "</div>" +
      "</div>"
    );
  }

  function messageHtml(m, snap) {
    if (m.role === "user") {
      return (
        '<div class="qa-row user">' +
          '<div class="qa-avatar">我</div>' +
          '<div class="qa-bubble"><div class="qa-body">' + escapeHtml(m.text) + "</div></div>" +
        "</div>"
      );
    }
    const cites = m.citations || [];
    const open = Boolean(snap.citationsOpen[m.id]);
    const pending = m.pending;
    const flags = [];
    if (m.refused) flags.push('<span class="qa-tag warn">文档未写</span>');
    if (m.conflict) flags.push('<span class="qa-tag demo">冲突并列</span>');
    if (m.kind === "gen_fail") flags.push('<span class="qa-tag warn">出处不是回答</span>');
    let body;
    if (pending && !m.text) {
      body = '<div class="qa-stage">' + escapeHtml(STAGE_LABEL[m.stage] || "处理中…") + "</div>";
    } else if (pending && m.text) {
      body = '<div class="qa-stage">' + escapeHtml(STAGE_LABEL[m.stage] || "生成中…") + '</div><div class="qa-body">' + escapeHtml(m.text) + "</div>";
    } else {
      body = '<div class="qa-body">' + escapeHtml(m.text) + "</div>";
    }
    const citeBlock = cites.length
      ? (
          '<div class="qa-actions">' +
            '<button class="kb-btn" type="button" data-toggle-cite="' + escapeHtml(m.id) + '">' +
              (open ? "收起出处" : (cites.length + " 条出处")) +
            "</button>" +
            (m.role === "assistant" && m.text && !pending
              ? '<button class="kb-btn" type="button" data-copy="' + escapeHtml(m.id) + '">复制回答</button>'
              : "") +
          "</div>" +
          (open ? '<div class="qa-cite-list">' + cites.map(citeButton).join("") + "</div>" : "")
        )
      : (m.role === "assistant" && m.text && !pending
          ? '<div class="qa-actions"><button class="kb-btn" type="button" data-copy="' + escapeHtml(m.id) + '">复制回答</button></div>'
          : "");
    const cls = ["qa-bubble"];
    if (m.role === "system") cls.push("system");
    if (m.refused) cls.push("refuse");
    if (m.conflict) cls.push("conflict");
    return (
      '<div class="qa-row">' +
        '<div class="qa-avatar">' + (m.role === "system" ? "!" : "答") + "</div>" +
        '<div class="' + cls.join(" ") + '">' +
          (flags.length ? '<div class="qa-flags">' + flags.join("") + "</div>" : "") +
          body +
          citeBlock +
        "</div>" +
      "</div>"
    );
  }

  function emptyHtml() {
    const chips = window.KbQaMockData.SUGGESTIONS.map((q) => {
      return '<button class="qa-chip" type="button" data-suggest="' + escapeHtml(q) + '">' + escapeHtml(q) + "</button>";
    }).join("");
    return (
      '<div class="qa-empty">' +
        "<h2>知识问答</h2>" +
        "<p>用口语问 Hayyo 现行规则。回答只根据 brief 的 chunk:default，不是需求合同。权威仍是各功能 PRD.md。左侧可建多条对话，刷新后仍恢复。</p>" +
        '<div class="qa-chips">' + chips + "</div>" +
      "</div>"
    );
  }

  function lockedRows() {
    const L = window.KbQaMockData.LOCKED;
    const rows = [
      ["Embedding", L.embeddingModel + " / " + L.embeddingDim + " 维"],
      ["重排", L.rerankModel],
      ["改写 / 回答", L.rewriteModel + " / " + L.answerModel],
      ["思考模式", "关闭（thinking = disabled）"],
      ["Collection", L.collections.join(" / ")],
      ["切块口径", L.chunkPolicy],
      ["DashScope Key", L.dashscopeKey + "（无明文）"],
      ["DeepSeek Key", L.deepseekKey + "（无明文）"]
    ];
    return rows.map((r) => "<div class=\"cfg-row\"><span>" + escapeHtml(r[0]) + "</span><b>" + escapeHtml(r[1]) + "</b></div>").join("");
  }

  window.KbQaProto = {
    init: function (opts) {
      const layout = opts.layout === "b" ? "b" : "a";
      const els = {
        app: document.querySelector(".app"),
        tabs: document.querySelectorAll(".tab"),
        qaWs: document.getElementById("qaWorkspace"),
        kbWs: document.getElementById("kbWorkspace"),
        graph: document.getElementById("graphPlaceholder"),
        messages: document.getElementById("qaMessages"),
        process: document.getElementById("qaProcess"),
        debug: document.getElementById("qaDebug"),
        input: document.getElementById("qaInput"),
        send: document.getElementById("qaSend"),
        health: document.getElementById("healthDot"),
        scenario: document.getElementById("scenarioSelect"),
        cfgRoot: document.getElementById("cfgRoot"),
        cfgBackdrop: document.getElementById("cfgBackdrop"),
        reindexRoot: document.getElementById("reindexRoot"),
        kbList: document.getElementById("kbList"),
        kbMeta: document.getElementById("kbMeta"),
        kbArticle: document.getElementById("kbArticle"),
        kbToc: document.getElementById("kbToc"),
        kbSearch: document.getElementById("kbSearch"),
        kbFail: document.getElementById("kbFail"),
        convList: document.getElementById("qaConvList")
      };

      let view = "qa";
      let snap = null;
      let lastArticleSrc = "";
      const citeIndex = {};

      const core = window.KbQaCore.create(function (next) {
        snap = next;
        render();
      });
      snap = core.snapshot();

      function setView(target) {
        view = target;
        const qa = target === "qa";
        const kb = target === "kb";
        const graph = target === "admin" || target === "client";
        els.app.classList.toggle("qa-active", qa);
        els.app.classList.toggle("kb-active", kb);
        els.app.classList.toggle("graph-active", graph);
        if (els.qaWs) {
          els.qaWs.hidden = !qa;
          els.qaWs.inert = !qa;
        }
        if (els.kbWs) {
          els.kbWs.hidden = !kb;
          els.kbWs.inert = !kb;
        }
        if (els.graph) {
          els.graph.hidden = !graph;
          els.graph.inert = !graph;
        }
        els.tabs.forEach((t) => t.classList.toggle("active", t.getAttribute("data-view") === target));
        if (kb) renderKbList();
      }

      function renderHealth() {
        if (!els.health) return;
        const h = snap.health;
        const ok = !h || h.ok;
        els.health.className = "health-dot" + (ok ? "" : " bad");
        els.health.innerHTML = "<i></i><span>" + escapeHtml((h && h.message) || "索引就绪 · Key 已配置") + "</span>";
      }

      function renderMessages() {
        if (!els.messages) return;
        const stick = els.messages.scrollHeight - els.messages.scrollTop - els.messages.clientHeight < 90;
        if (!snap.messages.length) {
          els.messages.innerHTML = emptyHtml();
        } else {
          els.messages.innerHTML = snap.messages.map((m) => messageHtml(m, snap)).join("");
        }
        if (stick || snap.busy) els.messages.scrollTop = els.messages.scrollHeight;
        (snap.lastRoundChunks || []).concat(
          snap.messages.reduce((acc, m) => acc.concat(m.citations || []), [])
        ).forEach((c) => { citeIndex[c.chunk_id] = c; });
      }

      function renderProcess() {
        const html = processHtml(snap);
        if (els.process) els.process.innerHTML = html;
        if (els.debug) {
          const box = els.debug.querySelector(".qa-debug-box");
          if (box) box.innerHTML = html;
        }
      }

      function renderScenario() {
        if (!els.scenario) return;
        if (els.scenario.value !== snap.scenario) els.scenario.value = snap.scenario;
      }

      function renderConvList() {
        if (!els.convList) return;
        const items = snap.conversations || [];
        els.convList.innerHTML = items.map((c) => {
          const active = c.id === snap.activeId ? " active" : "";
          return (
            '<div class="qa-conv-item' + active + '" data-conv="' + escapeHtml(c.id) + '" role="button" tabindex="0">' +
              '<span class="qa-conv-title">' + escapeHtml(c.title || "新对话") + "</span>" +
              '<button class="qa-conv-del" type="button" data-del-conv="' + escapeHtml(c.id) + '" title="删除">删除</button>' +
            "</div>"
          );
        }).join("");
      }

      function busyGuard() {
        if (!snap.busy) return false;
        toast("本轮生成中，请稍后再切换");
        return true;
      }

      function render() {
        renderHealth();
        renderConvList();
        renderMessages();
        renderProcess();
        renderScenario();
        if (els.send) els.send.disabled = snap.busy;
        if (els.input) els.input.disabled = snap.busy;
      }

      function submit(text) {
        const q = String(text || (els.input && els.input.value) || "").trim();
        if (!q) return;
        if (els.input) els.input.value = "";
        core.send(q);
      }

      async function openCitation(cite) {
        if (!cite) return;
        setView("kb");
        await openDocument(cite.path, { hash: cite.anchor, headingText: cite.heading });
      }

      function renderKbList() {
        if (!els.kbList) return;
        els.kbList.innerHTML = window.KbQaMockData.DOCS.map((d) => {
          return (
            '<button class="kb-list-item" type="button" data-path="' + escapeHtml(d.path) + '">' +
              '<span class="kb-list-name">' + escapeHtml(d.name) + "</span>" +
              '<span class="kb-list-path">' + escapeHtml(d.path) + "</span>" +
            "</button>"
          );
        }).join("");
      }

      function renderToc(article) {
        if (!els.kbToc) return;
        const hs = article.querySelectorAll("h2, h3");
        els.kbToc.innerHTML = [...hs].slice(0, 40).map((h) => {
          const id = h.id || "";
          return '<a href="#' + escapeHtml(id) + '" data-toc="' + escapeHtml(id) + '">' + escapeHtml(h.getAttribute("data-heading") || h.textContent) + "</a>";
        }).join("") || '<p class="kb-hint">本文无目录</p>';
      }

      async function openDocument(docPath, options) {
        const opts = options || {};
        if (els.kbFail) els.kbFail.hidden = true;
        if (els.kbMeta) {
          els.kbMeta.innerHTML = "<span>打开 <code>" + escapeHtml(docPath) + "</code></span>";
        }
        els.kbList && els.kbList.querySelectorAll("[data-path]").forEach((btn) => {
          btn.classList.toggle("active", btn.getAttribute("data-path") === docPath);
        });
        try {
          const res = await fetch("/" + docPath.replace(/^\/+/, ""));
          if (!res.ok) throw new Error("无法读取 " + docPath + "（HTTP " + res.status + "）");
          const src = await res.text();
          lastArticleSrc = src;
          const html = window.KBMarkdown.parse(src);
          els.kbArticle.innerHTML = html;
          renderToc(els.kbArticle);
          applyKbSearch();
          const hash = opts.hash || "";
          if (hash) {
            const el = document.getElementById(hash);
            if (el) el.scrollIntoView({ block: "start" });
          } else if (opts.headingText) {
            const h = [...els.kbArticle.querySelectorAll("h1,h2,h3")].find((n) => {
              const t = n.getAttribute("data-heading") || n.textContent.trim();
              return t === opts.headingText || t.indexOf(opts.headingText) >= 0;
            });
            if (h) h.scrollIntoView({ block: "start" });
          } else {
            els.kbArticle.scrollTop = 0;
          }
        } catch (err) {
          lastArticleSrc = "";
          els.kbArticle.innerHTML = "";
          if (els.kbFail) {
            els.kbFail.hidden = false;
            els.kbFail.textContent = err.message || String(err);
          }
        }
      }

      function applyKbSearch() {
        const q = (els.kbSearch && els.kbSearch.value || "").trim();
        if (!lastArticleSrc || !els.kbArticle) return;
        if (!q) return;
        const walk = document.createTreeWalker(els.kbArticle, NodeFilter.SHOW_TEXT);
        let node;
        const hits = [];
        while ((node = walk.nextNode())) {
          if (node.nodeValue && node.nodeValue.indexOf(q) >= 0) hits.push(node);
        }
        hits.slice(0, 20).forEach((textNode) => {
          const i = textNode.nodeValue.indexOf(q);
          if (i < 0) return;
          const mark = document.createElement("mark");
          mark.className = "hl-mark";
          const rest = textNode.splitText(i);
          rest.splitText(q.length);
          mark.appendChild(rest.cloneNode(true));
          rest.parentNode.replaceChild(mark, rest);
        });
        const first = els.kbArticle.querySelector("mark");
        if (first) first.scrollIntoView({ block: "center" });
      }

      function renderConfigForm() {
        const cfg = snap.config;
        const body =
          '<div class="cfg-head"><h2>本机配置</h2><button class="kb-btn" type="button" data-close-cfg>关闭</button></div>' +
          '<p class="kb-hint">锁死项只读。可改项保存后用于后续提问。Key 无明文。本页只覆盖问答链路。</p>' +
          '<div class="cfg-grid">' +
            '<div class="cfg-card"><h3>只读</h3>' + lockedRows() + "</div>" +
            '<div class="cfg-card"><h3>可改</h3>' +
              '<label>召回 K</label><input id="cfgK" type="number" min="1" max="200" value="' + escapeHtml(String(cfg.recallK)) + '">' +
              '<label>重排 n</label><input id="cfgN" type="number" min="1" max="50" value="' + escapeHtml(String(cfg.rerankN)) + '">' +
              '<label>历史轮数</label><input id="cfgTurns" type="number" min="1" max="20" value="' + escapeHtml(String(cfg.historyTurns)) + '">' +
              '<label>temperature</label><input id="cfgTemp" type="number" min="0" max="2" step="0.1" value="' + escapeHtml(String(cfg.temperature)) + '">' +
            "</div>" +
            '<div class="cfg-card wide"><h3>系统 Prompt</h3><textarea id="cfgSys">' + escapeHtml(cfg.systemPrompt) + "</textarea></div>" +
            '<div class="cfg-card wide"><h3>改写 Prompt</h3><textarea id="cfgRw">' + escapeHtml(cfg.rewritePrompt) + "</textarea></div>" +
          "</div>" +
          '<div class="cfg-actions">' +
            '<button class="qa-send" type="button" data-save-cfg>保存可改项</button>' +
            '<button class="kb-btn" type="button" data-reset-cfg>恢复默认</button>' +
          "</div>";
        if (layout === "a") {
          els.cfgRoot.innerHTML = body;
        } else {
          els.cfgRoot.innerHTML = '<div class="qa-overlay-card">' + body + "</div>";
        }
      }

      function openConfig() {
        renderConfigForm();
        if (layout === "a") {
          if (els.cfgBackdrop) els.cfgBackdrop.hidden = false;
          els.cfgRoot.classList.add("open");
          els.cfgRoot.hidden = false;
        } else {
          els.cfgRoot.hidden = false;
        }
      }

      function closeConfig() {
        if (layout === "a") {
          els.cfgRoot.classList.remove("open");
          if (els.cfgBackdrop) els.cfgBackdrop.hidden = true;
        }
        els.cfgRoot.hidden = true;
      }

      function saveConfigFromForm() {
        const num = (id, fallback) => {
          const el = document.getElementById(id);
          const v = el ? Number(el.value) : fallback;
          return Number.isFinite(v) ? v : fallback;
        };
        const val = (id) => {
          const el = document.getElementById(id);
          return el ? el.value : "";
        };
        core.setConfig({
          recallK: num("cfgK", 64),
          rerankN: num("cfgN", 8),
          historyTurns: num("cfgTurns", 5),
          temperature: num("cfgTemp", 0.2),
          systemPrompt: val("cfgSys"),
          rewritePrompt: val("cfgRw")
        });
        toast("已保存，将用于后续提问");
        closeConfig();
      }

      function openReindex(result) {
        const rows = []
          .concat(result.created || [])
          .concat(result.added || [])
          .concat(result.deleted || []);
        const fail = result.failed || [];
        const tr = (r) =>
          "<tr><td>" + escapeHtml(r.action) + "</td><td>" + escapeHtml(r.path) + "</td><td>" + escapeHtml(r.chunk_id) +
          "</td><td>" + escapeHtml(r.old_hash || "—") + "</td><td>" + escapeHtml(r.new_hash || "—") + "</td></tr>";
        const ftr = (r) =>
          "<tr><td>失败</td><td>" + escapeHtml(r.path) + "</td><td>" + escapeHtml(r.chunk_id) +
          '</td><td colspan="2">' + escapeHtml(r.reason) + "</td></tr>";
        els.reindexRoot.innerHTML =
          '<div class="qa-modal">' +
            '<div class="modal-head"><h2>重建索引 · 变更清单</h2><button class="kb-btn" type="button" data-close-reindex>关闭</button></div>' +
            "<p class=\"kb-hint\">扫描 " + escapeHtml(String(result.scanned)) +
            " 个 brief。增量对账：增 " + escapeHtml(String((result.created || []).length)) +
            " / 改 " + escapeHtml(String((result.added || []).length)) +
            " / 删 " + escapeHtml(String((result.deleted || []).length)) +
            " / 失败 " + escapeHtml(String(fail.length)) + "。不另存全文快照。</p>" +
            '<table class="reindex-table"><thead><tr><th>动作</th><th>path</th><th>chunk_id</th><th>旧 hash</th><th>新 hash</th></tr></thead><tbody>' +
            rows.map(tr).concat(fail.map(ftr)).join("") +
            "</tbody></table>" +
            '<div class="cfg-actions"><label class="kb-hint"><input type="checkbox" disabled> 强制全量（仅换 embedding 型号/维度或库损坏；配置页不能改维度）</label></div>' +
          "</div>";
        els.reindexRoot.hidden = false;
      }

      document.addEventListener("click", (ev) => {
        const tab = ev.target.closest(".tab");
        if (tab) {
          setView(tab.getAttribute("data-view"));
          return;
        }
        if (ev.target.closest("[data-back-qa]")) {
          setView("qa");
          return;
        }
        const sug = ev.target.closest("[data-suggest]");
        if (sug) { submit(sug.getAttribute("data-suggest")); return; }
        const cite = ev.target.closest("[data-cite]");
        if (cite) { openCitation(citeIndex[cite.getAttribute("data-cite")]); return; }
        const tog = ev.target.closest("[data-toggle-cite]");
        if (tog) { core.toggleCitations(tog.getAttribute("data-toggle-cite")); return; }
        const cp = ev.target.closest("[data-copy]");
        if (cp) {
          const msg = snap.messages.find((m) => m.id === cp.getAttribute("data-copy"));
          if (msg) copyText(msg.text);
          return;
        }
        if (ev.target.closest("[data-open-cfg]")) { openConfig(); return; }
        if (ev.target.closest("[data-close-cfg]") || ev.target === els.cfgBackdrop || (layout === "b" && ev.target === els.cfgRoot)) {
          closeConfig();
          return;
        }
        if (ev.target.closest("[data-save-cfg]")) { saveConfigFromForm(); return; }
        if (ev.target.closest("[data-reset-cfg]")) { core.resetConfig(); renderConfigForm(); toast("已恢复默认"); return; }
        if (ev.target.closest("[data-new-conv]")) {
          if (busyGuard()) return;
          core.createConversation();
          if (els.input) els.input.focus();
          return;
        }
        const del = ev.target.closest("[data-del-conv]");
        if (del) {
          ev.preventDefault();
          ev.stopPropagation();
          if (busyGuard()) return;
          if (!window.confirm("删除这条对话？删除后刷新也不能恢复。")) return;
          core.deleteConversation(del.getAttribute("data-del-conv"));
          return;
        }
        const convBtn = ev.target.closest("[data-conv]");
        if (convBtn) {
          if (busyGuard()) return;
          core.switchConversation(convBtn.getAttribute("data-conv"));
          return;
        }
        if (ev.target.closest("[data-clear]")) {
          if (busyGuard()) return;
          core.clear();
          return;
        }
        if (ev.target.closest("[data-reindex]")) {
          ev.target.closest("[data-reindex]").disabled = true;
          core.reindex().then((r) => { openReindex(r); }).finally(() => {
            const btn = document.querySelector("[data-reindex]");
            if (btn) btn.disabled = false;
          });
          return;
        }
        if (ev.target.closest("[data-close-reindex]") || ev.target === els.reindexRoot) {
          if (ev.target === els.reindexRoot || ev.target.closest("[data-close-reindex]")) els.reindexRoot.hidden = true;
          return;
        }
        const docBtn = ev.target.closest("#kbList [data-path]");
        if (docBtn) { openDocument(docBtn.getAttribute("data-path")); return; }
        const toc = ev.target.closest("[data-toc]");
        if (toc) {
          ev.preventDefault();
          const el = document.getElementById(toc.getAttribute("data-toc"));
          if (el) el.scrollIntoView({ block: "start" });
        }
      });

      if (els.scenario) {
        els.scenario.innerHTML = window.KbQaMockData.SCENARIOS.map((s) => {
          return '<option value="' + escapeHtml(s.id) + '">' + escapeHtml(s.label) + "</option>";
        }).join("");
        els.scenario.value = snap.scenario;
        els.scenario.addEventListener("change", () => {
          core.setScenario(els.scenario.value);
          core.refreshHealth();
        });
      }

      if (els.send) els.send.addEventListener("click", () => submit());
      if (els.input) {
        els.input.addEventListener("keydown", (ev) => {
          if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            submit();
          }
        });
      }

      let searchTimer = null;
      if (els.kbSearch) {
        els.kbSearch.addEventListener("input", () => {
          clearTimeout(searchTimer);
          searchTimer = setTimeout(() => {
            if (view === "kb" && lastArticleSrc && window.KBMarkdown) {
              els.kbArticle.innerHTML = window.KBMarkdown.parse(lastArticleSrc);
              renderToc(els.kbArticle);
              applyKbSearch();
            }
          }, 120);
        });
      }

      window.addEventListener("keydown", (ev) => {
        if (ev.key !== "/") return;
        if (isTextField(document.activeElement)) return;
        ev.preventDefault();
        if (view === "qa" && els.input) els.input.focus();
        else if (view === "kb" && els.kbSearch) els.kbSearch.focus();
      });

      renderKbList();
      setView("qa");
      render();
      core.refreshHealth();
    }
  };
})();
