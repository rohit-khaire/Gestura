// Turns a noisy stream of per-frame detections into stable "words" and finished sentences.
//
//   frame detections ──▶ sliding-window vote ──▶ word (once per gesture) ──▶ sentence (after a pause)
//
// Why: a detector fires on single frames and flickers. Speaking every frame would be unusable, so
//  1. a label must win `minVotes` of the last `windowSize` frames before it counts as a word,
//  2. holding a sign emits it only once; it can be repeated only after the hand was lowered
//     (`releaseFrames` frames showing something else),
//  3. words are grouped into a sentence once nothing has been seen for `pauseMs`.
//
// Pure JS, no dependencies -> unit-tested in Frontend/tests with `node --test`.

const DEFAULTS = {
  windowSize: 5,
  minVotes: 3,
  releaseFrames: 3,
  pauseMs: 2500,
  maxWords: 6,
};

export function createSignTranslator(options = {}) {
  const cfg = { ...DEFAULTS, ...options };

  let win = []; // last N frames: { label, score }
  let pending = []; // words of the sentence being built: { label, score, at }
  let lastWord = null;
  let idleFrames = 0; // consecutive frames in which lastWord was NOT the top label
  let released = false; // latched: the sign was lowered, so lastWord may be repeated
  let lastSeenAt = 0;
  let current = null;

  const flushSentence = (now) => {
    if (!pending.length) return null;
    const event = {
      type: "sentence",
      labels: pending.map((w) => w.label),
      score: pending.reduce((sum, w) => sum + w.score, 0) / pending.length,
      at: now,
    };
    pending = [];
    win = [];
    lastWord = null;
    idleFrames = 0;
    released = false;
    current = null;
    return event;
  };

  /**
   * Feed one frame. `detections` is the model output, best first ([] / null when nothing seen).
   * Returns the events this frame produced: { type: "word" | "sentence", ... }.
   */
  function push(detections, now = Date.now()) {
    const top = detections?.[0] ?? null;
    const label = top?.label ?? null;

    win.push({ label, score: top?.score ?? 0 });
    if (win.length > cfg.windowSize) win.shift();
    if (label) lastSeenAt = now;

    if (lastWord) {
      idleFrames = label === lastWord ? 0 : idleFrames + 1;
      if (idleFrames >= cfg.releaseFrames) released = true;
    }

    // Who is winning the vote?
    const tally = new Map();
    for (const f of win) {
      if (!f.label) continue;
      const t = tally.get(f.label) ?? { votes: 0, sum: 0 };
      t.votes += 1;
      t.sum += f.score;
      tally.set(f.label, t);
    }
    let leader = null;
    let leaderVotes = 0;
    for (const [name, t] of tally) {
      if (t.votes > leaderVotes) {
        leader = name;
        leaderVotes = t.votes;
      }
    }
    current = leaderVotes >= cfg.minVotes ? leader : null;

    const events = [];
    if (current && (current !== lastWord || released)) {
      const t = tally.get(current);
      const word = { label: current, score: t.sum / t.votes, at: now };
      pending.push(word);
      lastWord = current;
      idleFrames = 0;
      released = false;
      events.push({ type: "word", ...word });
    }

    if (pending.length && (pending.length >= cfg.maxWords || now - lastSeenAt >= cfg.pauseMs)) {
      events.push(flushSentence(now));
    }
    return events;
  }

  return {
    push,
    /** Force the pending words out as a sentence (e.g. a "speak now" button). */
    flush: (now = Date.now()) => flushSentence(now),
    reset() {
      win = [];
      pending = [];
      lastWord = null;
      idleFrames = 0;
      released = false;
      current = null;
    },
    getState: () => ({ pending: pending.map((w) => w.label), current }),
  };
}
