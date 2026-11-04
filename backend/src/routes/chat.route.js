import express from "express";
import { createGuest } from "../controllers/chat.controller.js";
import { rateLimit } from "../middleware/rateLimit.js";

const router = express.Router();

// Each call creates a Stream user, so cap it per client.
router.post("/guest", rateLimit({ windowMs: 60_000, max: 20 }), createGuest);

export default router;
