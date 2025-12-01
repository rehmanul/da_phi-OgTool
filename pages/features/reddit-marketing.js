import CTAButton from '../../components/CTAButton';
import SEO from '../../components/SEO';

const playbook = [
  { title: 'Live discovery', detail: 'Track priority subreddits and keywords; flag high-intent threads within minutes.' },
  { title: 'Persona-safe replies', detail: 'Drafts come with sourcing, tone, and claim checks; approvals keep risk low.' },
  { title: 'Attribution that proves value', detail: 'UTM + profile journey tracking shows visits, signups, and pipeline from each comment.' },
];

const trustElements = [
  'Compliance controls for regulated industries',
  'Shadowban-safe cadence recommendations',
  'Escalation paths for PR or legal review',
  'Team inbox to collaborate with SMEs before posting',
];

export default function RedditMarketing() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div>
      <SEO
        title="Reddit Marketing"
        description="Publish authentic Reddit replies at scale with approvals, sourcing, and full-funnel attribution."
        url={`${siteUrl}/features/reddit-marketing`}
      />

      <section className="bg-primary-dark text-white py-20 px-4">
        <div className="max-w-5xl mx-auto">
          <p className="uppercase text-sm tracking-wide mb-3">Community</p>
          <h1 className="text-4xl font-bold mb-4">Be the voice buyers trust on Reddit</h1>
          <p className="text-lg max-w-3xl mb-6">
            OGTool detects buyer conversations as they happen, drafts persona-safe replies, and routes approvals so you can win mindshare
            without risking bans or off-brand comments.
          </p>
          <div className="flex gap-4 flex-wrap">
            <CTAButton href="/contact" variant="inverse">Book a live demo</CTAButton>
            <CTAButton href="/pricing" variant="primary">See pricing</CTAButton>
          </div>
        </div>
      </section>

      <section className="py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-6">
          {playbook.map((step) => (
            <div key={step.title} className="bg-gray-50 rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-primary-dark mb-2">{step.title}</h2>
              <p className="text-gray-700">{step.detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="py-16 px-4 bg-gray-100">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8 items-start">
          <div className="space-y-4">
            <h2 className="text-3xl font-semibold text-primary-dark">Approvals and controls built in</h2>
            <p className="text-gray-700">
              Keep risk low with audit trails, SLAs for reviews, and persona locks that prevent off-brand messages. OGTool captures every edit,
              approval, and publish action for compliance.
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2">
              {trustElements.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </div>
          <div className="bg-white rounded-lg shadow p-6 space-y-3">
            <h3 className="text-xl font-semibold text-primary-dark">Proof of impact</h3>
            <p className="text-gray-700">
              Detailed reporting connects comment placements to traffic, signups, and influenced revenue. Export weekly summaries for leadership
              or integrate with your BI stack via the API.
            </p>
            <CTAButton href="/docs/api-reference" variant="primary" className="mt-2">View reporting API</CTAButton>
          </div>
        </div>
      </section>

      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto text-center space-y-5">
          <h2 className="text-3xl font-semibold">Scale authenticity without losing control</h2>
          <p className="text-gray-700 text-lg">
            Dedicated seats for SMEs, community managers, and compliance means everyone can collaborate while OGTool keeps posts organized,
            scheduled, and attributed.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <CTAButton href="/managed" variant="primary">Use our managed team</CTAButton>
            <CTAButton href="/features" variant="inverse">Explore other features</CTAButton>
          </div>
        </div>
      </section>
    </div>
  );
}
