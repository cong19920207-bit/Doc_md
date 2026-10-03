const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const context = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../kb-md.js'), 'utf8'), context);
const render = text => context.window.KBMarkdown.parse(text, { safeText: true });

test('answers render headings, emphasis, lists and source quotes as readable HTML', () => {
  const html = render('# 冻结规则\n\n**可以充值**，`不能转账`。\n\n- 仅代理账户\n- 不影响充值\n\n> 只进不出');
  assert.match(html, /<h1>冻结规则<\/h1>/);
  assert.match(html, /<strong>可以充值<\/strong>/);
  assert.match(html, /<code>不能转账<\/code>/);
  assert.match(html, /<ul><li>仅代理账户<\/li><li>不影响充值<\/li><\/ul>/);
  assert.match(html, /<blockquote>只进不出<\/blockquote>/);
  assert.doesNotMatch(html, /\bid=/);
});

test('answer tables keep header and cell contents', () => {
  const html = render('| 操作 | 状态 |\n| --- | --- |\n| 充值 | 允许 |\n| 转账 | 暂停 |');
  assert.match(html, /<th>操作<\/th><th>状态<\/th>/);
  assert.match(html, /<td>充值<\/td><td>允许<\/td>/);
  assert.match(html, /<td>转账<\/td><td>暂停<\/td>/);
});

test('model text cannot create executable HTML, links or remote image requests', () => {
  const html = render('<a id="x"><img src="https://example.invalid/x" onerror="alert(1)"></a>\n\n<script>alert(1)</script>\n\n![track](https://example.invalid/pixel) [click](javascript:alert(1))');
  assert.doesNotMatch(html, /<(?:a|img|script)\b/i);
  assert.match(html, /&lt;script&gt;/);
  assert.match(html, /!\[track\]/);
});

test('streaming partial Markdown and code fences keep text without executing it', () => {
  for (const input of ['**未完成', '`尚未闭合', '| 操作 |', '```html\n<img onerror="x">']) {
    assert.doesNotThrow(() => render(input));
  }
  assert.match(render('```html\n<img onerror="x">'), /<pre><code>&lt;img onerror=&quot;x&quot;&gt;<\/code><\/pre>/);
});

test('answer separators and literal HTML comments do not discard answer text', () => {
  const html = render('---\n\n结论保留\n\n<!-- 示例注释 -->');
  assert.match(html, /<hr>/);
  assert.match(html, /结论保留/);
  assert.match(html, /&lt;!-- 示例注释 --&gt;/);
});
