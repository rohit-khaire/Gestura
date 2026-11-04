import { StreamChat } from "stream-chat";
import { ENV } from "./env.js";

const streamClient = StreamChat.getInstance(
  ENV.STREAM_API_KEY,
  ENV.STREAM_API_SECRET,
);

export const upsertStreamUser = (userData) => streamClient.upsertUser(userData);

export const generateStreamToken = (userId) =>
  streamClient.createToken(userId.toString());

export const addUserToPublicChannels = async (userId) => {
  const publicChannels = await streamClient.queryChannels(
    { discoverable: true },
    {},
    { limit: 100 }, // Stream returns only 10 channels by default
  );
  await Promise.all(publicChannels.map((c) => c.addMembers([userId])));
};
