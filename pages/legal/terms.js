import SEO from '../../components/SEO';

const sections = [
  { title: 'Services', body: 'OGTool provides software for monitored discovery, content drafting, approvals, publishing, and analytics across supported channels.' },
  { title: 'Customer data', body: 'You retain ownership of all data you supply. We process it solely to deliver the services as described in our agreement.' },
  { title: 'Security', body: 'We maintain administrative, technical, and physical safeguards aligned with industry standards. Security documentation is available on request.' },
  { title: 'Acceptable use', body: 'No unlawful, harmful, or abusive behavior; no attempts to bypass platform safeguards; no posting prohibited content to third-party platforms.' },
  { title: 'SLAs & support', body: 'Standard support is business hours with 1-business-day response; premium support and uptime SLAs are available on enterprise plans.' },
];

export default function Terms() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div className="px-4 py-14">
      <SEO
        title="Terms of Service"
        description="Terms governing your use of OGTool, including data handling, acceptable use, and support."
        url={`${siteUrl}/legal/terms`}
      />
      <header className="max-w-5xl mx-auto mb-8">
        <p className="uppercase text-sm tracking-wide text-primary-dark mb-2">Legal</p>
        <h1 className="text-4xl font-bold text-primary-dark mb-3">Terms of Service</h1>
        <p className="text-gray-700">These terms outline how we deliver OGTool and the responsibilities of both parties.</p>
      </header>
      <div className="max-w-5xl mx-auto space-y-6">
        {sections.map((section) => (
          <section key={section.title} className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-semibold text-primary-dark mb-2">{section.title}</h2>
            <p className="text-gray-700">{section.body}</p>
          </section>
        ))}
      </div>
    </div>
  );
}
