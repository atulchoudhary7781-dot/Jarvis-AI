/* Simulated audio track only; not an acoustic or physical-device measurement. */
const {chromium}=require('playwright'),assert=require('node:assert/strict');
(async()=>{
 const b=await chromium.launch({executablePath:process.env.AMBER_TEST_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
 for (const mode of ['apply','reject','abort']) {
  const p=await b.newPage({viewport:{width:900,height:650}}),errors=[];p.on('pageerror',e=>errors.push(e.message));
  await p.addInitScript(mode=>{
   localStorage.setItem('amber:mic-on-open','off');window.confirm=()=>true;
   const q=window.qa={stops:0,applied:null,records:0};
   const track={stop(){q.stops++},getCapabilities(){return{echoCancellation:[true,false,'all']}},getConstraints(){return{noiseSuppression:true,echoCancellation:true}},applyConstraints(c){q.applied=c;if(mode==='reject')return Promise.reject(Error('unsupported'));if(mode==='abort')return new Promise(r=>q.resolve=r);return Promise.resolve()}};
   Object.defineProperty(navigator,'mediaDevices',{value:{getUserMedia:async()=>({getTracks:()=>[track],getAudioTracks:()=>[track]})},configurable:true});
   window.AudioContext=window.webkitAudioContext=class{constructor(){this.state='running';this.destination={}}resume(){return Promise.resolve()}close(){return Promise.resolve()}createBuffer(){return{}}createBufferSource(){return{connect(){},disconnect(){},start(){}}}createMediaStreamSource(){return{connect(){}}}createAnalyser(){return{fftSize:1024,getByteTimeDomainData(a){a.fill(128)}}}};
   window.MediaRecorder=class{static isTypeSupported(){return true}constructor(){this.state='inactive'}start(){this.state='recording';q.records++}stop(){this.state='inactive';this.onstop?.()}};
  },mode);
  let uploads=0;await p.route('**/api/transcribe',r=>{uploads++;return r.abort()});
  await p.goto('http://127.0.0.1:8765');await p.locator('#core').click({position:{x:450,y:325}});
  await p.waitForFunction(()=>qa.applied);
  assert.equal(await p.evaluate(()=>qa.applied.echoCancellation.ideal),'all');assert.equal(await p.evaluate(()=>qa.applied.noiseSuppression),true);
  if(mode!=='abort')await p.waitForFunction(()=>qa.records===1);
  await p.keyboard.press('Escape');
  if(mode==='abort'){await p.evaluate(()=>qa.resolve());await p.waitForTimeout(150);assert.equal(await p.evaluate(()=>qa.records),0)}
  assert.equal(await p.evaluate(()=>document.documentElement.dataset.conversation),'off');assert.ok(await p.evaluate(()=>qa.stops>0));assert.equal(uploads,0);assert.deepEqual(errors,[]);
  console.log('PASS:',mode,'echo preference, fallback and mic cancellation (mocked)');await p.close();
 }
 await b.close();
})().catch(e=>{console.error(e);process.exit(1)});
