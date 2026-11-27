/* Mocked Groq recognition, audio input and playback; not an acoustic test. */
const {chromium}=require('playwright'),assert=require('node:assert/strict');
(async()=>{
 const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--disable-dev-shm-usage']});
 const p=await b.newPage(),errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.addInitScript(()=>{
  localStorage.setItem('amber:mic-on-open','off');sessionStorage.setItem('amber:wake-only','on');sessionStorage.setItem('amber:language','en-IN');
  const q=window.qa={starts:0,stops:0,cancels:0,spoken:[],playing:false};window.confirm=()=>true;
  Object.defineProperty(navigator,'mediaDevices',{configurable:true,value:{getUserMedia:async()=>{const n=++q.starts,begin=performance.now();return {_n:n,_begin:begin,getTracks:()=>[{stop:()=>q.stops++}]}}}});
  window.AudioContext=window.webkitAudioContext=class{constructor(){this.state='running';this.currentTime=0;this.destination={}}resume(){return Promise.resolve()}close(){this.state='closed';return Promise.resolve()}createBuffer(){return{}}createBufferSource(){return{connect(){},disconnect(){},start(){this.onended?.()}}}createMediaStreamSource(s){this.stream=s;return{connect(){}}}createAnalyser(){const ctx=this;return{fftSize:1024,getByteTimeDomainData(a){const n=ctx.stream?._n||0,t=performance.now()-(ctx.stream?._begin||0),loud=n===1?t<800:t>600&&t<1500;for(let i=0;i<a.length;i++)a[i]=128+(i%2?(loud?16:0):(loud?-16:0))}}}};
  window.MediaRecorder=class{static isTypeSupported(t){return t.includes('webm')}constructor(s,o){this.state='inactive';this.mimeType=o?.mimeType||'audio/webm'}start(){this.state='recording'}stop(){if(this.state==='inactive')return;this.state='inactive';queueMicrotask(()=>{this.ondataavailable?.({data:new Blob([new Uint8Array(200)],{type:this.mimeType})});this.onstop?.()})}};
  window.SpeechSynthesisUtterance=class{constructor(text){this.text=text}};
  let timer,current;Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{get speaking(){return q.playing},get pending(){return false},getVoices(){return[]},cancel(){if(q.playing)q.cancels++;q.playing=false;clearTimeout(timer);current=null},speak(u){current=u;q.playing=true;q.spoken.push(u.text);setTimeout(()=>current===u&&u.onstart?.(),1);timer=setTimeout(()=>{if(current===u){q.playing=false;current=null;u.onend?.()}},15000)}}});
 });
 let uploads=0;await p.route('**/api/transcribe',async r=>{uploads++;const text=['jarvis help','people talking nearby','jarvis stop listening'][uploads-1]||'';await r.fulfill({json:{ok:true,text,language:'english'}})});
 try{
  await p.goto('http://127.0.0.1:8765');assert.equal(await p.locator('meta[name=jarvis-cloud]').getAttribute('content'),'preview');
  await p.keyboard.press('Space');await p.waitForFunction(()=>qa.playing&&qa.starts>=2,null,{timeout:12000});
  await p.waitForFunction(()=>qa.starts>=3,null,{timeout:12000});
  assert.equal(uploads,2);assert.equal(await p.evaluate(()=>qa.cancels),0);assert.equal(await p.evaluate(()=>qa.playing),true);
  await p.waitForFunction(()=>qa.cancels>=1,null,{timeout:12000});
  await p.waitForFunction(()=>document.documentElement.dataset.conversation==='off',null,{timeout:10000});
  assert.equal(uploads,3);assert.ok(await p.evaluate(()=>qa.stops>=3));assert.deepEqual(errors,[]);
  console.log('PASS mocked cloud wake gate: background transcription does not interrupt; wake stop releases mic. Audio was still uploaded.');
 }finally{await b.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
