import CTAButton from '../../components/CTAButton';
import SEO from '../../components/SEO';

const safeguards = [
  { title: 'Answer provenance', detail: 'Answers pull from approved sources with citations and freshness metadata.' },
  { title: 'Prompt interception', detail: 'Alerts when competitor mentions displace you in ChatGPT or Perplexity answers.' },
  { title: 'Governed publishing', detail: 'Legal and product approvals on any answer updates before they are shipped live.' },
];

const telemetry = [
  'Track answer-box share of voice across priority queries',
  'Monitor click-through and downstream conversions from AI answers',
  'Trigger refreshes when accuracy, sentiment, or rankings degrade',
];

export default function ChatGPTRanking() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div>
      <SEO
        title="ChatGPT Ranking"
        description="Make sure AI answers recommend your product with monitored prompts, governed updates, and measurable outcomes."
        url={`${siteUrl}/features/chatgpt-ranking`}
      />

      <section className="bg-gradient-to-r from-primary-dark to-gradientEnd text-white py-20 px-4">
        <div className="max-w-5xl mx-auto">
          <p className="uppercase text-sm tracking-wide mb-3">AI Search</p>
          <h1 className="text-4xl font-bold mb-4">Win the AI answer box every time</h1>
          <p className="text-lg max-w-3xl mb-6">
            OGTool monitors ChatGPT answers for your critical queries, keeps approved snippets in rotation, and alerts you the moment
            a competitor takes your spot or outdated info appears.
          </p>
          <div className="flex gap-4 flex-wrap">
            <CTAButton href="/pricing" variant="inverse">Pick a plan</CTAButton>
            <CTAButton href="/contact" variant="primary">Book a walkthrough</CTAButton>
          </div>
        </div>
      </section>

      <section className="py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-6">
          {safeguards.map((item) => (
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
            <h2 className="text-3xl font-semibold text-primary-dark">Trusted, accurate answers</h2>
            <p className="text-gray-700">
              Keep control over what AI answers say about you. OGTool enforces content sources, tone, and claim accuracy with approvals
              baked into every update, so AI-driven discovery becomes a reliable funnel.
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2">
              <li>Multi-persona answers tailored to each ICP</li>
              <li>Regional variations to respect product packaging and compliance</li>
              <li>Automated retries if an update is rejected by the model provider</li>
            </ul>
          </div>
          <div className="bg-white rounded-lg shadow p-6 space-y-3">
            <h3 className="text-xl font-semibold text-primary-dark">Measure the impact</h3>
            <ul className="space-y-2 text-gray-700">
              {telemetry.map((line) => <li key={line}>{line}</li>)}
            </ul>
            <CTAButton href="/docs/api-reference" variant="primary" className="mt-4">Use the API</CTAButton>
          </div>
        </div>
      </section>

      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto text-center space-y-5">
          <h2 className="text-3xl font-semibold">Stay ahead of competitors</h2>
          <p className="text-gray-700 text-lg">
            Daily competitive prompts, sentiment scoring, and alerting mean you are notified before leadership asks why
            you disappeared from AI answers.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <CTAButton href="/managed" variant="primary">Let our team handle it</CTAButton>
            <CTAButton href="/features" variant="inverse">Explore all features</CTAButton>
          </div>
        </div>
      </section>
    </div>
  );
}
