/* 独立管理站。按勾选展示内页；证书/开户/解锁仅超管。不套用演示皮肤。 */
(function () {
  const API = "/api/kb";
  const PAGES = [
    { id: "config", perm: "配置", label: "配置" },
    { id: "reindex", perm: "重建", label: "重建" },
    { id: "rounds", perm: "问答明细", label: "问答明细" },
    { id: "heatmap", perm: "功能热度", label: "功能热度" },
    { id: "convs", perm: "对话审计", label: "对话审计" },
    { id: "health", perm: "健康", label: "健康" },
    { id: "audits", perm: "操作审计", label: "操作审计" },
    { id: "feedback", perm: "反馈汇总", label: "反馈汇总" }
  ];
  const SUPER_PAGES = [
    { id: "accounts", label: "账号" },
    { id: "roles", label: "角色" },
    { id: "unlock", label: "解锁" },
    { id: "tls", label: "证书" }
  ];

  const els = {
    nav: document.getElementById("adminNav"),
    main: document.getElementById("adminMain"),
    user: document.getElementById("adminUser")
  };
  const state = { me: null, page: "rounds" };

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function hasPerm(name) {
    if (!state.me) return false;
    if (state.me.is_super) return true;
    return (state.me.permissions || []).indexOf(name) >= 0;
  }

  function visiblePages() {
    const out = PAGES.filter(function (p) { return hasPerm(p.perm); });
    if (state.me && state.me.is_super) {
      SUPER_PAGES.forEach(function (p) { out.push(p); });
    }
    return out;
  }

  async function api(path, opts) {
    const res = await fetch(API + path, Object.assign({ credentials: "same-origin" }, opts || {}));
    const data = await res.json().catch(function () { return {}; });
    if (!res.ok) {
      const err = new Error(data.message || ("HTTP " + res.status));
      err.status = res.status;
      throw err;
    }
    return data;
  }

  function renderNav() {
    const pages = visiblePages();
    if (!pages.some(function (p) { return p.id === state.page; })) {
      state.page = pages.length ? pages[0].id : "";
    }
    els.nav.innerHTML = pages.map(function (p) {
      return '<button type="button" data-page="' + p.id + '"' +
        (p.id === state.page ? ' class="active"' : "") + ">" + escapeHtml(p.label) + "</button>";
    }).join("");
  }

  async function showPage() {
    try {
      if (state.page === "config") await pageConfig();
      else if (state.page === "reindex") await pageReindex();
      else if (state.page === "rounds") await pageRounds();
      else if (state.page === "heatmap") await pageHeatmap();
      else if (state.page === "convs") await pageConvs();
      else if (state.page === "health") await pageHealth();
      else if (state.page === "audits") await pageAudits();
      else if (state.page === "feedback") await pageFeedback();
      else if (state.page === "accounts") await pageAccounts();
      else if (state.page === "roles") await pageRoles();
      else if (state.page === "unlock") await pageUnlock();
      else if (state.page === "tls") await pageTls();
      else els.main.innerHTML = "<p>没有可显示的页面。</p>";
    } catch (e) {
      els.main.innerHTML = '<h2>无法打开</h2><p class="kb-admin-err">' + escapeHtml(e.message) + "</p>";
    }
  }

  async function pageConfig() {
    const cfg = await api("/config");
    const wr = cfg.writable || {};
    const ro = cfg.readonly || {};
    const keys = Object.keys(wr);
    els.main.innerHTML =
      "<h2>配置</h2>" +
      '<form class="kb-admin-form" id="cfgForm">' +
        keys.map(function (k) {
          const val = wr[k];
          const tag = String(k).indexOf("prompt") >= 0 || String(k).indexOf("Prompt") >= 0 ? "textarea" : "input";
          if (tag === "textarea") {
            return "<label>" + escapeHtml(k) + "<textarea name=\"" + escapeHtml(k) + "\">" + escapeHtml(val) + "</textarea></label>";
          }
          return "<label>" + escapeHtml(k) + "<input name=\"" + escapeHtml(k) + "\" value=\"" + escapeHtml(val) + "\"></label>";
        }).join("") +
        '<button class="kb-btn" type="submit">保存</button>' +
      "</form>" +
      "<p class=\"kb-admin-msg\">只读：" + escapeHtml(JSON.stringify(ro)) + "</p>";
    document.getElementById("cfgForm").addEventListener("submit", async function (ev) {
      ev.preventDefault();
      const body = {};
      keys.forEach(function (k) {
        const node = ev.target.elements[k];
        body[k] = node ? node.value : wr[k];
      });
      await api("/config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      alert("已保存，下一轮生效");
    });
  }

  function renderReindexResult(data) {
    const rows = (data.changed || []).concat(data.failed || []);
    const table = rows.length
      ? "<table><thead><tr><th>path</th><th>chunk_id</th><th>action</th><th>旧 hash</th><th>新 hash</th><th>失败</th></tr></thead><tbody>" +
        rows.map(function (r) {
          return "<tr><td>" + escapeHtml(r.path) + "</td><td>" + escapeHtml(r.chunk_id) + "</td><td>" +
            escapeHtml(r.action) + "</td><td>" + escapeHtml(r.old_hash || "") + "</td><td>" +
            escapeHtml(r.new_hash || "") + "</td><td>" + escapeHtml(r.reason || "") + "</td></tr>";
        }).join("") + "</tbody></table>"
      : "<p>无变更。</p>";
    return "<p>扫描 " + escapeHtml(String(data.scanned || 0)) + " 块，库内 " +
      escapeHtml(String(data.chunk_count || 0)) + " 点。</p>" + table;
  }

  async function pageReindex() {
    els.main.innerHTML =
      "<h2>重建</h2>" +
      "<p>按内容 hash 增量对账。打开本页不会自动执行。</p>" +
      '<p><button class="kb-btn" type="button" id="reindexGo">开始重建</button></p>' +
      '<div id="reindexOut"></div>';
    document.getElementById("reindexGo").onclick = async function () {
      const btn = document.getElementById("reindexGo");
      const out = document.getElementById("reindexOut");
      btn.disabled = true;
      out.innerHTML = "<p>正在重建…</p>";
      try {
        const data = await api("/reindex", { method: "POST" });
        out.innerHTML = renderReindexResult(data);
      } catch (e) {
        out.innerHTML = '<p class="kb-admin-err">' + escapeHtml(e.message) + "</p>";
      }
      btn.disabled = false;
    };
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

  async function pageRounds(detailId) {
    if (detailId) {
      const row = await api("/rounds/" + encodeURIComponent(detailId));
      els.main.innerHTML =
        "<h2>问答明细</h2>" +
        '<p><button class="kb-btn" type="button" data-back-rounds>返回列表</button></p>' +
        "<p>round_id = " + escapeHtml(row.round_id) + "</p>" +
        "<p>账号 = " + escapeHtml(accountName(row)) + "</p>" +
        "<p>status = " + escapeHtml(row.status) + "</p>" +
        "<p><b>原句</b></p><div class=\"qa-detail-pre\">" + escapeHtml(row.original_query || "") + "</div>" +
        "<p><b>改写句</b></p><div class=\"qa-detail-pre\">" + escapeHtml(row.rewrite_query || "") + "</div>" +
        "<p><b>回答</b></p><div class=\"qa-detail-pre\">" + escapeHtml(row.answer || "") + "</div>" +
        "<p>反馈 " + escapeHtml(feedbackLabel(row)) + "</p>";
      document.querySelector("[data-back-rounds]").onclick = function () { pageRounds(); };
      return;
    }
    const data = await api("/rounds?limit=200");
    const items = data.items || [];
    const rows = items.map(function (r) {
      return "<tr><td>" + escapeHtml(r.created_at || "") + "</td><td>" + escapeHtml(accountName(r)) +
        "</td><td>" + escapeHtml(r.round_id || "") +
        "</td><td>" + escapeHtml(r.status || "") + "</td><td>" + escapeHtml(r.original_query || "") +
        "</td><td>" + escapeHtml(feedbackLabel(r)) +
        "</td><td><button class=\"kb-btn\" type=\"button\" data-round=\"" + escapeHtml(r.round_id) + "\">打开</button></td></tr>";
    }).join("");
    els.main.innerHTML =
      "<h2>问答明细</h2>" +
      (rows
        ? "<table><thead><tr><th>时间</th><th>账号</th><th>round_id</th><th>结果</th><th>原句</th><th>反馈</th><th></th></tr></thead><tbody>" + rows + "</tbody></table>"
        : "<p>暂无已写入的轮次。</p>");
    els.main.querySelectorAll("[data-round]").forEach(function (btn) {
      btn.onclick = function () { pageRounds(btn.getAttribute("data-round")); };
    });
  }

  async function pageHeatmap() {
    const data = await api("/admin/heatmap");
    const items = data.items || [];
    const rows = items.map(function (r) {
      return "<tr><td>" + escapeHtml(r.display_name || r.feature_id) + "</td><td>" + escapeHtml(String(r.count)) + "</td></tr>";
    }).join("");
    els.main.innerHTML = "<h2>功能热度</h2><table><thead><tr><th>功能</th><th>count</th></tr></thead><tbody>" +
      rows +
      (Number(data.unclassified || 0) > 0 ? "<tr><td>未归类</td><td>" + escapeHtml(String(data.unclassified)) + "</td></tr>" : "") +
      "</tbody></table>";
  }

  async function pageConvs() {
    const data = await api("/admin/conversations");
    const rows = (data.items || []).map(function (r) {
      return "<tr><td>" + escapeHtml(r.id) + "</td><td>" + escapeHtml(accountName(r)) + "</td><td>" + escapeHtml(r.title) + "</td></tr>";
    }).join("");
    els.main.innerHTML = "<h2>对话审计</h2><table><thead><tr><th>会话 id</th><th>账号</th><th>标题</th></tr></thead><tbody>" + rows + "</tbody></table>";
  }

  async function pageHealth() {
    const data = await fetch(API + "/health", { credentials: "same-origin" }).then(function (r) { return r.json(); });
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
    els.main.innerHTML = "<h2>健康</h2><table><tbody>" +
      rows.map(function (r) {
        return "<tr><th>" + escapeHtml(r[0]) + "</th><td>" + escapeHtml(r[1]) + "</td></tr>";
      }).join("") +
      "</tbody></table>";
  }

  async function pageAudits() {
    const data = await api("/admin/audits");
    const rows = (data.items || []).map(function (r) {
      return "<tr><td>" + escapeHtml(r.created_at) + "</td><td>" + escapeHtml(accountName({ username: r.actor_username })) +
        "</td><td>" + escapeHtml(r.action) + "</td><td>" + escapeHtml(r.object) +
        "</td><td>" + escapeHtml(JSON.stringify(r.detail || {})) + "</td></tr>";
    }).join("");
    els.main.innerHTML = "<h2>操作审计</h2><table><thead><tr><th>时间</th><th>操作者</th><th>动作</th><th>对象</th><th>字段</th></tr></thead><tbody>" + rows + "</tbody></table>";
  }

  async function pageFeedback() {
    const data = await api("/admin/feedback-summary");
    const rows = (data.down || []).map(function (r) {
      return "<tr><td>" + escapeHtml(r.round_id) + "</td><td>" + escapeHtml(r.created_at) +
        "</td><td>" + escapeHtml(r.original_query) +
        "</td><td><button class=\"kb-btn\" type=\"button\" data-fb-round=\"" + escapeHtml(r.round_id) + "\">详情</button></td></tr>";
    }).join("");
    els.main.innerHTML = "<h2>反馈汇总</h2><p>被踩列表</p>" +
      (rows ? "<table><thead><tr><th>round_id</th><th>时间</th><th>原句</th><th></th></tr></thead><tbody>" + rows + "</tbody></table>" : "<p>无</p>");
    els.main.querySelectorAll("[data-fb-round]").forEach(function (btn) {
      btn.onclick = function () {
        state.page = "rounds";
        renderNav();
        pageRounds(btn.getAttribute("data-fb-round"));
      };
    });
  }

  async function pageAccounts() {
    const roles = await api("/admin/roles");
    const data = await api("/admin/accounts");
    const roleOpts = (roles.items || []).map(function (r) {
      return "<option value=\"" + escapeHtml(r.id) + "\">" + escapeHtml(r.name) + "</option>";
    }).join("");
    const rows = (data.items || []).map(function (a) {
      return "<tr><td>" + escapeHtml(a.username) + "</td><td>" + escapeHtml(a.role_name) +
        "</td><td>" + (a.enabled ? "启用" : "禁用") +
        "</td><td><button class=\"kb-btn\" type=\"button\" data-toggle=\"" + escapeHtml(a.id) + "\" data-enabled=\"" + (a.enabled ? "0" : "1") + "\">" +
        (a.enabled ? "禁用" : "启用") + "</button></td></tr>";
    }).join("");
    els.main.innerHTML =
      "<h2>账号</h2>" +
      '<form class="kb-admin-form" id="createUser">' +
        "<label>用户名<input name=\"username\" required></label>" +
        "<label>初始密码<input name=\"password\" type=\"password\" required></label>" +
        "<label>角色<select name=\"role_id\">" + roleOpts + "</select></label>" +
        '<button class="kb-btn" type="submit">开户</button>' +
      "</form>" +
      "<table><thead><tr><th>用户</th><th>角色</th><th>状态</th><th></th></tr></thead><tbody>" + rows + "</tbody></table>";
    document.getElementById("createUser").onsubmit = async function (ev) {
      ev.preventDefault();
      await api("/admin/accounts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: ev.target.username.value,
          password: ev.target.password.value,
          role_id: ev.target.role_id.value
        })
      });
      pageAccounts();
    };
    els.main.querySelectorAll("[data-toggle]").forEach(function (btn) {
      btn.onclick = async function () {
        await api("/admin/accounts/" + encodeURIComponent(btn.getAttribute("data-toggle")), {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enabled: btn.getAttribute("data-enabled") === "1" })
        });
        pageAccounts();
      };
    });
  }

  async function pageRoles() {
    const data = await api("/admin/roles");
    const boxes = (data.checkboxes || []).map(function (p) {
      return "<label><input type=\"checkbox\" value=\"" + escapeHtml(p) + "\"> " + escapeHtml(p) + "</label>";
    }).join("");
    const rows = (data.items || []).map(function (r) {
      return "<tr><td>" + escapeHtml(r.name) + "</td><td>" + escapeHtml((r.permissions || []).join("、")) +
        "</td><td>" + (r.is_super ? "超管" : "") + "</td></tr>";
    }).join("");
    els.main.innerHTML =
      "<h2>角色</h2>" +
      '<form class="kb-admin-form" id="createRole">' +
        "<label>名称<input name=\"name\" required></label>" +
        "<div class=\"kb-admin-checks\">" + boxes + "</div>" +
        '<button class="kb-btn" type="submit">新建角色</button>' +
      "</form>" +
      "<table><thead><tr><th>角色</th><th>勾选</th><th></th></tr></thead><tbody>" + rows + "</tbody></table>";
    document.getElementById("createRole").onsubmit = async function (ev) {
      ev.preventDefault();
      const perms = Array.prototype.slice.call(ev.target.querySelectorAll("input[type=checkbox]:checked")).map(function (n) { return n.value; });
      await api("/admin/roles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: ev.target.name.value, permissions: perms })
      });
      pageRoles();
    };
  }

  async function pageUnlock() {
    els.main.innerHTML =
      "<h2>解锁</h2>" +
      '<form class="kb-admin-form" id="unlockForm">' +
        "<label>用户名<input name=\"username\" required></label>" +
        '<button class="kb-btn" type="submit">清除失败次数</button>' +
      "</form><p id=\"unlockMsg\" class=\"kb-admin-msg\"></p>";
    document.getElementById("unlockForm").onsubmit = async function (ev) {
      ev.preventDefault();
      await api("/admin/unlock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: ev.target.username.value })
      });
      document.getElementById("unlockMsg").textContent = "已解锁，可立即登录";
    };
  }

  async function pageTls() {
    const st = await api("/admin/tls");
    els.main.innerHTML =
      "<h2>证书</h2>" +
      "<p>当前：" + (st.enabled ? "已启用（本机非 80/443 不强制跳转）" : "HTTP") +
      "；已保存证书 " + (st.has_cert ? "是" : "否") + "</p>" +
      '<form class="kb-admin-form" id="tlsForm">' +
        "<label>证书 PEM<textarea name=\"cert_pem\" rows=\"8\"></textarea></label>" +
        "<label>私钥 PEM<textarea name=\"key_pem\" rows=\"8\"></textarea></label>" +
        '<button class="kb-btn" type="submit">只保存</button>' +
      "</form>" +
      '<p><button class="kb-btn" type="button" id="tlsEnable">启用 HTTPS</button> ' +
      '<button class="kb-btn" type="button" id="tlsDisable">关闭回 HTTP</button></p>' +
      '<p id="tlsMsg" class="kb-admin-msg"></p>';
    document.getElementById("tlsForm").onsubmit = async function (ev) {
      ev.preventDefault();
      await api("/admin/tls", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cert_pem: ev.target.cert_pem.value, key_pem: ev.target.key_pem.value })
      });
      document.getElementById("tlsMsg").textContent = "已保存，尚未启用";
    };
    document.getElementById("tlsEnable").onclick = async function () {
      try {
        await api("/admin/tls/enable", { method: "POST" });
        document.getElementById("tlsMsg").textContent = "已启用";
      } catch (e) {
        document.getElementById("tlsMsg").textContent = e.message;
      }
    };
    document.getElementById("tlsDisable").onclick = async function () {
      await api("/admin/tls/disable", { method: "POST" });
      document.getElementById("tlsMsg").textContent = "已关闭，对外仍为 HTTP";
    };
  }

  els.nav.addEventListener("click", function (ev) {
    const btn = ev.target.closest("[data-page]");
    if (!btn) return;
    state.page = btn.getAttribute("data-page");
    renderNav();
    showPage();
  });

  async function boot() {
    try {
      state.me = await api("/auth/me");
    } catch (e) {
      if (e.status === 401) {
        window.location.replace("/login/?next=" + encodeURIComponent("/kb-admin/"));
        return;
      }
      els.main.innerHTML = '<p class="kb-admin-err">没有权限</p>';
      return;
    }
    if (!hasPerm("进管理模块")) {
      els.main.innerHTML = '<p class="kb-admin-err">没有权限</p>';
      return;
    }
    els.user.textContent = state.me.username || "";
    renderNav();
    showPage();
  }

  boot();
})();
