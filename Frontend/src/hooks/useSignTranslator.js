import { useCallback, useEffect, useRef, useState } from "react";
import { useSignDetection } from "./useSignDetection";
import { createSignTranslator } from "../lib/signTranslator";
import { composeSentence, LANGUAGES } from "../lib/phrases";
import { speak } from "../lib/speech";

let nextId = 1;
const MAX_ENTRIES = 100;

/**
 * Camera frames -> detections -> stable words -> sentences -> (optional) spoken aloud.
 *
 * `transcript` entries:
 *   { id, at, kind: "sign",   labels: [...], name, remote? }   (text is rendered in the viewer's language)
 *   { id, at, kind: "speech", text,          name, remote? }
 * `onSentence(labels)` fires for every finished sentence you sign (used to broadcast it in a call).
 */
export function useSignTranslator({ stream, enabled, lang, autoSpeak, intervalMs = 400, onSentence }) {
  const translatorRef = useRef(null);
  if (translatorRef.current === null) translatorRef.current = createSignTranslator();

  const langRef = useRef(lang);
  const autoSpeakRef = useRef(autoSpeak);
  const onSentenceRef = useRef(onSentence);
  useEffect(() => {
    langRef.current = lang;
    autoSpeakRef.current = autoSpeak;
    onSentenceRef.current = onSentence;
  });

  const [pending, setPending] = useState([]);
  const [transcript, setTranscript] = useState([]);

  const addEntry = useCallback((entry) => {
    const full = { id: nextId++, at: Date.now(), ...entry };
    setTranscript((prev) => [...prev, full].slice(-MAX_ENTRIES));
  }, []);

  // A finished sentence: log it, speak it, tell the call.
  const commit = useCallback(
    (labels) => {
      if (!labels?.length) return;
      addEntry({ kind: "sign", labels, name: "You" });
      if (autoSpeakRef.current) {
        speak(composeSentence(labels, langRef.current), LANGUAGES[langRef.current].speech);
      }
      onSentenceRef.current?.(labels);
    },
    [addEntry],
  );

  const syncPending = useCallback(() => {
    const labels = translatorRef.current.getState().pending;
    setPending((prev) => (prev.join("|") === labels.join("|") ? prev : labels));
  }, []);

  const handleFrame = useCallback(
    (found, now) => {
      for (const event of translatorRef.current.push(found, now)) {
        if (event.type === "sentence") commit(event.labels);
      }
      syncPending();
    },
    [commit, syncPending],
  );

  const detection = useSignDetection({ stream, enabled, intervalMs, onFrame: handleFrame });

  // Switching detection off discards a half-built sentence.
  useEffect(() => {
    if (!enabled) {
      translatorRef.current.reset();
      setPending([]);
    }
  }, [enabled]);

  /** "Speak now": finish the sentence being built without waiting for the pause. */
  const flush = useCallback(() => {
    const event = translatorRef.current.flush(Date.now());
    if (event) commit(event.labels);
    syncPending();
  }, [commit, syncPending]);

  const clear = useCallback(() => {
    translatorRef.current.reset();
    setPending([]);
    setTranscript([]);
  }, []);

  return { ...detection, pending, transcript, addEntry, commit, flush, clear };
}
