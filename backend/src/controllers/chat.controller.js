import { randomUUID } from "node:crypto";
import {
  generateStreamToken,
  upsertStreamUser,
  addUserToPublicChannels,
} from "../config/stream.js";

// POST /api/chat/guest  { name } -> { id, name, token }
// The server generates the user id, so clients can't pick someone else's id.
export const createGuest = async (req, res) => {
  try {
    const name = String(req.body?.name ?? "").trim().slice(0, 30);
    if (!name) return res.status(400).json({ message: "Name is required" });

    const id = `user_${randomUUID()}`;
    await upsertStreamUser({ id, name });
    await addUserToPublicChannels(id).catch(() => {}); // non-fatal

    res.status(201).json({ id, name, token: generateStreamToken(id) });
  } catch (error) {
    console.log("Error creating guest", error);
    res.status(500).json({ message: "Failed to create guest" });
  }
};
