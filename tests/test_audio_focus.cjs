/* Audio graph selection tests only. Real devices and acoustic effectiveness untested. */
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('hologram/ui/index.html','utf8');
const code=html.split('// AUDIO_FOCUS_BEGIN')[1].split('// AUDIO_FOCUS_END')[0];
const make=vm.runInNewContext(`(()=>{${code};return makeFocusedAudio})()`);
const input={name:'input'}, output={name:'output'}, connections=[];
const node=name=>({name,connect(other){connections.push([name,other.name])}});
const filter={...node('filter'),frequency:{value:0}};
const ac={createMediaStreamSource(){return node('source')},createAnalyser(){return node('analyser')},createBiquadFilter(){return filter},createMediaStreamDestination(){return {...node('destination'),stream:output}}};
let result=make(ac,input);
assert.equal(result.recordStream,output);assert.equal(result.analyser.fftSize,1024);
assert.equal(filter.type,'highpass');assert.equal(filter.frequency.value,100);
assert.deepEqual(connections,[['source','filter'],['filter','analyser'],['filter','destination']]);
connections.length=0;delete ac.createBiquadFilter;
result=make(ac,input);assert.equal(result.recordStream,input);assert.deepEqual(connections,[['source','analyser']]);
connections.length=0;ac.createBiquadFilter=()=>{throw Error('unsupported')};
result=make(ac,input);assert.equal(result.recordStream,input);assert.deepEqual(connections,[['source','analyser']]);
console.log('PASS: focused audio graph, unsupported-browser fallback');
