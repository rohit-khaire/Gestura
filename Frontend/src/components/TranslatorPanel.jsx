import { ACTIVE_SIGNS, LANGUAGES, composeSentence, translateLabel } from "../lib/phrases";
import { speak } from "../lib/speech";

const ICON = { sign: "🤟", speech: "🎤" };

const entryText = (entry, lang) => (entry.kind === "sign" ? composeSentence(entry.labels, lang) : entry.text);
const timeOf = (t) => new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

/**
 * Shared UI for the standalone translator page and the call page:
 * language + voice settings, the sentence being built, a transcript, and test controls.
 */
export default function TranslatorPanel({
  lang,
  onLangChange,
  autoSpeak,
  onAutoSpeakChange,
  detectionOn,
  onDetectionChange,
  micOn,
  onMicChange,
  micSupported,
  micError,
  interim,
  pending,
  transcript,
  onFlush,
  onClear,
  onQuickPhrase,
  apiError,
  latencyMs,
  className = "",
}) {
  const live = composeSentence(pending, lang);

  const copyTranscript = async () => {
    const text = transcript.map((e) => `[${timeOf(e.at)}] ${e.name}: ${entryText(e, lang)}`).join("\n");
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // clipboard may be blocked; nothing else to do
    }
  };

  const toggle = (on) =>
    `rounded-md px-3 py-1.5 text-sm cursor-pointer ${on ? "bg-purple-600 text-white" : "bg-gray-700 text-gray-200"}`;

  return (
    <div className={`flex flex-col gap-3 rounded-xl bg-gray-800 p-4 text-white ${className}`}>
      {/* settings */}
      <div className="flex flex-wrap items-center gap-2">
        <label className="flex items-center gap-2 text-sm">
          <span className="text-gray-300">Output language</span>
          <select
            value={lang}
            onChange={(e) => onLangChange(e.target.value)}
            className="rounded-md bg-gray-700 px-2 py-1.5 text-sm outline-none"
          >
            {Object.entries(LANGUAGES).map(([code, l]) => (
              <option key={code} value={code}>
                {l.name}
              </option>
            ))}
          </select>
        </label>
        <button className={toggle(autoSpeak)} onClick={() => onAutoSpeakChange(!autoSpeak)}>
          🔊 Speak aloud: {autoSpeak ? "On" : "Off"}
        </button>
        <button className={toggle(detectionOn)} onClick={() => onDetectionChange(!detectionOn)}>
          🤟 Sign detection: {detectionOn ? "On" : "Off"}
        </button>
        <button
          className={toggle(micOn)}
          disabled={!micSupported}
          title={micSupported ? "Turn what you say into captions" : "Speech recognition needs Chrome, Edge or Safari"}
          onClick={() => onMicChange(!micOn)}
        >
          🎤 Live captions: {micOn ? "On" : "Off"}
        </button>
      </div>

      {apiError && detectionOn && (
        <p className="rounded-md bg-red-600/80 px-3 py-1.5 text-xs">
          Detection service unavailable – check your connection or the model API URL.
        </p>
      )}
      {micError && <p className="rounded-md bg-amber-600/80 px-3 py-1.5 text-xs">{micError}</p>}

      {/* sentence being built */}
      <div className="rounded-lg bg-gray-900 p-3">
        <p className="mb-1 text-xs uppercase tracking-wide text-gray-400">Live translation</p>
        <p className="min-h-10 text-2xl font-semibold leading-snug">
          {live || interim || <span className="text-base font-normal text-gray-500">Show a sign to the camera…</span>}
        </p>
        {interim && live && <p className="mt-1 text-sm text-gray-400">🎤 {interim}</p>}
        <div className="mt-2 flex gap-2">
          <button
            onClick={onFlush}
            disabled={!pending.length}
            className="cursor-pointer rounded-md bg-purple-600 px-3 py-1 text-sm disabled:opacity-40"
          >
            Speak now
          </button>
          <span className="self-center text-xs text-gray-400">
            Sentences finish automatically after a short pause.
          </span>
        </div>
      </div>

      {/* transcript */}
      <div className="flex min-h-40 flex-1 flex-col rounded-lg bg-gray-900 p-3">
        <div className="mb-2 flex items-center justify-between">
          <p className="text-xs uppercase tracking-wide text-gray-400">Conversation</p>
          <div className="flex gap-2 text-xs">
            <button onClick={copyTranscript} className="cursor-pointer text-gray-300 hover:text-white">
              Copy
            </button>
            <button onClick={onClear} className="cursor-pointer text-gray-300 hover:text-white">
              Clear
            </button>
          </div>
        </div>
        <ul className="max-h-72 space-y-2 overflow-y-auto">
          {transcript.length === 0 && <li className="text-sm text-gray-500">Nothing yet.</li>}
          {[...transcript].reverse().map((e) => {
            const text = entryText(e, lang);
            return (
              <li key={e.id} className="flex items-start gap-2 text-sm">
                <span>{ICON[e.kind]}</span>
                <div className="flex-1">
                  <p>{text}</p>
                  <p className="text-xs text-gray-500">
                    {e.name}
                    {e.remote ? " (in call)" : ""} · {timeOf(e.at)}
                  </p>
                </div>
                <button
                  title="Speak this again"
                  className="cursor-pointer opacity-70 hover:opacity-100"
                  onClick={() => speak(text, LANGUAGES[lang].speech)}
                >
                  🔊
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      {/* test strip + status */}
      {onQuickPhrase && (
        <div className="flex flex-wrap items-center gap-2 text-xs text-gray-400">
          <span>Test the voice pipeline without a camera (simulated signs):</span>
          {ACTIVE_SIGNS.map((label) => (
            <button
              key={label}
              onClick={() => onQuickPhrase([label])}
              className="cursor-pointer rounded bg-gray-700 px-2 py-1 text-gray-200 hover:bg-gray-600"
            >
              {translateLabel(label, "en")}
            </button>
          ))}
        </div>
      )}
      <p className="text-xs text-gray-500">
        {detectionOn ? (apiError ? "Model: offline" : `Model: online${latencyMs != null ? ` · ${latencyMs} ms/frame` : ""}`) : "Model: paused"}
        {" · "}Signs understood: {ACTIVE_SIGNS.map((l) => translateLabel(l, "en")).join(", ")}
      </p>
    </div>
  );
}
