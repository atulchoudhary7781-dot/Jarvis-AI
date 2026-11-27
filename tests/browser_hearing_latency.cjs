/* Mocked recognition, speech, and server. Does not test physical microphones. */
const {chromium}=require('playwright'),assert=require('node:assert/strict');
(async()=>{
 const b=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 async function setup(opts={}){
  const p=await b.newPage(),errors=[];p.on('pageerror',e=>errors.push(e.message));
  await p.addInitScript(()=>{
   localStorage.setItem('amber:mic-on-open','off');sessionStorage.setItem('amber:language','en-IN');
   const x=window.qa={active:null,spoken:[],requests:0,commands:[]};
   window.SpeechRecognition=class{start(){x.active=this}abort(){if(x.active===this)x.active=null;queueMicrotask(()=>this.onend?.())}};
   x.say=(text,confidence=.9)=>{if(!x.active)throw Error('not listening');x.active.onresult({resultIndex:0,results:[Object.assign([{transcript:text,confidence}],{isFinal:true})]})};
   window.SpeechSynthesisUtterance=class{constructor(text){this.text=text}};
   Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{get speaking(){return !!x.utterance},get pending(){return false},getVoices(){return[]},cancel(){x.utterance=null},speak(u){x.utterance=u;x.spoken.push({text:u.text,time:performance.now()});setTimeout(()=>x.utterance===u&&u.onstart?.(),2);setTimeout(()=>{if(x.utterance===u){x.utterance=null;u.onend?.()}},30)}}});
  });
  let calls=[],voiceCalls=0;
  await p.route('**/api/voice',async r=>{voiceCalls++;if(opts.slowVoice)await new Promise(resolve=>setTimeout(resolve,3500));try{await r.fulfill({json:{ok:false,reason:'system'}})}catch(_){}});
  await p.route('**/api/command',async r=>{
   const data=r.request().postDataJSON();calls.push(data);
   const result=data.chatTerms==='gemma-2026-04-01'?{source:'Companion',text:'A model reply.',lang:'en-IN'}:{source:'Chat terms',terms:'gemma-2026-04-01',text:'Gemma terms apply. Do you agree?',lang:'en-IN'};
   await r.fulfill({json:result});
  });
  await p.goto(process.env.AMBER_TEST_URL||'http://127.0.0.1:8765');
  await p.keyboard.press('Space');await p.waitForFunction(()=>!!qa.active);
  return {p,calls,errors,voiceCalls:()=>voiceCalls};
 }
 async function speakAndWait(p,text,check,confidence=.9){
  const previous=await p.evaluate(()=>qa.spoken.length);await p.evaluate(([s,c])=>qa.say(s,c),[text,confidence]);
  await p.waitForFunction(({previous,check})=>qa.spoken.slice(previous).some(x=>x.text.includes(check)),{previous,check},{timeout:10000});
  await p.waitForFunction(()=>qa.active&&!speechSynthesis.speaking&&document.documentElement.dataset.state==='listening',null,{timeout:10000});
 }
 try{
  {
   const {p,calls,errors}=await setup();
   await speakAndWait(p,'garbled request','could not match');
   assert.equal(calls.length,1);assert.equal(await p.evaluate(()=>sessionStorage.getItem('amber:chat:terms')),null);
   // A random yes after an unmatched request must not become agreement.
   await speakAndWait(p,'yes','could not match');
   assert.equal(await p.evaluate(()=>sessionStorage.getItem('amber:chat:terms')),null);
   await speakAndWait(p,'open chat','Open chat uses Gemma');
   assert.equal(await p.evaluate(()=>sessionStorage.getItem('amber:chat:terms')),null);
   await speakAndWait(p,'yes','Open chat is enabled');
   assert.equal(await p.evaluate(()=>sessionStorage.getItem('amber:chat:terms')),'gemma-2026-04-01');
   await speakAndWait(p,'my question for the model','A model reply');
   assert.equal(calls.at(-1).chatTerms,'gemma-2026-04-01');
   assert.deepEqual(errors,[]);await p.close();console.log('PASS unmatched speech asks retry; explicit open-chat consent remains necessary');
  }
  {
   const {p,calls}=await setup();await speakAndWait(p,'uncertain words','didn’t catch',.25);
   assert.equal(calls.length,0);assert.equal(await p.evaluate(()=>sessionStorage.getItem('amber:chat:terms')),null);
   await speakAndWait(p,'what did you hear','I may have heard: uncertain words');
   assert.equal(calls.length,0);
   await p.evaluate(()=>qa.active.onnomatch?.());
   await p.waitForFunction(()=>qa.active&&!speechSynthesis.speaking&&document.documentElement.dataset.state==='listening');
   await speakAndWait(p,'what did you hear','No earlier phrase');
   await speakAndWait(p,'uncertain words','didn’t catch',.25);
   await p.keyboard.press('Escape');await p.keyboard.press('Space');await p.waitForFunction(()=>qa.active);
   await speakAndWait(p,'what did you hear','No earlier phrase');
   await p.close();console.log('PASS unclear speech is never executed; opt-in repeat is marked uncertain and cleared on stop');
  }
  {
   const {p,calls}=await setup();await p.evaluate(()=>{document.querySelector('#type-action').click();document.querySelector('#command').value='an ordinary typed question';document.querySelector('#typebox').requestSubmit()});
   await p.waitForFunction(()=>qa.spoken.some(x=>x.text.includes('Gemma terms')),{timeout:10000});
   assert.equal(calls.length,1);assert.equal(await p.evaluate(()=>sessionStorage.getItem('amber:chat:terms')),null);
   await p.close();console.log('PASS typed open-ended request still receives the terms');
  }
  {
   const {p,voiceCalls}=await setup({slowVoice:true});
   assert.equal(await p.locator('meta[name=jarvis-voice]').getAttribute('content'),'neural');
   await speakAndWait(p,'तेज़ आवाज़ चालू करो','Fast voice on');
   assert.equal(voiceCalls(),0);assert.equal(await p.evaluate(()=>sessionStorage.getItem('amber:fast-voice')),'on');
   await speakAndWait(p,'तेज आवाज बंद करो','Fast voice off');
   assert.ok(voiceCalls()>0);assert.equal(await p.evaluate(()=>sessionStorage.getItem('amber:fast-voice')),'off');
   await p.close();console.log('PASS optional fast device voice skips neural request and can be turned off');
  }
  {
   const {p}=await setup({slowVoice:true});
   assert.equal(await p.locator('meta[name=jarvis-voice]').getAttribute('content'),'neural');
   const start=await p.evaluate(()=>{qa.say('garbled request');return performance.now()});
   await p.waitForFunction(()=>qa.spoken.some(x=>x.text.includes('could not match')),null,{timeout:7000});
   const elapsed=await p.evaluate(start=>qa.spoken[0].time-start,start);
   assert.ok(elapsed>=1300 && elapsed<4000,`device fallback at ${elapsed}ms`);
   await p.close();console.log('PASS slow neural response falls back to device voice in',Math.round(elapsed),'ms after mocked recognition');
  }
 }finally{await b.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
