import CTAButton from '../../components/CTAButton';
import SEO from '../../components/SEO';

const capabilities = [
  { title: 'Calendar + scheduling', detail: 'Plan posts, comments, and repurposed content across time zones with approvals baked in.' },
  { title: 'Persona-safe generation', detail: 'Drafts inherit brand voice, proof points, and compliance statements per segment.' },
  { title: 'Engagement routing', detail: 'Alerts route high-priority mentions to the right SME to respond within minutes.' },
];

const metrics = [
  'Follower growth and engagement rate by persona',
  'Click-through and conversion tracking on every post',
  'Share of voice vs competitors on priority topics',
  'Lead capture from DMs and comments with CRM sync',
];

export default function LinkedInMarketing() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div>
      <SEO
        title="LinkedIn Marketing"
        description="Publish, approve, and attribute LinkedIn content that fuels pipeline, not vanity metrics."
        url={`${siteUrl}/features/linkedin-marketing`}
      />

      <section className="bg-gradient-to-r from-gradientStart to-primary-dark text-white py-20 px-4">
        <div className="max-w-5xl mx-auto">
          <p className="uppercase text-sm tracking-wide mb-3">Social</p>
          <h1 className="text-4xl font-bold mb-4">LinkedIn programs that convert</h1>
          <p className="text-lg max-w-3xl mb-6">
            OGTool gives marketing, sales, and leadership one workspace to plan LinkedIn content, generate persona-safe drafts, and measure
            how every post and comment contributes to pipeline.
          </p>
          <div className="flex gap-4 flex-wrap">
            <CTAButton href="/pricing" variant="inverse">See plans</CTAButton>
            <CTAButton href="/contact" variant="primary">Talk with us</CTAButton>
          </div>
        </div>
      </section>

      <section className="py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-6">
          {capabilities.map((item) => (
            <div key={item.title} className="bg-gray-50 rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-primary-dark mb-2">{item.title}</h2>
              <p className="text-gray-700">{item.detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="py-16 px-4 bg-gray-100">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8 items-start">
          <div className="space-y-4">
            <h2 className="text-3xl font-semibold text-primary-dark">Governed, multi-seat workflows</h2>
            <p className="text-gray-700">
              Assign roles for creators, reviewers, and leadership; capture every edit and approval; and enforce messaging guidelines across
              teams. OGTool ensures thought leadership stays consistent even when multiple voices post.
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2">
              <li>Reusable content pillars and campaign templates</li>
              <li>Auto-generated captions tailored per audience segment</li>
              <li>Version control and rollback for sensitive announcements</li>
            </ul>
          </div>
          <div className="bg-white rounded-lg shadow p-6 space-y-3">
            <h3 className="text-xl font-semibold text-primary-dark">Metrics that sales and marketing share</h3>
            <ul className="space-y-2 text-gray-700">
              {metrics.map((line) => <li key={line}>{line}</li>)}
            </ul>
            <CTAButton href="/docs/best-practices" variant="primary" className="mt-2">Review best practices</CTAButton>
          </div>
        </div>
      </section>

      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto text-center space-y-5">
          <h2 className="text-3xl font-semibold">Move beyond vanity likes</h2>
          <p className="text-gray-700 text-lg">
            Connect LinkedIn performance to opportunities. OGTool maps posts to CRM outcomes so you can double down on content that accelerates deals.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <CTAButton href="/managed" variant="primary">Need an extension of your team?</CTAButton>
            <CTAButton href="/features" variant="inverse">Explore the platform</CTAButton>
          </div>
        </div>
      </section>
    </div>
  );
}
