import { useMemo } from 'react';
import CTAButton from '../components/CTAButton';
import Hero from '../components/Hero';
import PricingGrid from '../components/PricingGrid';
import SEO from '../components/SEO';
import StatGrid from '../components/StatGrid';
import { performanceMetrics, pricingPlans } from '../lib/marketingContent';

const guarantees = [
  { title: 'Fast setup', text: 'Connect accounts and ship your first AI-assisted replies in under 15 minutes.' },
  { title: 'Persona-safe', text: 'Lock tone, approvals, and compliance rules per persona—no risky auto-posting.' },
  { title: 'Attribution-first', text: 'Track traffic, share of voice, and deal influence across Reddit and search.' },
];

export default function Pricing() {
  const siteUrl = useMemo(() => process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com', []);

  return (
    <div>
      <SEO
        title="Pricing"
        description="Choose a plan that fits: start with live Reddit monitoring, scale with AI-powered replies, SEO, and multi-persona workflows."
        url={`${siteUrl}/pricing`}
      />

      <Hero
        title="Pricing built for revenue teams"
        subtitle="Start with monitoring and AI-assisted replies, then layer in SEO and multi-persona workflows as you grow."
        primaryCta={{ href: '#plans', label: 'View Plans' }}
        secondaryCta={{ href: '/managed', label: 'Need a Team?' }}
      />

      <StatGrid title="What every plan includes" items={guarantees} />

      <PricingGrid
        id="plans"
        plans={pricingPlans}
        subtitle="Pick the plan that matches your motion—self-serve for squads that want to move fast, or go custom when you need integrations and approvals."
      />

      <StatGrid
        title="Proof you can defend budget with"
        items={performanceMetrics}
        columns="md:grid-cols-4"
        className="bg-gray-100"
      />

      <section className="py-16 px-4 text-center">
        <div className="max-w-3xl mx-auto space-y-4">
          <h2 className="text-3xl font-semibold">Ready to own the conversations that convert?</h2>
          <p className="text-gray-700">
            Spin up a workspace, invite your team, and see the threads and keywords that matter inside 24 hours.
            Switch plans anytime—your data, personas, and approvals stay intact.
          </p>
          <div className="flex justify-center gap-4 flex-wrap">
            <CTAButton href="/pricing#plans" variant="primary">Start self-serve</CTAButton>
            <CTAButton href="/managed" variant="inverse">Talk to sales</CTAButton>
          </div>
        </div>
      </section>
    </div>
  );
}
