import { useEffect, useRef, useState } from "react";
import { DETECT_URL } from "../lib/config";

const INTERVAL_MS = 500; // default time between frames sent to the model
const MAX_WIDTH = 640; // frames are downscaled before upload; the model works at 224px anyway
const REQUEST_TIMEOUT_MS = 4000;
const MIN_STREAK = 2; // the same top label must win this many frames in a row before we show it
const HOLD_MS = 1500; // keep showing the last label this long after it disappears (avoids flicker)

// The model can return several boxes for the same sign; the list is sorted best-first, so keep the first.
const uniqueByLabel = (list) => list.filter((d, i) => list.findIndex((x) => x.label === d.label) === i);

/**
 * Periodically sends a frame of the local camera to the detection API.
 *
 * `stream` is the local participant's MediaStream. If it isn't available we fall back to the
 * first <video> element on the page (what the app used before).
 * `intervalMs` sets the frame rate; `onFrame(found, now)` receives every raw result (even an empty
 * one), which is what the sign translator needs for its voting and pause detection.
 *
 * Returns `{ detections, error, latencyMs, frameSize }`:
 *  - `detections`: the latest confirmed list ([{ label, score, bbox }], best first)
 *  - `error`:      true while the API is unreachable
 *  - `latencyMs`:  round-trip time of the last request
 *  - `frameSize`:  { width, height } of the uploaded frame (bbox values are in these pixels)
 */
export function useSignDetection({ stream, enabled, intervalMs = INTERVAL_MS, onFrame }) {
  const [detections, setDetections] = useState([]);
  const [error, setError] = useState(false);
  const [stats, setStats] = useState({ latencyMs: null, frameSize: null });

  const onFrameRef = useRef(onFrame);
  useEffect(() => {
    onFrameRef.current = onFrame;
  });

  useEffect(() => {
    if (!enabled) return;

    const video = document.createElement("video");
    video.muted = true;
    video.playsInline = true;
    if (stream) {
      video.srcObject = stream;
      video.play().catch(() => {}); // autoplay can be refused; the next tick simply skips the frame
    }
    const canvas = document.createElement("canvas");

    let stopped = false;
    let timer = null;
    let controller = null;
    let candidate = null; // label currently being confirmed
    let streak = 0;
    let lastConfirmedAt = 0;

    const grabFrame = () => {
      const source = stream ? video : document.querySelector("video");
      if (!source || source.readyState < 2 || !source.videoWidth) return Promise.resolve(null);

      const width = Math.min(MAX_WIDTH, source.videoWidth);
      canvas.width = width;
      canvas.height = Math.round(source.videoHeight * (width / source.videoWidth));
      canvas.getContext("2d").drawImage(source, 0, 0, canvas.width, canvas.height);
      return new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.8));
    };

    const requestDetections = async (blob) => {
      controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
      try {
        const form = new FormData();
        form.append("file", blob, "frame.jpg");
        const res = await fetch(DETECT_URL, {
          method: "POST",
          body: form,
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`Detection API returned ${res.status}`);
        const data = await res.json();
        return uniqueByLabel(Array.isArray(data?.detections) ? data.detections : []);
      } finally {
        clearTimeout(timeout);
      }
    };

    const applyResult = (found) => {
      const now = Date.now();
      const top = found[0]?.label ?? null;

      streak = top && top === candidate ? streak + 1 : top ? 1 : 0;
      candidate = top;

      if (top && streak >= MIN_STREAK) {
        lastConfirmedAt = now;
        setDetections(found);
      } else if (now - lastConfirmedAt > HOLD_MS) {
        setDetections((prev) => (prev.length ? [] : prev));
      }
    };

    // One request at a time: the next tick is only scheduled once the previous one finished.
    const tick = async () => {
      try {
        if (!document.hidden) {
          const blob = await grabFrame();
          if (blob && !stopped) {
            const frameSize = { width: canvas.width, height: canvas.height };
            const startedAt = performance.now();
            const found = await requestDetections(blob);
            if (!stopped) {
              const latencyMs = Math.round(performance.now() - startedAt);
              try {
                onFrameRef.current?.(found, Date.now());
              } catch (e) {
                console.error("onFrame handler failed:", e);
              }
              applyResult(found);
              setStats({ latencyMs, frameSize });
              setError(false);
            }
          }
        }
      } catch {
        if (!stopped) setError(true);
      } finally {
        if (!stopped) timer = setTimeout(tick, intervalMs);
      }
    };
    tick();

    return () => {
      stopped = true;
      clearTimeout(timer);
      controller?.abort();
      video.srcObject = null;
      setDetections([]);
      setError(false);
    };
  }, [stream, enabled, intervalMs]);

  return { detections, error, latencyMs: stats.latencyMs, frameSize: stats.frameSize };
}
