/* Pure grammar regression, not an audio-recognition test. */
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const text=fs.readFileSync('hologram/ui/index.html','utf8');
const code=text.split('/* PILOT GRAMMAR:')[1].split('/* PILOT END */')[0];
const pilot=vm.runInNewContext('(()=>{/* PILOT GRAMMAR:'+code+';return Pilot;})()',{URL});
for(const x of ['दिल्ली में कितने','सत्रह गुणा','भारत की','what time in','seventeen multiplied by'])assert.equal(pilot.dangling(x),true,x);
for(const x of ['दिल्ली में कितने बजे हैं','और मुंबई में','aur london mein','सत्रह गुणा तेइस कितना है','नेपाल की राजधानी क्या है','open youtube'])assert.equal(pilot.dangling(x),false,x);
console.log('PASS: partial endings and complete Hindi/English questions (synthetic grammar only)');

for(const x of ['Jarvis time in Delhi','जार्विस सत्रह गुणा तेइस','hey jarvis what time','जारविस'])assert.equal(pilot.hasWake(x),true,x);
for(const x of ['random jarvis time','the jarvis app','jarvisian','what time'])assert.equal(pilot.hasWake(x),false,x);
for(const x of ['stop listening','माइक बंद करो','mic band karo','turn microphone off','जार्विस माइक बंद करो'])assert.equal(pilot.isStop(x),true,x);
for(const x of ['never stop listening','please do not stop listening','what time'])assert.equal(pilot.isStop(x),false,x);
console.log('PASS: strict wake boundaries and spoken stop expressions');
