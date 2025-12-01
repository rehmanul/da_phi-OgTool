import CTAButton from '../../components/CTAButton';
import SEO from '../../components/SEO';

const posts = [
  {
    title: 'How to win AI answer boxes consistently',
    summary: 'A playbook for monitoring queries, enforcing answer quality, and recovering when rankings slip.',
    tag: 'AI Search',
    readTime: '7 min read',
  },
  {
    title: 'Reddit programs that drive pipeline, not PR headaches',
    summary: 'Governance, approvals, and attribution tactics to keep community efforts safe and measurable.',
    tag: 'Reddit',
    readTime: '6 min read',
  },
  {
    title: 'LinkedIn content pillars that align with sales',
    summary: 'Align GTM, marketing, and leadership voices into one LinkedIn calendar that actually converts.',
    tag: 'LinkedIn',
    readTime: '5 min read',
  },
  {
    title: 'SEO refresh cadence for durable rankings',
    summary: 'How to detect decay early, prioritize refreshes, and keep landing pages converting.',
    tag: 'SEO',
    readTime: '8 min read',
  },
];

export default function Blog() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div>
      <SEO
        title="Blog"
        description="Strategic guidance on AI search, Reddit, LinkedIn, and SEO from the OGTool team."
        url={`${siteUrl}/blog`}
      />

      <section className="bg-gradient-to-b from-gradientStart to-gradientEnd text-white text-center py-20 px-4">
        <p className="uppercase text-sm tracking-wide mb-3">Insights</p>
        <h1 className="text-4xl font-bold mb-4">OGTool Blog</h1>
        <p className="text-lg max-w-3xl mx-auto mb-6">
          Hands-on articles and playbooks for teams who need measurable growth across AI search, communities, and SEO.
        </p>
        <div className="flex justify-center gap-4 flex-wrap">
          <CTAButton href="/pricing" variant="inverse">See pricing</CTAButton>
          <CTAButton href="/contact" variant="primary">Get in touch</CTAButton>
        </div>
      </section>

      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-6">
          {posts.map((post) => (
            <article key={post.title} className="bg-white rounded-lg shadow p-6 flex flex-col">
              <div className="flex items-center justify-between text-sm text-primary-dark mb-2">
                <span className="font-semibold">{post.tag}</span>
                <span>{post.readTime}</span>
              </div>
              <h2 className="text-2xl font-semibold text-primary-dark mb-2">{post.title}</h2>
              <p className="text-gray-700 flex-1">{post.summary}</p>
              <CTAButton href="/contact" variant="subtle" className="mt-4">Discuss with us</CTAButton>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
