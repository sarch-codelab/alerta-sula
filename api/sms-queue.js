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
    const [pending, heartbeat] = await Promise.all([
      r.llen("sms_queue"),
      r.get("sms:heartbeat"),
    ]);
    return res.status(200).json({
      pending: pending || 0,
      lastHeartbeat: heartbeat ? parseInt(heartbeat, 10) : 0,
    });
  } catch (err) {
    return res.status(502).json({ success: false, error: err.message });
  }
}
