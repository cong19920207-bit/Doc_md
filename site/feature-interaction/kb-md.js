/**
 * 知识库 Markdown 等价渲染：标题、表格、列表、链接、图片、引用。
 * 不引入 npm；有限保留 Word 残留 HTML；禁止脚本与事件属性。
 */
(function () {
  const ALLOWED_TAGS = {
    A: true, ABBR: true, B: true, BLOCKQUOTE: true, BR: true, CODE: true,
    DIV: true, EM: true, H1: true, H2: true, H3: true, H4: true, H5: true, H6: true,
    HR: true, I: true, IMG: true, LI: true, MARK: true, OL: true, P: true,
    PRE: true, SPAN: true, STRONG: true, TABLE: true, TBODY: true, TD: true,
    TH: true, THEAD: true, TR: true, UL: true, NAV: true
  };

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function isAllowedAttr(tag, name, value) {
    const n = name.toLowerCase();
    if (n.startsWith("on")) return false;
    if (n === "style") return false;
    if ((n === "href" || n === "src") && /^\s*javascript:/i.test(value || "")) return false;
    if (tag === "A" && (n === "href" || n === "title" || n === "id" || n === "name" || n === "target" || n === "rel")) return true;
    if (tag === "IMG" && (n === "src" || n === "alt" || n === "title")) return true;
    if (n === "id" || n === "class" || n === "colspan" || n === "rowspan" || n === "align") return true;
    if (n === "data-toc-id" || n === "data-src-img" || n === "data-heading") return true;
    return false;
  }

  function sanitizeHtml(html) {
    const tpl = document.createElement("template");
    tpl.innerHTML = html;
    const walk = (root) => {
      [...root.childNodes].forEach((node) => {
        if (node.nodeType === 1) {
          const tag = node.tagName;
          if (!ALLOWED_TAGS[tag]) {
            const parent = node.parentNode;
            while (node.firstChild) parent.insertBefore(node.firstChild, node);
            parent.removeChild(node);
            return;
          }
          [...node.attributes].forEach((attr) => {
            if (!isAllowedAttr(tag, attr.name, attr.value)) node.removeAttribute(attr.name);
          });
          walk(node);
        } else if (node.nodeType === 8) {
          node.parentNode.removeChild(node);
        }
      });
    };
    walk(tpl.content);
    const wrap = document.createElement("div");
    wrap.appendChild(tpl.content);
    return wrap.innerHTML;
  }

  function inline(text, safeText) {
    const tokens = [];
    const save = (html) => {
      tokens.push(html);
      return "\u0000T" + (tokens.length - 1) + "\u0000";
    };
    let s = String(text);
    if (!safeText) {
      s = s.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_, alt, url) => {
        return save("<img alt=\"" + escapeHtml(alt) + "\" src=\"" + escapeHtml(url.trim()) + "\">");
      });
      s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, url) => {
        return save("<a href=\"" + escapeHtml(url.trim()) + "\">" + escapeHtml(label) + "</a>");
      });
    }
    s = s.replace(/`([^`]+)`/g, (_, code) => save("<code>" + escapeHtml(code) + "</code>"));
    if (!safeText) {
      s = s.replace(/<br\s*\/?>/gi, () => save("<br>"));
      s = s.replace(/<a\s+([^>]*id\s*=\s*["'][^"']+["'][^>]*)><\/a>/gi, (m) => save(m));
    }
    s = escapeHtml(s);
    s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/__(.+?)__/g, "<strong>$1</strong>");
    s = s.replace(/\u0000T(\d+)\u0000/g, (_, i) => tokens[Number(i)]);
    return s;
  }

  function isHr(line) {
    return /^(?:-{3,}|\*{3,}|_{3,})\s*$/.test(line.trim());
  }

  function isTableSep(line) {
    return /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);
  }

  function splitRow(line) {
    let s = line.trim();
    if (s.startsWith("|")) s = s.slice(1);
    if (s.endsWith("|")) s = s.slice(0, -1);
    return s.split("|").map((c) => c.trim());
  }

  function headingLevel(line) {
    const m = /^(#{1,6})\s+(.*)$/.exec(line);
    return m ? { level: m[1].length, text: m[2].replace(/\s+#+\s*$/, "") } : null;
  }

  function parse(src, options) {
    // 模型回答仅排版文本，不解释原始 HTML、链接或图片；文档默认渲染保持原有行为。
    const safeText = Boolean(options && options.safeText);
    const renderInline = (text) => inline(text, safeText);
    const lines = String(src).replace(/\r\n/g, "\n").split("\n");
    const html = [];
    let headingIndex = 0;
    let i = 0;

    const pushHeading = (level, raw) => {
      const am = /\s*\{#([A-Za-z0-9._:-]+)\}\s*$/.exec(raw);
      const text = am ? raw.slice(0, am.index).trim() : raw;
      headingIndex += 1;
      const id = am ? am[1] : "kb-h-" + headingIndex;
      const attrs = safeText ? "" : ` id="${id}" data-toc-id="${id}" data-heading="${escapeHtml(text)}"`;
      html.push(`<h${level}${attrs}>${renderInline(text)}</h${level}>`);
    };

    // 丢掉 YAML frontmatter，避免现行说明文首变成横线和字段段落。
    if (!safeText && lines[0] && lines[0].trim() === "---") {
      i = 1;
      while (i < lines.length && lines[i].trim() !== "---") i += 1;
      if (i < lines.length) i += 1;
    }

    while (i < lines.length) {
      const line = lines[i];
      const trimmed = line.trim();

      if (!trimmed) {
        i += 1;
        continue;
      }

      if (!safeText && trimmed.startsWith("<!--")) {
        while (i < lines.length && lines[i].indexOf("-->") < 0) i += 1;
        i += 1;
        continue;
      }

      if (trimmed.startsWith("```")) {
        const buf = [];
        i += 1;
        while (i < lines.length && !lines[i].trim().startsWith("```")) {
          buf.push(lines[i]);
          i += 1;
        }
        if (i < lines.length) i += 1;
        html.push(`<pre><code>${escapeHtml(buf.join("\n"))}</code></pre>`);
        continue;
      }

      if (i + 1 < lines.length && trimmed.includes("|") && isTableSep(lines[i + 1])) {
        const header = splitRow(line);
        i += 2;
        const body = [];
        while (i < lines.length && lines[i].includes("|") && !isTableSep(lines[i]) && lines[i].trim()) {
          body.push(splitRow(lines[i]));
          i += 1;
        }
        const thead = "<thead><tr>" + header.map((c) => `<th>${renderInline(c)}</th>`).join("") + "</tr></thead>";
        const tbody = "<tbody>" + body.map((row) => {
          const cells = header.map((_, idx) => `<td>${renderInline(row[idx] || "")}</td>`).join("");
          return `<tr>${cells}</tr>`;
        }).join("") + "</tbody>";
        html.push(`<table>${thead}${tbody}</table>`);
        continue;
      }

      const h = headingLevel(trimmed);
      if (h) {
        pushHeading(h.level, h.text);
        i += 1;
        continue;
      }

      if (isHr(trimmed)) {
        html.push("<hr>");
        i += 1;
        continue;
      }

      if (!safeText && (/^<a\s/i.test(trimmed) || /^<\/a>/i.test(trimmed))) {
        html.push(trimmed);
        i += 1;
        continue;
      }

      if (trimmed.startsWith(">")) {
        const buf = [];
        while (i < lines.length && lines[i].trim().startsWith(">")) {
          buf.push(lines[i].replace(/^\s*>\s?/, ""));
          i += 1;
        }
        html.push(`<blockquote>${renderInline(buf.join(" "))}</blockquote>`);
        continue;
      }

      if (/^[-*+]\s+/.test(trimmed) || /^\d+\.\s+/.test(trimmed)) {
        const ordered = /^\d+\.\s+/.test(trimmed);
        const items = [];
        while (i < lines.length) {
          const t = lines[i];
          if (!t.trim()) break;
          const m = ordered ? /^\s*\d+\.\s+(.*)$/.exec(t) : /^\s*[-*+]\s+(.*)$/.exec(t);
          if (!m) break;
          items.push(`<li>${renderInline(m[1])}</li>`);
          i += 1;
        }
        html.push(ordered ? `<ol>${items.join("")}</ol>` : `<ul>${items.join("")}</ul>`);
        continue;
      }

      const buf = [line];
      i += 1;
      while (i < lines.length) {
        const n = lines[i];
        if (!n.trim()) break;
        if (headingLevel(n.trim()) || n.trim().startsWith("```") || n.trim().startsWith(">") ||
            /^[-*+]\s+/.test(n.trim()) || /^\d+\.\s+/.test(n.trim()) ||
            (i + 1 < lines.length && n.includes("|") && isTableSep(lines[i + 1]))) {
          break;
        }
        buf.push(n);
        i += 1;
      }
      html.push(`<p>${renderInline(buf.join("\n")).replace(/\n/g, "<br>")}</p>`);
    }

    return safeText ? html.join("\n") : sanitizeHtml(html.join("\n"));
  }

  window.KBMarkdown = { parse, sanitizeHtml, escapeHtml };
})();
