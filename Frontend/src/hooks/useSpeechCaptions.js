import { useEffect, useRef, useState } from "react";
import { createRecognizer, getRecognitionCtor } from "../lib/speech";

/**
 * Live speech-to-text for the hearing person, so the deaf / hard-of-hearing person can read it.
 * `onFinal(text)` is called for every finished phrase; `interim` is the phrase still being spoken.
 */
export function useSpeechCaptions({ enabled, lang, onFinal, onError }) {
  const [interim, setInterim] = useState("");
  const supported = Boolean(getRecognitionCtor());

  const onFinalRef = useRef(onFinal);
  const onErrorRef = useRef(onError);
  useEffect(() => {
    onFinalRef.current = onFinal;
    onErrorRef.current = onError;
  });

  useEffect(() => {
    if (!enabled || !supported) return;
    const recognizer = createRecognizer({
      lang,
      onInterim: setInterim,
      onFinal: (text) => {
        setInterim("");
        onFinalRef.current?.(text);
      },
      onError: (message) => onErrorRef.current?.(message),
    });
    recognizer.start();
    return () => {
      recognizer.stop();
      setInterim("");
    };
  }, [enabled, lang, supported]);

  return { supported, interim };
}
