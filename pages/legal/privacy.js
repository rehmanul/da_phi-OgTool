import SEO from '../../components/SEO';

const topics = [
  { title: 'Data we collect', detail: 'Account details, workspace configuration, content drafts, analytics data, and logs required to provide the service.' },
  { title: 'How we use data', detail: 'To deliver and improve the service, provide support, enforce security, and comply with legal obligations. We do not sell personal data.' },
  { title: 'Subprocessors', detail: 'We use vetted infrastructure and service providers. A current list is available on request and in enterprise agreements.' },
  { title: 'Retention', detail: 'Data is retained for as long as needed to deliver the service and fulfill legal requirements. Customers can request deletion.' },
  { title: 'Your rights', detail: 'Access, correct, or delete personal data; object to processing; and export data where applicable by law.' },
];

export default function Privacy() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div className="px-4 py-14">
      <SEO
        title="Privacy Policy"
        description="How OGTool collects, uses, protects, and retains your data."
        url={`${siteUrl}/legal/privacy`}
      />
      <header className="max-w-5xl mx-auto mb-8">
        <p className="uppercase text-sm tracking-wide text-primary-dark mb-2">Legal</p>
        <h1 className="text-4xl font-bold text-primary-dark mb-3">Privacy Policy</h1>
        <p className="text-gray-700">We respect your data and outline exactly how we handle it.</p>
      </header>
      <div className="max-w-5xl mx-auto space-y-6">
        {topics.map((topic) => (
          <section key={topic.title} className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-semibold text-primary-dark mb-2">{topic.title}</h2>
            <p className="text-gray-700">{topic.detail}</p>
          </section>
        ))}
      </div>
    </div>
  );
}
