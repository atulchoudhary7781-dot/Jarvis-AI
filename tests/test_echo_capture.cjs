/* Browser-track API simulations; actual acoustic echo cancellation is not measured. */
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('hologram/ui/index.html','utf8');
const code=html.split('// ECHO_CAPTURE_BEGIN')[1].split('// ECHO_CAPTURE_END')[0];
const prefer=vm.runInNewContext(`(()=>{${code};return preferAllEchoCancellation})()`,{setTimeout,clearTimeout});
(async()=>{
 let captured;
 const track={getCapabilities:()=>({echoCancellation:[true,false,'all']}),getConstraints:()=>({echoCancellation:true,noiseSuppression:true}),applyConstraints:async x=>{captured=x}};
 await prefer({getAudioTracks:()=>[track]});
 assert.equal(captured.echoCancellation.ideal,'all');assert.equal(captured.noiseSuppression,true);
 captured=null;track.getCapabilities=()=>({echoCancellation:[true,false]});await prefer({getAudioTracks:()=>[track]});assert.equal(captured,null);
 track.getCapabilities=()=>({echoCancellation:['all']});track.applyConstraints=async()=>{throw Error('unsupported')};await prefer({getAudioTracks:()=>[track]});
 await prefer({getAudioTracks:()=>[]});await prefer({});
 track.applyConstraints=()=>new Promise(()=>{});const start=Date.now();await prefer({getAudioTracks:()=>[track]});assert.ok(Date.now()-start<1300);
 console.log('PASS: all-output echo preference only on advertised support; safe fallback');
})().catch(e=>{console.error(e);process.exitCode=1});
