const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

// Execute the browser login script; replace only DOM/network boundaries.
function harness({ search = '', fetchLogin, alreadyIn = false } = {}) {
  const elements = new Map();
  const calls = [];
  const redirects = [];
  function element(id) {
    if (!elements.has(id)) elements.set(id, {
      value: '', hidden: true, disabled: false, type: id === 'loginPass' ? 'password' : 'text',
      textContent: '', events: {}, attributes: {},
      addEventListener(type, fn) { this.events[type] = fn; },
      setAttribute(key, value) { this.attributes[key] = String(value); },
      getAttribute(key) { return this.attributes[key]; },
      removeAttribute(key) { delete this.attributes[key]; },
      focus() {}, classList: { toggle() {} }
    });
    return elements.get(id);
  }
  const context = {
    URL, URLSearchParams,
    window: { location: { search, origin: 'http://localhost', replace: value => redirects.push(value) } },
    document: { getElementById: element },
    fetch: async (url, options) => {
      if (url.endsWith('/me')) return { ok: alreadyIn };
      calls.push({ url, options });
      return fetchLogin ? fetchLogin() : { ok: true, json: async () => ({ ok: true }) };
    }
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../login.js'), 'utf8'), context);
  element('loginUser').value = '  test-user  ';
  element('loginPass').value = ' test-password ';
  return { element, calls, redirects, submit: () => element('loginForm').events.submit({ preventDefault() {} }) };
}

test('pending login submits once and presents a busy state', async () => {
  let resolve;
  const request = new Promise(r => { resolve = r; });
  const h = harness({ fetchLogin: () => request });
  const first = h.submit();
  const second = h.submit();
  assert.equal(h.calls.length, 1);
  assert.equal(h.element('loginSubmit').disabled, true);
  assert.equal(h.element('loginForm').attributes['aria-busy'], 'true');
  resolve({ ok: true, json: async () => ({ ok: true }) });
  await Promise.all([first, second]);
});

test('a server rejection remains visible and permits retry', async () => {
  let tries = 0;
  const h = harness({ fetchLogin: async () => ++tries === 1
    ? { ok: false, json: async () => ({ message: '用户名或密码不正确' }) }
    : { ok: true, json: async () => ({ ok: true }) } });
  await h.submit();
  assert.equal(h.element('loginErr').textContent, '用户名或密码不正确');
  assert.equal(h.element('loginErr').hidden, false);
  assert.equal(h.element('loginSubmit').disabled, false);
  assert.equal(h.redirects.length, 0);
  await h.submit();
  assert.equal(h.redirects[0], '/feature-interaction/');
});

test('network failure restores the form and explains retry', async () => {
  const h = harness({ fetchLogin: async () => { throw new Error('offline'); } });
  await h.submit();
  assert.equal(h.element('loginSubmit').disabled, false);
  assert.match(h.element('loginErr').textContent, /网络|连接/);
  assert.equal(h.redirects.length, 0);
});

test('password visibility is accessible and does not submit credentials', () => {
  const h = harness();
  const toggle = h.element('passwordToggle');
  assert.equal(typeof toggle.events.click, 'function');
  toggle.events.click();
  assert.equal(h.element('loginPass').type, 'text');
  assert.equal(toggle.attributes['aria-pressed'], 'true');
  assert.equal(toggle.attributes['aria-label'], '隐藏密码');
  toggle.events.click();
  assert.equal(h.element('loginPass').type, 'password');
  assert.equal(toggle.attributes['aria-pressed'], 'false');
  assert.equal(h.calls.length, 0);
});

test('credentials retain password whitespace and use the existing Session endpoint', async () => {
  const h = harness();
  await h.submit();
  assert.equal(h.calls[0].url, '/api/kb/auth/login');
  assert.equal(h.calls[0].options.credentials, 'same-origin');
  assert.deepEqual(JSON.parse(h.calls[0].options.body), { username: 'test-user', password: ' test-password ' });
  assert.equal(h.element('loginPass').value, '');
});

test('successful login preserves an internal next path and query', async () => {
  const h = harness({ search: '?next=' + encodeURIComponent('/kb-admin/?tab=overview#top') });
  await h.submit();
  assert.deepEqual(h.redirects, ['/kb-admin/?tab=overview#top']);
});

test('unsafe, external and recursive destinations fall back to the workbench', async () => {
  for (const next of ['https://example.com', '//example.com', '/\\example.com', '/login/', '/login?x=1', '']) {
    const h = harness({ search: '?next=' + encodeURIComponent(next) });
    await h.submit();
    assert.deepEqual(h.redirects, ['/feature-interaction/'], next);
  }
});

test('an existing session follows the same safe redirect without submitting', async () => {
  const h = harness({ alreadyIn: true, search: '?next=%2Fkb-admin%2F' });
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(h.redirects, ['/kb-admin/']);
  assert.equal(h.calls.length, 0);
});
