import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

import { createSignTranslator } from "../src/lib/signTranslator.js";
import { composeSentence, translateLabel, PHRASES, LANGUAGES, ACTIVE_SIGNS } from "../src/lib/phrases.js";

const det = (label, score = 0.95) => [{ label, score }];
const NONE = [];

// Feed frames every 500 ms (the app's default rate) and collect every event.
function run(translator, frames, start = 0, step = 500) {
  const events = [];
  frames.forEach((f, i) => events.push(...translator.push(f, start + i * step)));
  return { events, end: start + frames.length * step };
}

test("a single frame is not enough to count as a word", () => {
  const t = createSignTranslator();
  const { events } = run(t, [det("hello")]);
  assert.equal(events.length, 0);
});

test("three consistent frames emit exactly one word", () => {
  const t = createSignTranslator();
  const { events } = run(t, [det("hello"), det("hello"), det("hello")]);
  assert.deepEqual(events.map((e) => [e.type, e.label]), [["word", "hello"]]);
});

test("holding a sign does not repeat it", () => {
  const t = createSignTranslator();
  const { events } = run(t, Array(20).fill(det("hello")));
  assert.equal(events.filter((e) => e.type === "word").length, 1);
});

test("one flickering frame does not break recognition", () => {
  const t = createSignTranslator();
  const { events } = run(t, [det("hello"), det("hello"), det("thankyou"), det("hello")]);
  assert.deepEqual(events.filter((e) => e.type === "word").map((e) => e.label), ["hello"]);
});

test("noise below the vote threshold is ignored", () => {
  const t = createSignTranslator();
  const { events } = run(t, [det("hello"), NONE, det("thankyou"), NONE, det("iloveyou"), NONE]);
  assert.equal(events.length, 0);
});

test("the same sign can be repeated after the hand is lowered", () => {
  const t = createSignTranslator();
  const frames = [
    ...Array(4).fill(det("hello")),
    ...Array(4).fill(NONE),
    ...Array(4).fill(det("hello")),
  ];
  const { events } = run(t, frames);
  assert.equal(events.filter((e) => e.type === "word").length, 2);
});

test("switching directly to another sign emits it", () => {
  const t = createSignTranslator();
  const frames = [...Array(3).fill(det("hello")), ...Array(4).fill(det("thankyou"))];
  const { events } = run(t, frames);
  assert.deepEqual(events.filter((e) => e.type === "word").map((e) => e.label), ["hello", "thankyou"]);
});

test("words become one sentence after a pause", () => {
  const t = createSignTranslator();
  const first = run(t, [...Array(3).fill(det("hello")), ...Array(3).fill(det("thankyou"))]);
  assert.equal(first.events.filter((e) => e.type === "sentence").length, 0);
  assert.deepEqual(t.getState().pending, ["hello", "thankyou"]);

  // hand lowered; nothing seen for > pauseMs (2500 ms)
  const second = run(t, Array(7).fill(NONE), first.end);
  const sentence = second.events.find((e) => e.type === "sentence");
  assert.deepEqual(sentence.labels, ["hello", "thankyou"]);
  assert.ok(sentence.score > 0.9);
  assert.deepEqual(t.getState().pending, []);
});

test("a sign can start the next sentence after a flush", () => {
  const t = createSignTranslator();
  let r = run(t, Array(3).fill(det("hello")));
  r = run(t, Array(7).fill(NONE), r.end);
  r = run(t, Array(3).fill(det("hello")), r.end);
  assert.deepEqual(t.getState().pending, ["hello"]);
});

test("a long run of signs is flushed at maxWords", () => {
  const t = createSignTranslator({ maxWords: 2 });
  const frames = [...Array(3).fill(det("hello")), ...Array(3).fill(det("thankyou"))];
  const { events } = run(t, frames);
  assert.equal(events.filter((e) => e.type === "sentence").length, 1);
});

test("flush() and reset()", () => {
  const t = createSignTranslator();
  run(t, Array(3).fill(det("iloveyou")));
  const ev = t.flush(5000);
  assert.deepEqual(ev.labels, ["iloveyou"]);
  assert.equal(t.flush(5000), null);
  run(t, Array(3).fill(det("hello")));
  t.reset();
  assert.deepEqual(t.getState(), { pending: [], current: null });
});

test("composeSentence: English, Hindi, Spanish", () => {
  assert.equal(composeSentence(["hello"], "en"), "Hello.");
  assert.equal(composeSentence(["hello", "iloveyou", "thankyou"], "en"), "Hello, I love you, thank you.");
  assert.equal(composeSentence(["hello", "thankyou"], "hi"), "नमस्ते, धन्यवाद।");
  assert.equal(composeSentence(["hello", "thankyou"], "es"), "Hola, gracias.");
  assert.equal(composeSentence([], "en"), "");
});

test("unknown labels and languages fall back gracefully", () => {
  assert.equal(translateLabel("need_water", "en"), "Need water");
  assert.equal(translateLabel("hello", "xx"), "Hello");
});

test("every sign has a translation for every language", () => {
  for (const [label, entry] of Object.entries(PHRASES)) {
    for (const lang of Object.keys(LANGUAGES)) {
      assert.ok(entry[lang], `${label} is missing "${lang}"`);
    }
  }
});

test("ACTIVE_SIGNS all have translations", () => {
  for (const label of ACTIVE_SIGNS) assert.ok(PHRASES[label], `${label} has no phrases`);
});

test("ACTIVE_SIGNS matches the model's classes in Model/src/config.json", (t) => {
  const path = new URL("../../Model/src/config.json", import.meta.url);
  if (!fs.existsSync(path)) return t.skip("Model/ folder not present (frontend deployed alone)");
  const { classes } = JSON.parse(fs.readFileSync(path, "utf8"));
  assert.deepEqual(ACTIVE_SIGNS, classes, "run: python src/utils/add_signs.py <names>  (or edit both files)");
});
