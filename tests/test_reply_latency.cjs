/* Deterministic segmentation and endpointing checks; not a network benchmark. */
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const s=fs.readFileSync('hologram/ui/index.html','utf8');
const phraseCode=s.slice(s.indexOf('  function phrases(text) {'),s.indexOf('  const b64bytes',s.indexOf('  function phrases(text) {')));
const phrases=vm.runInNewContext(`(()=>{${phraseCode};return phrases})()`);
const text='This is the first sentence of a longer response with several meaningful clauses, so the user should hear a quick start and then a complete answer without losing a word.';
const parts=phrases(text);assert.ok(parts[0].length<=56);assert.equal(parts.join(' '),text);
const gateCode=s.split('// VOICE_GATE_BEGIN')[1].split('// VOICE_GATE_END')[0];const make=vm.runInNewContext(`(()=>{${gateCode};return makeVoiceGate})()`);
let g=make(false),events=[];for(let t=100;t<=2400;t+=100)events.push([t,g(t<=500?.03:.001,t)]);
assert.equal(events.find(x=>x[1]==='complete')[0],1600);
g=make(true);events=[];for(let t=100;t<=3200;t+=100)events.push([t,g(t<=500?.03:.001,t)]);
assert.equal(events.find(x=>x[1]==='complete')[0],3100);
console.log('PASS: faster normal endpoint, longer patient pauses, intact shorter first spoken clause');
