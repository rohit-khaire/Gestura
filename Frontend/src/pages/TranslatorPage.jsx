import { useEffect, useRef, useState } from "react";
import { Link } from "react-router";

import TranslatorPanel from "../components/TranslatorPanel";
import { useSignTranslator } from "../hooks/useSignTranslator";
import { useSpeechCaptions } from "../hooks/useSpeechCaptions";
import { LANGUAGES, translateLabel } from "../lib/phrases";

/**
 * Standalone sign -> text -> speech translator. No account, no Stream keys: just a camera and the
 * detection API (VITE_DETECT_URL). This is the page to demo.
 */
export default function TranslatorPage() {
  const videoRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [camError, setCamError] = useState("");

  const [lang, setLang] = useState("en");
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [detectionOn, setDetectionOn] = useState(true);
  const [micOn, setMicOn] = useState(false);
  const [micError, setMicError] = useState("");

  const translator = useSignTranslator({
    stream,
    enabled: Boolean(stream) && detectionOn,
    lang,
    autoSpeak,
  });

  const { supported: micSupported, interim } = useSpeechCaptions({
    enabled: micOn,
    lang: LANGUAGES[lang].recog,
    onFinal: (text) => translator.addEntry({ kind: "speech", text, name: "Speaker" }),
    onError: (message) => {
      setMicError(message);
      setMicOn(false);
    },
  });

  const startCamera = async () => {
    try {
      const s = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 960 }, height: { ideal: 540 }, facingMode: "user" },
        audio: false,
      });
      setStream(s);
      setCamError("");
    } catch {
      setCamError("Camera access was blocked, or no camera was found.");
    }
  };

  useEffect(() => {
    if (videoRef.current) videoRef.current.srcObject = stream;
  }, [stream]);

  useEffect(() => () => stream?.getTracks().forEach((t) => t.stop()), [stream]);

  const { detections, frameSize } = translator;

  return (
    <div className="min-h-screen bg-gray-900 p-4 text-white">
      <header className="mx-auto mb-4 flex max-w-6xl items-center justify-between">
        <div className="flex items-center gap-3">
          <img src="/hello.png" alt="" className="size-9" />
          <div>
            <h1 className="text-xl font-bold leading-tight">Fluent Meet · Sign Translator</h1>
            <p className="text-xs text-gray-400">Sign language → text → speech, and speech → live captions</p>
          </div>
        </div>
        <Link to="/" className="text-sm text-gray-300 hover:text-white">
          Video calls →
        </Link>
      </header>

      <main className="mx-auto grid max-w-6xl gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        {/* camera */}
        <section className="relative aspect-video overflow-hidden rounded-xl bg-black">
          <video ref={videoRef} autoPlay playsInline muted className="size-full object-cover" />

          {stream &&
            frameSize &&
            detections.slice(0, 3).map((d) => {
              const [x1, y1, x2, y2] = d.bbox;
              return (
                <div
                  key={d.label}
                  className="absolute rounded border-2 border-purple-400"
                  style={{
                    left: `${(x1 / frameSize.width) * 100}%`,
                    top: `${(y1 / frameSize.height) * 100}%`,
                    width: `${((x2 - x1) / frameSize.width) * 100}%`,
                    height: `${((y2 - y1) / frameSize.height) * 100}%`,
                  }}
                >
                  <span className="absolute -top-6 left-0 whitespace-nowrap rounded bg-purple-600 px-2 py-0.5 text-xs">
                    {translateLabel(d.label, lang)} {(d.score * 100).toFixed(0)}%
                  </span>
                </div>
              );
            })}

          {!stream && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-6 text-center">
              <p className="text-gray-300">Allow the camera and sign to it – nothing leaves your browser except small frames sent to the model API.</p>
              <button onClick={startCamera} className="cursor-pointer rounded-md bg-purple-600 px-4 py-2 hover:bg-purple-500">
                Start camera
              </button>
              {camError && <p className="text-sm text-red-300">{camError}</p>}
            </div>
          )}
        </section>

        <TranslatorPanel
          lang={lang}
          onLangChange={setLang}
          autoSpeak={autoSpeak}
          onAutoSpeakChange={setAutoSpeak}
          detectionOn={detectionOn}
          onDetectionChange={setDetectionOn}
          micOn={micOn}
          onMicChange={(on) => {
            setMicError("");
            setMicOn(on);
          }}
          micSupported={micSupported}
          micError={micError}
          interim={interim}
          pending={translator.pending}
          transcript={translator.transcript}
          onFlush={translator.flush}
          onClear={translator.clear}
          onQuickPhrase={translator.commit}
          apiError={translator.error}
          latencyMs={translator.latencyMs}
        />
      </main>
    </div>
  );
}
