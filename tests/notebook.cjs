/* Test the exact notebook embedded in the shipped standalone HTML. No browser, network or npm dependencies. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const page = fs.readFileSync(path.join(root, "hologram/ui/index.html"), "utf8");
const notebook = page.slice(page.indexOf("/* COMPANION START"), page.indexOf("/* COMPANION END"));
const make = vm.runInNewContext(notebook + "\nmakeCompanion", { URL });
const community = JSON.parse(fs.readFileSync(path.join(root, "community/skills.json"))).skills;
const db = new Map(),
  storage = () => ({
    getItem: (k) => db.get(k),
    setItem: (k, v) => db.set(k, v),
    removeItem: (k) => db.delete(k),
  });
let lang = "en-IN",
  time = 100,
  book;
function init(store = storage) {
  book = make({ storage: store, language: () => lang, now: () => time, random: () => 0 });
  book.updateCatalog(community);
}
const say = (q) => book.handle(q),
  heard = (q, re) => assert.match(say(q)?.text || "", re);
init();
assert.equal(say("a long quiet walk"), null);
heard("hello friend", /day|mind/);
heard("surprise me", /nearest object|café|movie/);
assert.equal(db.size, 0);
heard("Call me Sky", /remember/);
heard("no", /leave/);
heard("what is my name", /haven’t saved/);
assert.equal(db.size, 0);
heard("Call me Sky", /remember/);
heard("yes", /Sky/);
heard("hello", /Sky/);
init();
heard("what is my name", /Sky/);
heard("when I say sunrise check, time in Tokyo and date in Delhi", /Save/);
assert.equal(say("sunrise check"), null);
heard("teach a shortcut", /short phrase/);
heard("sunrise check", /should/);
heard("time in Tokyo and date in Delhi", /Save/);
heard("yes", /saved in this browser/);
init();
assert.deepEqual(JSON.parse(JSON.stringify(say("sunrise check").recipe.steps)), [
  { kind: "time", city: "Tokyo" },
  { kind: "date", city: "Delhi" },
]);
heard("when I say sunrise check, time in London", /Replace/);
heard("no", /leave/);
assert.equal(say("sunrise check").recipe.steps.length, 2);
heard("when I say odd job, upload a file", /Try a city/);
assert.equal(say("odd job"), null);
heard("teach a quiz", /call this quiz/);
heard("cricket quiz", /What question/);
heard("How many balls in a standard over?", /what answer/);
heard("six", /Save/);
heard("yes", /saved/);
init();
heard("cricket quiz", /standard over/);
heard("six", /You got it/);
heard("cricket quiz", /standard over/);
heard("three", /answer on this card is six/);
heard("community skills", /planet pop quiz/);
heard("planet pop quiz", /Great Red Spot/);
heard("Jupiter", /You got it/);
assert.equal(say("सिटी डुएट").recipe.steps.length, 2);
heard("share my skill sunrise check", /GitHub issues are public/);
assert.equal(book.takeReview(), "");
heard("no", /leave/);
assert.equal(book.takeReview(), "");
heard("share skill sunrise check", /only/);
const draft = say("yes");
assert.equal(draft.disarm, true);
const u = new URL(book.takeReview());
assert.equal(u.origin, "https://github.com");
assert.equal(u.pathname, "/atulchoudhary7781-dot/Jarvis-AI/issues/new");
assert.match(u.searchParams.get("body"), /Tokyo/);
assert.doesNotMatch(u.searchParams.get("body"), /Sky|cricket/);
assert.equal(book.takeReview(), "");
const obs = (q) => book.observe(q, { topic: "time" });
assert.equal(obs("Jarvis, time in Paris"), "");
assert.match(obs("time in Paris"), /checked that twice/);
heard("yes", /call/);
heard("paris clock", /Save/);
heard("yes", /saved/);
assert.equal(say("paris clock").recipe.steps[0].city, "Paris");
book.reset();
heard("suggestions off", /No more/);
assert.equal(obs("time in Berlin") + obs("time in Berlin"), "");
heard("riddle", /wetter/);
heard("hint", /bathroom/);
heard("tell me", /towel/);
heard("yes", /hands/);
heard("clock", /Exactly/);
lang = "hi-IN";
heard("जब मैं सुबह की घंटी बोलूँ तो दिल्ली का समय", /याद रखूँ/);
heard("हाँ", /याद रख लिया/);
assert.equal(say("सुबह की घंटी").recipe.steps[0].kind, "time");
heard("मुझे अमन बुलाओ", /अमन/);
time += 180001;
assert.equal(say("हाँ"), null);
heard("मेरा नाम क्या है", /Sky/);
lang = "en-IN";
heard("forget skill sunrise check", /Removed/);
assert.equal(say("sunrise check"), null);
heard("forget everything", /erase/);
heard("yes", /cleared/);
assert.equal(db.size, 0);
init();
heard("my shortcuts", /No saved/);
init(() => {
  throw Error("Storage blocked");
});
heard("when I say short break, five minutes", /Save/);
heard("yes", /this page only/);
assert.equal(say("short break").recipe.steps[0].minutes, 5);
console.log(
  "PASS: local consent, persistence, cancellation/expiry, overwrite, deletion, Hindi, bounded recipes, quiz, contextual ideas, public draft isolation and blocked storage."
);
