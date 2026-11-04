import "dotenv/config";

const required = ["STREAM_API_KEY", "STREAM_API_SECRET"];
const missing = required.filter((name) => !process.env[name]);
if (missing.length > 0) {
  // Fail fast with a clear message instead of a cryptic Stream SDK error on the first request.
  throw new Error(`Missing required environment variables: ${missing.join(", ")}`);
}

const defaultOrigin =
  process.env.NODE_ENV === "development"
    ? "http://localhost:5173"
    : "https://sign-detection.vercel.app";

export const ENV = {
  PORT: process.env.PORT || 5000,
  NODE_ENV: process.env.NODE_ENV,
  STREAM_API_KEY: process.env.STREAM_API_KEY,
  STREAM_API_SECRET: process.env.STREAM_API_SECRET,
  // Comma-separated list of sites allowed to call this API from a browser.
  CORS_ORIGINS: (process.env.CORS_ORIGIN || defaultOrigin)
    .split(",")
    .map((origin) => origin.trim())
    .filter(Boolean),
};
