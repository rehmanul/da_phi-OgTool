import CTAButton from '../../components/CTAButton';
import SEO from '../../components/SEO';

const practices = [
  {
    title: 'Guardrails first',
    detail: 'Create personas with approved claims, tone settings, and banned phrases. Require approvals for sensitive categories.',
  },
  {
    title: 'Attribution everywhere',
    detail: 'Use consistent UTMs, profile journeys, and form capture to attribute Reddit, ChatGPT answers, LinkedIn, and blog traffic.',
  },
  {
    title: 'Refresh cadence',
    detail: 'Set decay thresholds and auto-generate refresh tasks for blog posts and answer snippets before rankings slip.',
  },
  {
    title: 'Multi-team workflows',
    detail: 'Define roles for creators, SMEs, legal, and leadership. Use SLAs and escalation to keep velocity without sacrificing review.',
  },
  {
    title: 'Quality signals',
    detail: 'Run plagiarism, sentiment, and compliance checks before submission. Auto-flag drafts missing sources or proof points.',
  },
];

const templates = [
  'Reddit reply templates per persona and funnel stage',
  'LinkedIn post pillars with weekly publishing slots',
  'Blog brief templates with structured schema guidance',
  'Incident playbook for off-brand or inaccurate content',
];

export default function BestPractices() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div>
      <SEO
        title="Best Practices"
        description="Use these playbooks to keep OGTool programs safe, high-quality, and accountable to revenue."
        url={`${siteUrl}/docs/best-practices`}
      />

      <section className="bg-gradient-to-b from-primary-dark to-gradientEnd text-white py-20 px-4">
        <div className="max-w-5xl mx-auto">
          <p className="uppercase text-sm tracking-wide mb-3">Docs</p>
          <h1 className="text-4xl font-bold mb-4">Scale with confidence</h1>
          <p className="text-lg max-w-3xl mb-6">
            Apply these best practices to keep every channel on-brand, compliant, and measurable while you scale OGTool across teams.
          </p>
          <CTAButton href="/contact" variant="inverse">Request a review</CTAButton>
        </div>
      </section>

      <section className="py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-6">
          {practices.map((practice) => (
            <div key={practice.title} className="bg-gray-50 rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-primary-dark mb-2">{practice.title}</h2>
              <p className="text-gray-700">{practice.detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="py-16 px-4 bg-gray-100">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8 items-start">
          <div className="space-y-4">
            <h2 className="text-3xl font-semibold text-primary-dark">Templates to speed adoption</h2>
            <ul className="list-disc list-inside text-gray-700 space-y-2">
              {templates.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </div>
          <div className="bg-white rounded-lg shadow p-6 space-y-3">
            <h3 className="text-xl font-semibold text-primary-dark">Operational guardrails</h3>
            <p className="text-gray-700">
              Set SLA reminders, auto-archive stale drafts, and enforce two-person review for regulated industries. Export audits on-demand
              for compliance teams.
            </p>
            <CTAButton href="/docs/api-reference" variant="primary">Automate with the API</CTAButton>
          </div>
        </div>
      </section>
    </div>
  );
}
