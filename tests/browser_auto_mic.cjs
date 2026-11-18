/* Browser lifecycle tests. The granted case uses the browser's real permission
   store; recognition events, device speech and policy failures are controlled
   fixtures. No physical microphone or third-party recognizer is used. */
const assert = require("node:assert/strict");
const { chromium } = require("playwright");
function fixture(mode) {
  const x = (window.micQA = {
    attempts: 0,
    starts: 0,
    active: null,
    pending: null,
    utterance: null,
    spoken: [],
    errors: 0,
    overlap: 0,
    queries: 0,
    gesture: [],
  });
  // Playwright's evaluate can set Chromium's user-activation bit. Model a
  // gesture-only output policy with actual trusted input events instead.
  for (const type of ["pointerdown", "keydown"])
    addEventListener(
      type,
      (e) => {
        if (e.isTrusted) x.hadInput = true;
      },
      true
    );
  sessionStorage.setItem("amber:language", "en-IN");
  const perm = new EventTarget();
  perm.state = mode === "denied" ? "denied" : mode === "prompt" ? "prompt" : "granted";
  x.perm = (v) => {
    perm.state = v;
    perm.dispatchEvent(new Event("change"));
  };
  if (mode !== "native-granted")
    Object.defineProperty(navigator, "permissions", {
      configurable: true,
      value: {
        query() {
          x.queries++;
          if (mode === "no-permissions-api") throw TypeError("Unsupported permission descriptor");
          if (mode === "deferred" || mode === "race")
            return new Promise((r) => {
              x.complete = () => r(perm);
            });
          return Promise.resolve(perm);
        },
      },
    });
  if (mode === "hidden") Object.defineProperty(document, "hidden", { configurable: true, value: true });
  if (mode === "unsupported") {
    Object.defineProperty(window, "SpeechRecognition", { value: undefined });
    Object.defineProperty(window, "webkitSpeechRecognition", { value: undefined });
  } else
    window.SpeechRecognition = class {
      start() {
        x.attempts++;
        x.gesture.push(navigator.userActivation?.hasBeenActive === true);
        if (mode === "gesture" && !navigator.userActivation?.isActive)
          throw new DOMException("Activation required", "NotAllowedError");
        if (x.active || x.utterance) x.overlap++;
        x.pending = this;
        const self = this;
        x.begin = () => {
          if (x.pending !== self) return;
          x.pending = null;
          x.active = self;
          x.starts++;
          self.onstart?.();
          self.onaudiostart?.();
        };
        if (mode !== "prompt") queueMicrotask(x.begin);
      }
      abort() {
        if (x.active === this) x.active = null;
        if (x.pending === this) x.pending = null;
        const end = this.onend;
        setTimeout(() => end?.(), 5);
      }
    };
  x.say = (s) =>
    x.active.onresult({ resultIndex: 0, results: [Object.assign([{ transcript: s }], { isFinal: true })] });
  window.SpeechSynthesisUtterance = class {
    constructor(t) {
      this.text = t;
    }
  };
  Object.defineProperty(window, "speechSynthesis", {
    configurable: true,
    value: {
      get speaking() {
        return !!x.utterance;
      },
      get pending() {
        return false;
      },
      getVoices() {
        return [];
      },
      cancel() {
        const u = x.utterance;
        x.utterance = null;
        u?.onerror?.({ error: "canceled" });
      },
      speak(u) {
        if (x.active) x.overlap++;
        if (mode === "autoplay" && !x.hadInput) {
          x.errors++;
          queueMicrotask(() => u.onerror?.({ error: "not-allowed" }));
          return;
        }
        x.utterance = u;
        x.spoken.push(u.text);
        setTimeout(() => {
          if (x.utterance === u) u.onstart?.();
        }, 3);
        setTimeout(() => {
          if (x.utterance === u) {
            x.utterance = null;
            u.onend?.();
          }
        }, 70);
      },
    },
  });
}
(async () => {
  const url = process.env.AMBER_TEST_URL || "http://127.0.0.1:8765",
    origin = new URL(url).origin;
  const opts = { headless: true };
  if (process.env.AMBER_TEST_CHROMIUM) opts.executablePath = process.env.AMBER_TEST_CHROMIUM;
  if (process.env.AMBER_TEST_ARGS) opts.args = JSON.parse(process.env.AMBER_TEST_ARGS);
  const b = await chromium.launch(opts);
  async function test(name, mode, run, { frame = false } = {}) {
    const c = await b.newContext({ viewport: { width: 390, height: 330 }, reducedMotion: "reduce" });
    try {
      if (mode === "native-granted") await c.grantPermissions(["microphone"], { origin });
      const p = await c.newPage();
      await p.addInitScript(fixture, mode);
      const errors = [],
        qs = [];
      p.on("pageerror", (e) => errors.push(e.message));
      p.on("request", (r) => {
        if (r.url().endsWith("/api/command")) qs.push(r.postDataJSON().query);
      });
      await p.route("**/api/voice", (r) => r.fulfill({ json: { ok: false, reason: "system" } }));
      if (frame)
        await p.route("**/qa-frame-only", (r) =>
          r.fulfill({ contentType: "text/html", body: '<iframe src="/" allow="microphone"></iframe>' })
        );
      await p.goto(frame ? origin + "/qa-frame-only" : url, { waitUntil: "load" });
      const wait = (fn, arg) => p.waitForFunction(fn, arg, { polling: 30, timeout: 7000 });
      await run(p, wait, qs);
      assert.deepEqual(errors, []);
      assert.equal(await p.evaluate(() => micQA.overlap), 0);
      console.log("PASS:", name);
    } finally {
      await c.close();
    }
  }
  try {
    await test(
      "saved native permission: zero gestures, two successive clock questions, spoken stop",
      "native-granted",
      async (p, w) => {
        await w(() => micQA.starts === 1 && document.documentElement.dataset.state === "listening");
        assert.equal(
          await p.evaluate(async () => (await navigator.permissions.query({ name: "microphone" })).state),
          "granted"
        );
        assert.deepEqual(await p.evaluate(() => micQA.gesture), [false]);
        await p.evaluate(() => micQA.say("time in Tokyo"));
        await w(() => micQA.starts === 2);
        assert.match(await p.evaluate(() => micQA.spoken.join(" ")), /Tokyo/i);
        await p.evaluate(() => micQA.say("what about London"));
        await w(() => micQA.starts === 3);
        assert.match(await p.evaluate(() => micQA.spoken.join(" ")), /London/i);
        await p.evaluate(() => micQA.say("stop listening"));
        await w(
          () =>
            document.documentElement.dataset.conversation === "off" &&
            document.documentElement.dataset.state === "idle"
        );
        await p.waitForTimeout(600);
        assert.equal(await p.evaluate(() => micQA.starts), 3);
      }
    );
    await test(
      "first visit asks only once; waits for browser approval, respects revocation",
      "prompt",
      async (p, w) => {
        await w(() => micQA.attempts === 1 && document.documentElement.dataset.micLaunch === "requesting");
        assert.equal(await p.locator("#core").getAttribute("aria-pressed"), "false");
        assert.equal(await p.evaluate(() => micQA.active), null);
        await p.evaluate(() => {
          micQA.perm("granted");
          micQA.begin();
        });
        await w(() => micQA.starts === 1 && document.documentElement.dataset.conversation === "on");
        await p.evaluate(() => micQA.perm("denied"));
        await w(() => micQA.active === null && document.documentElement.dataset.conversation === "off");
        await p.waitForTimeout(550);
        assert.equal(await p.evaluate(() => micQA.attempts), 1);
      }
    );
    await test("deny produces no start attempts or error-speech loop", "denied", async (p, w) => {
      await w(() => micQA.queries === 1 && /blocked/i.test(document.querySelector("#status").textContent));
      await p.waitForTimeout(600);
      assert.equal(await p.evaluate(() => micQA.attempts + micQA.spoken.length), 0);
    });
    await test("native denial after the prompt never re-prompts", "prompt", async (p, w) => {
      await w(() => !!micQA.pending);
      await p.evaluate(() => micQA.pending.onerror({ error: "not-allowed" }));
      await w(() => !micQA.pending && document.documentElement.dataset.state === "idle");
      await p.waitForTimeout(650);
      assert.equal(await p.evaluate(() => micQA.attempts), 1);
    });
    await test(
      "gesture-only browser: a single real tap/Space starts the manual path",
      "gesture",
      async (p, w) => {
        await w(() => micQA.attempts === 1 && document.documentElement.dataset.state === "idle");
        await p.keyboard.press("Space");
        await w(() => micQA.starts === 1);
        assert.deepEqual(await p.evaluate(() => micQA.gesture), [false, true]);
        await p.keyboard.press("Escape");
      }
    );
    await test("Escape cancels a pending grant; a later result cannot restart", "deferred", async (p, w) => {
      await w(() => !!micQA.complete);
      await p.keyboard.press("Escape");
      await p.evaluate(() => micQA.complete());
      await p.waitForTimeout(250);
      assert.equal(await p.evaluate(() => micQA.attempts), 0);
    });
    await test("manual start wins a slow Permissions API query, no second recognizer", "race", async (p, w) => {
      await w(() => !!micQA.complete);
      await p.keyboard.press("Space");
      await w(() => micQA.starts === 1);
      await p.evaluate(() => micQA.complete());
      await p.waitForTimeout(200);
      assert.equal(await p.evaluate(() => micQA.attempts), 1);
    });
    await test("a stale native start after hiding the tab does not rearm on return", "prompt", async (p, w) => {
      await w(() => !!micQA.pending);
      await p.evaluate(() => {
        const late = micQA.pending.onstart;
        Object.defineProperty(document, "hidden", { value: true, configurable: true });
        document.dispatchEvent(new Event("visibilitychange"));
        delete document.hidden;
        document.dispatchEvent(new Event("visibilitychange"));
        late?.();
      });
      await p.waitForTimeout(350);
      assert.equal(await p.locator("#core").getAttribute("aria-pressed"), "false");
      assert.equal(await p.evaluate(() => micQA.attempts), 1);
    });
    await test(
      "a tap cancels a pending native request without immediately requesting again",
      "prompt",
      async (p, w) => {
        await w(() => !!micQA.pending);
        await p.locator("#core").click({ position: { x: 195, y: 165 } });
        await w(() => !micQA.pending && document.documentElement.dataset.state === "idle");
        assert.equal(await p.evaluate(() => micQA.attempts), 1);
      }
    );
    await test(
      "recognition still starts when the permissions query is unsupported",
      "no-permissions-api",
      async (p, w) => {
        await w(() => micQA.starts === 1 && document.documentElement.dataset.state === "listening");
      }
    );
    await test(
      "background-created tab waits for its first opening; later visits do not rearm",
      "hidden",
      async (p, w) => {
        assert.equal(await p.evaluate(() => micQA.attempts), 0);
        await p.evaluate(() => {
          delete document.hidden;
          document.dispatchEvent(new Event("visibilitychange"));
        });
        await w(() => micQA.starts === 1);
        await p.evaluate(() => {
          Object.defineProperty(document, "hidden", { value: true, configurable: true });
          document.dispatchEvent(new Event("visibilitychange"));
          delete document.hidden;
          document.dispatchEvent(new Event("visibilitychange"));
        });
        await p.waitForTimeout(600);
        assert.equal(await p.evaluate(() => micQA.attempts), 1);
        assert.equal(await p.locator("#core").getAttribute("aria-pressed"), "false");
      }
    );
    for (const m of ["unsupported", "embedded"])
      await test(
        "no launch capture: " + m,
        m,
        async (p) => {
          if (m === "embedded") {
            const f = p.frames().find((z) => z !== p.mainFrame());
            await f.waitForFunction(() => document.documentElement.dataset.state === "idle");
            assert.equal(await f.evaluate(() => micQA.attempts), 0);
          } else {
            await p.waitForTimeout(200);
            assert.equal(await p.evaluate(() => micQA.attempts), 0);
          }
        },
        { frame: m === "embedded" }
      );
    await test(
      "persistent manual preference; A restores automatic startup for the next opening",
      "normal",
      async (p, w) => {
        await w(() => micQA.starts === 1);
        await p.evaluate(() => micQA.say("auto mic off"));
        await w(
          () =>
            localStorage.getItem("amber:mic-on-open") === "off" &&
            document.documentElement.dataset.state === "idle"
        );
        await p.reload();
        await w(() => document.documentElement.dataset.state === "idle");
        assert.equal(await p.evaluate(() => micQA.attempts), 0);
        await p.keyboard.press("a");
        await w(() => localStorage.getItem("amber:mic-on-open") === null);
        await p.reload();
        await w(() => micQA.starts === 1);
      }
    );
    await test(
      "autoplay blocked: mic pauses, gesture plays the saved answer without re-running the command",
      "autoplay",
      async (p, w, qs) => {
        await w(() => micQA.starts === 1);
        await p.evaluate(() => micQA.say("time in Tokyo"));
        await w(() => micQA.errors > 0 && document.documentElement.dataset.conversation === "off");
        assert.equal(await p.evaluate(() => micQA.active), null);
        await p.keyboard.press("Space");
        await w(() => micQA.starts === 2);
        assert.deepEqual(qs, ["time in Tokyo"]);
        assert.match(await p.evaluate(() => micQA.spoken.join(" ")), /Tokyo/);
      }
    );
  } finally {
    await b.close();
  }
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
