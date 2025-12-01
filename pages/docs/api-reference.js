import SEO from '../../components/SEO';

const sections = [
  {
    title: 'Authentication',
    detail: 'Use Bearer tokens scoped per workspace. Rotate keys from Settings → API and restrict IPs for additional security.',
    examples: [
      'Authorization: Bearer <token>',
      'Scopes: content:write, approvals:write, analytics:read',
      'Webhook signature using SHA256 + shared secret',
    ],
  },
  {
    title: 'Publishing endpoints',
    detail: 'Create drafts, submit for approval, and publish to Reddit, LinkedIn, blog, or AI answer coverage.',
    examples: [
      'POST /v1/drafts with channel, persona, and sources',
      'POST /v1/drafts/{id}/submit for approval routing',
      'POST /v1/publish to schedule or post immediately',
    ],
  },
  {
    title: 'Analytics and exports',
    detail: 'Fetch performance across channels for BI, including attribution and share-of-voice data.',
    examples: [
      'GET /v1/analytics/comments?source=reddit',
      'GET /v1/analytics/answers?query=chatgpt',
      'GET /v1/exports/sov?group_by=keyword&interval=weekly',
    ],
  },
  {
    title: 'Webhooks',
    detail: 'Receive events for approvals, publishing, alerts, and decay signals.',
    examples: [
      'event=approval.requested, approval.completed',
      'event=content.published, content.rejected',
      'event=alert.rank_drop, alert.sentiment_shift',
    ],
  },
];

export default function APIReference() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div className="px-4 py-14">
      <SEO
        title="API Reference"
        description="Integrate OGTool into your stack with secure auth, publishing, analytics, and webhook endpoints."
        url={`${siteUrl}/docs/api-reference`}
      />

      <header className="max-w-5xl mx-auto mb-10">
        <p className="uppercase text-sm tracking-wide text-primary-dark mb-2">Docs</p>
        <h1 className="text-4xl font-bold text-primary-dark mb-4">API reference</h1>
        <p className="text-gray-700 text-lg">
          Build OGTool into your workflows: publish content programmatically, sync analytics to your warehouse, and react to events in real time.
        </p>
      </header>

      <main className="max-w-5xl mx-auto space-y-6">
        {sections.map((section) => (
          <section key={section.title} className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-semibold text-primary-dark mb-2">{section.title}</h2>
            <p className="text-gray-700 mb-3">{section.detail}</p>
            <ul className="list-disc list-inside text-gray-700 space-y-2">
              {section.examples.map((example) => <li key={example}>{example}</li>)}
            </ul>
          </section>
        ))}
      </main>
    </div>
  );
}
