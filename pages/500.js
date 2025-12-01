import CTAButton from '../components/CTAButton';
import SEO from '../components/SEO';

export default function ServerError() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com';

  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4 py-20">
      <SEO title="Server Error" description="Something went wrong. Try again or get help from the OGTool team." url={`${siteUrl}/500`} noIndex />
      <div className="max-w-2xl text-center space-y-6 bg-white shadow rounded-lg p-10">
        <p className="text-sm uppercase tracking-wide text-primary-dark">500</p>
        <h1 className="text-4xl font-bold text-primary-dark">We hit a snag</h1>
        <p className="text-gray-700">
          Please try again in a moment. If the issue persists, contact us and we’ll sort it out quickly.
        </p>
        <div className="flex justify-center gap-4 flex-wrap">
          <CTAButton href="/" variant="primary">Back home</CTAButton>
          <CTAButton href="/resources" variant="inverse">View resources</CTAButton>
          <CTAButton href="/contact" variant="subtle">Contact support</CTAButton>
        </div>
      </div>
    </div>
  );
}
