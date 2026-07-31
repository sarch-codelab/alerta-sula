import Redis from "ioredis";

let redis;

function getRedis() {
  if (!redis) {
    const url = process.env.REDIS_URL || process.env.KV_URL || "";
    if (!url) return null;
    redis = new Redis(url, {
      maxRetriesPerRequest: 1,
      connectTimeout: 5000,
      lazyConnect: true,
    });
  }
  return redis;
}

export default async function handler(req, res) {
  const r = getRedis();
  if (!r) {
    return res.status(500).json({ success: false, error: "Redis no configurado" });
  }
  try {
    if (req.method === "GET") {
      const raw = await r.get("stations:state");
      return res.status(200).json({ stations: raw ? JSON.parse(raw) : null });
    }
    if (req.method === "POST") {
      const { stations } = req.body;
      if (!stations) {
        return res.status(400).json({ success: false, error: "Falta stations" });
      }
      await r.set("stations:state", JSON.stringify(stations));
      return res.status(200).json({ success: true });
    }
    return res.status(405).json({ success: false, error: "Method not allowed" });
  } catch (err) {
    return res.status(502).json({ success: false, error: err.message });
  }
}
