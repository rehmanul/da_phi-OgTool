import { useMemo } from 'react';
import CTAButton from '../components/CTAButton';
import LeadForm from '../components/LeadForm';
import Hero from '../components/Hero';
import SEO from '../components/SEO';
import StatGrid from '../components/StatGrid';
import { performanceMetrics, successStoryStats } from '../lib/marketingContent';

const approachSteps = [
  { title: '1. Setup', text: 'Define strategy, create personas, import knowledgebase assets, and lock compliance rules.' },
  { title: '2. Research', text: 'Scrape viral Reddit threads and competitor blogs to surface the highest-intent topics.' },
  { title: '3. Reddit', text: 'Publish 50–100 authentic comments/month in your voice, offering genuine help where buyers ask.' },
  { title: '4. SEO', text: 'Ship 4–8 SEO-optimized posts/month targeting viral topics—on your site or via reverse proxy.' },
  { title: '5. Win', text: 'Drive compounding traffic across Reddit, Google, and AI search with consistent execution.' },
];

const pricingTiers = [
  { name: 'Self-Serve', price: '$100–$250/mo', detail: 'Choose 10–30 keywords, connect accounts, and run our workflows with chat support.' },
  { name: 'Semi-Managed', price: '$500/mo', detail: 'We handle onboarding and setup, create your Reddit account and blog system, then hand off with private Slack support.' },
  { name: 'Fully Managed', price: '$3,000/mo', detail: 'End-to-end execution: Reddit, blogs, approvals, reporting, and integrations run for you.' },
];

const roiTracking = [
  { title: 'Reddit', text: 'Track visitors and signups from comment links and profile journeys.' },
  { title: 'Blogs', text: 'Monitor rankings, impressions, and conversions per post with clear owners.' },
  { title: 'AI Search', text: 'Measure answer visibility and resulting traffic from AI search surfaces.' },
  { title: 'Attribution', text: 'Capture self-reported attribution in sign-up flows to tie revenue back to channels.' },
];

const timeline = [
  { title: 'Kickoff (Day 0)', text: 'Strategy alignment, success metrics, and persona guardrails.' },
  { title: 'Launch (Day 1)', text: 'Comments and blogs begin publishing with approvals in place.' },
  { title: 'Weekly', text: 'Reports on comments posted, blogs shipped, wins, and next bets.' },
  { title: 'Monthly', text: 'Rankings, share of voice, revenue influence, and roadmap adjustments.' },
];

export default function Managed() {
  const siteUrl = useMemo(() => process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com', []);

  return (
    <div>
      <SEO
        title="Managed Service"
        description="Full-service OGTool team handles research, persona replies, SEO, and reporting so you can own AI search and Reddit."
        url={`${siteUrl}/managed`}
      />

      <Hero
        title="Managed service that wins AI search and Reddit for you"
        subtitle="Hand the work to a team that already knows the playbooks. We execute, report, and iterate so you see revenue—not just activity."
        primaryCta={{ href: '#booking', label: 'Book a consultation' }}
        secondaryCta={{ href: '#approach', label: 'See the plan' }}
      />

      <section className="py-12 px-4">
        <div className="bg-blue-50 p-4 rounded-lg mb-8 max-w-2xl mx-auto">
          <strong className="block mb-2">On this page</strong>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-sm">
            <a href="#results" className="text-primary-dark">Results</a>
            <a href="#approach" className="text-primary-dark">Approach</a>
            <a href="#pricing" className="text-primary-dark">Pricing</a>
            <a href="#roi" className="text-primary-dark">ROI Tracking</a>
            <a href="#timeline" className="text-primary-dark">Timeline</a>
            <a href="#booking" className="text-primary-dark">Next Steps</a>
          </div>
        </div>

        <StatGrid title="Results you can show leadership" items={successStoryStats} id="results" />

        <section id="approach" className="py-16 px-4">
          <h2 className="text-3xl font-semibold text-center mb-6">How we run your motion</h2>
          <div className="max-w-4xl mx-auto grid gap-6 md:grid-cols-2">
            {approachSteps.map((step) => (
              <div key={step.title} className="bg-white rounded-lg shadow p-6">
                <h3 className="text-xl font-semibold text-primary-dark mb-2">{step.title}</h3>
                <p className="text-gray-700">{step.text}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="pricing" className="py-16 px-4 bg-gray-100">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-semibold">Engagement models</h2>
            <p className="text-gray-700 max-w-2xl mx-auto">
              Pick the level of support your team needs; every option includes strategy, reporting, and persona safety checks.
            </p>
          </div>
          <div className="max-w-5xl mx-auto grid gap-6 md:grid-cols-3">
            {pricingTiers.map((tier) => (
              <div key={tier.name} className="bg-white rounded-lg shadow p-6 flex flex-col">
                <h3 className="text-xl font-semibold text-primary-dark mb-2">{tier.name}</h3>
                <div className="text-2xl font-bold text-primary-dark mb-3">{tier.price}</div>
                <p className="text-gray-700 flex-1">{tier.detail}</p>
                <CTAButton href="#booking" variant="primary" className="mt-6">Talk with us</CTAButton>
              </div>
            ))}
          </div>
        </section>

        <StatGrid
          id="roi"
          title="ROI tracking and reporting"
          items={roiTracking}
          columns="md:grid-cols-4"
        />

        <StatGrid id="timeline" title="Timeline & cadence" items={timeline} columns="md:grid-cols-4" className="bg-gray-100" />

        <section id="proof" className="py-16 px-4">
          <div className="max-w-5xl mx-auto text-center space-y-6">
            <h2 className="text-3xl font-semibold">We report like a revenue team, not an agency</h2>
            <p className="text-gray-700">
              Weekly wins, monthly share-of-voice, and a single view of Reddit + SEO performance. No vanity metrics, just deal impact.
            </p>
            <div className="grid md:grid-cols-3 gap-6 text-left">
              {performanceMetrics.map((metric) => (
                <div key={metric.title} className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-primary-dark mb-2">{metric.title}</h3>
                  <p className="text-gray-700">{metric.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="booking" className="py-16 px-4">
          <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-6 items-start">
            <div className="bg-primary-dark text-white rounded-lg p-6">
              <h2 className="text-3xl font-semibold mb-4">Let’s win the conversations that move revenue</h2>
              <p className="text-blue-100 mb-4">
                We take on a limited number of new managed clients each month to preserve quality and speed.
                Book a call to lock in your slot and get a tailored plan.
              </p>
              <ul className="list-disc list-inside text-blue-100 space-y-2">
                <li>Persona-safe replies with approvals</li>
                <li>Reddit + SEO share-of-voice reporting</li>
                <li>Playbooks proven across SaaS and B2B</li>
              </ul>
            </div>
            <LeadForm subtitle="Tell us about your motion and we’ll reply with a tailored approach within one business day." />
          </div>
        </section>
      </section>
    </div>
  );
}
