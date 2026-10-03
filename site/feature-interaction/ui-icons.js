/* 工作台统一图标：24px 几何线框，断开边角与连接节点共用同一笔画。 */
(function () {
  const paths = {
    palette: '<path d="m7 3 4 4-4 4-4-4Zm10 0 4 4-4 4-4-4ZM7 13l4 4-4 4-4-4Z"/><path d="M15 17h6m-3-3v6"/>',
    chevron: '<path d="m6 9 6 6 6-6"/>',
    check: '<path d="m5 12 4 4L19 6"/>',
    core: '<path d="m12 2 8.5 5v10L12 22l-8.5-5V7Z"/><path d="M8 7v10m8-10v10M8 12h8"/><path d="M3.5 7 8 9m8 6 4.5 2"/>',
    qa: '<path d="M8 4H4v13h5l3 3 3-3h5V4h-4M9 4h6"/><path d="M8 9h8M8 13h5"/><circle cx="18" cy="4" r="1"/>',
    admin: '<rect x="2" y="5" width="7" height="14" rx="1.5"/><path d="M15 3h7v7h-7zM15 14h7v7h-7zM9 12h3m0-5v10m0-10h3m-3 10h3"/>',
    client: '<path d="m12 3 4 4-4 4-4-4Zm-6 9 4 4-4 4-4-4Zm12 0 4 4-4 4-4-4ZM8 10l-2 2m10-2 2 2M10 16h4"/>',
    book: '<path d="M3 4h7l2 2 2-2h7v15h-7l-2 2-2-2H3ZM12 6v15M6 8h3M6 12h3m6-4h3m-3 4h3"/>',
    search: '<path d="M10 3H6L3 6v7l3 3h7l3-3V6l-3-3ZM16 16l5 5M7 7h5"/>',
    plus: '<path d="M4 8V4h4m8 0h4v4m0 8v4h-4M8 20H4v-4M12 7v10m-5-5h10"/>',
    thread: '<path d="M4 3h16v13h-8l-5 5v-5H4ZM8 7h8m-8 5h5"/>',
    send: '<path d="m4 20 6-16h4l6 16-8-4Zm8-4V8"/>',
    close: '<path d="m6 6 12 12M18 6 6 18"/>',
    trash: '<path d="M3 6h18M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7m4-7v7"/>',
    copy: '<path d="M8 8h13v13H8ZM16 4V2H2v14h2"/>',
    up: '<path d="M4 10h4v11H4Zm4 0 4-8 3 1-1 7h6l1 3-3 8H8"/>',
    down: '<path d="M4 3h4v11H4Zm4 11 4 8 3-1-1-7h6l1-3-3-8H8"/>',
    regen: '<path d="M20 8a9 9 0 0 0-15-3L2 8m0-6v6h6m-4 8a9 9 0 0 0 15 3l3-3m0 6v-6h-6"/>',
    cite: '<path d="M4 3h11l5 5v13H4ZM15 3v5h5M8 12h8m-8 4h5"/>',
    fit: '<path d="M3 8V3h5m8 0h5v5M3 16v5h5m8 0h5v-5M8 8h8v8H8Z"/>',
    zoomIn: '<path d="M5 12h14M12 5v14"/>',
    zoomOut: '<path d="M5 12h14"/>',
    focus: '<path d="M3 8V3h5m8 0h5v5M3 16v5h5m8 0h5v-5"/><circle cx="12" cy="12" r="4"/><path d="M12 10v4m-2-2h4"/>',
    arrow: '<path d="M4 12h16m-6-6 6 6-6 6"/>',
    filter: '<path d="M3 5h18M6 12h12m-9 7h6"/><path d="M7 3v4m10 3v4m-5 3v4"/>',
    folder: '<path d="M3 5h7l2 3h9v12H3ZM3 12h18"/>',
    history: '<path d="M3 9a9 9 0 1 1 0 7M3 3v6h6M12 7v6l4 2"/>',
    link: '<path d="m9 7 3-3a5 5 0 0 1 7 7l-3 3M8 10l-3 3a5 5 0 0 0 7 7l3-3M8 16l8-8"/>',
    user: '<path d="m12 3 4 2v5l-4 2-4-2V5Zm-8 18v-4l5-3h6l5 3v4"/>'
  };
  function svg(name, className) {
    const cls = String(className || 'ui-icon').replace(/[^a-zA-Z0-9 _-]/g, '');
    return '<svg class="' + cls + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (paths[name] || paths.core) + '</svg>';
  }
  function hydrate(root) {
    (root || document).querySelectorAll('[data-icon]').forEach(function (el) {
      el.innerHTML = svg(el.getAttribute('data-icon'));
    });
  }
  window.HayyoIcons = { svg, hydrate };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { hydrate(); });
  else hydrate();
})();
