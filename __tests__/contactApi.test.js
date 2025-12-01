import handler from '../pages/api/contact';

const originalFetch = global.fetch;
const originalWebhook = process.env.CONTACT_WEBHOOK_URL;

function createRes() {
  const res = {};
  res.statusCode = null;
  res.body = null;
  res.status = jest.fn((code) => {
    res.statusCode = code;
    return res;
  });
  res.json = jest.fn((body) => {
    res.body = body;
    return res;
  });
  return res;
}

describe('/api/contact handler', () => {
  afterEach(() => {
    if (originalFetch) {
      global.fetch = originalFetch;
    } else {
      delete global.fetch;
    }
    if (originalWebhook) {
      process.env.CONTACT_WEBHOOK_URL = originalWebhook;
    } else {
      delete process.env.CONTACT_WEBHOOK_URL;
    }
    jest.resetAllMocks();
  });

  it('rejects unsupported methods', async () => {
    const req = { method: 'GET' };
    const res = createRes();

    await handler(req, res);

    expect(res.status).toHaveBeenCalledWith(405);
    expect(res.body).toEqual({ error: 'Method not allowed' });
  });

  it('validates required fields and email format', async () => {
    const resMissing = createRes();
    await handler({ method: 'POST', body: { name: 'A' } }, resMissing);
    expect(resMissing.status).toHaveBeenCalledWith(400);

    const resInvalidEmail = createRes();
    await handler(
      { method: 'POST', body: { name: 'A', email: 'invalid', company: 'C', message: 'Hi' } },
      resInvalidEmail,
    );
    expect(resInvalidEmail.status).toHaveBeenCalledWith(400);
    expect(resInvalidEmail.body).toEqual({ error: 'Invalid email' });
  });

  it('blocks honeypot submissions', async () => {
    const res = createRes();
    await handler(
      {
        method: 'POST',
        body: { name: 'A', email: 'a@example.com', company: 'C', message: 'Hi', website: 'bot' },
      },
      res,
    );
    expect(res.status).toHaveBeenCalledWith(400);
    expect(res.body).toEqual({ error: 'Invalid submission' });
  });

  it('succeeds without webhook configured', async () => {
    delete process.env.CONTACT_WEBHOOK_URL;
    const res = createRes();
    await handler(
      {
        method: 'POST',
        body: { name: 'A', email: 'a@example.com', company: 'C', message: 'Hi' },
      },
      res,
    );
    expect(res.status).toHaveBeenCalledWith(200);
    expect(res.body).toEqual({ status: 'ok' });
  });

  it('forwards to webhook and handles success', async () => {
    const fetchMock = jest.fn(() =>
      Promise.resolve({ ok: true, status: 200, text: () => Promise.resolve('ok') }),
    );
    global.fetch = fetchMock;
    process.env.CONTACT_WEBHOOK_URL = 'https://example.com/webhook';

    const res = createRes();
    await handler(
      { method: 'POST', body: { name: 'A', email: 'a@example.com', company: 'C', message: 'Hi' } },
      res,
    );

    expect(fetchMock).toHaveBeenCalled();
    expect(res.status).toHaveBeenCalledWith(200);
    expect(res.body).toEqual({ status: 'ok' });
  });
});
