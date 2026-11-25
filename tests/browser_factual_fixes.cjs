/* Browser speech recognition and device speech are mocked; the HTTP command
   endpoint and Wikipedia lookup are real. Does not test acoustics or speakers. */
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({headless: true, args: ['--no-sandbox']});
  try {
    for (const [question, expected, source] of [
      ['नेपाल की राजधानी क्या है', 'काठमांडू', 'Wikipedia'],
      ['What is 17 modulo 5', '2', 'Calculator'],
      ['In what year did India become independent', '1947', 'local'],
      ['17 को 23 से गुणा करो', '391', 'Calculator'],
    ]) {
      const page = await browser.newPage({viewport: {width: 900, height: 650}});
      const errors = []; page.on('pageerror', e => errors.push(e.message));
      await page.addInitScript(() => {
        localStorage.setItem('amber:mic-on-open', 'off');
        const t = window.testSpeech = {active: null, spoken: []};
        window.SpeechRecognition = window.webkitSpeechRecognition = class {
          start(){ t.active=this; setTimeout(()=>this.onstart?.(), 5); }
          abort(){ if(t.active===this)t.active=null; setTimeout(()=>this.onend?.(), 5); }
        };
        window.SpeechSynthesisUtterance = class { constructor(text){this.text=text;} };
        Object.defineProperty(window, 'speechSynthesis', {configurable:true, value:{
          getVoices:()=>[{lang:'hi-IN',name:'Hindi test voice',localService:true}],
          cancel(){}, get speaking(){return false}, get pending(){return false},
          speak(u){t.spoken.push(u.text);setTimeout(()=>u.onstart?.(),5);setTimeout(()=>u.onend?.(),30)}
        }});
      });
      await page.goto(process.env.AMBER_TEST_URL || 'http://127.0.0.1:8765');
      await page.keyboard.press('Space');
      await page.waitForFunction(() => !!window.testSpeech.active, null, {timeout:10000});
      const reply = page.waitForResponse(r => r.url().endsWith('/api/command'), {timeout:20000});
      await page.evaluate(s => window.testSpeech.active.onresult({resultIndex:0,results:[Object.assign([{transcript:s}],{isFinal:true})]}), question);
      const response = await (await reply).json();
      assert.equal(response.source, source); assert.ok(response.text.includes(expected), JSON.stringify(response));
      await page.waitForFunction(e => window.testSpeech.spoken.some(s=>s.includes(e)), expected, {timeout:10000});
      assert.deepEqual(errors, []);
      console.log('PASS', question, '->', response.text, '(recognition and voice mocked)');
      await page.close();
    }
  } finally { await browser.close(); }
})().catch(e => {console.error(e);process.exitCode=1});
