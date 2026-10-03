const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

// Real qa.js with controlled network and minimal DOM; visual layout is checked in a browser.
function harness(history = null) {
  const elements = new Map(), clicks = [], requests = [];
  let stream, requestBody;
  function el(id) {
    if (!elements.has(id)) elements.set(id, {
      id, innerHTML:'', textContent:'', hidden:false, value:'', disabled:false,
      scrollTop:0, scrollHeight:100, clientHeight:100, style:{}, events:{},
      classList:{add(){},remove(){},toggle(){},contains(){return false;}},
      addEventListener(name, fn){this.events[name]=fn;}, setAttribute(){},
      querySelector(){return null;},querySelectorAll(){return [];},contains(){return false;},
      appendChild(){}, insertAdjacentHTML(_position, html){this.innerHTML += html;}, focus(){}, remove(){}
    });
    return elements.get(id);
  }
  const response = data => ({ok:true,status:200,json:async()=>data});
  async function fetch(url, opts={}) {
    requests.push(url);
    if (url.endsWith('/auth/me')) return response({id:'u1',username:'test',is_super:true});
    if (url.endsWith('/health')) return response({index_ready:true,qdrant_ready:true,key_dashscope:'已配置',key_deepseek:'已配置'});
    if (url.endsWith('/heatmap')) return response({items:[]});
    if (url.endsWith('/answer-history')) return response(history || {authoritative:false,messages:[]});
    if (url.endsWith('/conversations')) return response({items:[{id:'c1',title:'测试',messages:[]}]});
    if (url.endsWith('/ask')) {
      requestBody = JSON.parse(opts.body);
      return {ok:true,status:200,body:new ReadableStream({start(c){stream=c;}})};
    }
    return response({ok:true});
  }
  const doc = {
    getElementById:el, querySelector:()=>el('root'), querySelectorAll:()=>[],
    addEventListener(name, fn){if(name==='click') clicks.push(fn);},
    createElement:()=>el('created'), body:{appendChild(){}}, documentElement:{clientWidth:1200}
  };
  const win = {location:{pathname:'/',search:'',hash:'',replace(){}},
    HayyoIcons:{svg(){return '<svg></svg>';}}, addEventListener(){}, innerWidth:1200};
  const context = {window:win,document:doc,location:win.location,fetch,TextDecoder,TextEncoder,
    AbortController,ReadableStream,URL,console,setTimeout,clearTimeout,
    localStorage:{getItem(){return null;},setItem(){}},navigator:{clipboard:{writeText:async()=>{}}},
    requestAnimationFrame(fn){fn();}};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../qa.js'),'utf8'),context);
  return {win,el,requests,async start(){await flush();el('qaInput').value='VIP 保级规则';el('qaSend').events.click();await flush();},
    event(name,data){stream.enqueue(new TextEncoder().encode('event: '+name+'\ndata: '+JSON.stringify(data)+'\n\n'));},
    end(){stream.close();},exec(){return requestBody.round_id;},
    click(selector,attrs){const node={getAttribute:key=>attrs[key]};const ev={target:{closest:q=>q===selector?node:null},stopPropagation(){}};clicks.forEach(fn=>fn(ev));}
  };
}
async function flush(){for(let i=0;i<12;i++) await new Promise(resolve=>setImmediate(resolve));}
function process(exec, state='running') {
  return {version:1,exec_id:exec,state,summary:state==='completed'?'已完成':'',document_count:1,
    steps:[{id:'1',stage:'retrieve',title:'查找相关资料',state:state==='completed'?'done':'running',
      details:['找到 3 个候选片段'],sources:[]}]};
}

test('process opens before body, folds on first text, and honors a manual reopen through completion',async()=>{
  const h=harness();await h.start();
  h.event('process',{exec_id:h.exec(),process:process(h.exec())});await flush();
  assert.match(h.el('qaMessages').innerHTML,/找到 3 个候选片段/);
  assert.match(h.el('qaMessages').innerHTML,/aria-expanded="true"/);
  h.event('token',{text:'初步回答'});await flush();
  assert.match(h.el('qaMessages').innerHTML,/aria-expanded="false"/);
  const m=h.win.HayyoQA.getConversations()[0].messages.at(-1);
  h.el('qaMessages').scrollTop=20;
  h.click('[data-toggle-process]',{'data-toggle-process':m.id});
  assert.match(h.el('qaMessages').innerHTML,/aria-expanded="true"/);
  assert.equal(h.el('qaMessages').scrollTop,20,'opening the process must keep the reader in place');
  h.event('process',{exec_id:h.exec(),process:process(h.exec())});
  h.event('done',{status:'success',exec_id:h.exec(),text:'正式回答',process:process(h.exec(),'completed')});h.end();await flush();
  assert.match(h.el('qaMessages').innerHTML,/aria-expanded="true"/);
  assert.match(h.el('qaMessages').innerHTML,/正式回答/);
  assert.equal(h.win.HayyoQA.isBusy(),false);
});

test('manually collapsed process stays collapsed while new steps arrive',async()=>{
  const h=harness();await h.start();h.event('process',{exec_id:h.exec(),process:process(h.exec())});await flush();
  const m=h.win.HayyoQA.getConversations()[0].messages.at(-1);
  h.click('[data-toggle-process]',{'data-toggle-process':m.id});
  h.event('process',{exec_id:h.exec(),process:process(h.exec())});await flush();
  assert.match(h.el('qaMessages').innerHTML,/aria-expanded="false"/);
  h.event('done',{status:'success',exec_id:h.exec(),text:'完成',process:process(h.exec(),'completed')});h.end();await flush();
});

test('history loads authoritative versions and old answers do not invent a process',async()=>{
  const first={round_id:'e1',role:'assistant',text:'旧回答',process:null};
  const second={round_id:'e2',role:'assistant',text:'新回答',process:process('e2','completed')};
  second.process.steps[0].details=['<img src=x onerror=alert(1)>'];
  const h=harness({authoritative:true,messages:[{id:'u',role:'user',text:'问题'},
    {id:'a',logical_round_id:'lr',versions:[first,second],viewIndex:1,...second}]});await flush();
  assert.match(h.el('qaMessages').innerHTML,/新回答/);
  h.click('[data-toggle-process]',{'data-toggle-process':'a'});
  assert.match(h.el('qaMessages').innerHTML,/&lt;img/);
  assert.doesNotMatch(h.el('qaMessages').innerHTML,/<img src=x/);
  h.click('[data-ver-step]',{'data-msg':'a','data-ver-step':'-1'});
  assert.match(h.el('qaMessages').innerHTML,/旧回答/);
  assert.doesNotMatch(h.el('qaMessages').innerHTML,/data-toggle-process/);
});
