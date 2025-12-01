import CTAButton from '../../components/CTAButton';
import SEO from '../../components/SEO';

const workflow = [
  { title: 'Topic intelligence', detail: 'Cluster keywords by intent, difficulty, and competitors to target the fastest paths to page one.' },
  { title: 'Briefs in your voice', detail: 'Generate outlines with persona notes, examples, and internal links to keep content on-brand and compliant.' },
  { title: 'Performance automation', detail: 'Track rankings, conversions, and share of voice per post; trigger refreshes when performance slips.' },
];

const outcomes = [
  { label: 'Faster production', value: '3-5x', caption: 'content throughput with AI-assisted briefs and drafts' },
  { label: 'Conversion lift', value: '28%', caption: 'average uplift from intent-focused topic selection' },
  { label: 'Operational time saved', value: '12 hrs', caption: 'per week reclaimed from manual reporting and QA' },
];

export default function BlogRanking() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div>
      <SEO
        title="Blog Ranking"
        description="Outrank competitors with AI-assisted briefs, governed publishing, and measurable conversion lift."
        url={`${siteUrl}/features/blog-ranking`}
      />

      <section className="bg-gradient-to-r from-gradientStart to-gradientEnd text-white py-20 px-4">
        <div className="max-w-5xl mx-auto">
          <p className="uppercase text-sm tracking-wide mb-3">Features</p>
          <h1 className="text-4xl font-bold mb-4">Own your category’s search traffic</h1>
          <p className="text-lg max-w-3xl mb-6">
            OGTool turns research, briefs, and publishing into one governed workflow so you can ship high-intent content faster,
            measure revenue impact, and refresh pages before rankings drop.
          </p>
          <div className="flex gap-4 flex-wrap">
            <CTAButton href="/pricing" variant="inverse">Compare plans</CTAButton>
            <CTAButton href="/contact" variant="primary">Talk to sales</CTAButton>
          </div>
        </div>
      </section>

      <section className="py-14 px-4 bg-white">
        <div className="max-w-6xl mx-auto grid md:grid-cols-3 gap-6">
          {outcomes.map((item) => (
            <div key={item.label} className="bg-gray-50 rounded-lg shadow p-6 text-center">
              <div className="text-sm uppercase tracking-wide text-primary-dark mb-2">{item.label}</div>
              <div className="text-3xl font-bold text-primary-dark mb-2">{item.value}</div>
              <p className="text-gray-700 text-sm">{item.caption}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="py-16 px-4 bg-gray-100">
        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-6">
          {workflow.map((step) => (
            <div key={step.title} className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-primary-dark mb-2">{step.title}</h2>
              <p className="text-gray-700">{step.detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8 items-start">
          <div className="space-y-4">
            <h2 className="text-3xl font-semibold text-primary-dark">Ship posts that convert, not just rank</h2>
            <p className="text-gray-700">
              Each brief includes persona pain points, narrative angles, and CTAs that match funnel stage. Drafts inherit those constraints,
              giving editors more time for polish instead of structural rewrites.
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2">
              <li>Built-in plagiarism checks and tone controls</li>
              <li>Approval workflows with roles for SEO, product, and legal</li>
              <li>Automatic internal link and schema recommendations</li>
            </ul>
            <div className="flex gap-4 flex-wrap">
              <CTAButton href="/docs/getting-started" variant="primary">See how it works</CTAButton>
              <CTAButton href="/managed" variant="inverse">Done-for-you option</CTAButton>
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg shadow p-6 space-y-3">
            <h3 className="text-xl font-semibold text-primary-dark">Analytics that leaders care about</h3>
            <ul className="space-y-2 text-gray-700">
              <li><strong>Pipeline attribution:</strong> tie influenced revenue to keywords and posts.</li>
              <li><strong>Share of voice:</strong> monitor who controls page one and answer boxes.</li>
              <li><strong>Refresh cues:</strong> detect decay and generate prioritized refresh plans.</li>
              <li><strong>Exec-ready exports:</strong> one-click reports with trends and next bets.</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
