/* Mocked Web Speech events; verifies routing and lifecycle, not mic accuracy. */
const {chromium}=require('playwright'),assert=require('node:assert/strict');
(async()=>{
 const b=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 async function setup(){
  const p=await b.newPage(),errors=[];p.on('pageerror',e=>errors.push(e.message));
  await p.addInitScript(()=>{
   localStorage.setItem('amber:mic-on-open','off');sessionStorage.setItem('amber:language','hi-IN');
   const q=window.qa={active:null,starts:0,spoken:[],u:null,requests:[]};
   window.SpeechRecognition=class{start(){q.active=this;q.starts++}abort(){if(q.active===this)q.active=null;queueMicrotask(()=>this.onend?.())}};
   q.say=(s)=>q.active.onresult({resultIndex:0,results:[Object.assign([{transcript:s,confidence:.9}],{isFinal:true})]});
   q.end=()=>{const r=q.active;q.active=null;r.onend?.()};q.fault=err=>q.active?.onerror?.({error:err});
   window.SpeechSynthesisUtterance=class{constructor(text){this.text=text}};
   Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{get speaking(){return !!q.u},get pending(){return false},getVoices(){return[]},cancel(){q.u=null},speak(u){q.u=u;q.spoken.push(u.text);setTimeout(()=>q.u===u&&u.onstart?.(),2);setTimeout(()=>{if(q.u===u){q.u=null;u.onend?.()}},30)}}});
  });
  let queries=[];await p.route('**/api/command',async r=>{queries.push(r.request().postDataJSON().query);await r.fulfill({json:{text:'जवाब है 391।',lang:'hi-IN',source:'Calculator'}})});
  await p.route('**/api/voice',r=>r.fulfill({json:{ok:false,reason:'system'}}));
  await p.goto(process.env.AMBER_TEST_URL||'http://127.0.0.1:8765');await p.keyboard.press('Space');await p.waitForFunction(()=>qa.active);
  return {p,errors,queries};
 }
 async function scenario(mode){
  const {p,errors,queries}=await setup();
  try{
   if(mode==='continue'){
    await p.evaluate(()=>{qa.say('दिल्ली में कितने');qa.end()});
    await p.waitForFunction(()=>qa.starts===2&&qa.active);assert.deepEqual(queries,[]);
    await p.evaluate(()=>qa.say('बजे हैं'));
    await p.waitForFunction(()=>qa.spoken.some(x=>x.includes('391')));
    assert.deepEqual(queries,['दिल्ली में कितने बजे हैं']);
   }else if(mode==='no-followup'){
    await p.evaluate(()=>{qa.say('सत्रह गुणा');qa.end()});await p.waitForFunction(()=>qa.starts===2&&qa.active);
    await p.evaluate(()=>qa.fault('no-speech'));
    await p.waitForFunction(()=>qa.spoken.some(x=>x.includes('साफ़ नहीं सुन पाया')));
    assert.deepEqual(queries,[]);
   }else if(mode==='timer'){
    await p.evaluate(()=>qa.say('राजधानी क्या है और'));
    await p.waitForFunction(()=>qa.spoken.some(x=>x.includes('साफ़ नहीं सुन पाया')),null,{timeout:5000});
    assert.deepEqual(queries,[]);
   }else if(mode==='complete'){
    await p.evaluate(()=>{qa.say('दिल्ली में कितने बजे हैं');qa.end()});
    await p.waitForFunction(()=>qa.spoken.some(x=>x.includes('391')));
    assert.deepEqual(queries,['दिल्ली में कितने बजे हैं']);
   }else{
    await p.evaluate(()=>{qa.say('भारत की');qa.end()});await p.waitForFunction(()=>qa.starts===2&&qa.active);
    await p.evaluate(()=>{qa.late=qa.active});await p.keyboard.press('Escape');
    await p.evaluate(()=>qa.late.onresult?.({resultIndex:0,results:[Object.assign([{transcript:'राजधानी',confidence:.9}],{isFinal:true})]}));
    await p.waitForTimeout(300);assert.deepEqual(queries,[]);
    assert.equal(await p.evaluate(()=>document.documentElement.dataset.conversation),'off');
   }
   assert.deepEqual(errors,[]);console.log('PASS',mode,'fragment handling (mocked speech)');
  }finally{await p.close()}
 }
 try{for(const mode of ['continue','no-followup','timer','complete','escape'])await scenario(mode)}finally{await b.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
