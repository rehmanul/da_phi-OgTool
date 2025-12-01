import CTAButton from '../../components/CTAButton';
import SEO from '../../components/SEO';

const milestones = [
  { year: '2022', detail: 'Founded OGTool to give GTM teams controlled AI-assisted publishing.' },
  { year: '2023', detail: 'Launched Reddit + SEO modules with attribution and approvals.' },
  { year: '2024', detail: 'Released AI answer coverage and enterprise security (SSO, SCIM, audit logs).' },
  { year: '2025', detail: 'Expanded to LinkedIn and launched managed service for high-growth teams.' },
];

const commitments = [
  'Security-first: SOC2-aligned controls, data residency, and least-privilege architecture.',
  'Compliance-ready: granular approvals, audit trails, and role-based permissions.',
  'Outcome-obsessed: we tie every feature to revenue, pipeline, or risk reduction.',
];

export default function About() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div>
      <SEO
        title="About Us"
        description="Learn why we built OGTool and how we help teams win AI search, communities, and SEO with safety and speed."
        url={`${siteUrl}/company/about`}
      />

      <section className="bg-gradient-to-b from-primary-dark to-gradientEnd text-white py-20 px-4">
        <div className="max-w-5xl mx-auto">
          <p className="uppercase text-sm tracking-wide mb-3">Company</p>
          <h1 className="text-4xl font-bold mb-4">Building the growth engine for AI-first teams</h1>
          <p className="text-lg max-w-3xl mb-6">
            We’re a distributed team of builders, marketers, and compliance leaders who believe AI and community-first channels
            should be measurable, safe, and fast to execute.
          </p>
          <CTAButton href="/company/careers" variant="inverse">Join the team</CTAButton>
        </div>
      </section>

      <section className="py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-6">
          {milestones.map((milestone) => (
            <div key={milestone.year} className="bg-gray-50 rounded-lg shadow p-6">
              <div className="text-sm uppercase tracking-wide text-primary-dark mb-1">{milestone.year}</div>
              <p className="text-gray-700">{milestone.detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="py-16 px-4 bg-gray-100">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8 items-start">
          <div className="space-y-4">
            <h2 className="text-3xl font-semibold text-primary-dark">How we work</h2>
            <p className="text-gray-700">
              We partner closely with customers, iterating weekly with real-world feedback from GTM, security, and legal teams.
              That’s how OGTool stays both powerful and governed.
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2">
              {commitments.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </div>
          <div className="bg-white rounded-lg shadow p-6 space-y-3">
            <h3 className="text-xl font-semibold text-primary-dark">Want to learn more?</h3>
            <p className="text-gray-700">
              Get a tailored roadmap, see security documentation, or meet the team that will guide your rollout.
            </p>
            <CTAButton href="/contact" variant="primary">Contact us</CTAButton>
          </div>
        </div>
      </section>
    </div>
  );
}
