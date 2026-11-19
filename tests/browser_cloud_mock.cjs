/* Fake media, Groq and translation, Chromium emulation only. No real provider/mic test. */
const {chromium,devices}=require('playwright'),assert=require('node:assert/strict');
(async()=>{const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
for(const [name,opts] of [['desktop',{viewport:{width:1000,height:700}}],['android',devices['Pixel 7']],['ios',devices['iPhone 13']]]){
 const c=await b.newContext(opts),p=await c.newPage(),errs=[];p.on('pageerror',e=>errs.push(e.message));
 await p.addInitScript(()=>{
  localStorage.setItem('amber:mic-on-open','off');window.qa={spoken:[],urls:[],starts:0,stops:0,prompts:0,first:0};
  window.confirm=()=>{qa.prompts++;return true};window.open=u=>qa.urls.push(String(u));
  Object.defineProperty(navigator,'mediaDevices',{value:{getUserMedia:async()=>{qa.starts++;qa.first=performance.now();return {getTracks:()=>[{stop:()=>qa.stops++}]}}},configurable:true});
  window.AudioContext=window.webkitAudioContext=class{constructor(){this.state='running';this.currentTime=0;this.destination={}}resume(){return Promise.resolve()}close(){this.state='closed';return Promise.resolve()}createBuffer(){return {}}createBufferSource(){return {connect(){},disconnect(){},start(){this.onended?.()}}}createMediaStreamSource(){return {connect(){}}}createAnalyser(){return {fftSize:1024,getByteTimeDomainData(a){const loud=performance.now()-qa.first<800;for(let i=0;i<a.length;i++)a[i]=loud?(i%2?160:96):128}}}};
  window.MediaRecorder=class{static isTypeSupported(t){return t.includes('webm')}constructor(s,opts){this.state='inactive';this.mimeType=opts?.mimeType||'audio/webm'}start(){this.state='recording'}stop(){this.state='inactive';queueMicrotask(()=>{this.ondataavailable?.({data:new Blob([new Uint8Array(200)],{type:this.mimeType})});this.onstop?.()})}};
  window.SpeechSynthesisUtterance=class{constructor(t){this.text=t}};
  Object.defineProperty(window,'speechSynthesis',{value:{get speaking(){return false},get pending(){return false},getVoices(){return[]},cancel(){},speak(u){qa.spoken.push({text:u.text,lang:u.lang});setTimeout(()=>u.onstart?.(),1);setTimeout(()=>u.onend?.(),20)}}});
 });
 let uploads=0,translations=0;
 await p.route('**/api/transcribe',async r=>{uploads++;let data=r.request().postDataJSON();assert.match(data.mime,/audio\/webm/);await r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:true,text:'abre youtube',language:'spanish',command:'open youtube'})})});
 await p.route('**/api/translate',async r=>{translations++;await r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:true,text:'Pulsa el holograma para abrir YouTube.'})})});
 await p.goto('http://127.0.0.1:8765');assert.equal(await p.locator('meta[name=jarvis-cloud]').getAttribute('content'),'preview');assert.equal(await p.locator('#mobilebar').isVisible(),false);
 await p.locator('#core').click({position:{x:opts.viewport.width/2,y:opts.viewport.height/2}});
 await p.waitForFunction(()=>!document.querySelector('#review').hidden,null,{timeout:12000});
 await p.waitForFunction(()=>qa.spoken.some(s=>s.lang==='es'),null,{timeout:8000});
 assert.equal(uploads,1);assert.ok(translations>=1);assert.equal(await p.evaluate(()=>qa.prompts),1);assert.ok(await p.evaluate(()=>qa.stops>=1));assert.deepEqual(await p.evaluate(()=>qa.urls),[]);
 await p.locator('#core').click({position:{x:opts.viewport.width/2,y:opts.viewport.height/2}});assert.deepEqual(await p.evaluate(()=>qa.urls),['https://www.youtube.com/']);assert.deepEqual(errs,[]);
 console.log('PASS',name,'consent, simulated Spanish capture, translated approval and mic release');await c.close();
}await b.close()})().catch(e=>{console.error(e);process.exit(1)});
