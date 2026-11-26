/* Optional browser regression: install Playwright + Chromium, start the local
   server, then run node tests/browser_conversation.cjs. Only browser recognition
   and system speech events are simulated. Two answers use the real clock API.
   The optional real-neural smoke is exercised separately without credentials. */
const assert = require("node:assert/strict");
const { chromium } = require("playwright");
function installFixture() {
  // This regression exercises explicit one-gesture activation, not auto-start.
  localStorage.setItem("amber:mic-on-open", "off");
  const x = (window.voiceTest = { starts: 0, stops: 0, active: null, spoken: [], overlap: 0, utterance: null });
  window.SpeechRecognition = class {
    start() {
      if (x.active) x.overlap++;
      x.active = this;
      x.starts++;
    }
    abort() {
      if (x.active === this) x.active = null;
      x.stops++;
      setTimeout(() => this.onend?.(), 18);
    }
  };
  x.say = (s) => {
    if (!x.active) throw Error("No active recognizer");
    x.active.onresult?.({ resultIndex: 0, results: [Object.assign([{ transcript: s }], { isFinal: true })] });
  };
  x.fault = (s) => x.active?.onerror?.({ error: s });
  window.SpeechSynthesisUtterance = class {
    constructor(text) {
      this.text = text;
    }
  };
  const synth = {
    get pending() {
      return false;
    },
    get speaking() {
      return !!x.utterance;
    },
    getVoices: () => [
      { lang: "hi-IN", name: "Microsoft Kalpana", localService: true },
      { lang: "hi-IN", name: "Microsoft Madhur Online (Natural)", localService: false },
      { lang: "en-GB", name: "Daniel (Enhanced)", localService: true },
    ],
    cancel() {
      const u = x.utterance;
      x.utterance = null;
      if (u) u.onerror?.({ error: "canceled" });
    },
    speak(u) {
      x.utterance = u;
      x.spoken.push({ text: u.text, voice: u.voice?.name });
      setTimeout(() => {
        if (x.utterance === u) u.onstart?.();
      }, 12);
    },
  };
  Object.defineProperty(window, "speechSynthesis", { configurable: true, value: synth });
  x.finish = () => {
    const u = x.utterance;
    x.utterance = null;
    u?.onend?.();
  };
}
(async () => {
  const root = process.env.AMBER_TEST_URL || "http://127.0.0.1:8765",
    launch = { headless: true };
  if (process.env.AMBER_TEST_CHROMIUM) launch.executablePath = process.env.AMBER_TEST_CHROMIUM;
  if (process.env.AMBER_TEST_ARGS) launch.args = JSON.parse(process.env.AMBER_TEST_ARGS);
  const b = await chromium.launch(launch);
  try {
    const p = await b.newPage({ viewport: { width: 880, height: 610 }, reducedMotion: "reduce" });
    await p.addInitScript(installFixture);
    const errors = [];
    p.on("pageerror", (e) => errors.push(e.message));
    // Force the device fallback even on a host that has downloaded the neural model.
    await p.route("**/api/voice", (r) => r.fulfill({ json: { ok: false, reason: "system" } }));
    await p.goto(root);
    const ev = (fn) => p.evaluate(fn),
      wait = (fn, ms = 7000) => p.waitForFunction(fn, null, { timeout: ms });
    await wait(() => document.documentElement.dataset.state === "idle");
    assert.equal(await ev(() => voiceTest.starts), 0);
    await p.keyboard.press("Space");
    await wait(() => voiceTest.starts === 1);
    await ev(() => voiceTest.say("जार्विस टोक्यो में कितने बजे हैं"));
    await wait(() => document.documentElement.dataset.state === "speaking");
    assert.match(await ev(() => voiceTest.spoken.at(-1).text), /टोक्यो/);
    assert.match(await ev(() => voiceTest.spoken.at(-1).voice), /Madhur/);
    await wait(() => voiceTest.active !== null);
    assert.equal(await ev(() => voiceTest.starts), 2);
    await p.waitForTimeout(600);
    assert.equal(await ev(() => voiceTest.starts), 2);
    await ev(() => voiceTest.finish());
    await wait(() => voiceTest.active !== null && voiceTest.starts >= 3);
    await ev(() => voiceTest.say("और लंदन में?"));
    await wait(() => document.documentElement.dataset.state === "speaking");
    assert.match(await ev(() => voiceTest.spoken.at(-1).text), /लंदन/);
    await wait(() => voiceTest.active !== null);
    await ev(() => voiceTest.finish());
    await wait(() => voiceTest.active !== null && voiceTest.starts >= 5);
    await ev(() => voiceTest.say("Jarvis, mic band karo"));
    await wait(() => document.documentElement.dataset.state === "speaking");
    assert.equal(await p.getAttribute("#core", "aria-pressed"), "false");
    await ev(() => voiceTest.finish());
    await p.waitForTimeout(800);
    const stoppedStarts = await ev(() => voiceTest.starts);
    assert.equal(await ev(() => voiceTest.active), null);
    console.log(
      "PASS: one gesture, two real answers including a contextual follow-up, mid-reply listening and spoken stop."
    );
    await p.keyboard.press("Space");
    await wait(() => voiceTest.active !== null);
    const n = await ev(() => voiceTest.spoken.length);
    await ev(() => voiceTest.fault("no-speech"));
    await p.waitForFunction((n) => voiceTest.starts === n + 2, stoppedStarts);
    assert.equal(await ev(() => voiceTest.spoken.length), n);
    await ev(() => voiceTest.fault("not-allowed"));
    await wait(() => document.documentElement.dataset.conversation === "off");
    await p.keyboard.press("Escape");
    await p.waitForTimeout(650);
    assert.equal(await ev(() => voiceTest.starts), stoppedStarts + 2);
    console.log("PASS: silence rearms quietly, permission denial never loops.");
    await p.keyboard.press("Space");
    await wait(() => voiceTest.active !== null);
    await ev(() => {
      Object.defineProperty(document, "hidden", { configurable: true, value: true });
      document.dispatchEvent(new Event("visibilitychange"));
    });
    await p.waitForTimeout(70);
    await ev(() => {
      delete document.hidden;
      document.dispatchEvent(new Event("visibilitychange"));
    });
    await p.waitForTimeout(700);
    assert.equal(await ev(() => voiceTest.active), null);
    assert.equal(await p.getAttribute("#core", "aria-pressed"), "false");
    let waiting;
    const delayed = new Promise((ok) => {
      waiting = ok;
    });
    await p.route("**/api/command", async (r) => {
      waiting();
      await new Promise((ok) => setTimeout(ok, 650));
      await r.fulfill({ json: { text: "late answer", lang: "en-IN" } }).catch(() => {});
    });
    await p.keyboard.press("Space");
    await wait(() => voiceTest.active !== null);
    await ev(() => voiceTest.say("time in Paris"));
    await delayed;
    await p.keyboard.press("Escape");
    await p.waitForTimeout(950);
    assert.ok(!(await ev(() => voiceTest.spoken)).some((v) => v.text === "late answer"));
    assert.equal(await ev(() => voiceTest.overlap), 0);
    assert.equal(await ev(() => voiceTest.active), null);
    assert.equal(errors.length, 0, errors.join("; "));
    console.log("PASS: hidden tab stays disarmed, late answer ignored, no duplicate recognizers or JS errors.");
  } finally {
    await b.close();
  }
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
