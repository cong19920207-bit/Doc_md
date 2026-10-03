const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

// 只替代浏览器边界与网络时序，执行真实阅读器代码；布局另由浏览器验证。
function harness(fetch) {
  const elements = new Map();
  const timers = new Map();
  let timerId = 0;
  function element(id) {
    if (!elements.has(id)) elements.set(id, {
      innerHTML: '', textContent: '', hidden: true, value: '', scrollTop: 0,
      events: {}, classList: { add() {}, remove() {}, toggle() {} },
      querySelectorAll() { return []; }, querySelector() { return null; },
      addEventListener(name, fn) { this.events[name] = fn; },
      setAttribute() {}, contains() { return false; }
    });
    return elements.get(id);
  }
  const context = {
    window: { KBMarkdown: { escapeHtml: String, parse: String }, FEATURE_DATA: { features: [], adminNodes: [] }, addEventListener() {} },
    document: { readyState: 'complete', getElementById: element, querySelector: () => element('app'), querySelectorAll: () => [] },
    location: { protocol: 'http:' }, URL, fetch,
    setTimeout(fn) { timers.set(++timerId, fn); return timerId; },
    clearTimeout(id) { timers.delete(id); },
    requestAnimationFrame(fn) { return 0; }
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../kb.js'), 'utf8'), context);
  return { kb: context.window.KB, element, flushTimers() {
    const pending = [...timers.values()]; timers.clear(); pending.forEach(fn => fn());
  } };
}
const response = text => ({ ok: true, text: async () => text });
function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

test('an older failed document request cannot replace the newly opened document', async () => {
  const old = deferred();
  const h = harness(url => url === '/prd/old.md' ? old.promise : Promise.resolve(response('新文档正文')));
  const first = h.kb.openDocument('prd/old.md');
  await h.kb.openDocument('prd/new.md');
  old.reject(new Error('旧请求失败'));
  await first;
  assert.equal(h.element('kbArticle').innerHTML, '新文档正文');
  assert.equal(h.element('kbFail').hidden, true);
});

test('reopening the same path keeps the latest response rather than the oldest response', async () => {
  const old = deferred(); let calls = 0;
  const h = harness(() => ++calls === 1 ? old.promise : Promise.resolve(response('最新正文')));
  const first = h.kb.openDocument('prd/same.md');
  await h.kb.openDocument('prd/same.md');
  old.resolve(response('过期正文'));
  await first;
  assert.equal(h.element('kbArticle').innerHTML, '最新正文');
});

test('clearing search while the index loads does not bring old results back', async () => {
  const doc = deferred();
  const h = harness(url => url.endsWith('llm-manifest.json')
    ? Promise.resolve({ok:true,json:async()=>({scan_roots:['prd/topic.md']})})
    : doc.promise);
  const input = h.element('kbSearch');
  input.value = '关键词'; input.events.input(); h.flushTimers();
  input.value = ''; input.events.input(); h.flushTimers();
  doc.resolve(response('# 关键词\n正文'));
  for(let i=0;i<20;i++) await Promise.resolve();
  assert.equal(h.element('kbSearchPanel').hidden, true);
});
