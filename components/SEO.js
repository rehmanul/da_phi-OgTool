import Head from 'next/head';

const defaultMeta = {
  title: 'OGTool',
  description: 'OGTool is the AI search and community growth platform that ranks your brand across Reddit, ChatGPT answers, LinkedIn, and your blog.',
  siteUrl: process.env.NEXT_PUBLIC_SITE_URL || 'https://ogtool.example.com',
  imageWidth: 1200,
  imageHeight: 630,
};

export default function SEO({ title, description, url, image, noIndex }) {
  const metaTitle = title ? `${title} | OGTool` : defaultMeta.title;
  const metaDescription = description || defaultMeta.description;
  const metaUrl = url || defaultMeta.siteUrl;
  const metaImage = image || `${defaultMeta.siteUrl}/og-image.png`;

  return (
    <Head>
      <title>{metaTitle}</title>
      <meta name="description" content={metaDescription} />
      <meta property="og:title" content={metaTitle} />
      <meta property="og:description" content={metaDescription} />
      <meta property="og:url" content={metaUrl} />
      <meta property="og:type" content="website" />
      <meta property="og:image" content={metaImage} />
      <meta property="og:image:width" content={defaultMeta.imageWidth} />
      <meta property="og:image:height" content={defaultMeta.imageHeight} />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={metaTitle} />
      <meta name="twitter:description" content={metaDescription} />
      <meta name="twitter:image" content={metaImage} />
      {noIndex && <meta name="robots" content="noindex" />}
      <link rel="canonical" href={metaUrl} />
    </Head>
  );
}
