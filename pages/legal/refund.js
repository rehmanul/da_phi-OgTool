import SEO from '../../components/SEO';

const policyItems = [
  { title: 'Eligibility', detail: 'Monthly plans: cancel anytime; unused time is not refunded. Annual plans: refunds available within 30 days of initial purchase.' },
  { title: 'Service levels', detail: 'If we miss uptime SLAs on eligible plans, service credits are issued according to your contract.' },
  { title: 'Managed services', detail: 'Managed retainers include a 30-day opt-out if deliverables are missed; otherwise governed by the SOW.' },
  { title: 'How to request', detail: 'Email billing@ogtool.com from an admin account with your workspace name, plan, and reason for the request.' },
];

export default function RefundPolicy() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div className="px-4 py-14">
      <SEO
        title="Refund Policy"
        description="Understand when refunds or service credits apply for OGTool subscriptions and managed services."
        url={`${siteUrl}/legal/refund`}
      />
      <header className="max-w-5xl mx-auto mb-8">
        <p className="uppercase text-sm tracking-wide text-primary-dark mb-2">Legal</p>
        <h1 className="text-4xl font-bold text-primary-dark mb-3">Refund Policy</h1>
        <p className="text-gray-700">Transparent guidelines for cancellations, service credits, and managed service commitments.</p>
      </header>
      <div className="max-w-5xl mx-auto space-y-6">
        {policyItems.map((item) => (
          <section key={item.title} className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-semibold text-primary-dark mb-2">{item.title}</h2>
            <p className="text-gray-700">{item.detail}</p>
          </section>
        ))}
      </div>
    </div>
  );
}
