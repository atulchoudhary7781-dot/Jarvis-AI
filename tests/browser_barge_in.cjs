/* Simulated Chromium only; acoustic echo-cancellation is NOT validated here. */
const {chromium}=require('playwright'),assert=require('node:assert/strict');
(async()=>{const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
async function run(mode){const p=await b.newPage({viewport:{width:900,height:650}}),errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.addInitScript(mode=>{
 localStorage.setItem('amber:mic-on-open','off');window.qa={starts:0,stops:0,cancels:0,spoken:[],playing:false};window.confirm=()=>true;
 Object.defineProperty(navigator,'mediaDevices',{value:{getUserMedia:async(c)=>{const n=++qa.starts,begin=performance.now();qa.constraints=c;return{_n:n,_begin:begin,getTracks:()=>[{stop:()=>qa.stops++}]}}},configurable:true});
 window.AudioContext=window.webkitAudioContext=class{constructor(){this.state='running';this.currentTime=0;this.destination={}}resume(){return Promise.resolve()}close(){this.state='closed';return Promise.resolve()}createBuffer(){return{}}createBufferSource(){return{connect(){},disconnect(){},start(){this.onended?.()}}}createMediaStreamSource(s){this.stream=s;return{connect(){}}}createAnalyser(){const ctx=this;return{fftSize:1024,getByteTimeDomainData(a){const n=ctx.stream?._n||0,t=performance.now()-(ctx.stream?._begin||0);let loud=n===1 ? t<800 : (mode==='interrupt'||mode==='echo') && t>650 && t<1700;let amp=loud?12:0;for(let i=0;i<a.length;i++)a[i]=128+(i%2?amp:-amp)}}}};
 window.MediaRecorder=class{static isTypeSupported(t){return t.includes('webm')}constructor(s,o){this.state='inactive';this.mimeType=o?.mimeType||'audio/webm'}start(){this.state='recording'}stop(){if(this.state==='inactive')return;this.state='inactive';queueMicrotask(()=>{this.ondataavailable?.({data:new Blob([new Uint8Array(200)],{type:this.mimeType})});this.onstop?.()})}};
 window.SpeechSynthesisUtterance=class{constructor(t){this.text=t}};
 let timer=null,current=null;Object.defineProperty(window,'speechSynthesis',{value:{get speaking(){return qa.playing},get pending(){return false},getVoices(){return[]},cancel(){if(qa.playing)qa.cancels++;qa.playing=false;clearTimeout(timer);current=null},speak(u){qa.spoken.push(u.text);qa.playing=true;current=u;setTimeout(()=>{if(current===u)u.onstart?.()},1);timer=setTimeout(()=>{if(current===u){qa.playing=false;current=null;u.onend?.()}},mode==='interrupt'?8000:4500)}}});
},mode);
let uploads=0;await p.route('**/api/transcribe',async r=>{uploads++;const text=uploads===1?'help':mode==='echo'?'open YouTube, time in Tokyo, or teach a shortcut':'stop listening';await r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:true,text,language:'english'})})});
await p.goto('http://127.0.0.1:8765');await p.locator('#core').click({position:{x:450,y:325}});
await p.waitForFunction(()=>qa.playing&&qa.starts>=2,null,{timeout:12000});assert.equal(await p.evaluate(()=>qa.constraints.audio.echoCancellation),true);
if(mode==='interrupt'){
 await p.waitForFunction(()=>qa.cancels>=1,null,{timeout:5000});
 await p.waitForFunction(()=>qa.spoken.some(x=>/microphone off|माइक बंद/i.test(x)),null,{timeout:8000});
 assert.equal(uploads,2);assert.ok(await p.evaluate(()=>qa.stops>=2));console.log('PASS barge-in: playback cancelled, next utterance handled once, mic stopped');
}else if(mode==='echo'){
 await p.waitForFunction(()=>qa.cancels>=1,null,{timeout:5000});await p.waitForTimeout(3800);assert.equal(uploads,2);assert.equal(await p.evaluate(()=>qa.spoken.length),1);await p.keyboard.press('Escape');console.log('PASS obvious speaker echo suppressed; no echoed command executed');
}else{
 await p.waitForTimeout(1800);assert.equal(uploads,1);assert.equal(await p.evaluate(()=>qa.cancels),0);
 await p.keyboard.press('Escape');await p.waitForTimeout(200);assert.equal(await p.evaluate(()=>document.documentElement.dataset.conversation),'off');assert.ok(await p.evaluate(()=>qa.stops>=2));assert.equal(uploads,1);console.log('PASS no speech: no extra upload, Escape stops playback and mic');
}
assert.deepEqual(errs,[]);await p.close();}
await run('interrupt');await run('quiet');await run('echo');await b.close();})().catch(e=>{console.error(e);process.exit(1)});
