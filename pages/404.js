import CTAButton from '../components/CTAButton';
import SEO from '../components/SEO';

export default function NotFound() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4 py-20">
      <SEO title="Page Not Found" description="We could not find that page. Explore OGTool features and plans." url={`${siteUrl}/404`} noIndex />
      <div className="max-w-2xl text-center space-y-6 bg-white shadow rounded-lg p-10">
        <p className="text-sm uppercase tracking-wide text-primary-dark">404</p>
        <h1 className="text-4xl font-bold text-primary-dark">This page is missing</h1>
        <p className="text-gray-700">
          The link you followed might be broken. Keep exploring OGTool’s self-serve platform or talk with our managed
          team.
        </p>
        <div className="flex justify-center gap-4 flex-wrap">
          <CTAButton href="/" variant="primary">Go to homepage</CTAButton>
          <CTAButton href="/pricing" variant="inverse">See pricing</CTAButton>
          <CTAButton href="/managed" variant="subtle">Managed service</CTAButton>
        </div>
      </div>
    </div>
  );
}
