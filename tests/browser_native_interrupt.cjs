/* Simulated Web Speech and playback only; this is not an acoustic test. */
const {chromium}=require('playwright'), assert=require('node:assert/strict');
(async()=>{
 const launch={headless:true,args:JSON.parse(process.env.AMBER_TEST_ARGS||'["--no-sandbox"]')};
 if(process.env.AMBER_TEST_CHROMIUM)launch.executablePath=process.env.AMBER_TEST_CHROMIUM;
 const browser=await chromium.launch(launch);
 async function scenario(mode){
  const page=await browser.newPage(), errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>{
   localStorage.setItem('amber:mic-on-open','off'); sessionStorage.setItem('amber:language','en-IN');
   const q=window.qa={active:null,starts:0,aborts:0,cancels:0,spoken:[],utterance:null};
   window.SpeechRecognition=class{
    start(){if(q.active)throw Error('duplicate recognizer');q.active=this;q.starts++;}
    abort(){if(q.active===this)q.active=null;q.aborts++;queueMicrotask(()=>this.onend?.());}
   };
   q.result=(rows)=>q.active?.onresult?.({resultIndex:0,results:rows.map(([text,final,confidence=0.9])=>Object.assign([{transcript:text,confidence}],{isFinal:final}))});
   q.fault=(error)=>q.active?.onerror?.({error});
   q.finish=()=>{const u=q.utterance;q.utterance=null;u?.onend?.();};
   window.SpeechSynthesisUtterance=class{constructor(text){this.text=text}};
   Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{get speaking(){return !!q.utterance},get pending(){return false},getVoices(){return[]},cancel(){if(q.utterance)q.cancels++;q.utterance=null},speak(u){q.utterance=u;q.spoken.push(u.text);setTimeout(()=>q.utterance===u&&u.onstart?.(),1)}}});
  });
  const queries=[];await page.route('**/api/command',async r=>{queries.push(r.request().postDataJSON().query);await r.fulfill({json:{text:'The answer is 42.',lang:'en-IN'}})});
  await page.goto(process.env.AMBER_TEST_URL||'http://127.0.0.1:8765');
  assert.equal(await page.locator('meta[name=jarvis-cloud]').getAttribute('content'),'off');
  await page.keyboard.press('Space');await page.waitForFunction(()=>qa.active);
  await page.evaluate(()=>qa.result([['help',true]]));
  await page.waitForFunction(()=>qa.utterance&&qa.active);
  const text=await page.evaluate(()=>qa.spoken[0]);
  assert.ok(text.length>4);
  if(mode==='interrupt'){
   // An exact piece of playback (also after punctuation normalization) is ignored.
   await page.evaluate(text=>qa.result([[text,true]]),text);
   await page.waitForTimeout(1000);
   assert.equal(await page.evaluate(()=>qa.cancels),0);
   await page.evaluate(()=>qa.result([['what time in',false]]));
   await page.waitForFunction(()=>qa.cancels===1);
   // The old echo is in the cumulative event and must not enter the new command.
   await page.evaluate(text=>qa.result([[text,true],['stop listening',true]]),text);
   await page.waitForFunction(()=>document.documentElement.dataset.conversation==='off');
   assert.equal(await page.evaluate(()=>qa.active),null);
   console.log('PASS native: echo ignored, interim interrupts, cumulative echo excluded, spoken stop releases mic');
  }else if(mode==='question'){
   await page.evaluate(()=>qa.result([['calculate seventeen',false]]));
   await page.waitForFunction(()=>qa.cancels===1);
   await page.evaluate(()=>qa.result([['calculate seventeen',true],['times twenty three',true]]));
   await page.waitForFunction(()=>qa.spoken.some(t=>t.includes('42')));
   assert.deepEqual(queries,['calculate seventeen times twenty three']);
   await page.keyboard.press('Escape');
   console.log('PASS native: interrupted multi-part question submitted exactly once');
  }else if(mode==='late-echo'){
   await page.evaluate(()=>{qa.old=qa.active;qa.finish()});
   // Multiple speech clauses may follow. End them until playback is done.
   for(let i=0;i<10;i++) { await page.waitForTimeout(40); if(!await page.evaluate(()=>!!qa.utterance))break; await page.evaluate(()=>qa.finish()); }
   await page.waitForFunction(()=>qa.active&&!qa.utterance);
   const before=await page.evaluate(()=>qa.spoken.length);
   // A queued result from the discarded recognizer cannot act on the new turn.
   await page.evaluate(text=>qa.old.onresult?.({resultIndex:0,results:[Object.assign([{transcript:text}],{isFinal:true})]}),text);
   await page.waitForTimeout(1000);
   assert.equal(await page.evaluate(()=>qa.spoken.length),before);
   await page.keyboard.press('Escape');assert.equal(await page.evaluate(()=>qa.active),null);
   console.log('PASS native: delayed playback transcript never executed; Escape disarms');
  }else{
   await page.evaluate(()=>qa.fault('audio-capture'));
   await page.waitForFunction(()=>!qa.active&&!!qa.utterance);
   assert.equal(await page.evaluate(()=>document.documentElement.dataset.conversation),'on');
   await page.evaluate(()=>qa.finish());
   for(let i=0;i<10;i++) { await page.waitForTimeout(40); if(!await page.evaluate(()=>!!qa.utterance))break; await page.evaluate(()=>qa.finish()); }
   await page.waitForFunction(()=>qa.active);
   await page.keyboard.press('Escape');assert.equal(await page.evaluate(()=>qa.active),null);
   console.log('PASS native: recognition failure during playback keeps answer, retries after playback, Escape stops');
  }
  assert.deepEqual(errors,[]);await page.close();
 }
 try{for(const mode of ['interrupt','question','late-echo','failure'])await scenario(mode);}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
