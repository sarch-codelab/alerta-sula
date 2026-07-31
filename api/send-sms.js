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
  if (req.method !== "POST") {
    return res.status(405).json({ success: false, error: "Method not allowed" });
  }
  const { to, message } = req.body;
  if (!to || !message) {
    return res.status(400).json({ success: false, error: "Faltan parametros" });
  }
  const r = getRedis();
  if (!r) {
    return res.status(500).json({ success: false, error: "Redis no configurado - falta REDIS_URL" });
  }
  const id = "msg_" + Date.now() + "_" + Math.random().toString(36).slice(2, 8);
  try {
    const entry = JSON.stringify({ id, to, message, created: Date.now() });
    await r.lpush("sms_queue", entry);
    return res.status(200).json({ success: true, id });
  } catch (err) {
    return res.status(502).json({ success: false, error: err.message });
  }
}
