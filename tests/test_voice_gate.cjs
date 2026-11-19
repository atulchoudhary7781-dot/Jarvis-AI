/* Deterministic energy-gate simulations; not a substitute for real microphone tests. */
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('hologram/ui/index.html','utf8');
const code=html.split('// VOICE_GATE_BEGIN')[1].split('// VOICE_GATE_END')[0];
const make=vm.runInNewContext(`(()=>{${code}; return makeVoiceGate})()`);
function feed(g, level, start, end, step=100){let events=[];for(let t=start;t<=end;t+=step){const e=g(level,t);if(e!=='wait')events.push([t,e])}return events}
let g=make(false);
assert.deepEqual(feed(g,.003,100,3000),[]);
assert.deepEqual(feed(g,.012,3100,3500),[[3200,'speech']]);
assert.equal(feed(g,.003,3600,5100).at(-1)[1],'complete');
g=make(false);assert.deepEqual(feed(g,.003,100,1000),[]);assert.deepEqual(feed(g,.05,1100,1100),[]);assert.deepEqual(feed(g,.003,1200,2100),[]);
g=make(true);assert.deepEqual(feed(g,.03,100,500),[[200,'speech']]);assert.deepEqual(feed(g,.003,600,2300),[]);assert.equal(feed(g,.003,2400,3100).at(-1)[1],'complete');
g=make(false);assert.equal(feed(g,.003,100,10000).at(-1)[1],'quiet');
g=make(false);let long=feed(g,.04,100,20000);assert.equal(long[0][1],'speech');assert.equal(long.at(-1)[1],'too-long');
console.log('PASS: quiet background, soft voice, spikes, patient pauses, silence and bounded long speech');
