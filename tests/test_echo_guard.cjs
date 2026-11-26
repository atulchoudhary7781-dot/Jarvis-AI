/* Text echo matching is a conservative heuristic, not acoustic speaker identity. */
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('hologram/ui/index.html','utf8');
const code=html.split('// ECHO_GUARD_BEGIN')[1].split('// ECHO_GUARD_END')[0];
const echo=vm.runInNewContext(`(()=>{${code};return likelyPlaybackEcho})()`);
assert.equal(echo('दिल्ली में', 'भारत में दिल्ली में मौसम अच्छा है।'),true);
assert.equal(echo('Hi, THERE!', 'Well, hi there. What next?'),true);
assert.equal(echo('open youtube', 'Please open youtube when ready.'),true);
assert.equal(echo('open youtube', 'Please do not open youtubers.'),false);
assert.equal(echo('', 'anything'),false);
assert.equal(echo('question', ''),false);
assert.equal(echo('weather in Mumbai', 'weather in Delhi'),false);
console.log('PASS: normalized Hindi and English echo matching uses word boundaries');
