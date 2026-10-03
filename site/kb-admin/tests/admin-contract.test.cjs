const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

// Exercise the shipped handlers with controlled DOM/network. Layout is a browser check.
function harness(response = {}) {
  const elements = new Map(), requests = [], confirmations = [];
  let selected = [], consent = false, drawerHtml = '';
  const el = id => {
    if (!elements.has(id)) elements.set(id, {
      innerHTML:'', textContent:'', hidden:false, disabled:false, isConnected:false,
      elements:{role_id:{value:''}}, events:{},
      addEventListener(name, fn){this.events[name]=fn;},
      querySelectorAll(){return selected.map(value=>({value}));},
      querySelector(){return el('submit');}, close(){},
      classList:{add(){},remove(){},toggle(){}}
    });
    return elements.get(id);
  };
  const win = {addEventListener(){}, confirm(text){confirmations.push(text);return consent;}};
  const context = {window:win, document:{getElementById:el,addEventListener(){}}, console, URLSearchParams};
  const src = fs.readFileSync(path.join(__dirname,'../admin.js'),'utf8');
  assert(src.includes('  boot();\n})();'));
  vm.runInNewContext(src.replace('  boot();\n})();', `
    window.testApi = {configColumns, openAccountEditor, openRoleEditor, paneRoles,
      setup(overrides) {
        state.me = {is_super:true};
        state.accessTab = 'roles';
        api = overrides.api; openDrawer = overrides.openDrawer;
        paneAccounts = async function() {}; pageAccess = async function() {}; setMsg = function() {};
      }};
  })();`), context);
  win.testApi.setup({
    api:async (url, opts)=>{requests.push({url,...opts});return response;},
    openDrawer:(_title, html)=>{drawerHtml=html;return {querySelector:s=>el(s),close(){}};}
  });
  return {...win.testApi, el, requests, confirmations,
    consent(value){consent=value;}, picked(values){selected=values;}, html(){return drawerHtml;}};
}

const roles = [{id:'reader',name:'阅读者'}, {id:'operator',name:'运营者'}];

test('the built-in super role renders checked disabled permissions without a save form',async()=>{
  const h=harness({items:[{id:'super',name:'超级管理员',is_super:true,account_count:1}],
    checkboxes:['知识问答','配置发布'],pending:[]});
  h.el('accessBody').isConnected=true;
  await h.paneRoles();
  const html=h.el('roleEdit').innerHTML;
  const inputs=html.match(/<input\b[^>]*>/g) || [];
  assert.equal(inputs.length,2);
  for(const input of inputs){assert.match(input,/ checked/);assert.match(input,/ disabled/);}
  assert.doesNotMatch(html,/<form\b|id="roleSave"/);
  assert(h.requests.every(r=>!r.method || r.method==='GET'),'viewing super permissions must be read-only');
});

test('account role change requires confirmation and sends only the selected role', async()=>{
  const h=harness();
  h.openAccountEditor({id:'u1',username:'test',role_id:'reader',role_name:'阅读者',enabled:true},roles);
  const form=h.el('#accountForm');form.elements.role_id.value='operator';
  await form.onsubmit({preventDefault(){}});
  assert.equal(h.requests.length,0,'cancel must not change account permissions');
  assert.equal(h.confirmations.length,1);
  h.consent(true);await form.onsubmit({preventDefault(){}});
  assert.equal(h.requests.length,1);
  assert.equal(h.requests[0].url,'/admin/accounts/u1');
  assert.equal(h.requests[0].method,'PATCH');
  assert.deepEqual(JSON.parse(h.requests[0].body),{role_id:'operator'});
});

test('new accounts require an explicit role selection',()=>{
  const h=harness();h.openAccountEditor(null,roles);
  assert.match(h.html(),/<select name="role_id" required>/);
  assert.match(h.html(),/<option value="" disabled selected>/);
  assert.doesNotMatch(h.html(),/<option value="(?:reader|operator)" selected>/);
});

test('role permissions need a fresh preview and confirmation before saving',async()=>{
  const h=harness();h.picked(['问答明细','反馈汇总']);
  h.openRoleEditor({id:'r1',name:'审核员',permissions:['问答明细'],account_count:3},['问答明细','反馈汇总'],[]);
  const form=h.el('roleEditForm');
  h.consent(true);await form.onsubmit({preventDefault(){}});
  assert.equal(h.requests.length,0,'no preview means no permission write');
  h.el('rolePreview').onclick();
  assert.match(h.el('roleDiff').innerHTML,/新增：反馈汇总/);
  assert.match(h.el('roleDiff').innerHTML,/影响 3 个账号/);
  h.consent(false);await form.onsubmit({preventDefault(){}});
  assert.equal(h.requests.length,0,'cancel must preserve role permissions');
  h.picked(['反馈汇总']);form.events.change();h.consent(true);
  await form.onsubmit({preventDefault(){}});
  assert.equal(h.requests.length,0,'editing after preview invalidates that preview');
  h.el('rolePreview').onclick();await form.onsubmit({preventDefault(){}});
  assert.equal(h.requests.length,1);
  assert.equal(h.requests[0].url,'/admin/roles/r1/permissions');
  assert.deepEqual(JSON.parse(h.requests[0].body),{permissions:['反馈汇总']});
});

test('fixed configuration rules stay visible and have no editable controls',()=>{
  const h=harness();
  const html=h.configColumns({visible:{config:true,prompt:true},editable:{config:true,prompt:true},
    writable:{recall_k:64,rerank_n:8,temperature:0.2},package_id:'pkg-test',draft_rev:0,
    fixed_rules:[{id:'l1_rounds',title:'L1 回合上限',value:'10 个完整回合'},
      {id:'repair_max',title:'修正次数',value:'最多 1 次'}],readonly:{},pools:{},prompts:[]});
  const aside=html.match(/<aside\b[^>]*>([\s\S]*?)<\/aside>/);
  assert(aside,'fixed rules must be presented alongside runtime parameters');
  assert.match(aside[1],/10 个完整回合/);assert.match(aside[1],/最多 1 次/);
  assert.doesNotMatch(aside[1],/<(?:input|textarea|select)\b/);
  assert.doesNotMatch(html,/name="(?:l1_rounds|l1_tokens|repair_max|cross_session)"/);
  assert.equal(h.requests.length,0,'rendering rules must not call models or write configuration');
});
