const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

// Test the actual controls and animation lifecycle, not GPU appearance.
function harness({ reduced = false, webgl = true } = {}) {
  const elements = new Map(), callbacks = new Map();
  let sequence = 0, now = 0;
  const noop = () => {};
  const gl = new Proxy({}, { get(_, key) {
    if (key === 'getShaderParameter' || key === 'getProgramParameter') return () => true;
    if (key === 'isContextLost') return () => false;
    if (key === 'getUniformLocation' || key === 'getAttribLocation') return (_, name) => name;
    if (key.startsWith('create')) return () => ({});
    return /^[A-Z_]+$/.test(key) ? key : noop;
  } });
  const ctx = new Proxy({}, { get: () => noop });
  function element(id) {
    if (!elements.has(id)) elements.set(id, {
      dataset: {}, attributes: {}, events: {}, hidden: true, textContent: '',
      getBoundingClientRect: () => ({ width: 800, height: 720, left: 0, top: 0 }),
      getContext: kind => kind === 'webgl' ? (webgl ? gl : null) : ctx,
      addEventListener(name, fn) { this.events[name] = fn; },
      setAttribute(key, value) { this.attributes[key] = value; }
    });
    return elements.get(id);
  }
  const doc = { hidden: false, events: {}, getElementById: element, querySelectorAll: () => [],
    addEventListener(name, fn) { this.events[name] = fn; } };
  const context = {
    document: doc, window: { addEventListener() {} }, console: { warn() {} },
    devicePixelRatio: 1, innerWidth: 1280, innerHeight: 720,
    matchMedia: query => ({ matches: query.includes('reduced') ? reduced : false, addEventListener() {} }),
    requestAnimationFrame(fn) { callbacks.set(++sequence, fn); return sequence; },
    cancelAnimationFrame(id) { callbacks.delete(id); }
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../ion-scene.js'), 'utf8'), context);
  return {
    element, doc, pending: () => callbacks.size,
    click(id) { element(id).events.click(); },
    advance(frames) {
      for (let i = 0; i < frames; i++) {
        now += 34;
        const frame = [...callbacks.values()]; callbacks.clear(); frame.forEach(fn => fn(now));
      }
    }
  };
}

test('a manual request during an automatic transition advances beyond the visible shape', () => {
  const h = harness(); h.advance(225);
  assert.equal(h.element('shapeNumber').textContent, '02');
  h.click('shapeNext'); h.advance(120);
  assert.equal(h.element('shapeNumber').textContent, '03');
});

test('reduced motion starts with a static field and explicit controls still work', () => {
  const h = harness({ reduced: true });
  assert.equal(h.pending(), 0);
  assert.equal(h.element('motionToggle').attributes['aria-label'], '播放动效');
  h.click('shapeNext');
  assert.equal(h.element('shapeNumber').textContent, '02');
  assert.equal(h.pending(), 0);
  h.click('motionToggle');
  assert.equal(h.pending(), 1);
});

test('pause freezes the field and visibility restoration cannot override a user pause', () => {
  const h = harness(); h.advance(40); h.click('motionToggle');
  const name = h.element('shapeName').textContent;
  h.advance(400);
  assert.equal(h.element('shapeName').textContent, name);
  assert.equal(h.pending(), 0);
  h.doc.hidden = true; h.doc.events.visibilitychange();
  h.doc.hidden = false; h.doc.events.visibilitychange();
  assert.equal(h.pending(), 0);
  h.click('motionToggle'); assert.equal(h.pending(), 1);
});

test('WebGL failure leaves the static fallback and schedules no animation', () => {
  const h = harness({ webgl: false });
  assert.equal(h.element('ionScene').dataset.render, 'fallback');
  assert.equal(h.element('sceneToolbar').hidden, true);
  assert.equal(h.pending(), 0);
});
