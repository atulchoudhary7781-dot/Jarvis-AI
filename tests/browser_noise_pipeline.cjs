/* Real AudioWorklet + synthetic media stream; no real microphone, voice or provider. */
const {chromium}=require('playwright'),assert=require('node:assert/strict');
(async()=>{
 const b=await chromium.launch({executablePath:process.env.AMBER_TEST_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox','--disable-dev-shm-usage','--autoplay-policy=no-user-gesture-required']});
 try{for(const mode of ['ready','unavailable','disabled','declined','slow']){
  const p=await b.newPage({viewport:{width:900,height:650}}),errors=[];p.on('pageerror',e=>errors.push(e.message));
  await p.addInitScript(mode=>{
   localStorage.setItem('amber:mic-on-open','off');if(mode==='disabled')sessionStorage.setItem('amber:noise-filter','off');window.confirm=()=>mode!=='declined';window.qa={requests:0,tracks:[],contexts:[]};
   Object.defineProperty(navigator,'mediaDevices',{configurable:true,value:{getUserMedia:async()=>{
    qa.requests++;qa.sourceContext=new AudioContext({sampleRate:48000});qa.contexts.push(qa.sourceContext);await qa.sourceContext.resume();
    const osc=qa.sourceContext.createOscillator(),gain=qa.sourceContext.createGain(),dest=qa.sourceContext.createMediaStreamDestination();gain.gain.value=.05;osc.connect(gain);gain.connect(dest);osc.start();qa.tracks=dest.stream.getTracks();return dest.stream;
   }}});
  },mode);
  let assets=0,uploads=0;
  await p.route('**/api/audio/**',async r=>{assets++;if(mode==='slow')await new Promise(resolve=>setTimeout(resolve,3800));return (mode==='unavailable'?r.abort():r.continue()).catch(()=>{});});
  await p.route('**/api/transcribe',r=>{uploads++;return r.abort()});
  await p.goto('http://127.0.0.1:8765');await p.locator('#core').click({position:{x:450,y:325}});
  if(mode==='declined'){
   await p.waitForTimeout(250);assert.equal(await p.evaluate(()=>qa.requests),0);assert.equal(assets,0);
  }else if(mode==='slow'){
   await p.waitForFunction(()=>qa.requests===1);await p.waitForTimeout(150);await p.keyboard.press('Escape');
   await p.waitForFunction(()=>qa.tracks.length&&qa.tracks.every(t=>t.readyState==='ended'));
   await p.waitForTimeout(3800);
   assert.equal(await p.evaluate(()=>document.documentElement.dataset.conversation),'off');
   assert.equal(await p.evaluate(()=>document.documentElement.dataset.noise),'off');assert.equal(uploads,0);
   await p.evaluate(()=>Promise.all(qa.contexts.map(c=>c.close())));
  }else{
   await p.waitForFunction(expected=>document.documentElement.dataset.noise===expected,mode==='ready'?'rnnoise':'browser',{timeout:10000});
   assert.equal(await p.evaluate(()=>qa.requests),1);
   if(mode==='disabled'){
    assert.equal(assets,0);await p.keyboard.press('n');
    await p.waitForFunction(()=>qa.requests===2&&document.documentElement.dataset.noise==='rnnoise',null,{timeout:10000});
    assert.ok(assets>0);
   }else assert.ok(assets>0);
   await p.keyboard.press('Escape');await p.waitForFunction(()=>document.documentElement.dataset.conversation==='off');
   assert.equal(await p.evaluate(()=>document.documentElement.dataset.noise),'off');
   assert.equal(await p.evaluate(()=>qa.tracks.every(t=>t.readyState==='ended')),true);assert.equal(uploads,0);
   await p.evaluate(()=>Promise.all(qa.contexts.map(c=>c.close())));
  }
  assert.deepEqual(errors,[]);console.log('PASS',mode,'actual processing/fallback/consent lifecycle on synthetic media');await p.close();
 }}finally{await b.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
