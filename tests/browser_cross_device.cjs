/* Chromium emulation only: no real Android, iOS, microphone, app association, or macOS. */
const {chromium,devices}=require('playwright'), assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
 for(const [name,opts] of [['phone-android',devices['Pixel 7']],['phone-ios',devices['iPhone 13']],['desktop',{viewport:{width:1280,height:800}}]]){
  const ctx=await browser.newContext({...opts, reducedMotion:'reduce'});
  const p=await ctx.newPage();const errors=[];p.on('pageerror',e=>errors.push(e.message));
  await p.addInitScript(()=>{sessionStorage.setItem('amber:language','en-IN');delete window.SpeechRecognition;delete window.webkitSpeechRecognition;window.open=(u)=>{(window.opened??=[]).push(String(u));return null};window.speechSynthesis.cancel();});
  await p.goto('http://127.0.0.1:8765');
  await p.locator('#type-action').click();
  assert.equal(await p.locator('#mobilebar').isVisible(),false);
  assert.equal(await p.locator('#command').isVisible(),true);
  await p.locator('#command').fill('open youtube');
  await p.locator('#send-command').click();
  await p.waitForFunction(()=>!document.querySelector('#review').hidden);
  assert.match(await p.locator('#destination').innerText(),/youtube.com/);
  assert.equal((await p.evaluate(()=>window.opened||[])).length,0);
  await p.evaluate(()=>document.querySelector('#approve').click());
  assert.equal((await p.evaluate(()=>window.opened||[])).length,0);
  await p.locator('#approve').click();
  assert.deepEqual(await p.evaluate(()=>window.opened),['https://www.youtube.com/']);
  await p.locator('#type-action').click();await p.locator('#command').fill('open maps');await p.locator('#send-command').click();
  await p.waitForFunction(()=>!document.querySelector('#review').hidden);
  await p.locator('#dismiss').click();assert.equal((await p.evaluate(()=>window.opened)).length,1);
  await p.locator('#type-action').click();await p.locator('#cancel-command').click();
  assert.equal(await p.locator('#typebox').isVisible(),false);assert.equal(await p.locator('#mobilebar').isVisible(),true);
  assert.deepEqual(errors,[]);console.log('PASS:',name,'visible typed input, tap-to-approve, cancellation, voice unavailable (Chromium emulation)');
  await ctx.close();
 }
 // User-agent emulation and a fake recognizer only; this is not actual Safari or speech.
 for(const [name,opts,expected] of [['ios',devices['iPhone 13'],false],['android',devices['Pixel 7'],true]]){
  const ctx=await browser.newContext(opts),p=await ctx.newPage();
  await p.addInitScript(()=>{window.SpeechRecognition=class{start(){window.qa=this;this.onstart?.()}abort(){this.onend?.()}};window.webkitSpeechRecognition=window.SpeechRecognition});
  await p.goto('http://127.0.0.1:8765');await p.locator('#mic-action').click();
  await p.waitForFunction(()=>window.qa);assert.equal(await p.evaluate(()=>window.qa.continuous),expected);
  console.log('PASS:',name,'recognition mode (simulated recognizer)');await ctx.close();
 }
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
