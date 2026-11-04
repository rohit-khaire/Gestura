import express from "express";
import cors from "cors";
import { ENV } from "./config/env.js";
import chatRoutes from "./routes/chat.route.js";

const app = express();

const origin =
  ENV.NODE_ENV === "development"
    ? "http://localhost:5173"
    : "https://sign-detection.vercel.app";

app.use(cors({ origin }));
app.use(express.json());

app.get("/", (_req, res) => res.send("health-test"));
app.use("/api/chat", chatRoutes);

if (ENV.NODE_ENV !== "production" || !process.env.VERCEL) {
  app.listen(ENV.PORT, () => console.log("Server started on port:", ENV.PORT));
}

export default app;
