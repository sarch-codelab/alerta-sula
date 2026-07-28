export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ success: false, error: "Method not allowed" });
  }
  const { to, message } = req.body;
  if (!to || !message) {
    return res.status(400).json({ success: false, error: "Faltan parametros" });
  }
  const ngrokUrl = process.env.NGROK_URL || "http://localhost:8080";
  try {
    const resp = await fetch(ngrokUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ to, message }),
      signal: AbortSignal.timeout(30000),
    });
    const data = await resp.json();
    return res.status(resp.status).json(data);
  } catch (err) {
    return res.status(502).json({ success: false, error: err.message });
  }
}
