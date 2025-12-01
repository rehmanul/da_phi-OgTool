export default function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { name, email, company, message, website } = req.body || {};
  if (!name || !email || !company || !message) {
    return res.status(400).json({ error: 'Missing required fields' });
  }
  const emailPattern = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
  if (!emailPattern.test(email)) {
    return res.status(400).json({ error: 'Invalid email' });
  }
  // Honeypot field to deter bots
  if (website) {
    return res.status(400).json({ error: 'Invalid submission' });
  }

  const payload = { name, email, company, message, submittedAt: new Date().toISOString() };
  const webhookUrl = process.env.CONTACT_WEBHOOK_URL;

  async function forwardToWebhook() {
    if (!webhookUrl) return null;
    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Webhook failed: ${response.status} ${text}`.trim());
    }
    return response.status;
  }

  return forwardToWebhook()
    .then(() => res.status(200).json({ status: 'ok' }))
    .catch((err) => {
      console.error('Contact submission failed', err);
      return res.status(502).json({ error: 'Unable to process request right now' });
    });
}
