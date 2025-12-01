import CTAButton from '../../components/CTAButton';
import SEO from '../../components/SEO';

const assets = [
  {
    title: 'Pricing',
    href: '/pricing',
    summary: 'Compare self-serve, semi-managed, and fully managed plans.',
  },
  {
    title: 'Blog',
    href: '/blog',
    summary: 'Long-form guidance on winning AI search, Reddit, and LinkedIn.',
  },
  {
    title: 'Managed Service',
    href: '/managed',
    summary: 'Hand execution to our team while you keep strategic control.',
  },
  {
    title: 'Docs',
    href: '/docs',
    summary: 'Implementation guides, APIs, and best practices.',
  },
];

const downloads = [
  'AI Answer Coverage Checklist (ChatGPT, Perplexity, Gemini)',
  'Reddit Community Health Scoring Worksheet',
  'LinkedIn Content Pillar Planner',
  'SEO Refresh Cadence Template',
];

export default function Resources() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div>
      <SEO
        title="Resources"
        description="All OGTool resources in one place—pricing, docs, managed service details, and strategic guides."
        url={`${siteUrl}/resources`}
      />

      <section className="bg-gradient-to-b from-gradientStart to-gradientEnd text-white text-center py-20 px-4">
        <p className="uppercase text-sm tracking-wide mb-3">Resources</p>
        <h1 className="text-4xl font-bold mb-4">Stay ahead with OGTool</h1>
        <p className="text-lg max-w-3xl mx-auto mb-6">
          Everything you need to evaluate, implement, and scale OGTool—from pricing to playbooks and managed options.
        </p>
        <div className="flex justify-center gap-4 flex-wrap">
          <CTAButton href="/pricing" variant="inverse">See pricing</CTAButton>
          <CTAButton href="/contact" variant="primary">Talk to us</CTAButton>
        </div>
      </section>

      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-6">
          {assets.map((asset) => (
            <div key={asset.title} className="bg-white rounded-lg shadow p-6 flex flex-col">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-xl font-semibold text-primary-dark">{asset.title}</h2>
                <CTAButton href={asset.href} variant="subtle">Open</CTAButton>
              </div>
              <p className="text-gray-700 flex-1">{asset.summary}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="py-16 px-4 bg-gray-100">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8 items-start">
          <div className="space-y-4">
            <h2 className="text-3xl font-semibold text-primary-dark">Downloadable templates</h2>
            <ul className="list-disc list-inside text-gray-700 space-y-2">
              {downloads.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </div>
          <div className="bg-white rounded-lg shadow p-6 space-y-3">
            <h3 className="text-xl font-semibold text-primary-dark">Need help choosing?</h3>
            <p className="text-gray-700">
              We’ll tailor a rollout plan, share a sample growth model, and align stakeholders on success metrics before you commit.
            </p>
            <CTAButton href="/managed" variant="primary">Talk with our team</CTAButton>
          </div>
        </div>
      </section>
    </div>
  );
}
