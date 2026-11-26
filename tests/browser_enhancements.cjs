/* Synthetic browser events: does not measure real speech accuracy or Windows execution. */
const {chromium}=require('playwright'), assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.AMBER_TEST_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox','--disable-dev-shm-usage']});
 const p=await browser.newPage({viewport:{width:600,height:500},reducedMotion:'reduce'}), errors=[]; p.on('pageerror',e=>errors.push(e.message));
 await p.addInitScript(()=>{
  sessionStorage.setItem('amber:language','en-IN');
  const q=window.qa={r:null,spoken:[],urls:[],starts:0,overlap:0,u:null};
  window.open=(u)=>{q.urls.push(String(u));return null};
  window.SpeechRecognition=class{start(){if(q.r)q.overlap++;q.r=this;q.starts++;queueMicrotask(()=>this.onstart?.())}abort(){if(q.r===this)q.r=null;setTimeout(()=>this.onend?.(),10)}};
  q.results=(rs)=>q.r.onresult({resultIndex:0,results:rs.map(r=>Object.assign(r.a.map(([transcript,confidence])=>({transcript,confidence})),{isFinal:r.fin}))});
  q.end=()=>{const r=q.r;q.r=null;r.onend?.()};
  window.SpeechSynthesisUtterance=class{constructor(t){this.text=t}};
  Object.defineProperty(window,'speechSynthesis',{value:{get speaking(){return !!q.u},get pending(){return false},getVoices(){return []},cancel(){q.u=null},speak(u){q.u=u;q.spoken.push(u.text);setTimeout(()=>u.onstart?.(),2);setTimeout(()=>{if(q.u===u){q.u=null;u.onend?.()}},30)}}});
 });
 await p.context().grantPermissions(['microphone'],{origin:'http://127.0.0.1:8765'});
 await p.goto('http://127.0.0.1:8765');
 const wait=fn=>p.waitForFunction(fn,null,{timeout:7000}), say=async(t,c=.95)=>p.evaluate(([t,c])=>qa.results([{fin:true,a:[[t,c]]}]),[t,c]);
 await wait(()=>qa.r);assert.equal(await p.evaluate(()=>qa.r.maxAlternatives),3);
 // Pauses across cumulative final segments combine into one action, never execute the fragment.
 await say('open');await p.waitForTimeout(500);assert.equal(await p.locator('#review').isVisible(),false);
 await p.evaluate(()=>qa.results([{fin:true,a:[['open',.9]]},{fin:true,a:[['YouTube',.95]]}]));
 await wait(()=>!document.querySelector('#review').hidden);assert.match(await p.locator('#destination').innerText(),/youtube.com/);assert.deepEqual(await p.evaluate(()=>qa.urls),[]);
 // Synthetic programmatic event is not an approval; trusted click is.
 await p.evaluate(()=>document.querySelector('#approve').click());assert.deepEqual(await p.evaluate(()=>qa.urls),[]);
 await p.locator('#core').click({position:{x:300,y:250}});assert.deepEqual(await p.evaluate(()=>qa.urls),['https://www.youtube.com/']);
 await p.keyboard.press('Space');await wait(()=>qa.r);
 await p.evaluate(()=>qa.results([{fin:true,a:[['open youtube',.72],['open maps',.68]]}]));await wait(()=>qa.spoken.some(x=>/missed the last bit/i.test(x)));assert.equal(await p.locator('#review').isVisible(),false);
 await wait(()=>qa.r && !qa.r.barge);await say('do not open youtube');await wait(()=>qa.spoken.some(x=>/won.t open anything/i.test(x)));assert.equal(await p.locator('#review').isVisible(),false);
 await wait(()=>qa.r && !qa.r.barge);await say('open https://evil.com');await wait(()=>qa.spoken.some(x=>/isn.t on my launch list/i.test(x)));assert.equal(await p.locator('#review').isVisible(),false);
 await wait(()=>qa.r && !qa.r.barge);await say('यूट्यूब खोल दो');await wait(()=>!document.querySelector('#review').hidden);await p.keyboard.press('Escape');await p.waitForTimeout(250);assert.equal(await p.locator('#review').isVisible(),false);assert.equal((await p.evaluate(()=>qa.urls)).length,1);
 // Recognition ends after fragment and continues in a fresh session.
 await p.keyboard.press('Space');await wait(()=>qa.r);let n=await p.evaluate(()=>qa.starts);await say('open');await p.evaluate(()=>qa.end());await wait(()=>qa.starts>1 && qa.r);assert.ok(await p.evaluate(n=>qa.starts>n,n));await say('maps');await wait(()=>!document.querySelector('#review').hidden);assert.match(await p.locator('#destination').innerText(),/google.com/);
 assert.equal(await p.evaluate(()=>qa.overlap),0);assert.deepEqual(errors,[]);console.log('PASS: pauses, continued recognition, conflicting alternatives, negatives, URL denial, consent and Escape (simulated).');
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
