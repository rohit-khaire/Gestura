import { useState } from "react";
import toast from "react-hot-toast";
import { createGuest } from "../lib/api";
import { saveSession } from "../lib/session";

const JoinPage = ({ onJoin }) => {
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    setLoading(true);
    try {
      const session = await createGuest(trimmed);
      saveSession(session);
      onJoin(session);
    } catch {
      toast.error("Could not join. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 p-4">
      <form
        onSubmit={submit}
        className="w-full max-w-sm bg-gray-800 rounded-xl p-6 flex flex-col gap-4 text-white"
      >
        <div className="flex items-center gap-3">
          <img src="/hello.png" alt="Logo" className="size-10" />
          <h1 className="text-2xl font-bold">Fluent Meet</h1>
        </div>
        <p className="text-sm text-gray-300">
          Video calls with live sign language detection. Pick a name to start.
        </p>
        <input
          autoFocus
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={30}
          placeholder="Your name"
          className="px-3 py-2 rounded-md bg-gray-700 outline-none focus:ring-2 focus:ring-purple-500"
        />
        <button
          disabled={loading || !name.trim()}
          className="px-3 py-2 rounded-md bg-purple-600 hover:bg-purple-500 disabled:opacity-50 cursor-pointer"
        >
          {loading ? "Joining..." : "Continue"}
        </button>
      </form>
    </div>
  );
};

export default JoinPage;
