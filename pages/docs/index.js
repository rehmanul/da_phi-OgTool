import CTAButton from '../../components/CTAButton';
import SEO from '../../components/SEO';

const guides = [
  {
    title: 'Getting Started',
    href: '/docs/getting-started',
    summary: 'Connect sources, set up personas, and ship your first approvals in under 30 minutes.',
    items: ['Workspace setup checklist', 'Persona guardrails', 'First campaign launch'],
  },
  {
    title: 'API Reference',
    href: '/docs/api-reference',
    summary: 'Integrate OGTool data, publish programmatically, and sync metrics to your BI stack.',
    items: ['Authentication and webhooks', 'Publishing endpoints', 'Analytics exports'],
  },
  {
    title: 'Best Practices',
    href: '/docs/best-practices',
    summary: 'Proven playbooks for compliance, attribution, and scaling without losing authenticity.',
    items: ['Approvals that keep speed', 'Attribution instrumentation', 'Content refresh cadences'],
  },
];

export default function DocsHome() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div>
      <SEO
        title="Docs"
        description="Everything you need to configure, integrate, and scale OGTool across your team."
        url={`${siteUrl}/docs`}
      />

      <section className="bg-gradient-to-b from-gradientStart to-gradientEnd text-white text-center py-20 px-4">
        <p className="uppercase text-sm tracking-wide mb-3">Documentation</p>
        <h1 className="text-4xl font-bold mb-4">Implement OGTool with confidence</h1>
        <p className="text-lg max-w-3xl mx-auto mb-6">
          Follow guided setup, integrate via API, and adopt best practices for governed publishing, attribution,
          and AI-driven content programs.
        </p>
        <div className="flex justify-center gap-4 flex-wrap">
          <CTAButton href="/docs/getting-started" variant="inverse">Start here</CTAButton>
          <CTAButton href="/contact" variant="primary">Talk to customer success</CTAButton>
        </div>
      </section>

      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-6">
          {guides.map((guide) => (
            <div key={guide.title} className="bg-white rounded-lg shadow p-6 flex flex-col">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-xl font-semibold text-primary-dark">{guide.title}</h2>
                <CTAButton href={guide.href} variant="subtle">Open</CTAButton>
              </div>
              <p className="text-gray-700 mb-4">{guide.summary}</p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 flex-1">
                {guide.items.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
          ))}
        </div>
      </section>

      <section className="py-16 px-4 bg-gray-100">
        <div className="max-w-5xl mx-auto text-center space-y-5">
          <h2 className="text-3xl font-semibold">Need a tailored rollout?</h2>
          <p className="text-gray-700 text-lg">
            Our solutions team helps with enablement, SSO/SCIM, data residency, and custom workflows so your launch is fast and safe.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <CTAButton href="/managed" variant="primary">Request white-glove onboarding</CTAButton>
            <CTAButton href="/docs/api-reference" variant="inverse">Review the API</CTAButton>
          </div>
        </div>
      </section>
    </div>
  );
}
