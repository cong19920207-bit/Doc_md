/**
 * 功能交互关系图：点选、筛选、拖拽、缩放。
 */
(function () {
  const DATA = window.FEATURE_DATA;
  const NODE_W = 164;
  const NODE_H = 44;
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
    hoverId: null,
    focusOnly: false,
    autoFit: true
  };

  const els = {
    graph: document.getElementById("graph"),
    stats: document.getElementById("stats"),
    detail: document.getElementById("detailBody"),
    filters: document.getElementById("filters"),
    search: document.getElementById("search"),
    tabs: document.querySelectorAll(".tab"),
    nodeList: document.getElementById("graphNodeList"),
    focus: document.getElementById("btnFocus"),
    context: document.getElementById("graphContext"),
    zoom: document.getElementById("graphZoom")
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
    const pool = state.view === "admin" ? allNodes() : DATA.features;
    const eligible = pool.filter((n) => state.domainFilter.has(n.domain));
    const allowed = new Set(eligible.map((n) => n.id));
    const ids = new Set(eligible.filter((n) => !q ||
      [n.name, n.id, n.admin || "", n.kind || ""].join(" ").toLowerCase().includes(q)).map((n) => n.id));
    const matched = new Set(ids);
    if (q) currentEdges().forEach((e) => {
      if (matched.has(e.from) && allowed.has(e.to)) ids.add(e.to);
      if (matched.has(e.to) && allowed.has(e.from)) ids.add(e.from);
    });
    if (state.focusOnly && state.selectedId) {
      const connected = connectedIds(state.selectedId);
      return new Set([...ids].filter((id) => connected.has(id)));
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
    const vis = visibleIds();
    const clients = DATA.features.filter((n) => vis.has(n.id));
    const admins = DATA.adminNodes.filter((n) => vis.has(n.id));
    const clientRows = Math.ceil(clients.length / (clients.length > 12 ? 2 : 1));
    const adminRows = Math.ceil(admins.length / (admins.length > 13 ? 2 : 1));
    const rightX = clients.length > 12 ? 600 : 440;
    clients.forEach((n, i) => {
      state.positions[n.id] = { x: 36 + Math.floor(i / clientRows) * 196, y: 32 + (i % clientRows) * 54 };
    });
    admins.forEach((n, i) => {
      state.positions[n.id] = { x: rightX + Math.floor(i / adminRows) * 196, y: 32 + (i % adminRows) * 54 };
    });
  }

  function layoutClient() {
    const byDomain = {};
    DOMAINS.forEach((d) => { byDomain[d] = []; });
    const vis = visibleIds();
    DATA.features.forEach((f) => {
      if (vis.has(f.id)) byDomain[f.domain].push(f);
    });
    DOMAINS.filter((d) => byDomain[d].length).forEach((d, col) => {
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
      DOMAINS.filter((d) => nodes.some((n) => n.domain === d)).forEach((d, i) => {
        parts.push(`<text class="cluster-label" x="${36 + i * 250}" y="18">${d}</text>`);
      });
    } else {
      const clientCount = nodes.filter((n) => !isAdmin(n.id)).length;
      parts.push('<text class="cluster-label" x="36" y="12">客户端功能</text>');
      parts.push('<text class="cluster-label" x="' + (clientCount > 12 ? 600 : 440) + '" y="12">运营后台</text>');
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
        <g class="${cls}" data-id="${n.id}" role="button" tabindex="0" aria-label="${escapeXml(n.name)}" aria-pressed="${state.selectedId === n.id}" transform="translate(${p.x},${p.y})">
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
    renderNodeList(vis);
    document.getElementById("graphEmpty").hidden = nodes.length > 0;
    els.focus.disabled = !state.selectedId;
    els.focus.setAttribute("aria-pressed", String(state.focusOnly));
    document.getElementById("btnClear").disabled = !state.selectedId;
    els.context.textContent = state.focusOnly ? (nodeOf(state.selectedId).name + " · 直接关联") : (state.query ? "搜索结果 · 含直接关联" : "全局关系");
    els.zoom.textContent = Math.round(state.camera.k * 100) + "%";
  }

  function fitGraph(ids) {
    const vis = ids || visibleIds();
    const positions = [...vis].map((id) => state.positions[id]).filter(Boolean);
    const rect = els.graph.getBoundingClientRect();
    if (!positions.length || !rect.width || !rect.height) return;
    const minX = Math.min(...positions.map((p) => p.x));
    const minY = Math.min(...positions.map((p) => p.y)) - 28;
    const width = Math.max(...positions.map((p) => p.x)) + NODE_W - minX;
    const height = Math.max(...positions.map((p) => p.y)) + NODE_H - minY;
    const availableWidth = Math.max(80, rect.width - 80);
    const availableHeight = Math.max(80, rect.height - 160);
    const k = Math.min(1.3, Math.max(.15, Math.min(availableWidth / width, availableHeight / height)));
    state.camera = { k, x: (rect.width - width * k) / 2 - minX * k,
      y: 64 + (availableHeight - height * k) / 2 - minY * k };
    updateCamera();
  }

  function zoomBy(factor) {
    state.autoFit = false;
    const rect = els.graph.getBoundingClientRect();
    const k = Math.max(.15, Math.min(2.4, state.camera.k * factor));
    const ratio = k / state.camera.k;
    state.camera.x = rect.width / 2 - (rect.width / 2 - state.camera.x) * ratio;
    state.camera.y = rect.height / 2 - (rect.height / 2 - state.camera.y) * ratio;
    state.camera.k = k;
    updateCamera();
  }

  function updateCamera() {
    els.zoom.textContent = Math.round(state.camera.k * 100) + "%";
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
    els.stats.innerHTML = `<span><b>${vis.size}</b> 可见节点</span><span><b>${edges.length}</b> 文档关系</span>`;
  }

  function renderNodeList(vis) {
    const pool = state.view === "admin" ? allNodes() : DATA.features;
    const nodes = pool.filter((n) => vis.has(n.id));
    document.getElementById("graphNodeCount").textContent = nodes.length;
    els.nodeList.innerHTML = nodes.map((n) => `<button class="graph-node-item${n.id === state.selectedId ? " active" : ""}" type="button" data-node-jump="${n.id}" aria-pressed="${n.id === state.selectedId}"><span class="node-index-dot" style="background:${domainColor(n.domain)}"></span><span>${escapeXml(n.name)}<small>${escapeXml(isAdmin(n.id) ? "后台" : n.id)}</small></span>${window.HayyoIcons.svg("arrow")}</button>`).join("") || '<p class="empty">没有匹配项</p>';
  }

  function renderFilters() {
    const items = DOMAINS.concat(state.view === "admin" ? ["后台"] : []);
    els.filters.innerHTML = items.map((d) => {
      const active = state.domainFilter.has(d);
      return `<button class="chip${active ? " active" : " muted"}" type="button" aria-pressed="${active}" data-domain="${d}">
        <span class="dot" style="background:${domainColor(d)}"></span>${d}
      </button>`;
    }).join("");
  }

  function renderDetail() {
    const id = state.selectedId;
    if (!id) {
      els.detail.innerHTML = `<div class="detail-empty">${window.HayyoIcons.svg("client")}<h3>从一个功能开始</h3><p>选择左侧目录或图中节点，查看它的上下游关系与文档依据。</p><div class="interaction-tip"><span>拖动画布</span><span>滚轮缩放</span><span>Esc 取消选中</span></div></div>`;
      return;
    }
    const n = nodeOf(id);
    if (!n) return;
    const edges = currentEdges();
    const outs = edges.filter((e) => e.from === id);
    const ins = edges.filter((e) => e.to === id);
    const prd = n.prd
      ? `<a class="prd-link" href="${n.prd}">打开 PRD</a>`
      : "";
    els.detail.innerHTML = `
      <div class="detail-title"><span class="section-kicker">${escapeXml(n.domain)}</span><h3>${escapeXml(n.name)}</h3><code>${escapeXml(n.id)}</code></div>
      <div class="kv">
        <div><dt>功能</dt><dd>${escapeXml(n.name)}</dd></div>
        <div><dt>域</dt><dd>${escapeXml(n.domain)}</dd></div>
        <div><dt>${isAdmin(id) ? "类型" : "关联后台"}</dt><dd>${escapeXml(n.admin || (n.kind === "pure" ? "纯后台，不挂客户端" : "后台章节"))}</dd></div>
        <div><dt>文档</dt><dd>${prd || "—"}</dd></div>
      </div>
      <h2 class="relation-section">影响的功能 <span>${outs.length}</span></h2>
      <div class="edge-list">${renderEdgeItems(outs, "to") || '<p class="empty">无</p>'}</div>
      <h2 class="relation-section">来自其他功能 <span>${ins.length}</span></h2>
      <div class="edge-list">${renderEdgeItems(ins, "from") || '<p class="empty">无</p>'}</div>
    `;
    els.detail.querySelectorAll("[data-jump]").forEach((btn) => {
      btn.addEventListener("click", () => selectNode(btn.getAttribute("data-jump"), { reveal: true }));
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

  function selectNode(id, options) {
    if (id && !nodeOf(id)) return;
    const wasFocused = state.focusOnly;
    if (id && isAdmin(id) && state.view !== "admin") setView("admin");
    if (id && !visibleIds().has(id)) {
      state.query = ""; els.search.value = "";
      state.domainFilter.add(nodeOf(id).domain);
      state.focusOnly = false;
      applyLayout(); renderFilters();
    }
    state.selectedId = id;
    if (!id) state.focusOnly = false;
    if (state.panel === "graph") {
      if (state.focusOnly || wasFocused) applyLayout();
      renderGraph(); renderDetail();
      if (!id && wasFocused) { state.autoFit = true; fitGraph(); }
      if (id && options && options.reveal) {
        state.autoFit = false;
        fitGraph(new Set([...connectedIds(id)].filter((key) => visibleIds().has(key))));
      }
      if (id && window.matchMedia("(max-width: 980px)").matches) {
        document.querySelector('.workspace').classList.remove('rail-open');
        document.querySelector('.workspace').classList.add('detail-open');
      }
    }
  }

  function updateTabs(target) {
    els.tabs.forEach((tab) => {
      const active = tab.getAttribute('data-view') === target;
      tab.classList.toggle('active', active);
      tab.setAttribute('role', 'tab');
      tab.setAttribute('aria-selected', String(active));
      tab.tabIndex = active ? 0 : -1;
    });
  }

  /**
   * 切换关系图 / 知识库。preserveSelection 用于从节点打开文档或「查看关系」，
   * 不套用两关系图 Tab 互切时的清空选中与复位镜头。
   */
  function setView(target, options) {
    const preserve = options && options.preserveSelection;
    updateTabs(target);
    state.dragging = null; state.panning = null;
    els.graph.classList.remove('panning');
    document.querySelector('.workspace').classList.remove('rail-open', 'detail-open');
    const appEl = document.querySelector(".app");
    const kbWs = document.getElementById("kbWorkspace");
    const qaWs = document.getElementById("qaWorkspace");

    if (target === "qa") {
      if (!preserve) { state.selectedId = null; state.focusOnly = false; }
      state.panel = "qa";
      appEl.classList.add("qa-active");
      appEl.classList.remove("kb-active");
      if (kbWs) kbWs.hidden = true;
      if (qaWs) {
        qaWs.hidden = false;
        qaWs.inert = false;
      }

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
      if (!preserve) { state.selectedId = null; state.focusOnly = false; }
      state.panel = "kb";
      appEl.classList.add("kb-active");
      if (kbWs) kbWs.hidden = false;

      if (window.KB) window.KB.onEnter();
      return;
    }

    const viewChanged = state.view !== target;
    state.panel = "graph";
    state.view = target;
    appEl.classList.remove("kb-active");
    if (kbWs) kbWs.hidden = true;

    if (state.view === "admin") state.domainFilter.add("后台");
    if (!preserve || viewChanged) {
      state.selectedId = null;
      state.focusOnly = false;
      state.autoFit = true;
      state.camera = { x: 24, y: 36, k: 1 };
      applyLayout();
    }
    document.getElementById('graphTitle').textContent = target === 'admin' ? '客户端 ↔ 后台' : '客户端交叉';
    document.getElementById('graphSubtitle').textContent = target === 'admin' ? '追踪客户端功能对应的后台入口与文档依据。' : '查看功能之间的依赖与影响，定位改动涉及的业务范围。';
    renderFilters(); renderGraph(); renderDetail();
    if (!preserve || viewChanged) requestAnimationFrame(() => {
      if (state.panel === 'graph' && state.autoFit) fitGraph();
    });
  }

  function bindNodeEvents() {
    els.graph.querySelectorAll(".node").forEach((g) => {
      g.addEventListener('keydown', (ev) => {
        if (ev.key === 'Enter' || ev.key === ' ') {
          ev.preventDefault();
          const id = g.getAttribute('data-id');
          selectNode(id);
          els.graph.querySelector('.node[data-id="' + id + '"]')?.focus();
        }
      });
      g.addEventListener("pointerdown", (ev) => {
        if (ev.button !== 0) return;
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
    if (state.panel !== "graph" || ev.button !== 0) return;
    if (ev.target.closest(".node")) return;
    els.graph.setPointerCapture(ev.pointerId);
    state.panning = { x: ev.clientX, y: ev.clientY, cx: state.camera.x, cy: state.camera.y };
    els.graph.classList.add("panning");
  });

  window.addEventListener("pointermove", (ev) => {
    if (state.panel !== "graph") return;
    if (state.dragging) {
      const dx = (ev.clientX - state.dragging.startX) / state.camera.k;
      const dy = (ev.clientY - state.dragging.startY) / state.camera.k;
      if (Math.abs(dx) + Math.abs(dy) > 3) { state.dragging.moved = true; state.autoFit = false; }
      state.positions[state.dragging.id] = {
        x: state.dragging.origX + dx,
        y: state.dragging.origY + dy
      };
      updateDraggedNode(state.dragging.id);
      return;
    }
    if (state.panning) {
      state.autoFit = false;
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
    state.autoFit = false;
    const next = Math.min(2.4, Math.max(0.15, state.camera.k * factor));
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

  window.addEventListener('pointercancel', () => { state.dragging = null; state.panning = null; els.graph.classList.remove('panning'); });

  els.tabs.forEach((tab, index) => {
    tab.addEventListener('keydown', (ev) => {
      let next = index;
      if (ev.key === 'ArrowRight') next = (index + 1) % els.tabs.length;
      else if (ev.key === 'ArrowLeft') next = (index + els.tabs.length - 1) % els.tabs.length;
      else if (ev.key === 'Home') next = 0;
      else if (ev.key === 'End') next = els.tabs.length - 1;
      else return;
      ev.preventDefault(); els.tabs[next].focus(); setView(els.tabs[next].getAttribute('data-view'));
    });
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
    const domains = DOMAINS.concat(state.view === 'admin' ? ['后台'] : []);
    if (!domains.some((name) => state.domainFilter.has(name))) state.domainFilter.add(d);
    refreshGraphSelection();
  });

  function refreshGraphSelection() {
    if (state.selectedId && !visibleIds().has(state.selectedId)) { state.selectedId = null; state.focusOnly = false; }
    applyLayout(); renderFilters(); renderGraph(); renderDetail();
    state.autoFit = true; fitGraph();
  }

  els.search.addEventListener("input", () => { state.query = els.search.value; refreshGraphSelection(); });
  els.nodeList.addEventListener('click', (ev) => {
    const btn = ev.target.closest('[data-node-jump]');
    if (btn) selectNode(btn.getAttribute('data-node-jump'), { reveal: true });
  });
  document.getElementById('btnRestoreFilters').addEventListener('click', () => {
    state.query = ''; els.search.value = ''; state.domainFilter = new Set(DOMAINS.concat(['后台']));
    refreshGraphSelection();
  });
  document.getElementById('btnFocus').addEventListener('click', () => {
    if (!state.selectedId) return;
    state.focusOnly = !state.focusOnly; refreshGraphSelection();
  });
  document.getElementById('btnZoomIn').addEventListener('click', () => zoomBy(1.2));
  document.getElementById('btnZoomOut').addEventListener('click', () => zoomBy(1 / 1.2));
  document.getElementById('btnFit').addEventListener('click', () => { state.autoFit = true; fitGraph(); });
  document.getElementById("btnReset").addEventListener("click", () => { applyLayout(); renderGraph(); state.autoFit = true; fitGraph(); });
  document.getElementById("btnClear").addEventListener("click", () => { selectNode(null); refreshGraphSelection(); });
  document.querySelectorAll('[data-graph-panel]').forEach((btn) => btn.addEventListener('click', () => {
    const ws = document.querySelector('.workspace');
    const cls = btn.getAttribute('data-graph-panel') + '-open';
    const open = !ws.classList.contains(cls);
    ws.classList.remove('rail-open', 'detail-open');
    if (open) ws.classList.add(cls);
  }));
  if (window.ResizeObserver) new ResizeObserver(() => {
    if (state.panel === 'graph' && state.autoFit) fitGraph();
  }).observe(els.graph);

  window.addEventListener("keydown", (ev) => {
    const kbSearch = document.getElementById("kbSearch");
    const qaInput = document.getElementById("qaInput");
    const inKb = document.querySelector(".app").classList.contains("kb-active");
    const inQa = document.querySelector(".app").classList.contains("qa-active");
    if (ev.key === "Escape" && !inKb && !inQa) {
      document.querySelector('.workspace').classList.remove('rail-open', 'detail-open');
      selectNode(null); refreshGraphSelection();
    }
    if (ev.key === "/" && !ev.target.closest("input, textarea, select, [contenteditable=true]")) {
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
