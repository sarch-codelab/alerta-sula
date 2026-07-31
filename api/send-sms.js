export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ success: false, error: "Method not allowed" });
  }
  const { to, message } = req.body;
  if (!to || !message) {
    return res.status(400).json({ success: false, error: "Faltan parametros" });
  }
  const id = "msg_" + Date.now() + "_" + Math.random().toString(36).slice(2, 8);
  const kvUrl = process.env.KV_REST_API_URL || process.env.KV_URL;
  const kvToken = process.env.KV_REST_API_TOKEN;

  const envs = {
    KV_REST_API_URL: !!process.env.KV_REST_API_URL,
    KV_REST_API_TOKEN: !!process.env.KV_REST_API_TOKEN,
    KV_URL: !!process.env.KV_URL,
  };

  if (!kvUrl || !kvToken) {
    return res.status(500).json({ success: false, error: "KV no configurado", envs });
  }

  try {
    const entry = JSON.stringify({ id, to, message, created: Date.now() });
    const kvResp = await fetch(`${kvUrl}/lpush/sms_queue`, {
      method: "POST",
      headers: { Authorization: `Bearer ${kvToken}` },
      body: JSON.stringify([entry]),
    });
    const kvData = await kvResp.json();
    if (kvData.error) throw new Error(kvData.error);
    return res.status(200).json({ success: true, id });
  } catch (err) {
    return res.status(502).json({ success: false, error: err.message });
  }
}
