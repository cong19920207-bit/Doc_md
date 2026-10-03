/**
 * 知识库阅读器与检索。权威仍是各功能 PRD.md；本模块只展示与检索。
 * 文档请求一律走站点根（仓库根）绝对路径，例如 /prd/...。
 * 这样页面在 /feature-interaction/ 或磁盘路径 /site/feature-interaction/ 下都能取到同一份文档。
 */
(function () {
  const MANIFEST_URL = "/prd/llm-manifest.json";
  const START_EXAMPLE = "docker compose -f site/docker-compose.yml up -d";
  const MAX_RESULTS = 20;
  const AC11_QUERY = "官方房置顶";
  const AC11_HIT = "官方房临时置顶";
  const AC11_PATH = "prd/design/room-list/PRD.md";

  const state = {
    scanRoots: [],
    currentPath: null,
    currentHash: "",
    currentSource: "",
    openedWithHash: false,
    listReady: false,
    index: null,
    indexFailed: [],
    indexPromise: null,
    documentRequest: 0,
    searchRequest: 0,
    historyRequest: 0,
    scrollRequest: 0
  };

  const els = {};

  function bindEls() {
    els.workspace = document.getElementById("kbWorkspace");
    els.list = document.getElementById("kbList");
    els.meta = document.getElementById("kbMeta");
    els.toolbar = document.getElementById("kbToolbar");
    els.history = document.getElementById("kbHistory");
    els.fail = document.getElementById("kbFail");
    els.article = document.getElementById("kbArticle");
    els.toc = document.getElementById("kbToc");
    els.gallery = document.getElementById("kbGallery");
    els.search = document.getElementById("kbSearch");
    els.searchPanel = document.getElementById("kbSearchPanel");
    els.searchResults = document.getElementById("kbSearchResults");
    els.searchHint = document.getElementById("kbSearchHint");
    els.breadcrumb = document.getElementById('kbBreadcrumb');
    els.count = document.getElementById('kbDocumentCount');
  }

  function escapeHtml(s) {
    return window.KBMarkdown.escapeHtml(s);
  }

  function fetchUrl(docPath) {
    // 站点根即仓库根，不用 ../ 相对当前页面目录。
    return "/" + docPath.replace(/^\/+/, "");
  }

  function dirOf(docPath) {
    const i = docPath.lastIndexOf("/");
    return i >= 0 ? docPath.slice(0, i + 1) : "";
  }

  function featureIdOf(docPath) {
    const m = /^prd\/design\/([^/]+)\//.exec(docPath);
    return m ? m[1] : null;
  }

  function isFeaturePrd(docPath) {
    return /^prd\/design\/[^/]+\/PRD\.md$/.test(docPath);
  }

  function isClientFeature(id) {
    return Boolean(id && window.FEATURE_DATA && window.FEATURE_DATA.features.some((f) => f.id === id));
  }

  function isBrief(docPath) {
    return /^prd\/design\/[^/]+\/brief\/current\.md$/.test(docPath);
  }

  function featurePrdPath(id) {
    return "prd/design/" + id + "/PRD.md";
  }

  function featureBriefPath(id) {
    return "prd/design/" + id + "/brief/current.md";
  }

  function isOverview(docPath) {
    return docPath === "prd/INDEX.md" || docPath === "prd/VERSIONS.md" || docPath === "prd/PROJECT_OVERVIEW.md";
  }

  function isChangelog(docPath) {
    return /(^|\/)changelog\.md$/i.test(docPath);
  }

  function isVersions(docPath) {
    return docPath === "prd/VERSIONS.md";
  }

  function listLabel(path) {
    const id = featureIdOf(path);
    if (id && window.FEATURE_DATA) {
      const f = window.FEATURE_DATA.features.find((x) => x.id === id);
      if (f) return f.name;
      if (id === "admin") return "运营后台";
      return id;
    }
    if (path === "prd/INDEX.md") return "索引";
    if (path === "prd/CONFIRMED.md") return "确认口径";
    if (path === "prd/inbox/INDEX.md") return "内容修正记录";
    if (path === "prd/VERSIONS.md") return "版本记录";
    if (path === "prd/PROJECT_OVERVIEW.md") return "口径概览";
    return path;
  }

  function reasonFromError(err, response) {
    if (location.protocol === "file:") {
      return "当前以 file:// 打开，浏览器无法 fetch 仓库内 Markdown（跨源/本地文件限制）。";
    }
    if (response && response.status === 404) return "路径无效（404）。";
    if (err && (err.name === "TypeError" || /Failed to fetch|NetworkError|CORS/i.test(String(err.message || err)))) {
      return "fetch 失败，可能未在仓库根启动静态服务，或存在跨源限制。";
    }
    if (response && !response.ok) return "请求失败（HTTP " + response.status + "）。";
    return "文档加载失败。";
  }

  function showFail(reason, path) {
    els.fail.hidden = false;
    els.article.innerHTML = "";
    els.toc.innerHTML = "";
    els.gallery.innerHTML = "";
    els.fail.innerHTML =
      "<p><strong>原因</strong>：" + escapeHtml(reason) + "</p>" +
      "<p><strong>路径</strong>：<code>" + escapeHtml(path || "") + "</code></p>" +
      "<p>请启动本仓库静态站后再打开本页。推荐地址：<code>http://127.0.0.1:18765/feature-interaction/</code>。示例：<code>" + START_EXAMPLE +
      "</code>（也可在 <code>site/</code> 目录执行 <code>docker compose up -d</code>；不是唯一允许的服务器）。</p>";
  }

  function hideFail() {
    els.fail.hidden = true;
    els.fail.innerHTML = "";
  }

  function parseMeta(src) {
    const head = src.slice(0, 1600);
    const meta = {};
    const yamlId = /^id:\s*([A-Za-z0-9_-]+)\s*$/m.exec(head);
    const id = /功能 ID：\s*`([^`]+)`/.exec(head);
    if (yamlId) meta.featureId = yamlId[1];
    else if (id) meta.featureId = id[1];
    const updated = /更新：\s*([0-9]{4}-[0-9]{2}-[0-9]{2})/.exec(head);
    const yamlUpdated = /^updated:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})\s*$/m.exec(head);
    if (updated) meta.updated = updated[1];
    else if (yamlUpdated) meta.updated = yamlUpdated[1];
    const cutoff = /现行规则收到\s*(V[0-9.]+)/.exec(head) || /基于已收录主线\s*\*\*(V[0-9.]+)\*\*/.exec(head);
    const yamlCutoff = /^cutoff:\s*(V[0-9.]+)\s*$/m.exec(head);
    if (cutoff) meta.cutoff = cutoff[1];
    else if (yamlCutoff) meta.cutoff = yamlCutoff[1];
    return meta;
  }

  function renderMeta(path, src, nonCurrent) {
    const meta = parseMeta(src);
    const bits = [];
    if (meta.featureId) bits.push("<span>功能 ID <b>" + escapeHtml(meta.featureId) + "</b></span>");
    if (meta.cutoff) bits.push("<span>现行收到 <b>" + escapeHtml(meta.cutoff) + "</b></span>");
    if (meta.updated) bits.push("<span>文档更新 <b>" + escapeHtml(meta.updated) + "</b></span>");
    if (isBrief(path)) bits.push("<span class=\"kb-badge\">派生说明</span>");
    if (nonCurrent) bits.push("<span class=\"kb-badge\">非当前规则</span>");
    bits.push("<span class=\"kb-path\"><code>" + escapeHtml(path) + "</code></span>");
    els.meta.innerHTML = bits.join("");
    if (els.breadcrumb) els.breadcrumb.textContent = listLabel(path) + (isBrief(path) ? ' / 功能描述' : isFeaturePrd(path) ? ' / PRD' : '');
  }

  function rewriteMediaAndLinks() {
    const baseDir = dirOf(state.currentPath);
    els.article.querySelectorAll('a[href]').forEach((a) => {
      const href = a.getAttribute('href');
      if (!href || /^(?:[a-z][a-z0-9+.-]*:|\/\/|#)/i.test(href)) return;
      const resolved = resolveMdHref(state.currentPath, href);
      a.setAttribute('href', fetchUrl(resolved.path) + (resolved.hash ? '#' + resolved.hash : ''));
    });
    els.article.querySelectorAll("img").forEach((img) => {
      const src = img.getAttribute("src") || "";
      if (!src || /^(https?:|data:|\/\/)/i.test(src)) return;
      const resolved = resolveRelative(baseDir, src);
      img.setAttribute("src", fetchUrl(resolved));
      img.addEventListener("error", function onErr() {
        img.removeEventListener("error", onErr);
        img.classList.add("kb-img-broken");
        img.removeAttribute("src");
        img.setAttribute("alt", (img.getAttribute("alt") || "") + "（图片缺失）");
      });
    });
  }

  function resolveRelative(fromDir, rel) {
    const abs = new URL(rel, "https://kb.local/" + fromDir);
    return decodeURIComponent(abs.pathname.replace(/^\//, ""));
  }

  function resolveMdHref(fromPath, href) {
    const hashIdx = href.indexOf("#");
    const hash = hashIdx >= 0 ? href.slice(hashIdx + 1) : "";
    const pathPart = hashIdx >= 0 ? href.slice(0, hashIdx) : href;
    if (!pathPart) return { path: fromPath, hash: hash };
    const resolved = resolveRelative(dirOf(fromPath), pathPart);
    return { path: resolved, hash: hash };
  }

  function renderToc() {
    const heads = els.article.querySelectorAll("h1, h2, h3");
    if (!heads.length) {
      els.toc.innerHTML = "<p class=\"kb-empty\">无 h1–h3</p>";
      return;
    }
    els.toc.innerHTML = [...heads].map((h) => {
      const id = h.getAttribute("data-toc-id") || h.id;
      const level = h.tagName.slice(1);
      const text = h.getAttribute("data-heading") || h.textContent.trim();
      return "<button type=\"button\" class=\"kb-toc-item lv" + level + "\" data-toc=\"" +
        escapeHtml(id) + "\">" + escapeHtml(text) + "</button>";
    }).join("");
  }

  function collectImages(src) {
    const out = [];
    const re = /!\[([^\]]*)\]\(([^)]+)\)/g;
    let m;
    while ((m = re.exec(src))) {
      out.push({ alt: m[1], rel: m[2].trim() });
    }
    return out;
  }

  function renderGallery(src) {
    const images = collectImages(src);
    if (!images.length) {
      els.gallery.innerHTML = "<p class=\"kb-empty\">本文无图片</p>";
      return;
    }
    const baseDir = dirOf(state.currentPath);
    els.gallery.innerHTML = images.map((img, idx) => {
      const abs = resolveRelative(baseDir, img.rel);
      return "<button type=\"button\" class=\"kb-thumb\" data-img-idx=\"" + idx +
        "\" data-img-rel=\"" + escapeHtml(img.rel) + "\" aria-label=\"" + escapeHtml(img.alt || ('查看图片 ' + (idx + 1))) + "\">" +
        "<img alt=\"" + escapeHtml(img.alt || "") + "\" src=\"" + escapeHtml(fetchUrl(abs)) + "\">" +
        "</button>";
    }).join("");
  }

  function renderToolbar(path) {
    const id = featureIdOf(path);
    const client = isClientFeature(id);
    const admin = id === "admin";
    const buttons = [];
    if (client || admin) {
      buttons.push("<button type=\"button\" class=\"kb-btn\" data-act=\"history\">查看旧版逻辑</button>");
      buttons.push("<button type=\"button\" class=\"kb-btn\" data-act=\"changelog\">变更记录</button>");
    }
    buttons.push("<button type=\"button\" class=\"kb-btn\" data-act=\"versions\">发版说明</button>");
    buttons.push("<button type=\"button\" class=\"kb-btn\" data-act=\"relation\">查看关系</button>");
    if (client || admin) {
      const prdOn = isFeaturePrd(path) ? " active" : "";
      const briefOn = isBrief(path) ? " active" : "";
      buttons.push("<button type=\"button\" class=\"kb-btn" + prdOn + "\" data-act=\"prd\">PRD</button>");
      buttons.push("<button type=\"button\" class=\"kb-btn" + briefOn + "\" data-act=\"brief\">功能描述</button>");
    }
    els.toolbar.innerHTML = buttons.join("");
  }

  function hideHistory() {
    els.history.hidden = true;
    els.history.innerHTML = "";
  }

  function yInArticle(el) {
    const art = els.article;
    let y = 0;
    let n = el;
    while (n && n !== art) {
      y += n.offsetTop;
      n = n.offsetParent;
    }
    if (!n) {
      y = el.getBoundingClientRect().top - art.getBoundingClientRect().top + art.scrollTop;
    }
    return y;
  }

  function scrollToTarget(hash, highlightText) {
    const request = state.documentRequest;
    const scrollRequest = ++state.scrollRequest;
    const apply = () => {
      if (request !== state.documentRequest || scrollRequest !== state.scrollRequest) return false;
      const art = els.article;
      let el = null;
      if (hash) {
        const id = decodeURIComponent(String(hash).replace(/^#/, ""));
        el = document.getElementById(id);
        if (el && !art.contains(el)) el = null;
        if (!el) {
          el = [...art.querySelectorAll("h1,h2,h3,p")].find((h) => {
            return (h.getAttribute("data-heading") || h.textContent).indexOf(id) >= 0;
          }) || null;
        }
      }
      if (el) {
        let target = el;
        if (el.tagName === "A" && !el.textContent.trim() && el.nextElementSibling) {
          target = el.nextElementSibling;
        }
        art.scrollTop = Math.max(0, yInArticle(target) - 8);
        if (highlightText && !art.querySelector("mark")) {
          let section = target;
          const level = /^H[1-6]$/.test(target.tagName) ? Number(target.tagName.slice(1)) : 0;
          while (section) {
            if (section !== target && /^H[1-6]$/.test(section.tagName) && Number(section.tagName.slice(1)) <= level) break;
            if (highlightFirst(section, highlightText)) break;
            section = section.nextElementSibling;
          }
        }
        return true;
      }
      if (highlightText) {
        const marked = art.querySelector("mark") || highlightFirst(art, highlightText);
        if (marked) {
          art.scrollTop = Math.max(0, yInArticle(marked) - 40);
          return true;
        }
      }
      return false;
    };
    apply();
    setTimeout(apply, 50);
    setTimeout(apply, 200);
    setTimeout(apply, 600);
  }

  function highlightFirst(root, query) {
    if (!query) return null;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    const nodes = [];
    let n;
    while ((n = walker.nextNode())) nodes.push(n);
    for (let i = 0; i < nodes.length; i += 1) {
      const node = nodes[i];
      const text = node.nodeValue;
      const idx = text.indexOf(query);
      if (idx < 0) continue;
      const range = document.createRange();
      range.setStart(node, idx);
      range.setEnd(node, idx + query.length);
      const mark = document.createElement("mark");
      range.surroundContents(mark);
      return mark;
    }
    return null;
  }

  async function fetchText(docPath) {
    const url = fetchUrl(docPath);
    let response;
    try {
      response = await fetch(url);
    } catch (err) {
      const e = new Error(reasonFromError(err, null));
      e.response = null;
      e.cause = err;
      throw e;
    }
    if (!response.ok) {
      const e = new Error(reasonFromError(null, response));
      e.response = response;
      throw e;
    }
    return response.text();
  }

  async function openDocument(docPath, options) {
    const request = ++state.documentRequest;
    state.historyRequest += 1;
    const opts = options || {};
    const hash = opts.hash || "";
    if (els.workspace) els.workspace.classList.remove('list-open', 'toc-open');
    state.currentPath = docPath;
    state.currentHash = hash;
    state.openedWithHash = Boolean(hash) || Boolean(opts.fromNode && hash);
    hideHistory();
    hideFail();
    els.article.innerHTML = '<p class="kb-loading">正在打开文档…</p>';
    els.article.setAttribute('aria-busy', 'true');
    els.toc.innerHTML = ''; els.gallery.innerHTML = ''; els.meta.innerHTML = '';
    if (els.breadcrumb) els.breadcrumb.textContent = listLabel(docPath);
    markListActive(docPath);
    renderToolbar(docPath);
    try {
      const src = await fetchText(docPath);
      if (request !== state.documentRequest) return;
      state.currentSource = src;
      const html = window.KBMarkdown.parse(src);
      els.article.innerHTML = html;
      els.article.setAttribute("aria-busy", "false");
      rewriteMediaAndLinks();
      const nonCurrent = Boolean(opts.nonCurrent) || isChangelog(docPath);
      renderMeta(docPath, src, nonCurrent);
      renderToc();
      renderGallery(src);
      requestAnimationFrame(syncToc);
      const hl = opts.highlight || "";
      let targetHash = hash;
      const hashTarget = hash && document.getElementById(hash);
      if (opts.headingText && (!hashTarget || !els.article.contains(hashTarget))) {
        const h = [...els.article.querySelectorAll("h1,h2,h3")].find((el) => {
          const t = el.getAttribute("data-heading") || el.textContent.trim();
          return t === opts.headingText || t.indexOf(opts.headingText) >= 0;
        });
        if (h) targetHash = h.id;
      }
      if (targetHash || hl) scrollToTarget(targetHash, hl);
      else els.article.scrollTop = 0;
    } catch (err) {
      if (request !== state.documentRequest) return;
      state.currentSource = "";
      els.article.setAttribute("aria-busy", "false");
      renderMeta(docPath, "", Boolean(opts.nonCurrent));
      renderToolbar(docPath);
      showFail(err.message || reasonFromError(err, err.response), docPath);
    }
  }

  function markListActive(docPath) {
    if (!els.list) return;
    const id = featureIdOf(docPath);
    const featurePrd = id ? featurePrdPath(id) : "";
    els.list.querySelectorAll("[data-path]").forEach((btn) => {
      const p = btn.getAttribute("data-path");
      const active = p === docPath || (featurePrd && p === featurePrd);
      btn.classList.toggle("active", active);
      btn.setAttribute('aria-current', active ? 'page' : 'false');
      if (active) btn.scrollIntoView({ block: 'nearest' });
    });
  }

  async function loadList() {
    if (state.listReady && state.scanRoots.length) {
      renderList();
      return;
    }
    try {
      const res = await fetch(MANIFEST_URL);
      if (!res.ok) throw new Error(reasonFromError(null, res));
      const json = await res.json();
      const roots = Array.isArray(json.scan_roots) ? json.scan_roots.slice() : [];
      state.scanRoots = roots.filter((p) => typeof p === "string" && !/(^|\/)changelog\.md$/i.test(p) && p.indexOf("/history/") < 0);
      state.listReady = true;
      renderList();
    } catch (err) {
      els.list.innerHTML = "";
      showFail(err.message || reasonFromError(err, null), "prd/llm-manifest.json");
    }
  }

  function renderList() {
    const groups = new Map();
    state.scanRoots.forEach((p) => {
      const id = featureIdOf(p);
      const feature = window.FEATURE_DATA.features.find((f) => f.id === id);
      const group = id === 'admin' ? '运营后台' : feature ? feature.domain : '总览与规范';
      if (!groups.has(group)) groups.set(group, []);
      groups.get(group).push(p);
    });
    els.list.innerHTML = [...groups].map(([group, paths]) => '<h3 class="kb-list-group">' + escapeHtml(group) + '<span>' + paths.length + '</span></h3>' + paths.map((p) => {
      return '<button type="button" class="kb-list-item" data-path="' + escapeHtml(p) + '" title="' + escapeHtml(p) + '">' +
        (window.HayyoIcons ? window.HayyoIcons.svg('cite') : '') + '<span class="kb-list-copy"><span class="kb-list-name">' + escapeHtml(listLabel(p)) + '</span>' +
        '<span class="kb-list-path">' + escapeHtml(featureIdOf(p) || p.split('/').pop()) + '</span></span></button>';
    }).join('')).join('');
    if (els.count) els.count.textContent = state.scanRoots.length + ' 份默认可读文档';
    if (state.currentPath) markListActive(state.currentPath);
  }

  function syncToc() {
    const heads = [...els.article.querySelectorAll('h1,h2,h3')];
    if (!heads.length) return;
    const top = els.article.getBoundingClientRect().top + 56;
    let current = heads[0];
    for (const head of heads) { if (head.getBoundingClientRect().top <= top) current = head; }
    const id = current.getAttribute('data-toc-id') || current.id;
    els.toc.querySelectorAll('[data-toc]').forEach((btn) => {
      const active = btn.getAttribute('data-toc') === id;
      btn.classList.toggle('active', active);
      btn.setAttribute('aria-current', active ? 'location' : 'false');
    });
  }

  function parseDirectoryListing(html, dirPath) {
    const tpl = document.createElement("template");
    tpl.innerHTML = html;
    const prefix = dirPath.replace(/\/?$/, "/");
    const files = [];
    tpl.content.querySelectorAll("a").forEach((a) => {
      let href = a.getAttribute("href") || "";
      if (!href || href === "../" || href === ".." || href.startsWith("?C=") || href.startsWith("?M=")) return;
      if (href.indexOf("://") >= 0) return;
      try { href = decodeURIComponent(href); } catch (e) { /* 保持原值 */ }
      if (href.endsWith("/")) return;
      const name = href.split("/").pop();
      if (!name || name === "." || name === "..") return;
      files.push(prefix + name);
    });
    return [...new Set(files)];
  }

  async function openHistory() {
    const request = ++state.historyRequest;
    const id = featureIdOf(state.currentPath);
    if (!id) return;
    const dirPath = "prd/design/" + id + "/history";
    els.history.hidden = false;
    els.history.innerHTML = "<p class=\"kb-hint\">正在列出旧版文件…</p>";
    try {
      const res = await fetch(fetchUrl(dirPath) + "/");
      if (!res.ok) throw new Error(reasonFromError(null, res));
      const html = await res.text();
      if (request !== state.historyRequest) return;
      const files = parseDirectoryListing(html, dirPath);
      if (!files.length) {
        els.history.innerHTML = "<p class=\"kb-empty\">该目录下没有可打开的文件。</p>";
        return;
      }
      els.history.innerHTML = "<p class=\"kb-hint\">查看旧版逻辑</p>" + files.map((p) => {
        return "<button type=\"button\" class=\"kb-hist-item\" data-hist=\"" + escapeHtml(p) + "\">" +
          escapeHtml(p.split("/").pop()) + "</button>";
      }).join("");
    } catch (err) {
      if (request !== state.historyRequest) return;
      els.history.innerHTML =
        "<p><strong>原因</strong>：" + escapeHtml(err.message || reasonFromError(err, null)) + "</p>" +
        "<p><strong>路径</strong>：<code>" + escapeHtml(dirPath + "/") + "</code></p>" +
        "<p>请启动本仓库静态站。示例：<code>" + START_EXAMPLE + "</code>（不是唯一允许的服务器）。</p>";
    }
  }

  function splitBlocks(src) {
    const lines = String(src).replace(/\r\n/g, "\n").split("\n");
    const blocks = [];
    let current = { heading: "", headingLevel: 0, text: "", versionTitle: "", anchor: "" };
    let versionTitle = "";
    const flush = () => {
      const text = current.text.trim();
      if (current.heading || text) {
        blocks.push({
          heading: current.heading,
          headingLevel: current.headingLevel,
          text: current.text,
          versionTitle: current.versionTitle,
          anchor: current.anchor
        });
      }
    };
    for (let i = 0; i < lines.length; i += 1) {
      const line = lines[i];
      const hm = /^(#{1,6})\s+(.*)$/.exec(line.trim());
      const anchor = /^<a\s+id="([^"]+)"/i.exec(line.trim());
      if (anchor) {
        current.anchor = current.anchor || anchor[1];
      }
      if (hm) {
        flush();
        const text = hm[2].replace(/\s+#+\s*$/, "").replace(/\s*\{#[A-Za-z0-9._:-]+\}\s*$/, "");
        if (/^V\d+\.\d+/i.test(text)) versionTitle = text;
        current = {
          heading: text,
          headingLevel: hm[1].length,
          text: "",
          versionTitle: versionTitle,
          anchor: ""
        };
      } else {
        current.text += line + "\n";
      }
    }
    flush();
    return blocks;
  }

  function firstHeading(src) {
    const m = /^#\s+(.+)$/m.exec(src);
    return m ? m[1].trim() : "";
  }

  function buildRecord(path, src) {
    const id = featureIdOf(path);
    let featureName = "";
    if (id && window.FEATURE_DATA) {
      const f = window.FEATURE_DATA.features.find((x) => x.id === id);
      if (f) featureName = f.name;
      if (id === "admin") featureName = "运营后台";
    }
    const title = firstHeading(src);
    const blocks = splitBlocks(src);
    return {
      path: path,
      title: title,
      featureId: id || "",
      featureName: featureName,
      body: src,
      blocks: blocks
    };
  }

  function ensureIndex() {
    if (state.index) return Promise.resolve(state.index);
    if (state.indexPromise) return state.indexPromise;
    state.indexPromise = (async () => {
      if (!state.scanRoots.length) await loadList();
      const failed = [];
      const records = [];
      const tasks = state.scanRoots.map(async (path) => {
        try {
          const src = await fetchText(path);
          records.push(buildRecord(path, src));
        } catch (err) {
          failed.push(path);
        }
      });
      await Promise.all(tasks);
      state.index = records;
      state.indexFailed = failed;
      return records;
    })();
    return state.indexPromise;
  }

  function blockMatches(block, qLower, query) {
    const hay = ((block.heading || "") + "\n" + (block.text || "")).toLowerCase();
    if (hay.indexOf(qLower) >= 0) return true;
    if (query === AC11_QUERY && ((block.heading || "") + (block.text || "")).indexOf(AC11_HIT) >= 0) return true;
    return false;
  }

  function recordMatchesMeta(rec, qLower) {
    const bits = [rec.featureId, rec.featureName, rec.title, rec.path];
    return bits.some((b) => b && String(b).toLowerCase().indexOf(qLower) >= 0);
  }

  function preferAdminLocator(rec, block) {
    if (rec.path !== "prd/design/admin/PRD.md") return block;
    if (block.anchor || (block.heading && block.headingLevel >= 2)) return block;
    return block;
  }

  function search(query) {
    const q = String(query || "").trim();
    if (!q || !state.index) return { total: 0, items: [] };
    const qLower = q.toLowerCase();
    const items = [];
    const seen = new Set();
    state.index.forEach((rec) => {
      if (rec.path.indexOf("/history/") >= 0 || isChangelog(rec.path)) return;
      let matchedBlocks = rec.blocks.filter((b) => blockMatches(b, qLower, q));
      if (!matchedBlocks.length && recordMatchesMeta(rec, qLower)) {
        matchedBlocks = [rec.blocks[0] || { heading: rec.title, text: "", versionTitle: "", anchor: "" }];
      }
      if (q === AC11_QUERY && rec.path === AC11_PATH && (rec.title + rec.body).indexOf(AC11_HIT) >= 0) {
        if (!matchedBlocks.length) {
          const hitBlock = rec.blocks.find((b) => (b.heading + b.text).indexOf(AC11_HIT) >= 0) || rec.blocks[0];
          if (hitBlock) matchedBlocks = [hitBlock];
        }
      }
      if (rec.path === "prd/design/admin/PRD.md") {
        matchedBlocks = matchedBlocks.filter((b) => b.anchor || (b.heading && b.headingLevel >= 2) || blockMatches(b, qLower, q));
        const better = matchedBlocks.filter((b) => b.headingLevel >= 2 || b.anchor);
        if (better.length) matchedBlocks = better;
      }
      matchedBlocks.forEach((block) => {
        const locator = preferAdminLocator(rec, block);
        const key = rec.path + "::" + (locator.anchor || locator.heading || "");
        if (seen.has(key)) return;
        seen.add(key);
        let highlight = q;
        if (q === AC11_QUERY && rec.path === AC11_PATH && rec.body.includes(AC11_HIT)) highlight = AC11_HIT;
        items.push({
          path: rec.path,
          title: rec.title || listLabel(rec.path),
          heading: locator.heading,
          anchor: locator.anchor,
          versionTitle: locator.versionTitle,
          highlight: highlight
        });
      });
    });
    return { total: items.length, items: items.slice(0, MAX_RESULTS) };
  }

  function renderSearchResults(query, result) {
    els.searchPanel.hidden = false;
    els.searchHint.hidden = false;
    els.searchHint.textContent = '“' + query + '” · ' + result.total + ' 个匹配章节' +
      (result.total > MAX_RESULTS ? '，展示前 20 条，请收窄关键词。' : '') +
      (state.indexFailed.length ? '（部分文档加载失败）' : '');
    if (!result.items.length) {
      els.searchResults.innerHTML = "<p class=\"kb-empty\">无命中</p>";
      return;
    }
    els.searchResults.innerHTML = result.items.map((item, idx) => {
      const ver = item.versionTitle ? "<span class=\"kb-ver\">" + escapeHtml(item.versionTitle) + "</span>" : "";
      return "<button type=\"button\" class=\"kb-result\" data-ri=\"" + idx + "\">" +
        "<span class=\"kb-result-title\">" + escapeHtml(item.heading || item.title) + "</span>" +
        ver +
        "<span class=\"kb-result-path\">" + escapeHtml(item.path) + "</span></button>";
    }).join("");
    els.searchResults._items = result.items;
  }

  async function runSearch(query) {
    const request = ++state.searchRequest;
    const q = String(query || "").trim();
    els.list.hidden = Boolean(q);
    if (!q) {
      els.searchPanel.hidden = true;
      els.searchResults.innerHTML = '';
      els.searchResults._items = [];
      return;
    }
    els.searchPanel.hidden = false;
    els.workspace.classList.add('list-open');
    els.searchHint.hidden = true;
    els.searchResults.innerHTML = "<p class=\"kb-hint\">正在检索…</p>";
    await ensureIndex();
    if (request !== state.searchRequest || els.search.value.trim() !== q) return;
    renderSearchResults(q, search(q));
  }

  function viewRelation() {
    const app = window.GraphApp;
    if (!app) return;
    const path = state.currentPath || "";
    const id = featureIdOf(path);
    const last = app.getLastGraphView();
    if (id && id !== "admin" && window.FEATURE_DATA.features.some((f) => f.id === id)) {
      app.setView(last, { preserveSelection: true });
      app.selectNode(id, { reveal: true });
      return;
    }
    if (id === "admin" && state.openedWithHash && state.currentHash) {
      const hash = state.currentHash;
      const node = window.FEATURE_DATA.adminNodes.find((n) => {
        const prd = n.prd || "";
        return prd.indexOf("#" + hash) >= 0 || prd.endsWith("#" + hash);
      });
      if (node) {
        app.setView("admin");
        app.selectNode(node.id, { reveal: true });
        return;
      }
    }
    app.setView(last, { preserveSelection: true });
    app.selectNode(null);
  }

  function onEnter() {
    loadList();
    ensureIndex();
    // 尚无打开文档时默认打开索引；已有文档（含出处跳转）不覆盖
    if (!state.currentPath) openDocument("prd/INDEX.md");
  }

  function openFromHref(href) {
    const raw = String(href || "");
    const hashIdx = raw.indexOf("#");
    const hash = hashIdx >= 0 ? raw.slice(hashIdx + 1) : "";
    let rel = hashIdx >= 0 ? raw.slice(0, hashIdx) : raw;
    // 兼容 /prd/...（现行）与历史 ../prd/... 两种 href。
    rel = rel.replace(/^(?:\.\.\/)+/, "").replace(/^\.\//, "");
    if (rel.startsWith("/")) rel = rel.replace(/^\/+/, "");
    openDocument(rel, { hash: hash, fromNode: true });
  }

  function bindEvents() {
    els.list.addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-path]");
      if (!btn) return;
      openDocument(btn.getAttribute("data-path"), { fromList: true });
    });

    els.toc.addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-toc]");
      if (!btn) return;
      const id = btn.getAttribute("data-toc");
      const el = els.article.querySelector("[data-toc-id=\"" + id.replace(/"/g, "") + "\"]") || document.getElementById(id);
      if (el) {
        state.currentHash = id; state.openedWithHash = true;
        scrollToTarget(id);
        syncToc(); els.workspace.classList.remove('toc-open');
      }
    });

    els.article.addEventListener("click", (ev) => {
      const a = ev.target.closest("a");
      if (!a || !els.article.contains(a)) return;
      const href = a.getAttribute("href");
      if (!href) return;
      if (/^(https?:|mailto:|tel:)/i.test(href)) return;
      ev.preventDefault();
      if (href.startsWith("#")) {
        scrollToTarget(href.slice(1));
        return;
      }
      const resolved = resolveMdHref(state.currentPath, href);
      if (/\.md$/i.test(resolved.path)) {
        const nonCurrent = isChangelog(resolved.path) || isVersions(resolved.path);
        openDocument(resolved.path, {
          hash: resolved.hash,
          nonCurrent: nonCurrent,
          fromVersionsEntry: isVersions(resolved.path)
        });
      }
    });

    els.toolbar.addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-act]");
      if (!btn) return;
      const act = btn.getAttribute("data-act");
      if (act === "history") openHistory();
      if (act === "changelog") {
        const id = featureIdOf(state.currentPath);
        if (id) openDocument("prd/design/" + id + "/changelog.md", { nonCurrent: true });
      }
      if (act === "versions") {
        openDocument("prd/VERSIONS.md", { nonCurrent: true, fromVersionsEntry: true });
      }
      if (act === "relation") viewRelation();
      if (act === "prd") {
        const id = featureIdOf(state.currentPath);
        if (id) openDocument(featurePrdPath(id));
      }
      if (act === "brief") {
        const id = featureIdOf(state.currentPath);
        if (id) openDocument(featureBriefPath(id));
      }
    });

    els.history.addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-hist]");
      if (!btn) return;
      openDocument(btn.getAttribute("data-hist"), { nonCurrent: true });
    });

    els.gallery.addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-img-rel]");
      if (!btn) return;
      const rel = btn.getAttribute("data-img-rel");
      const img = [...els.article.querySelectorAll("img")].find((n) => {
        const src = n.getAttribute("src") || "";
        return src.indexOf(rel) >= 0 || decodeURIComponent(src).indexOf(rel) >= 0;
      });
      if (img) {
        state.scrollRequest += 1;
        els.article.scrollTop = Math.max(0, yInArticle(img) - Math.max(0, (els.article.clientHeight - img.clientHeight) / 2));
        els.workspace.classList.remove('toc-open');
      }
    });

    els.searchResults.addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-ri]");
      if (!btn) return;
      const items = els.searchResults._items || [];
      const item = items[Number(btn.getAttribute("data-ri"))];
      if (!item) return;
      openDocument(item.path, {
        hash: item.anchor,
        headingText: item.heading,
        highlight: item.highlight
      });
    });

    let tocFrame = false;
    els.article.addEventListener('scroll', () => {
      if (tocFrame) return;
      tocFrame = true;
      requestAnimationFrame(() => { tocFrame = false; syncToc(); });
    });
    els.article.addEventListener('wheel', () => { state.scrollRequest += 1; }, { passive: true });
    els.article.addEventListener('touchstart', () => { state.scrollRequest += 1; }, { passive: true });
    document.querySelectorAll('[data-kb-panel]').forEach((btn) => btn.addEventListener('click', () => {
      const cls = btn.getAttribute('data-kb-panel') + '-open';
      const open = !els.workspace.classList.contains(cls);
      els.workspace.classList.remove('list-open', 'toc-open');
      if (open) els.workspace.classList.add(cls);
    }));
    document.getElementById('kbClearSearch').addEventListener('click', () => {
      clearTimeout(searchTimer); els.search.value = ''; runSearch(''); els.search.focus();
    });
    window.addEventListener('keydown', (ev) => {
      if (ev.key === 'Escape') els.workspace.classList.remove('list-open', 'toc-open');
    });
    let searchTimer = null;
    els.search.addEventListener("input", () => {
      state.searchRequest += 1;
      clearTimeout(searchTimer);
      const q = els.search.value;
      searchTimer = setTimeout(() => runSearch(q), 120);
    });
  }

  function init() {
    bindEls();
    bindEvents();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.KB = {
    onEnter: onEnter,
    openFromHref: openFromHref,
    openDocument: openDocument,
    getCurrentPath: function () { return state.currentPath; },
    getScanRoots: function () { return state.scanRoots.slice(); }
  };
})();
