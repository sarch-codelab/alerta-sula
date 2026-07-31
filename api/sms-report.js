export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ success: false, error: "Method not allowed" });
  }
  const { id, success, error } = req.body;
  if (!id) {
    return res.status(400).json({ success: false, error: "Falta id" });
  }
  const redisUrl = process.env.REDIS_URL || "";
  let kvUrl = process.env.KV_REST_API_URL;
  let kvToken = process.env.KV_REST_API_TOKEN;

  if (!kvUrl && redisUrl.startsWith("redis://")) {
    try {
      const u = new URL(redisUrl);
      kvUrl = `https://${u.hostname}`;
      kvToken = u.password;
    } catch (e) { /* fallback */ }
  }

  if (!kvUrl || !kvToken) {
    return res.status(500).json({ success: false, error: "KV no configurado" });
  }

  try {
    const entry = JSON.stringify({ id, success, error, reported: Date.now() });
    const kvResp = await fetch(`${kvUrl}/set/sms_result:${id}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${kvToken}` },
      body: JSON.stringify([entry]),
    });
    const kvData = await kvResp.json();
    if (kvData.error) throw new Error(kvData.error);
    return res.status(200).json({ success: true });
  } catch (err) {
    return res.status(502).json({ success: false, error: err.message });
  }
}
