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
  if (req.method !== "GET") {
    return res.status(405).json({ success: false, error: "Method not allowed" });
  }
  const r = getRedis();
  if (!r) {
    return res.status(500).json({ success: false, error: "Redis no configurado" });
  }
  try {
    const raw = await r.rpop("sms_queue");
    if (!raw) {
      return res.status(200).json({ message: null });
    }
    const msg = JSON.parse(raw);
    return res.status(200).json({ message: msg });
  } catch (err) {
    return res.status(502).json({ success: false, error: err.message });
  }
}
