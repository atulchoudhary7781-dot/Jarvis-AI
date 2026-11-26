/* Actual RNNoise WASM in OfflineAudioContext on synthetic signals: not a physical mic test. */
const {chromium}=require('playwright'),assert=require('node:assert/strict');
(async()=>{
 const b=await chromium.launch({executablePath:process.env.AMBER_TEST_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox','--disable-dev-shm-usage']});
 const p=await b.newPage();const errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.route('**/qa-synthetic-speech.wav',r=>r.fulfill({path:'tests/fixtures/synthetic_speech.wav',contentType:'audio/wav'}));
 await p.goto(process.env.AMBER_TEST_URL||'http://127.0.0.1:8765');
 const result=await p.evaluate(async()=>{
  const wasm=await fetch('/api/audio/rnnoise.wasm').then(r=>{if(!r.ok)throw Error('wasm missing');return r.arrayBuffer()});
  const wave=await fetch('/qa-synthetic-speech.wav').then(r=>r.arrayBuffer());
  const decode=new OfflineAudioContext(1,48000,48000), clean=(await decode.decodeAudioData(wave)).getChannelData(0);
  async function render(input){
   const ac=new OfflineAudioContext(1,input.length,48000);await ac.audioWorklet.addModule('/api/audio/rnnoise-worklet.js');
   const node=new AudioWorkletNode(ac,'@sapphi-red/web-noise-suppressor/rnnoise',{numberOfInputs:1,numberOfOutputs:1,outputChannelCount:[1],channelCount:1,processorOptions:{wasmBinary:wasm,maxChannels:1}});
   const ready=await new Promise(resolve=>{const t=setTimeout(()=>resolve('timeout'),4000);node.port.onmessage=e=>{clearTimeout(t);resolve(e.data)};node.onprocessorerror=()=>{clearTimeout(t);resolve('processor-error')}});
   if(ready!=='ready')throw Error('RNNoise failed: '+ready);
   const buffer=ac.createBuffer(1,input.length,48000);buffer.copyToChannel(input,0);const src=ac.createBufferSource();src.buffer=buffer;src.connect(node);node.connect(ac.destination);src.start();
   const output=(await ac.startRendering()).getChannelData(0);node.port.postMessage('destroy');return output;
  }
  let seed=99123;function rand(){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return(seed/4294967296)*2-1}
  const noise=Float32Array.from({length:144000},()=>rand()*.09),out=await render(noise);
  const rms=(a,from,to)=>{let sum=0;for(let i=from;i<to;i++)sum+=a[i]*a[i];return Math.sqrt(sum/(to-from))};
  const mixed=Float32Array.from(clean,x=>x*.18+rand()*.025),speech=await render(mixed);
  let best=0;for(let delay=0;delay<3072;delay+=8){let xy=0,xx=0,yy=0;for(let i=12000;i<Math.min(clean.length-5000,145000);i+=8){const x=clean[i],y=speech[i+delay]||0;xy+=x*y;xx+=x*x;yy+=y*y}best=Math.max(best,xy/Math.sqrt(xx*yy||1))}
  return {noiseInput:rms(noise,48000,120000),noiseOutput:rms(out,48000,120000),speechCorrelation:best};
 });
 assert.ok(result.noiseOutput < result.noiseInput*.8,JSON.stringify(result));
 assert.ok(result.noiseOutput>0,JSON.stringify(result));assert.ok(result.speechCorrelation>.15,JSON.stringify(result));
 assert.deepEqual(errors,[]);console.log('PASS: real RNNoise attenuates synthetic noise and retains synthetic speech',result);await b.close();
})().catch(e=>{console.error(e);process.exit(1)});
