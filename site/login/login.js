/**
 * 独立登录页：复用现有 Session 登录接口。
 * next 只接受站内相对路径，避免跳到站外。
 */
(function () {
  var API = "/api/kb";
  var DEFAULT_NEXT = "/feature-interaction/";

  var form = document.getElementById("loginForm");
  var userEl = document.getElementById("loginUser");
  var passEl = document.getElementById("loginPass");
  var errEl = document.getElementById("loginErr");
  var submitEl = document.getElementById("loginSubmit");
  var submitText = document.getElementById("loginSubmitText");
  var passwordToggle = document.getElementById("passwordToggle");
  var pending = false;

  function setPending(value) {
    pending = value;
    if (submitEl) submitEl.disabled = value;
    if (submitText) submitText.textContent = value ? "正在登录…" : "登录工作台";
    if (form) form.setAttribute("aria-busy", String(value));
  }

  function showErr(text) {
    if (!errEl) return;
    errEl.hidden = !text;
    errEl.textContent = text || "";
  }

  function safeNext(raw) {
    var value = String(raw || "").trim();
    if (!value || value.charAt(0) !== "/" || value.charAt(1) === "/") {
      return DEFAULT_NEXT;
    }
    if (value.indexOf("\\") >= 0 || value.indexOf("://") >= 0) {
      return DEFAULT_NEXT;
    }
    var path = value.split("?")[0].split("#")[0];
    if (path === "/login" || path.indexOf("/login/") === 0) {
      return DEFAULT_NEXT;
    }
    return value;
  }

  function nextFromQuery() {
    try {
      return safeNext(new URLSearchParams(window.location.search).get("next"));
    } catch (e) {
      return DEFAULT_NEXT;
    }
  }

  function goNext() {
    window.location.replace(nextFromQuery());
  }

  async function checkAlreadyIn() {
    try {
      var res = await fetch(API + "/auth/me", { credentials: "same-origin" });
      if (res.ok) goNext();
    } catch (e) {
      /* 未登录则留在本页 */
    }
  }

  async function submitLogin(ev) {
    if (ev) ev.preventDefault();
    if (pending) return;
    var username = userEl ? String(userEl.value || "").trim() : "";
    var password = passEl ? String(passEl.value || "") : "";
    showErr("");
    setPending(true);
    try {
      var res = await fetch(API + "/auth/login", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username, password: password })
      });
      var data = await res.json().catch(function () { return {}; });
      if (!res.ok) {
        showErr(data.message || "登录失败");
        return;
      }
      if (passEl) passEl.value = "";
      goNext();
    } catch (e) {
      showErr("连接失败，请检查网络后重试。");
    } finally {
      setPending(false);
    }
  }

  if (passwordToggle && passEl) passwordToggle.addEventListener("click", function () {
    var visible = passEl.type === "password";
    passEl.type = visible ? "text" : "password";
    passwordToggle.setAttribute("aria-pressed", String(visible));
    passwordToggle.setAttribute("aria-label", visible ? "隐藏密码" : "显示密码");
  });
  if (form) form.addEventListener("submit", submitLogin);
  checkAlreadyIn();
})();
