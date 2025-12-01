import LeadForm from '../components/LeadForm';
import SEO from '../components/SEO';

const contactOptions = [
  { title: 'Sales', detail: 'Get a tailored demo, pricing guidance, and a rollout plan for your team.' },
  { title: 'Support', detail: 'Need help with configuration, APIs, or approvals? Our support team responds within one business day.' },
  { title: 'Security', detail: 'Request security documents, data flow diagrams, and details on SSO/SCIM and audit logging.' },
];

export default function Contact() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div>
      <SEO
        title="Contact"
        description="Talk with OGTool about pricing, onboarding, security reviews, or partnership opportunities."
        url={`${siteUrl}/contact`}
      />

      <section className="bg-primary-dark text-white py-20 px-4">
        <div className="max-w-5xl mx-auto text-center space-y-4">
          <p className="uppercase text-sm tracking-wide">Contact</p>
          <h1 className="text-4xl font-bold">Talk to the OGTool team</h1>
          <p className="text-lg text-blue-100">
            Share what you’re trying to achieve—AI answers, Reddit, LinkedIn, SEO—and we’ll reply with the fastest path to value.
          </p>
        </div>
      </section>

      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-6 items-start">
          <div className="bg-white rounded-lg shadow p-6 space-y-3">
            <h2 className="text-2xl font-semibold text-primary-dark">How we can help</h2>
            <ul className="space-y-2 text-gray-700">
              {contactOptions.map((option) => (
                <li key={option.title}>
                  <strong>{option.title}:</strong> {option.detail}
                </li>
              ))}
            </ul>
            <p className="text-gray-700">
              Prefer email? Reach us at <a className="text-primary-dark font-semibold" href="mailto:hello@ogtool.com">hello@ogtool.com</a>.
            </p>
          </div>
          <LeadForm
            id="contact-form"
            title="Book time with our team"
            subtitle="Tell us about your goals so we can pair you with the right specialist."
          />
        </div>
      </section>
    </div>
  );
}
