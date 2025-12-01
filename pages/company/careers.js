import CTAButton from '../../components/CTAButton';
import SEO from '../../components/SEO';

const openings = [
  {
    role: 'Senior Full-Stack Engineer',
    location: 'Remote, North America',
    focus: 'Build governed publishing workflows, AI generation safety, and analytics.',
  },
  {
    role: 'Product Marketing Manager',
    location: 'Remote, US/EU',
    focus: 'Craft positioning, launch programs, and proof for AI search and community-led growth.',
  },
  {
    role: 'Customer Success Lead',
    location: 'Remote, US',
    focus: 'Partner with enterprise customers to deploy OGTool safely and drive adoption.',
  },
];

const benefits = [
  'Remote-first with home office support',
  'Competitive salary, equity, and 401(k)',
  'Comprehensive health, dental, and vision',
  'Learning budget and quarterly team onsites',
];

export default function Careers() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div>
      <SEO
        title="Careers"
        description="Join OGTool and help teams win AI search, Reddit, LinkedIn, and SEO with governed automation."
        url={`${siteUrl}/company/careers`}
      />

      <section className="bg-gradient-to-b from-gradientStart to-gradientEnd text-white py-20 px-4">
        <div className="max-w-5xl mx-auto">
          <p className="uppercase text-sm tracking-wide mb-3">Careers</p>
          <h1 className="text-4xl font-bold mb-4">Help teams own organic growth</h1>
          <p className="text-lg max-w-3xl mb-6">
            We’re assembling a team that cares about craft, security, and measurable outcomes. If you want to build at the intersection of AI and GTM, let’s talk.
          </p>
          <CTAButton href="/contact" variant="inverse">Reach out</CTAButton>
        </div>
      </section>

      <section className="py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-6">
          {openings.map((opening) => (
            <div key={opening.role} className="bg-gray-50 rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-primary-dark mb-1">{opening.role}</h2>
              <p className="text-sm text-gray-600 mb-2">{opening.location}</p>
              <p className="text-gray-700">{opening.focus}</p>
              <CTAButton href="/contact" variant="subtle" className="mt-4">Apply</CTAButton>
            </div>
          ))}
        </div>
      </section>

      <section className="py-16 px-4 bg-gray-100">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8 items-start">
          <div className="space-y-4">
            <h2 className="text-3xl font-semibold text-primary-dark">Benefits & culture</h2>
            <ul className="list-disc list-inside text-gray-700 space-y-2">
              {benefits.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </div>
          <div className="bg-white rounded-lg shadow p-6 space-y-3">
            <h3 className="text-xl font-semibold text-primary-dark">Our interview approach</h3>
            <p className="text-gray-700">
              We focus on practical work samples, collaboration, and product thinking. You’ll meet the people you’d work with and have time for your questions.
            </p>
            <CTAButton href="/company/about" variant="primary">Learn about us</CTAButton>
          </div>
        </div>
      </section>
    </div>
  );
}
