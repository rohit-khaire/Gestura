// Thin wrappers around the browser's Web Speech API (no server, no API key).
//  - speak():            text -> speech        (SpeechSynthesis, all modern browsers)
//  - createRecognizer(): speech -> live text   (SpeechRecognition, Chrome / Edge / Safari)

export const speechSupported = typeof window !== "undefined" && "speechSynthesis" in window;

export function speak(text, langTag = "en-US") {
  if (!speechSupported || !text) return false;
  const synth = window.speechSynthesis;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = langTag;

  // Prefer an exact locale match, then any voice of the same language (e.g. hi-IN vs hi).
  const voices = synth.getVoices();
  const base = langTag.split("-")[0];
  const voice = voices.find((v) => v.lang === langTag) || voices.find((v) => v.lang.startsWith(base));
  if (voice) utterance.voice = voice;

  synth.speak(utterance);
  return true;
}

export const stopSpeaking = () => speechSupported && window.speechSynthesis.cancel();

export const getRecognitionCtor = () =>
  typeof window === "undefined" ? null : window.SpeechRecognition || window.webkitSpeechRecognition || null;

/**
 * Continuous speech recogniser that restarts itself (browsers stop it after a few seconds of silence).
 * Returns { start(), stop() }. Callbacks: onInterim(text), onFinal(text), onError(message).
 */
export function createRecognizer({ lang, onInterim, onFinal, onError }) {
  const Ctor = getRecognitionCtor();
  let active = false;
  let rec = null;
  let restartTimer = null;

  const build = () => {
    rec = new Ctor();
    rec.lang = lang;
    rec.continuous = true;
    rec.interimResults = true;

    rec.onresult = (event) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          const text = result[0].transcript.trim();
          if (text) onFinal?.(text);
        } else {
          interim += result[0].transcript;
        }
      }
      onInterim?.(interim);
    };

    rec.onerror = (event) => {
      if (event.error === "not-allowed" || event.error === "service-not-allowed") {
        active = false;
        onError?.("Microphone permission was denied.");
      } else if (event.error !== "no-speech" && event.error !== "aborted") {
        onError?.(`Speech recognition error: ${event.error}`);
      }
    };

    rec.onend = () => {
      if (!active) return;
      restartTimer = setTimeout(() => {
        try {
          rec.start();
        } catch {
          // already running
        }
      }, 300);
    };
  };

  return {
    start() {
      if (!Ctor || active) return;
      active = true;
      build();
      try {
        rec.start();
      } catch {
        // already started
      }
    },
    stop() {
      active = false;
      clearTimeout(restartTimer);
      try {
        rec?.stop();
      } catch {
        // not running
      }
    },
  };
}
