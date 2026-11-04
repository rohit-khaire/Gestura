// Tiny fixed-window, in-memory rate limiter (per client IP).
// Enough to stop one client from creating thousands of guest users; if you run several
// instances, use a shared store (e.g. Redis) instead.
export const rateLimit = ({ windowMs, max }) => {
  const hits = new Map(); // ip -> { count, resetAt }

  const sweep = setInterval(() => {
    const now = Date.now();
    for (const [key, entry] of hits) if (entry.resetAt <= now) hits.delete(key);
  }, windowMs);
  sweep.unref(); // don't keep the process alive just for this timer

  return (req, res, next) => {
    const now = Date.now();
    const key = req.ip;

    let entry = hits.get(key);
    if (!entry || entry.resetAt <= now) {
      entry = { count: 0, resetAt: now + windowMs };
      hits.set(key, entry);
    }

    entry.count += 1;
    if (entry.count > max) {
      res.set("Retry-After", String(Math.ceil((entry.resetAt - now) / 1000)));
      return res.status(429).json({ message: "Too many requests, please slow down." });
    }
    next();
  };
};
