// Lightweight guest session (replaces Clerk login).
// Stored in localStorage: { id, name, token }
const KEY = "gestura_session";

export const getSession = () => {
  try {
    return JSON.parse(localStorage.getItem(KEY));
  } catch {
    return null;
  }
};

export const saveSession = (s) => localStorage.setItem(KEY, JSON.stringify(s));

export const clearSession = () => localStorage.removeItem(KEY);
