export default async function handler(req, res) {
  if (req.method !== "GET") {
    return res.status(405).json({ success: false, error: "Method not allowed" });
  }
  const kvUrl = process.env.KV_REST_API_URL || process.env.KV_URL;
  const kvToken = process.env.KV_REST_API_TOKEN;

  if (!kvUrl || !kvToken) {
    return res.status(500).json({ success: false, error: "KV no configurado" });
  }

  try {
    const kvResp = await fetch(`${kvUrl}/rpop/sms_queue`, {
      method: "POST",
      headers: { Authorization: `Bearer ${kvToken}` },
      body: JSON.stringify([]),
    });
    const kvData = await kvResp.json();
    if (kvData.error) throw new Error(kvData.error);
    if (!kvData.result) {
      return res.status(200).json({ message: null });
    }
    const msg = JSON.parse(kvData.result);
    return res.status(200).json({ message: msg });
  } catch (err) {
    return res.status(502).json({ success: false, error: err.message });
  }
}
