import express from "express";
import { createGuest } from "../controllers/chat.controller.js";

const router = express.Router();

router.post("/guest", createGuest);

export default router;
