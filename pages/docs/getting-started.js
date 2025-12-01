import CTAButton from '../../components/CTAButton';
import SEO from '../../components/SEO';

const steps = [
  { title: '1) Create your workspace', detail: 'Set org name, add domains, enable SSO/SCIM, and invite admins.' },
  { title: '2) Define personas', detail: 'Upload voice guidelines, approved claims, and compliance constraints per persona.' },
  { title: '3) Connect sources', detail: 'Add Reddit monitors, LinkedIn pages, and your CMS/reverse proxy to enable publishing.' },
  { title: '4) Configure approvals', detail: 'Set approvers per channel, SLAs, and escalation rules for regulated topics.' },
  { title: '5) Launch first playbook', detail: 'Pick Reddit replies, ChatGPT answer coverage, or blog ranking to start shipping value.' },
];

const checklists = [
  'Tracking: ensure UTMs and lead source mapping are enabled before go-live.',
  'Security: validate SSO, MFA, and data residency selections.',
  'Training: run a 30-minute enablement with your SMEs and approvers.',
  'Reporting: subscribe leaders to weekly performance summaries.',
];

export default function GettingStarted() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div>
      <SEO
        title="Getting Started"
        description="Launch OGTool in under 30 minutes with this guided setup for admins and creators."
        url={`${siteUrl}/docs/getting-started`}
      />

      <section className="bg-primary-dark text-white py-20 px-4">
        <div className="max-w-5xl mx-auto">
          <p className="uppercase text-sm tracking-wide mb-3">Docs</p>
          <h1 className="text-4xl font-bold mb-4">Launch checklist</h1>
          <p className="text-lg max-w-3xl mb-6">
            Follow these steps to configure OGTool, connect your channels, and ship your first approved content in under an hour.
          </p>
          <div className="flex gap-4 flex-wrap">
            <CTAButton href="/contact" variant="inverse">Need help?</CTAButton>
            <CTAButton href="/docs/api-reference" variant="primary">Use the API</CTAButton>
          </div>
        </div>
      </section>

      <section className="py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-6">
          {steps.map((step) => (
            <div key={step.title} className="bg-gray-50 rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-primary-dark mb-2">{step.title}</h2>
              <p className="text-gray-700">{step.detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="py-16 px-4 bg-gray-100">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8 items-start">
          <div className="space-y-4">
            <h2 className="text-3xl font-semibold text-primary-dark">Before you go live</h2>
            <ul className="list-disc list-inside text-gray-700 space-y-2">
              {checklists.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </div>
          <div className="bg-white rounded-lg shadow p-6 space-y-3">
            <h3 className="text-xl font-semibold text-primary-dark">Enable approvals</h3>
            <p className="text-gray-700">
              Use tiered approvals for regulated content, auto-approvals for trusted creators, and escalation routing for legal/PR.
              Capture every edit and approval in the audit log.
            </p>
            <CTAButton href="/docs/best-practices" variant="primary">Read best practices</CTAButton>
          </div>
        </div>
      </section>
    </div>
  );
}
