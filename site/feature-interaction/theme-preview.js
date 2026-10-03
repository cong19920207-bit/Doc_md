/**
 * 工作台主题运行时：读 localStorage / ?theme=，挂或卸皮肤 CSS。
 * 空或非法值生效暖夜，不覆盖用户已保存的合法主题。
 */
(function () {
  var STORAGE_KEY = "hayyo-h5-theme";
  var FIRST_ID = "warm-night";
  var THEMES = [
    { id: "warm-night", name: "暖夜", description: "暖灰底 · 柔和杏色", bg: "#121313", panel: "#202323", accent: "#e9b77c", secondary: "#86b6bb" },
    { id: "default", name: "现网蓝灰", description: "蓝灰底 · 经典蓝色", bg: "#111318", panel: "#1a1d24", accent: "#6ea8fe", secondary: "#7dcea0" },
    { id: "a-gits", name: "攻壳青", description: "冷黑底 · 清透浅青", bg: "#07090b", panel: "#0e1418", accent: "#7ec8d0", secondary: "#6db89a" },
    { id: "b-2049", name: "2049 琥珀", description: "暖黑底 · 浓郁琥珀", bg: "#0a0908", panel: "#14110e", accent: "#e08a2c", secondary: "#7eb8c4" },
    { id: "c-nightcity", name: "夜之城黄", description: "纯黑底 · 荧光明黄", bg: "#000000", panel: "#0a0a0f", accent: "#fcee0a", secondary: "#00f0ff" },
    { id: "d-edgerunners", name: "边缘行者粉", description: "紫黑底 · 霓虹品红", bg: "#050508", panel: "#0c0a12", accent: "#ff3cac", secondary: "#3dfff3" },
    { id: "c-prime", name: "黄主色", description: "深灰底 · 黄青点缀", bg: "#07070a", panel: "#0c0c12", accent: "#fcee0a", secondary: "#3dfff3" }
  ];
  var SHEET_ATTR = "data-hayyo-theme-sheet";
  var activeTheme = FIRST_ID;

  function isLegal(id) {
    return THEMES.some(function (theme) { return theme.id === id; });
  }

  function readStored() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (err) {
      return null;
    }
  }

  function writeStored(id) {
    try {
      localStorage.setItem(STORAGE_KEY, id);
    } catch (err) {
      /* 无存储时仍可换皮 */
    }
  }

  function removeSheets() {
    var nodes = document.querySelectorAll("link[" + SHEET_ATTR + "]");
    for (var i = 0; i < nodes.length; i++) {
      nodes[i].parentNode.removeChild(nodes[i]);
    }
  }

  function addSheet(href) {
    var link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    link.setAttribute(SHEET_ATTR, "1");
    document.head.appendChild(link);
    return link;
  }

  function afterThemeCss(cb) {
    var links = document.querySelectorAll("link[" + SHEET_ATTR + "]");
    var finished = false;
    function run() {
      if (finished) return;
      finished = true;
      requestAnimationFrame(function () {
        requestAnimationFrame(cb);
      });
    }
    if (!links.length) {
      run();
      return;
    }
    var left = links.length;
    function one() {
      left -= 1;
      if (left <= 0) run();
    }
    for (var i = 0; i < links.length; i++) {
      var link = links[i];
      if (link.sheet) one();
      else {
        link.addEventListener("load", one);
        link.addEventListener("error", one);
      }
    }
    setTimeout(run, 400);
  }

  function syncPicker(id) {
    var current = THEMES.find(function (theme) { return theme.id === id; });
    var label = document.getElementById("themeCurrentName");
    var trigger = document.getElementById("themeTrigger");
    if (!current || !trigger) return;
    label.textContent = current.name;
    trigger.setAttribute("aria-label", "主题：" + current.name);
    document.querySelectorAll("[data-theme-option]").forEach(function (option) {
      option.setAttribute("aria-checked", String(option.getAttribute("data-theme-option") === id));
    });
  }

  function redrawGraph() {
    if (window.GraphApp && typeof window.GraphApp.redrawTheme === "function") {
      window.GraphApp.redrawTheme();
    }
  }

  /**
   * 套上指定主题。非法 id 回退 FIRST_ID 且不写入该非法值。
   * @param {string} id
   * @param {{write?: boolean}} opts write 默认仅在合法 id 时写入
   * @returns {string} 实际生效的 id
   */
  function applyTheme(id, opts) {
    opts = opts || {};
    var legal = isLegal(id);
    var effective = legal ? id : FIRST_ID;
    activeTheme = effective;
    document.documentElement.setAttribute("data-theme", effective);
    if (opts.write === true && legal) writeStored(effective);
    if (opts.write !== false && legal && opts.write !== true) writeStored(effective);

    removeSheets();
    if (effective !== "d-edgerunners") {
      addSheet("themes/" + effective + ".css");
      addSheet("themes/_apply.css");
    }
    syncPicker(effective);
    afterThemeCss(redrawGraph);
    return effective;
  }

  function bootFromQueryAndStorage() {
    var params = new URLSearchParams(location.search);
    var fromQuery = params.get("theme");
    if (fromQuery) {
      if (isLegal(fromQuery)) {
        applyTheme(fromQuery, { write: true });
      } else {
        applyTheme(FIRST_ID, { write: false });
      }
    } else {
      var stored = readStored();
      if (!stored) {
        applyTheme(FIRST_ID, { write: false });
      } else if (!isLegal(stored)) {
        applyTheme(FIRST_ID, { write: false });
      } else {
        applyTheme(stored, { write: false });
      }
    }
    return params;
  }

  function bindPicker() {
    var picker = document.getElementById("themePicker");
    var trigger = document.getElementById("themeTrigger");
    var menu = document.getElementById("themeMenu");
    var list = document.getElementById("themeOptions");
    if (!picker || picker.getAttribute("data-theme-bound") === "1") return;
    picker.setAttribute("data-theme-bound", "1");
    // 候选色只来自上面的固定主题清单，不使用外部 HTML。
    list.innerHTML = THEMES.map(function (theme) {
      return '<button class="theme-option" type="button" role="menuitemradio" tabindex="-1" aria-checked="false" aria-label="' + theme.name + '" data-theme-option="' + theme.id + '">' +
        '<span class="theme-preview" aria-hidden="true" style="--preview-bg:' + theme.bg + ';--preview-panel:' + theme.panel + ';--preview-accent:' + theme.accent + ';--preview-secondary:' + theme.secondary + '"><span class="theme-preview-dot"></span></span>' +
        '<span class="theme-option-copy"><span class="theme-option-name">' + theme.name + '</span><span class="theme-option-description">' + theme.description + '</span></span>' +
        '<span class="theme-option-check" aria-hidden="true">' + window.HayyoIcons.svg("check") + '</span></button>';
    }).join("");
    var options = Array.from(list.querySelectorAll("[data-theme-option]"));

    function positionMenu() {
      if (menu.hidden) return;
      var rect = trigger.getBoundingClientRect();
      var top = rect.bottom + 10;
      var left = Math.max(12, Math.min(rect.right - menu.offsetWidth, window.innerWidth - menu.offsetWidth - 12));
      menu.style.left = left + "px";
      menu.style.top = top + "px";
      menu.style.maxHeight = Math.max(0, window.innerHeight - top - 12) + "px";
    }

    function focusOption(index) {
      options.forEach(function (option, i) { option.tabIndex = i === index ? 0 : -1; });
      options[index].focus({ preventScroll: true });
      options[index].scrollIntoView({ block: "nearest" });
    }

    function closeMenu(restoreFocus) {
      if (menu.hidden) return;
      menu.hidden = true;
      trigger.setAttribute("aria-expanded", "false");
      if (restoreFocus) trigger.focus({ preventScroll: true });
    }

    function openMenu() {
      menu.hidden = false;
      trigger.setAttribute("aria-expanded", "true");
      positionMenu();
      focusOption(Math.max(0, THEMES.findIndex(function (theme) { return theme.id === activeTheme; })));
    }

    trigger.addEventListener("click", function () {
      if (menu.hidden) openMenu();
      else closeMenu(false);
    });
    trigger.addEventListener("keydown", function (event) {
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault(); openMenu();
      }
    });
    list.addEventListener("click", function (event) {
      var option = event.target.closest("[data-theme-option]");
      if (!option) return;
      applyTheme(option.getAttribute("data-theme-option"));
      closeMenu(true);
    });
    picker.addEventListener("keydown", function (event) {
      if (menu.hidden) return;
      if (event.key === "Escape") {
        event.preventDefault(); event.stopPropagation(); closeMenu(true); return;
      }
      // 先回到触发器，再由浏览器自然移动到相邻控件。
      if (event.key === "Tab") { closeMenu(true); return; }
      if (!list.contains(event.target)) return;
      var index = options.indexOf(document.activeElement);
      if (event.key === "ArrowDown") index = (index + 1) % options.length;
      else if (event.key === "ArrowUp") index = (index + options.length - 1) % options.length;
      else if (event.key === "Home") index = 0;
      else if (event.key === "End") index = options.length - 1;
      else return;
      event.preventDefault(); focusOption(index);
    });
    document.addEventListener("pointerdown", function (event) {
      if (!picker.contains(event.target)) closeMenu(false);
    });
    document.addEventListener("focusin", function (event) {
      if (!picker.contains(event.target)) closeMenu(false);
    });
    window.addEventListener("resize", positionMenu);
  }

  function applyView(params) {
    var view = params.get("view");
    if (!view || !window.GraphApp || typeof window.GraphApp.setView !== "function") return;
    window.GraphApp.setView(view);
  }

  var params = bootFromQueryAndStorage();
  window.applyTheme = applyTheme;

  function onReady() {
    bindPicker();
    syncPicker(activeTheme);
    setTimeout(function () {
      applyView(params);
    }, 0);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onReady);
  } else {
    onReady();
  }
})();
