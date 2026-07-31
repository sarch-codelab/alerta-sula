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
  const { id } = req.query;
  if (!id) {
    return res.status(400).json({ success: false, error: "Falta id" });
  }
  const r = getRedis();
  if (!r) {
    return res.status(500).json({ success: false, error: "Redis no configurado" });
  }
  try {
    const raw = await r.get(`sms_result:${id}`);
    if (!raw) {
      return res.status(200).json({ pending: true, result: null });
    }
    return res.status(200).json({ pending: false, result: JSON.parse(raw) });
  } catch (err) {
    return res.status(502).json({ success: false, error: err.message });
  }
}
