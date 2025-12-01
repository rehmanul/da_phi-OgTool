# OGTool – Next.js Production Template

Production-ready marketing site inspired by OGTool, built with Next.js (pages router) and Tailwind CSS. Includes self-serve, managed, pricing, features, docs, blog, resources, company, legal, and contact pages with shared layout, SEO, and lead capture.

## Features

- Next.js 14 with pages-based routing and React 18.
- Tailwind CSS with custom palette and responsive layouts.
- Shared layout with navigation, footer, SEO meta, OG image, sitemap, robots, favicons, 404/500 pages.
- Hardened contact form with validation, honeypot, optional webhook forwarding.
- Optional Google Analytics (gtag) gated by env.
- Jest + Testing Library smoke tests for home, nav, and contact API.

## Getting Started

```bash
npm install
npm run dev      # http://localhost:5000
```

Build and serve production:

```bash
npm run build
npm start        # http://localhost:5000
```

## Configuration

- `CONTACT_WEBHOOK_URL` (optional): POST target for contact submissions.
- `NEXT_PUBLIC_ANALYTICS_ID` (optional): GA4 measurement ID (e.g., `G-XXXXXXX`).

Update `public/sitemap.xml` and `public/robots.txt` with your live domain before launch.

## Testing

```bash
npm test
```

## Deployment

Standard Next.js static+SSR deployment; ensure environment variables above are set, and serve the `public/` assets (favicons, manifest, OG image, sitemap, robots).
