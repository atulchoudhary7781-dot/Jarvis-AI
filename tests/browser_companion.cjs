/* Simulated microphone and short device playback; actual UI, notebook, catalog,
   command API and (when installed) chat model. No GitHub issue is opened or posted. */
const assert = require("node:assert/strict");
const { chromium } = require("playwright");
function fixture() {
  // This scenario explicitly starts the mic with Space.
  localStorage.setItem("amber:mic-on-open", "off");
  const x = (window.friendQA = { active: null, starts: 0, overlap: 0, u: null, drafts: [] });
  window.SpeechRecognition = class {
    start() {
      if (x.active || x.u) x.overlap++;
      x.active = this;
      x.starts++;
    }
    abort() {
      if (x.active === this) x.active = null;
      setTimeout(() => this.onend?.(), 8);
    }
  };
  x.say = (s) =>
    x.active.onresult({ resultIndex: 0, results: [Object.assign([{ transcript: s }], { isFinal: true })] });
  window.SpeechSynthesisUtterance = class {
    constructor(text) {
      this.text = text;
    }
  };
  Object.defineProperty(window, "speechSynthesis", {
    configurable: true,
    value: {
      get speaking() {
        return !!x.u;
      },
      get pending() {
        return false;
      },
      getVoices() {
        return [];
      },
      cancel() {
        const u = x.u;
        x.u = null;
        u?.onerror?.({ error: "canceled" });
      },
      speak(u) {
        if (x.active) x.overlap++;
        x.u = u;
        setTimeout(() => {
          if (x.u === u) u.onstart?.();
        }, 2);
        setTimeout(() => {
          if (x.u === u) {
            x.u = null;
            u.onend?.();
          }
        }, 45);
      },
    },
  });
  window.open = (url) => {
    x.drafts.push(String(url));
    return null;
  };
  sessionStorage.setItem("amber:language", "en-IN");
}
(async () => {
  const root = process.env.AMBER_TEST_URL || "http://127.0.0.1:8765";
  const opts = { headless: true };
  if (process.env.AMBER_TEST_ARGS) opts.args = JSON.parse(process.env.AMBER_TEST_ARGS);
  if (process.env.AMBER_TEST_CHROMIUM) opts.executablePath = process.env.AMBER_TEST_CHROMIUM;
  const b = await chromium.launch(opts);
  try {
    const p = await b.newPage({ viewport: { width: 460, height: 360 }, reducedMotion: "reduce" });
    await p.addInitScript(fixture);
    const errors = [],
      queries = [];
    p.on("pageerror", (e) => errors.push(e.message));
    p.on("request", (r) => {
      if (r.url().endsWith("/api/command")) queries.push(r.postDataJSON());
    });
    await p.route("**/api/voice", (r) => r.fulfill({ json: { ok: false, reason: "system" } }));
    const wait = (fn) => p.waitForFunction(fn, null, { timeout: 35000 });
    const boot = async (load) => {
      const shelf = p.waitForResponse((r) => r.url().endsWith("/api/community-skills"));
      await load();
      assert.equal((await (await shelf).json()).version, 1);
      await p.evaluate(() => localStorage.removeItem("amber:mic-on-open"));
      await p.keyboard.press("Space");
      await wait(() => friendQA.active);
    };
    async function turn(s, regex, off = false) {
      await wait(() => friendQA.active && !friendQA.u);
      await p.evaluate((v) => friendQA.say(v), s);
      await p.waitForFunction(
        (src) => new RegExp(src, "iu").test(document.querySelector("#status").textContent),
        regex.source,
        { timeout: 35000 }
      );
      if (off) await wait(() => document.documentElement.dataset.state === "idle");
      else await wait(() => friendQA.active);
    }
    await boot(() => p.goto(root));
    await turn("hello friend", /day|mind/);
    await turn("when I say night owl, time in Tokyo", /save it/);
    assert.equal(await p.evaluate(() => localStorage.length), 0);
    await turn("yes", /saved in this browser/);
    await turn("night owl", /in Tokyo/);
    assert.equal(queries.at(-1).query, "time in Tokyo");
    await turn("planet pop quiz", /Great Red Spot/);
    await turn("Jupiter", /you got it/);
    await turn("time in Paris", /in Paris/);
    await turn("time in Paris", /checked that twice/);
    await turn("no", /leave it/);
    if (process.env.AMBER_TEST_MODEL === "1") {
      await turn("Invent a creature that sleeps in a violin case", /terms/);
      const res1 = p.waitForResponse((r) => r.url().endsWith("/api/command"), { timeout: 45000 });
      await p.evaluate(() => friendQA.say("yes"));
      const one = await (await res1).json();
      assert.equal(one.source, "Companion", JSON.stringify(one));
      assert.ok(one.text.length > 8);
      await wait(() => friendQA.active);
      const res2 = p.waitForResponse((r) => r.url().endsWith("/api/command"), { timeout: 45000 });
      await p.evaluate(() => friendQA.say("What noise does that creature make?"));
      const two = await (await res2).json();
      await wait(() => friendQA.active);
      assert.equal(two.source, "Companion", JSON.stringify(two));
      assert.ok(two.text.length > 5);
      assert.ok(queries.at(-1).history.some((m) => m.role === "assistant" && m.content === one.text));
      console.log("Actual model answered initial and follow-up prompts; bounded recent context included.");
    }
    await p.keyboard.press("Escape");
    await boot(() => p.reload());
    await turn("night owl", /in Tokyo/);
    await turn("share skill night owl", /GitHub issues are public/);
    assert.equal(await p.evaluate(() => friendQA.drafts.length), 0);
    await turn("yes", /nothing is posted/, true);
    assert.equal(await p.evaluate(() => !!friendQA.active), false);
    assert.equal(await p.evaluate(() => friendQA.drafts.length), 0);
    await p.keyboard.press("s");
    let draft = await p.evaluate(() => friendQA.drafts[0]);
    assert.match(draft, /^https:\/\/github\.com\/atulchoudhary7781-dot\/Jarvis-AI\/issues\/new\?/);
    assert.equal(queries.filter((v) => /night owl|share skill|when I say/i.test(v.query)).length, 0);
    await p.keyboard.press("Space");
    await turn("forget everything", /erase/);
    await turn("yes", /cleared/);
    assert.equal(await p.evaluate(() => localStorage.length), 0);
    await p.keyboard.press("Escape");
    assert.equal(await p.evaluate(() => friendQA.overlap), 0);
    assert.deepEqual(errors, []);
    console.log(
      "PASS: one activation, teach → confirm → run → reload, reviewed quiz, proactive suggestion, draft requires manual gesture, memory clear, no JS or microphone overlap errors."
    );
  } finally {
    await b.close();
  }
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
