/* Chromium emulation only: no real Android, iOS, microphone, app association, or macOS. */
const {chromium,devices}=require('playwright'), assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.AMBER_TEST_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
 try{
  for(const [name,opts,continuous] of [['phone-android',devices['Pixel 7'],true],['phone-ios',devices['iPhone 13'],false],['desktop',{viewport:{width:1280,height:800}},true]]){
   const ctx=await browser.newContext({...opts,reducedMotion:'reduce'}),p=await ctx.newPage(),errors=[];p.on('pageerror',e=>errors.push(e.message));
   await p.addInitScript(()=>{
    localStorage.setItem('amber:mic-on-open','off');sessionStorage.setItem('amber:language','en-IN');window.opened=[];
    window.open=u=>{opened.push(String(u));return null};
    window.SpeechRecognition=window.webkitSpeechRecognition=class{start(){window.qa=this;this.onstart?.()}abort(){if(window.qa===this)window.qa=null;queueMicrotask(()=>this.onend?.())}};
    window.say=t=>window.qa.onresult?.({resultIndex:0,results:[Object.assign([{transcript:t,confidence:.9}],{isFinal:true})]});
    window.SpeechSynthesisUtterance=class{constructor(t){this.text=t}};
    Object.defineProperty(window,'speechSynthesis',{value:{get speaking(){return false},get pending(){return false},getVoices(){return[]},cancel(){},speak(u){setTimeout(()=>u.onstart?.(),1);setTimeout(()=>u.onend?.(),20)}}});
   });
   await p.goto(process.env.AMBER_TEST_URL||'http://127.0.0.1:8765');
   assert.equal(await p.locator('#mobilebar').isVisible(),false);assert.equal(await p.locator('#typebox').isVisible(),false);
   await p.locator('#core').click({position:{x:opts.viewport.width/2,y:opts.viewport.height/2}});await p.waitForFunction(()=>window.qa);
   assert.equal(await p.evaluate(()=>qa.continuous),continuous);
   await p.evaluate(()=>say('open youtube'));await p.waitForFunction(()=>!document.querySelector('#review').hidden);
   assert.match(await p.locator('#destination').innerText(),/youtube.com/);assert.deepEqual(await p.evaluate(()=>opened),[]);
   await p.evaluate(()=>document.querySelector('#approve').click());assert.deepEqual(await p.evaluate(()=>opened),[]);
   await p.locator('#core').click({position:{x:opts.viewport.width/2,y:opts.viewport.height/2}});assert.deepEqual(await p.evaluate(()=>opened),['https://www.youtube.com/']);
   await p.locator('#core').click({position:{x:opts.viewport.width/2,y:opts.viewport.height/2}});await p.waitForFunction(()=>window.qa);
   await p.evaluate(()=>say('open maps'));await p.waitForFunction(()=>!document.querySelector('#review').hidden);
   await p.keyboard.press('Escape');assert.equal(await p.locator('#review').isVisible(),false);assert.equal((await p.evaluate(()=>opened)).length,1);
   assert.deepEqual(errors,[]);console.log('PASS:',name,'voice-mode selection, trusted hologram approval, Escape (simulated)');await ctx.close();
  }
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
