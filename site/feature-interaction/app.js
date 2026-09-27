/**
 * 功能交互关系图：点选、筛选、拖拽、缩放。
 */
(function () {
  const DATA = window.FEATURE_DATA;
  const NODE_W = 148;
  const NODE_H = 40;
  const DOMAINS = ["房间社交", "资金商业", "身份成长", "账号触达"];
  const DOMAIN_COLOR = {
    "房间社交": "#6ea8fe",
    "资金商业": "#7dcea0",
    "身份成长": "#e2b657",
    "账号触达": "#c4a6ff",
    "后台": "#9aa0ab"
  };
  const DOMAIN_VAR = {
    "房间社交": "--social",
    "资金商业": "--money",
    "身份成长": "--growth",
    "账号触达": "--reach",
    "后台": "--admin"
  };
  // 对照配色时读 :root；无主题时与上面的原色一致
  function domainColor(name) {
    const key = DOMAIN_VAR[name];
    if (key) {
      const live = getComputedStyle(document.documentElement).getPropertyValue(key).trim();
      if (live) return live;
    }
    return DOMAIN_COLOR[name] || "#9aa0ab";
  }

  const state = {
    view: "admin",
    panel: "graph",
    selectedId: null,
    domainFilter: new Set(DOMAINS.concat(["后台"])),
    query: "",
    camera: { x: 24, y: 36, k: 1 },
    dragging: null,
    panning: null,
    positions: {},
    hoverId: null
  };

  const els = {
    graph: document.getElementById("graph"),
    stats: document.getElementById("stats"),
    detail: document.getElementById("detailBody"),
    filters: document.getElementById("filters"),
    search: document.getElementById("search"),
    tabs: document.querySelectorAll(".tab")
  };

  const featureMap = Object.fromEntries(DATA.features.map((f) => [f.id, f]));
  const adminMap = Object.fromEntries(DATA.adminNodes.map((f) => [f.id, f]));

  function allNodes() {
    return DATA.features.concat(DATA.adminNodes);
  }

  function nodeOf(id) {
    return featureMap[id] || adminMap[id];
  }

  function isAdmin(id) {
    return Boolean(adminMap[id]);
  }

  function currentEdges() {
    return state.view === "admin" ? DATA.adminEdges : DATA.clientEdges;
  }

  function visibleIds() {
    const q = state.query.trim().toLowerCase();
    const ids = new Set();
    const pool = state.view === "admin"
      ? DATA.features.concat(DATA.adminNodes)
      : DATA.features.slice();
    pool.forEach((n) => {
      if (!state.domainFilter.has(n.domain)) return;
      if (q) {
        const hay = [n.name, n.id, n.admin || "", n.kind || ""].join(" ").toLowerCase();
        if (!hay.includes(q)) return;
      }
      ids.add(n.id);
    });
    const matched = new Set(ids);
    if (q) {
      currentEdges().forEach((e) => {
        if (matched.has(e.from)) ids.add(e.to);
        if (matched.has(e.to)) ids.add(e.from);
      });
    }
    return ids;
  }

  function connectedIds(id) {
    const set = new Set([id]);
    currentEdges().forEach((e) => {
      if (e.from === id) set.add(e.to);
      if (e.to === id) set.add(e.from);
    });
    return set;
  }

  function layoutAdmin() {
    const leftX = 40;
    const rightX = 560;
    DATA.features.forEach((n, i) => {
      state.positions[n.id] = { x: leftX, y: 28 + i * 48 };
    });
    DATA.adminNodes.forEach((n, i) => {
      state.positions[n.id] = { x: rightX, y: 28 + i * 42 };
    });
  }

  function layoutClient() {
    const byDomain = {};
    DOMAINS.forEach((d) => { byDomain[d] = []; });
    DATA.features.forEach((f) => {
      byDomain[f.domain].push(f);
    });
    DOMAINS.forEach((d, col) => {
      byDomain[d].forEach((n, row) => {
        state.positions[n.id] = {
          x: 36 + col * 250,
          y: 42 + row * 64
        };
      });
    });
  }

  function applyLayout() {
    if (state.view === "admin") layoutAdmin();
    else layoutClient();
  }

  function edgePath(fromPos, toPos) {
    const x1 = fromPos.x + NODE_W;
    const y1 = fromPos.y + NODE_H / 2;
    const x2 = toPos.x;
    const y2 = toPos.y + NODE_H / 2;
    const mid = (x1 + x2) / 2;
    return `M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`;
  }

  function cssVar(name, fallback) {
    const live = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return live || fallback;
  }

  function redrawTheme() {
    renderFilters();
    renderGraph();
    renderDetail();
  }

  function renderGraph() {
    const vis = visibleIds();
    const edges = currentEdges().filter((e) => vis.has(e.from) && vis.has(e.to));
    const focus = state.selectedId ? connectedIds(state.selectedId) : null;
    const nodes = allNodes().filter((n) => vis.has(n.id) && state.positions[n.id]);

    const parts = [
      `<defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="${escapeXml(cssVar("--edge", "#4a5160"))}"></path>
        </marker>
        <marker id="arrow-active" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="${escapeXml(cssVar("--accent", "#6ea8fe"))}"></path>
        </marker>
      </defs>`
    ];

    if (state.view === "client") {
      DOMAINS.forEach((d, i) => {
        parts.push(`<text class="cluster-label" x="${36 + i * 250}" y="18">${d}</text>`);
      });
    } else {
      parts.push('<text class="cluster-label" x="40" y="16">客户端</text>');
      parts.push('<text class="cluster-label" x="560" y="16">运营后台</text>');
    }

    edges.forEach((e) => {
      const a = state.positions[e.from];
      const b = state.positions[e.to];
      if (!a || !b) return;
      const key = edgeKey(e);
      const active = focus ? (focus.has(e.from) && focus.has(e.to) && (e.from === state.selectedId || e.to === state.selectedId)) : false;
      const dimmed = focus && !active;
      const cls = `edge${active ? " active" : ""}${dimmed ? " dimmed" : ""}`;
      const marker = active ? "url(#arrow-active)" : "url(#arrow)";
      const labelX = (a.x + NODE_W + b.x) / 2;
      const labelY = (a.y + b.y) / 2 + NODE_H / 2 - 6;
      parts.push(`<path class="${cls}" data-edge="${escapeXml(key)}" d="${edgePath(a, b)}" style="marker-end:${marker}"></path>`);
      parts.push(`<text class="edge-label${active ? " active" : ""}${dimmed ? " dimmed" : ""}" data-edge-label="${escapeXml(key)}" x="${labelX}" y="${labelY}" text-anchor="middle">${escapeXml(e.label)}</text>`);
    });

    nodes.forEach((n) => {
      const p = state.positions[n.id];
      const unmapped = n.admin === "未挂指针";
      const cls = [
        "node",
        isAdmin(n.id) ? "admin" : "",
        n.kind === "pure" ? "pure" : "",
        unmapped ? "unmapped" : "",
        state.selectedId === n.id ? "selected" : "",
        focus && !focus.has(n.id) ? "dimmed" : ""
      ].filter(Boolean).join(" ");
      const color = domainColor(n.domain);
      const sub = isAdmin(n.id) ? (n.kind === "pure" ? "纯后台" : "后台章节") : n.domain;
      parts.push(`
        <g class="${cls}" data-id="${n.id}" transform="translate(${p.x},${p.y})">
          <rect width="${NODE_W}" height="${NODE_H}" rx="8"></rect>
          <circle cx="12" cy="20" r="4" fill="${color}"></circle>
          <text x="22" y="18">${escapeXml(n.name)}</text>
          <text class="meta" x="22" y="32">${escapeXml(sub)}</text>
        </g>
      `);
    });

    const { x, y, k } = state.camera;
    els.graph.innerHTML = `<g id="scene" transform="translate(${x},${y}) scale(${k})">${parts.join("")}</g>`;
    bindNodeEvents();
    renderStats(vis, edges);
  }

  function updateCamera() {
    const scene = document.getElementById("scene");
    if (scene) scene.setAttribute("transform", `translate(${state.camera.x},${state.camera.y}) scale(${state.camera.k})`);
  }

  function edgeKey(e) {
    return `${e.from}->${e.to}:${e.label}`;
  }

  function updateDraggedNode(id) {
    const p = state.positions[id];
    const g = els.graph.querySelector(`.node[data-id="${id}"]`);
    if (g) g.setAttribute("transform", `translate(${p.x},${p.y})`);
    const vis = visibleIds();
    currentEdges().forEach((e) => {
      if (e.from !== id && e.to !== id) return;
      if (!vis.has(e.from) || !vis.has(e.to)) return;
      const a = state.positions[e.from];
      const b = state.positions[e.to];
      const key = edgeKey(e);
      const paths = els.graph.querySelectorAll("path[data-edge]");
      const labels = els.graph.querySelectorAll("[data-edge-label]");
      let path = null;
      let label = null;
      paths.forEach((el) => { if (el.getAttribute("data-edge") === key) path = el; });
      labels.forEach((el) => { if (el.getAttribute("data-edge-label") === key) label = el; });
      if (path) path.setAttribute("d", edgePath(a, b));
      if (label) {
        label.setAttribute("x", String((a.x + NODE_W + b.x) / 2));
        label.setAttribute("y", String((a.y + b.y) / 2 + NODE_H / 2 - 6));
      }
    });
  }

  function escapeXml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderStats(vis, edges) {
    const clientCount = DATA.features.filter((f) => vis.has(f.id)).length;
    const unmapped = DATA.features.filter((f) => vis.has(f.id) && f.admin === "未挂指针").length;
    els.stats.innerHTML = `
      <span>可见节点 <b>${vis.size}</b></span>
      <span>关系 <b>${edges.length}</b></span>
      <span>客户端 <b>${clientCount}</b></span>
      <span>未挂指针 <b>${unmapped}</b></span>
    `;
  }

  function renderFilters() {
    const items = DOMAINS.concat(state.view === "admin" ? ["后台"] : []);
    els.filters.innerHTML = items.map((d) => {
      const active = state.domainFilter.has(d);
      return `<button class="chip${active ? " active" : " muted"}" data-domain="${d}">
        <span class="dot" style="background:${domainColor(d)}"></span>${d}
      </button>`;
    }).join("");
  }

  function renderDetail() {
    const id = state.selectedId;
    if (!id) {
      els.detail.innerHTML = `<p class="empty">点击图中节点查看进出关系。可拖拽节点、滚轮缩放、空白处拖动画布。Esc 取消选中。</p>
        <div class="legend">
          <span><i style="background:${domainColor("房间社交")}"></i>房间社交</span>
          <span><i style="background:${domainColor("资金商业")}"></i>资金商业</span>
          <span><i style="background:${domainColor("身份成长")}"></i>身份成长</span>
          <span><i style="background:${domainColor("账号触达")}"></i>账号触达</span>
          <span><i style="background:${domainColor("后台")}"></i>后台</span>
        </div>`;
      return;
    }
    const n = nodeOf(id);
    const edges = currentEdges();
    const outs = edges.filter((e) => e.from === id);
    const ins = edges.filter((e) => e.to === id);
    const prd = n.prd
      ? `<a class="prd-link" href="${n.prd}">打开 PRD</a>`
      : "";
    els.detail.innerHTML = `
      <div class="kv">
        <div><dt>功能</dt><dd>${escapeXml(n.name)}</dd></div>
        <div><dt>域</dt><dd>${escapeXml(n.domain)}</dd></div>
        <div><dt>${isAdmin(id) ? "类型" : "关联后台"}</dt><dd>${escapeXml(n.admin || (n.kind === "pure" ? "纯后台，不挂客户端" : "后台章节"))}</dd></div>
        <div><dt>文档</dt><dd>${prd || "—"}</dd></div>
      </div>
      <h2>指出（${outs.length}）</h2>
      <div class="edge-list">${renderEdgeItems(outs, "to") || '<p class="empty">无</p>'}</div>
      <h2 style="margin-top:14px">指入（${ins.length}）</h2>
      <div class="edge-list">${renderEdgeItems(ins, "from") || '<p class="empty">无</p>'}</div>
    `;
    els.detail.querySelectorAll("[data-jump]").forEach((btn) => {
      btn.addEventListener("click", () => selectNode(btn.getAttribute("data-jump")));
    });
  }

  function renderEdgeItems(list, key) {
    return list.map((e) => {
      const other = nodeOf(e[key]);
      return `<button class="edge-item" data-jump="${e[key]}">
        <span class="dir">${key === "to" ? "指向" : "来自"}</span>
        <span class="name">${escapeXml(other ? other.name : e[key])}</span>
        <span class="why">${escapeXml(e.label)} · ${escapeXml(e.evidence)}</span>
      </button>`;
    }).join("");
  }

  function selectNode(id) {
    state.selectedId = id;
    if (state.panel === "graph") {
      renderGraph();
      renderDetail();
    }
  }

  /**
   * 切换关系图 / 知识库。preserveSelection 用于从节点打开文档或「查看关系」，
   * 不套用两关系图 Tab 互切时的清空选中与复位镜头。
   */
  function setView(target, options) {
    const preserve = options && options.preserveSelection;
    const appEl = document.querySelector(".app");
    const kbWs = document.getElementById("kbWorkspace");
    const qaWs = document.getElementById("qaWorkspace");

    if (target === "qa") {
      if (!preserve) state.selectedId = null;
      state.panel = "qa";
      appEl.classList.add("qa-active");
      appEl.classList.remove("kb-active");
      if (kbWs) kbWs.hidden = true;
      if (qaWs) {
        qaWs.hidden = false;
        qaWs.inert = false;
      }
      els.tabs.forEach((t) => t.classList.toggle("active", t.getAttribute("data-view") === "qa"));
      if (window.HayyoQA && typeof window.HayyoQA.onEnter === "function") window.HayyoQA.onEnter();
      return;
    }

    appEl.classList.remove("qa-active");
    if (qaWs) {
      qaWs.hidden = true;
      qaWs.inert = true;
    }
    if (window.HayyoQA && typeof window.HayyoQA.closeOverlay === "function") {
      window.HayyoQA.closeOverlay();
    }

    if (target === "kb") {
      if (!preserve) state.selectedId = null;
      state.panel = "kb";
      appEl.classList.add("kb-active");
      if (kbWs) kbWs.hidden = false;
      els.tabs.forEach((t) => t.classList.toggle("active", t.getAttribute("data-view") === "kb"));
      if (window.KB) window.KB.onEnter();
      return;
    }

    state.panel = "graph";
    state.view = target;
    appEl.classList.remove("kb-active");
    if (kbWs) kbWs.hidden = true;
    els.tabs.forEach((t) => t.classList.toggle("active", t.getAttribute("data-view") === target));
    if (!preserve) {
      state.selectedId = null;
      state.camera = { x: 24, y: 36, k: 1 };
      applyLayout();
    }
    if (state.view === "admin") state.domainFilter.add("后台");
    renderFilters();
    renderGraph();
    renderDetail();
  }

  function bindNodeEvents() {
    els.graph.querySelectorAll(".node").forEach((g) => {
      g.addEventListener("pointerdown", (ev) => {
        ev.stopPropagation();
        const id = g.getAttribute("data-id");
        const p = state.positions[id];
        state.dragging = {
          id,
          moved: false,
          startX: ev.clientX,
          startY: ev.clientY,
          origX: p.x,
          origY: p.y
        };
        g.setPointerCapture(ev.pointerId);
      });
    });
  }

  function svgPoint(ev) {
    const rect = els.graph.getBoundingClientRect();
    return {
      x: (ev.clientX - rect.left - state.camera.x) / state.camera.k,
      y: (ev.clientY - rect.top - state.camera.y) / state.camera.k
    };
  }

  els.graph.addEventListener("pointerdown", (ev) => {
    if (state.panel !== "graph") return;
    if (ev.target.closest(".node")) return;
    state.panning = { x: ev.clientX, y: ev.clientY, cx: state.camera.x, cy: state.camera.y };
    els.graph.classList.add("panning");
  });

  window.addEventListener("pointermove", (ev) => {
    if (state.panel !== "graph") return;
    if (state.dragging) {
      const dx = (ev.clientX - state.dragging.startX) / state.camera.k;
      const dy = (ev.clientY - state.dragging.startY) / state.camera.k;
      if (Math.abs(dx) + Math.abs(dy) > 3) state.dragging.moved = true;
      state.positions[state.dragging.id] = {
        x: state.dragging.origX + dx,
        y: state.dragging.origY + dy
      };
      updateDraggedNode(state.dragging.id);
      return;
    }
    if (state.panning) {
      state.camera.x = state.panning.cx + (ev.clientX - state.panning.x);
      state.camera.y = state.panning.cy + (ev.clientY - state.panning.y);
      updateCamera();
    }
  });

  window.addEventListener("pointerup", (ev) => {
    if (state.dragging) {
      if (!state.dragging.moved) selectNode(state.dragging.id);
      state.dragging = null;
    }
    if (state.panning) {
      const moved = Math.abs(ev.clientX - state.panning.x) + Math.abs(ev.clientY - state.panning.y) > 4;
      if (!moved) selectNode(null);
      state.panning = null;
      els.graph.classList.remove("panning");
    }
  });

  els.graph.addEventListener("wheel", (ev) => {
    if (state.panel !== "graph") return;
    ev.preventDefault();
    const factor = ev.deltaY < 0 ? 1.08 : 0.92;
    const next = Math.min(2.4, Math.max(0.35, state.camera.k * factor));
    const rect = els.graph.getBoundingClientRect();
    const px = ev.clientX - rect.left;
    const py = ev.clientY - rect.top;
    const wx = (px - state.camera.x) / state.camera.k;
    const wy = (py - state.camera.y) / state.camera.k;
    state.camera.k = next;
    state.camera.x = px - wx * next;
    state.camera.y = py - wy * next;
    updateCamera();
  }, { passive: false });

  els.tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const view = tab.getAttribute("data-view");
      setView(view);
    });
  });

  els.detail.addEventListener("click", (ev) => {
    const a = ev.target.closest("a.prd-link");
    if (!a) return;
    ev.preventDefault();
    setView("kb", { preserveSelection: true });
    if (window.KB) window.KB.openFromHref(a.getAttribute("href"));
  });

  els.filters.addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-domain]");
    if (!btn) return;
    const d = btn.getAttribute("data-domain");
    if (state.domainFilter.has(d)) state.domainFilter.delete(d);
    else state.domainFilter.add(d);
    if (state.domainFilter.size === 0) state.domainFilter.add(d);
    applyLayout();
    renderFilters();
    renderGraph();
  });

  els.search.addEventListener("input", () => {
    state.query = els.search.value;
    renderGraph();
  });

  document.getElementById("btnReset").addEventListener("click", () => {
    state.camera = { x: 24, y: 36, k: 1 };
    applyLayout();
    renderGraph();
  });
  document.getElementById("btnClear").addEventListener("click", () => selectNode(null));

  window.addEventListener("keydown", (ev) => {
    const kbSearch = document.getElementById("kbSearch");
    const qaInput = document.getElementById("qaInput");
    const inKb = document.querySelector(".app").classList.contains("kb-active");
    const inQa = document.querySelector(".app").classList.contains("qa-active");
    if (ev.key === "Escape" && !inKb && !inQa) selectNode(null);
    if (ev.key === "/" && document.activeElement !== els.search && document.activeElement !== kbSearch && document.activeElement !== qaInput) {
      ev.preventDefault();
      if (inKb && kbSearch) kbSearch.focus();
      else if (!inQa) els.search.focus();
    }
  });

  applyLayout();
  renderFilters();
  renderGraph();
  renderDetail();

  window.GraphApp = {
    setView: setView,
    selectNode: selectNode,
    getSelectedId: function () { return state.selectedId; },
    getLastGraphView: function () { return state.view; },
    redrawTheme: redrawTheme
  };
  redrawTheme();

  // 落地页为知识问答；等 qa.js 挂上后再切，避免 onEnter 漏跑
  function bootLanding() {
    setView("qa");
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootLanding);
  } else {
    setTimeout(bootLanding, 0);
  }
})();
