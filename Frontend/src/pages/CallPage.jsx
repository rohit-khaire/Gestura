import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router";
import toast from "react-hot-toast";

import {
  StreamVideo,
  StreamVideoClient,
  StreamCall,
  CallControls,
  SpeakerLayout,
  StreamTheme,
  CallingState,
  useCall,
  useCallStateHooks,
} from "@stream-io/video-react-sdk";

import "@stream-io/video-react-sdk/dist/css/styles.css";

import { STREAM_API_KEY } from "../lib/config";
import TranslatorPanel from "../components/TranslatorPanel";
import { useSignTranslator } from "../hooks/useSignTranslator";
import { useSpeechCaptions } from "../hooks/useSpeechCaptions";
import { LANGUAGES, composeSentence, translateLabel } from "../lib/phrases";
import { speak } from "../lib/speech";

// Captions travel through the call as Stream "custom events" so every participant sees (and hears)
// them in their own language: signs are sent as labels, speech as text.
const CAPTION_EVENT = "fluent-caption";

const CallPage = ({ session }) => {
  const { id: callId } = useParams();

  const [client, setClient] = useState(null);
  const [call, setCall] = useState(null);
  const [isConnecting, setIsConnecting] = useState(true);

  useEffect(() => {
    let isMounted = true;
    let videoClientRef;
    let callRef;

    const initCall = async () => {
      if (!session?.token || !callId) return;

      try {
        const videoClient = new StreamVideoClient({
          apiKey: STREAM_API_KEY,
          user: { id: session.id, name: session.name },
          token: session.token,
        });
        videoClientRef = videoClient;

        const callInstance = videoClient.call("default", callId);
        callRef = callInstance;
        await callInstance.join({ create: true });

        if (!isMounted) return;
        setClient(videoClient);
        setCall(callInstance);
      } catch (error) {
        console.log("Error init call:", error);
        toast.error("Cannot connect to the call.");
      } finally {
        if (isMounted) setIsConnecting(false);
      }
    };

    initCall();

    return () => {
      isMounted = false;
      try {
        callRef?.leave?.();
      } catch {
        // ignore
      }
      try {
        // Disconnect the user/session; method presence varies by SDK version.
        videoClientRef?.disconnectUser?.();
        videoClientRef?.destroy?.();
      } catch {
        // ignore
      }
    };
  }, [session, callId]);

  if (isConnecting) {
    return (
      <div className="h-screen flex justify-center items-center">
        Connecting to call...
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-900 p-4">
      <div className="relative w-full max-w-6xl mx-auto">
        {client && call ? (
          <StreamVideo client={client}>
            <StreamCall call={call}>
              <CallContent />
            </StreamCall>
          </StreamVideo>
        ) : (
          <div className="flex items-center justify-center h-full">
            <p>Could not initialize call. Please refresh or try again later</p>
          </div>
        )}
      </div>
    </div>
  );
};

const CallContent = () => {
  const { useCallCallingState, useLocalParticipant } = useCallStateHooks();
  const call = useCall();
  const callingState = useCallCallingState();
  const localParticipant = useLocalParticipant();
  const navigate = useNavigate();

  const [lang, setLang] = useState("en");
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [detectionOn, setDetectionOn] = useState(true);
  const [micOn, setMicOn] = useState(false);
  const [micError, setMicError] = useState("");

  const myId = localParticipant?.userId;
  const myName = localParticipant?.name || "You";

  const broadcast = (payload) => {
    try {
      call?.sendCustomEvent({ type: CAPTION_EVENT, from: myId, name: myName, ...payload });
    } catch (e) {
      console.warn("Could not send caption to the call:", e);
    }
  };

  const translator = useSignTranslator({
    stream: localParticipant?.videoStream ?? null,
    enabled: detectionOn && callingState === CallingState.JOINED,
    lang,
    autoSpeak,
    onSentence: (labels) => broadcast({ kind: "sign", labels }),
  });

  const { supported: micSupported, interim } = useSpeechCaptions({
    enabled: micOn && callingState === CallingState.JOINED,
    lang: LANGUAGES[lang].recog,
    onFinal: (text) => {
      translator.addEntry({ kind: "speech", text, name: "You" });
      broadcast({ kind: "speech", text });
    },
    onError: (message) => {
      setMicError(message);
      setMicOn(false);
    },
  });

  // Captions from the other participants. Kept in a ref so the subscription isn't recreated
  // every time the language or voice setting changes.
  const incoming = useRef(null);
  useEffect(() => {
    incoming.current = (c) => {
      if (c.from && c.from === myId) return; // our own broadcast echoed back
      if (c.kind === "sign" && Array.isArray(c.labels)) {
        translator.addEntry({ kind: "sign", labels: c.labels, name: c.name || "Guest", remote: true });
        if (autoSpeak) speak(composeSentence(c.labels, lang), LANGUAGES[lang].speech);
      } else if (c.kind === "speech" && typeof c.text === "string") {
        translator.addEntry({ kind: "speech", text: c.text, name: c.name || "Guest", remote: true });
      }
    };
  });

  useEffect(() => {
    if (!call) return;
    const off = call.on("custom", (event) => {
      const c = event?.custom;
      if (c?.type === CAPTION_EVENT) incoming.current?.(c);
    });
    return () => {
      if (typeof off === "function") off();
    };
  }, [call]);

  useEffect(() => {
    if (callingState === CallingState.LEFT) navigate("/");
  }, [callingState, navigate]);

  return (
    <StreamTheme>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <div>
          <div className="relative">
            <SpeakerLayout />

            {/* recognised signs, shown on top of the video */}
            <div className="pointer-events-none absolute inset-0 flex items-start justify-end p-4">
              <div className="flex flex-col items-end gap-2">
                {translator.detections.slice(0, 3).map((d) => (
                  <div key={d.label} className="bg-black/70 text-white rounded-md px-3 py-2 shadow-md text-sm">
                    <span className="font-semibold mr-2">{translateLabel(d.label, lang)}</span>
                    <span className="opacity-80">{(d.score * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <CallControls />
        </div>

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
      </div>
    </StreamTheme>
  );
};

export default CallPage;
