import { useState, useEffect } from "react";
import { StreamChat } from "stream-chat";

const STREAM_API_KEY = import.meta.env.VITE_STREAM_API_KEY;

// Connects the guest session user to Stream Chat and disconnects on unmount
export const useStreamChat = (session) => {
  const [chatClient, setChatClient] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!session?.token || !session?.id || !STREAM_API_KEY) return;

    const client = StreamChat.getInstance(STREAM_API_KEY);
    let cancelled = false;

    client
      .connectUser({ id: session.id, name: session.name }, session.token)
      .then(() => !cancelled && setChatClient(client))
      .catch((err) => {
        console.log("Error connecting to stream", err);
        if (!cancelled) setError(err);
      });

    return () => {
      cancelled = true;
      client.disconnectUser();
    };
  }, [session?.token, session?.id, session?.name]);

  return { chatClient, isLoading: !chatClient && !error, error };
};
