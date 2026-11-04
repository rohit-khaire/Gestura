// Central place for runtime settings. Override any of these in Frontend/.env:
//   VITE_STREAM_API_KEY, VITE_API_URL, VITE_DETECT_URL
const isDev = import.meta.env.MODE === "development";

export const STREAM_API_KEY = import.meta.env.VITE_STREAM_API_KEY;

// Node backend (guest sessions + Stream tokens)
export const API_URL =
  import.meta.env.VITE_API_URL ||
  (isDev
    ? "http://localhost:5000/api"
    : "https://sign-detection-m4sm.onrender.com/api");

// Sign-detection model API (the FastAPI service in /Model). For a local model use
// VITE_DETECT_URL=http://localhost:7860/detect
export const DETECT_URL =
  import.meta.env.VITE_DETECT_URL ||
  "https://nick-localhost-sign-detect.hf.space/detect";
