import Head from 'next/head';

const trackingId = process.env.NEXT_PUBLIC_ANALYTICS_ID;

export default function Analytics() {
  if (!trackingId) return null;

  const gtagSrc = `https://www.googletagmanager.com/gtag/js?id=${trackingId}`;
  const gtagInit = `
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', '${trackingId}', { anonymize_ip: true });
  `;

  return (
    <Head>
      <script async src={gtagSrc} />
      <script id="gtag-init" dangerouslySetInnerHTML={{ __html: gtagInit }} />
    </Head>
  );
}
