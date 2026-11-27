/* Pure grammar regression, not an audio-recognition test. */
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const text=fs.readFileSync('hologram/ui/index.html','utf8');
const code=text.split('/* PILOT GRAMMAR:')[1].split('/* PILOT END */')[0];
const pilot=vm.runInNewContext('(()=>{/* PILOT GRAMMAR:'+code+';return Pilot;})()',{URL});
for(const x of ['दिल्ली में कितने','सत्रह गुणा','भारत की','what time in','seventeen multiplied by'])assert.equal(pilot.dangling(x),true,x);
for(const x of ['दिल्ली में कितने बजे हैं','और मुंबई में','aur london mein','सत्रह गुणा तेइस कितना है','नेपाल की राजधानी क्या है','open youtube'])assert.equal(pilot.dangling(x),false,x);
console.log('PASS: partial endings and complete Hindi/English questions (synthetic grammar only)');
