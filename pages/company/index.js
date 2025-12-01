import CTAButton from '../../components/CTAButton';
import SEO from '../../components/SEO';

const values = [
  { title: 'Bias for action', detail: 'We ship fast with guardrails, learning from every release and customer conversation.' },
  { title: 'Truth over theater', detail: 'We prioritize measurable impact over vanity metrics or performative marketing.' },
  { title: 'Earned trust', detail: 'Security, compliance, and accuracy are non-negotiable in every feature we ship.' },
];

const leadership = [
  { name: 'Ava Kim', role: 'CEO & Co-founder', highlight: 'Built GTM at high-growth B2B SaaS; led AI search initiatives at scale.' },
  { name: 'Luis Ortega', role: 'CTO & Co-founder', highlight: 'Former head of platform engineering; specialized in compliant AI systems.' },
  { name: 'Priya Desai', role: 'VP Customer', highlight: 'Scaled customer success teams for enterprise marketing stacks.' },
];

export default function Company() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div>
      <SEO
        title="Company"
        description="Meet the OGTool team building the platform for AI search, Reddit, LinkedIn, and SEO growth."
        url={`${siteUrl}/company`}
      />

      <section className="bg-primary-dark text-white py-20 px-4">
        <div className="max-w-5xl mx-auto">
          <p className="uppercase text-sm tracking-wide mb-3">Company</p>
          <h1 className="text-4xl font-bold mb-4">We build for measurable, safe growth</h1>
          <p className="text-lg max-w-3xl mb-6">
            OGTool exists to help teams own organic discovery across AI search and communities—without losing control or compliance.
          </p>
          <div className="flex gap-4 flex-wrap">
            <CTAButton href="/company/about" variant="inverse">About us</CTAButton>
            <CTAButton href="/company/careers" variant="primary">See open roles</CTAButton>
          </div>
        </div>
      </section>

      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-6">
          {values.map((value) => (
            <div key={value.title} className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-primary-dark mb-2">{value.title}</h2>
              <p className="text-gray-700">{value.detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="py-16 px-4 bg-gray-100">
        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-6">
          {leadership.map((leader) => (
            <div key={leader.name} className="bg-white rounded-lg shadow p-6">
              <h3 className="text-xl font-semibold text-primary-dark">{leader.name}</h3>
              <p className="text-sm text-gray-600 mb-2">{leader.role}</p>
              <p className="text-gray-700">{leader.highlight}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto text-center space-y-5">
          <h2 className="text-3xl font-semibold">Ready to partner with us?</h2>
          <p className="text-gray-700 text-lg">
            Whether you need self-serve guidance or a managed team, we’ll craft a plan tied to your goals and compliance needs.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <CTAButton href="/contact" variant="primary">Contact us</CTAButton>
            <CTAButton href="/managed" variant="inverse">Explore managed service</CTAButton>
          </div>
        </div>
      </section>
    </div>
  );
}
