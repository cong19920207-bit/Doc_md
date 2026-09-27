/**
 * 工作台主题运行时：读 localStorage / ?theme=，挂或卸皮肤 CSS。
 * 空或非法值生效边缘行者粉（:root 基线），不自动写入空键。
 */
(function () {
  var STORAGE_KEY = "hayyo-h5-theme";
  var FIRST_ID = "d-edgerunners";
  var THEME_IDS = {
    "default": true,
    "a-gits": true,
    "b-2049": true,
    "c-nightcity": true,
    "d-edgerunners": true,
    "c-prime": true
  };
  var SHEET_ATTR = "data-hayyo-theme-sheet";

  function isLegal(id) {
    return Boolean(id && THEME_IDS[id]);
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

  function syncSelect(id) {
    var sel = document.querySelector('select[aria-label="主题"]');
    if (sel && sel.value !== id) sel.value = id;
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
    if (opts.write === true && legal) writeStored(effective);
    if (opts.write !== false && legal && opts.write !== true) writeStored(effective);

    removeSheets();
    if (effective !== FIRST_ID) {
      addSheet("themes/" + effective + ".css");
      addSheet("themes/_apply.css");
    }
    syncSelect(effective);
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

  function bindSelect() {
    var sel = document.querySelector('select[aria-label="主题"]');
    if (!sel || sel.getAttribute("data-theme-bound") === "1") return;
    sel.setAttribute("data-theme-bound", "1");
    sel.addEventListener("change", function () {
      applyTheme(sel.value);
    });
  }

  function applyView(params) {
    var view = params.get("view");
    if (!view || !window.GraphApp || typeof window.GraphApp.setView !== "function") return;
    window.GraphApp.setView(view);
  }

  var params = bootFromQueryAndStorage();
  window.applyTheme = applyTheme;

  function onReady() {
    bindSelect();
    var stored = readStored();
    var current = isLegal(stored) ? stored : FIRST_ID;
    if (params.get("theme") && isLegal(params.get("theme"))) current = params.get("theme");
    syncSelect(current);
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
