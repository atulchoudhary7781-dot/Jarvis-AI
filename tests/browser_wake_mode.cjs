/* Simulated recognition and playback. Wake filtering is not speaker verification. */
const {chromium}=require('playwright'),assert=require('node:assert/strict');
(async()=>{
 const b=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 async function setup({enabled=false}={}){
  const p=await b.newPage(),errors=[];p.on('pageerror',e=>errors.push(e.message));
  await p.addInitScript(enabled=>{
   localStorage.setItem('amber:mic-on-open','off');sessionStorage.setItem('amber:language','en-IN');
   if(enabled)sessionStorage.setItem('amber:wake-only','on');
   const q=window.qa={active:null,starts:0,spoken:[],cancels:0,u:null,hold:false};
   window.SpeechRecognition=class{start(){q.active=this;q.starts++}abort(){if(q.active===this)q.active=null;queueMicrotask(()=>this.onend?.())}};
   q.say=(text,confidence=.9,final=true)=>q.active.onresult({resultIndex:0,results:[Object.assign([{transcript:text,confidence}],{isFinal:final})]});
   window.SpeechSynthesisUtterance=class{constructor(text){this.text=text}};
   Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{get speaking(){return !!q.u},get pending(){return false},getVoices(){return[]},cancel(){if(q.u)q.cancels++;q.u=null},speak(u){q.u=u;q.spoken.push(u.text);setTimeout(()=>q.u===u&&u.onstart?.(),2);setTimeout(()=>{if(q.u===u&&!q.hold){q.u=null;u.onend?.()}},40)}}});
  },enabled);
  let queries=[];await p.route('**/api/command',async r=>{queries.push(r.request().postDataJSON().query);await r.fulfill({json:{text:'The answer is 42.',lang:'en-IN'}})});
  await p.route('**/api/voice',r=>r.fulfill({json:{ok:false,reason:'system'}}));
  await p.goto(process.env.AMBER_TEST_URL||'http://127.0.0.1:8765');await p.keyboard.press('Space');await p.waitForFunction(()=>qa.active);
  return {p,queries,errors};
 }
 async function sayReply(p,text,expected){
  const n=await p.evaluate(()=>qa.spoken.length);await p.evaluate(t=>qa.say(t),text);
  await p.waitForFunction(({n,expected})=>qa.spoken.slice(n).some(t=>t.includes(expected)),{n,expected});
  await p.waitForFunction(()=>qa.active&&!qa.u&&document.documentElement.dataset.state==='listening');
 }
 try{
  {
   const {p,queries,errors}=await setup();
   await sayReply(p,'जार्विस वेक मोड चालू करो','Wake word on');
   assert.equal(await p.evaluate(()=>sessionStorage.getItem('amber:wake-only')),'on');
   let n=await p.evaluate(()=>qa.starts),spoken=await p.evaluate(()=>qa.spoken.length);
   await p.evaluate(()=>qa.say('what time in London',.2));
   await p.waitForFunction(n=>qa.starts>n&&qa.active,n);await p.waitForTimeout(150);
   assert.deepEqual(queries,[]);assert.equal(await p.evaluate(()=>qa.spoken.length),spoken);
   await sayReply(p,'jarvis what is the answer','42');
   assert.deepEqual(queries,['what is the answer']);
   await sayReply(p,'जार्विस वेक मोड बंद करो','Wake word off');
   assert.equal(await p.evaluate(()=>sessionStorage.getItem('amber:wake-only')),'off');
   await sayReply(p,'calculate seven times six','42');assert.equal(queries.length,2);
   assert.deepEqual(errors,[]);await p.close();console.log('PASS opt-in wake filtering, low-confidence background ignored, command passes, mode off');
  }
  {
   const {p,queries}=await setup({enabled:true});
   await p.evaluate(()=>qa.say('mic band karo'));
   await p.waitForFunction(()=>document.documentElement.dataset.conversation==='off');
   assert.deepEqual(queries,[]);assert.equal(await p.evaluate(()=>qa.active),null);await p.close();console.log('PASS spoken mic stop works without wake word');
  }
  {
   const {p,queries}=await setup({enabled:true});
   await p.evaluate(()=>{qa.hold=true;qa.say('jarvis calculate 42')});
   await p.waitForFunction(()=>qa.u&&qa.active);
   await p.evaluate(()=>qa.say('people talking nearby',.9,false));await p.waitForTimeout(200);
   await p.evaluate(()=>qa.say('people talking nearby',.9,true));await p.waitForTimeout(200);
   assert.equal(await p.evaluate(()=>qa.cancels),0);assert.ok(await p.evaluate(()=>!!qa.u));assert.equal(queries.length,1);
   const next=p.waitForResponse(r=>r.url().endsWith('/api/command'));
   await p.evaluate(()=>{qa.hold=false;qa.say('jarvis tell me more')});
   await p.waitForFunction(()=>qa.cancels===1);await p.waitForFunction(()=>qa.spoken.some(t=>t.includes('42')));
   await next;
   assert.deepEqual(queries,['calculate 42','tell me more']);
   await p.keyboard.press('Escape');await p.close();console.log('PASS background cannot interrupt; wake-word interruption passes (mocked)');
  }
 }finally{await b.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
