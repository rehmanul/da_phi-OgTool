import CTAButton from '../../components/CTAButton';
import SEO from '../../components/SEO';

const featureAreas = [
  {
    title: 'Blog Ranking',
    href: '/features/blog-ranking',
    summary: 'Outrank competitors with topic clustering, on-page scoring, and integrated publishing.',
    bullets: ['Opportunity scoring for every keyword', 'Content briefs with persona notes', 'Reverse-proxy or native publishing'],
  },
  {
    title: 'ChatGPT Ranking',
    href: '/features/chatgpt-ranking',
    summary: 'Win AI answer boxes with authoritative sources, prompt interception, and freshness checks.',
    bullets: ['SERP + answer-box monitoring', 'Answer snippets tied to your KB', 'Escalations when you lose rank'],
  },
  {
    title: 'Reddit Marketing',
    href: '/features/reddit-marketing',
    summary: 'Publish high-intent Reddit replies that stay in-voice, get approvals, and drive tracked clicks.',
    bullets: ['Live thread discovery by persona', 'Governed reply workflows', 'Attribution down to signup'],
  },
  {
    title: 'LinkedIn Marketing',
    href: '/features/linkedin-marketing',
    summary: 'Ship consistent LinkedIn posts and comments with scheduling, approvals, and performance reporting.',
    bullets: ['Content calendar + auto-scheduling', 'Persona-safe comment templates', 'Engagement scoring and alerts'],
  },
];

const operatingPillars = [
  { title: 'Governed AI', text: 'Persona guardrails, approvals, and audit trails keep every response compliant.' },
  { title: 'Attribution-first', text: 'Source/medium tracking across Reddit, ChatGPT answers, LinkedIn, and blogs feeds a single revenue view.' },
  { title: 'Ops automation', text: 'Playbooks automate discovery, drafting, QA, and publishing so teams move faster with less headcount.' },
  { title: 'Enterprise-ready', text: 'SSO, SCIM, data residency, and SOC2-aligned processes for security teams.' },
];

export default function Features() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div>
      <SEO
        title="Features"
        description="OGTool unifies AI search, community publishing, and SEO so you can rank everywhere buyers look."
        url={`${siteUrl}/features`}
      />

      <section className="bg-gradient-to-b from-gradientStart to-gradientEnd text-white text-center py-20 px-4">
        <p className="uppercase text-sm tracking-wide mb-3">Platform</p>
        <h1 className="text-4xl font-bold mb-4">One system to own organic growth everywhere</h1>
        <p className="text-lg max-w-3xl mx-auto mb-8">
          Discover the threads, questions, and keywords that move revenue. Draft persona-safe responses, approve in minutes,
          and publish across Reddit, ChatGPT answer boxes, LinkedIn, and your blog with full attribution.
        </p>
        <div className="flex justify-center gap-4 flex-wrap">
          <CTAButton href="/pricing" variant="inverse">View Pricing</CTAButton>
          <CTAButton href="/managed" variant="primary">Talk to sales</CTAButton>
        </div>
      </section>

      <section className="py-14 px-4">
        <div className="max-w-6xl mx-auto grid gap-6 md:grid-cols-2">
          {featureAreas.map((area) => (
            <div key={area.title} className="bg-white rounded-lg shadow p-6 flex flex-col">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-2xl font-semibold text-primary-dark">{area.title}</h2>
                <CTAButton href={area.href} variant="subtle">Open</CTAButton>
              </div>
              <p className="text-gray-700 mb-4">{area.summary}</p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 flex-1">
                {area.bullets.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
          ))}
        </div>
      </section>

      <section className="py-16 px-4 bg-gray-100">
        <div className="max-w-5xl mx-auto text-center space-y-6">
          <h2 className="text-3xl font-semibold">Built for governed, measurable growth</h2>
          <p className="text-lg text-gray-700">Every module shares approvals, audit logs, and attribution so you never sacrifice control for speed.</p>
          <div className="grid md:grid-cols-2 gap-6 text-left">
            {operatingPillars.map((pillar) => (
              <div key={pillar.title} className="bg-white rounded-lg shadow p-6">
                <h3 className="text-xl font-semibold text-primary-dark mb-2">{pillar.title}</h3>
                <p className="text-gray-700">{pillar.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto text-center space-y-5">
          <h2 className="text-3xl font-semibold">Ready to replace your patchwork stack</h2>
          <p className="text-gray-700 text-lg">
            Consolidate monitoring, drafting, approvals, publishing, and reporting into one platform. No more
            cobbling together point tools or wrangling screenshots for leadership.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <CTAButton href="/pricing" variant="primary">Choose a plan</CTAButton>
            <CTAButton href="/contact" variant="inverse">Talk to an expert</CTAButton>
          </div>
        </div>
      </section>
    </div>
  );
}
