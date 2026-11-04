import express from "express";
import cors from "cors";
import { ENV } from "./config/env.js";
import chatRoutes from "./routes/chat.route.js";

const app = express();

app.disable("x-powered-by");
app.set("trust proxy", 1); // we run behind one proxy (Render / Vercel), so req.ip is the real client
app.use(cors({ origin: ENV.CORS_ORIGINS }));
app.use(express.json({ limit: "10kb" }));

app.get("/", (_req, res) => res.send("health-test"));
app.get("/health", (_req, res) => res.json({ status: "ok" }));
app.use("/api/chat", chatRoutes);

app.use((_req, res) => res.status(404).json({ message: "Not found" }));

// eslint-disable-next-line no-unused-vars
app.use((err, _req, res, _next) => {
  const status = err.status ?? err.statusCode ?? 500;
  if (status >= 500) console.error(err);
  res.status(status).json({ message: status >= 500 ? "Internal server error" : err.message });
});

if (ENV.NODE_ENV !== "production" || !process.env.VERCEL) {
  app.listen(ENV.PORT, () => console.log("Server started on port:", ENV.PORT));
}

export default app;
