import { useMemo } from 'react';
import CTAButton from '../components/CTAButton';
import FaqAccordion from '../components/FaqAccordion';
import Hero from '../components/Hero';
import PricingGrid from '../components/PricingGrid';
import SEO from '../components/SEO';
import StatGrid from '../components/StatGrid';
import { faqItems, featureSteps, performanceMetrics, pricingPlans, successStoryStats } from '../lib/marketingContent';

export default function Home() {
  const siteUrl = useMemo(() => process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com', []);
  return (
    <div>
      <SEO
        title="Self-Serve Growth Platform"
        description="Engage high-intent conversations with OGTool—automate listening, respond with personas, and track revenue lift."
        url={`${siteUrl}/`}
      />
      <Hero
        title="Stop Missing Engaged Buyer Conversations"
        subtitle="Engage high-intent communities with AI-assisted replies, persona workflows, and SEO coverage your competitors cannot match."
        primaryCta={{ href: '#pricing', label: 'Start Now' }}
        secondaryCta={{ href: '/managed', label: 'See Managed' }}
      />

      <StatGrid title="Customer Success Story" items={successStoryStats} />

      <StatGrid
        title="Performance Metrics"
        items={performanceMetrics}
        columns="md:grid-cols-4"
        className="bg-gray-100"
      />

      <StatGrid title="Turn Conversations into Customers" items={featureSteps} />

      <section className="py-16 px-4 bg-primary-dark text-white">
        <div className="max-w-5xl mx-auto text-center space-y-6">
          <h2 className="text-3xl font-semibold">Ship faster with playbooks that already win</h2>
          <p className="text-lg text-blue-100">
            Plug in your brand voice, load competitors, and let OGTool surface the 5% of threads and blogs that move revenue.
            Track SEO + Reddit share of voice in one place, not 10 different tools.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <CTAButton href="/pricing" variant="inverse">Compare Plans</CTAButton>
            <CTAButton href="/managed" variant="primary" className="border border-white">Work With Our Team</CTAButton>
          </div>
        </div>
      </section>

      <PricingGrid plans={pricingPlans} className="bg-gray-100" id="pricing" />

      <FaqAccordion items={faqItems} />
    </div>
  );
}
