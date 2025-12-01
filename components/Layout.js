import Link from 'next/link';
import { useRouter } from 'next/router';
import { useState } from 'react';
import Analytics from './Analytics';

export default function Layout({ children }) {
  const { pathname } = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const navLinks = [
    { href: '/', label: 'Self-Serve' },
    { href: '/managed', label: 'Managed' },
    { href: '/features', label: 'Features' },
    { href: '/pricing', label: 'Pricing' },
    { href: '/docs', label: 'Docs' },
    { href: '/blog', label: 'Blog' },
    { href: '/resources', label: 'Resources' },
    { href: '/company', label: 'Company' },
    { href: '/contact', label: 'Contact' },
  ];

  return (
    <>
      <Analytics />
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:bg-white focus:text-primary-dark focus:px-3 focus:py-2 focus:rounded-md focus:shadow">Skip to main content</a>
      <header className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <Link href="/" className="font-bold text-xl text-primary-dark" aria-label="OGTool home">
          OGTool
        </Link>
        <nav className="hidden md:flex space-x-6" aria-label="Primary">
          {navLinks.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="hover:text-primary-dark"
              aria-current={pathname === item.href ? 'page' : undefined}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/pricing" className="bg-gradient-to-r from-gradientStart to-gradientEnd text-white px-4 py-2 rounded-lg text-sm font-semibold hidden md:inline-flex">Get started</Link>
          <button
            className="md:hidden border border-gray-200 rounded-md p-2"
            aria-label="Toggle navigation menu"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-expanded={menuOpen}
          >
            <span className="block w-5 h-0.5 bg-primary-dark mb-1" />
            <span className="block w-5 h-0.5 bg-primary-dark mb-1" />
            <span className="block w-5 h-0.5 bg-primary-dark" />
          </button>
        </div>
      </header>
      {menuOpen && (
        <div className="md:hidden px-4 pb-4">
          <nav className="bg-white rounded-lg shadow p-4 space-y-3" aria-label="Mobile primary">
            {navLinks.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="block text-primary-dark"
                aria-current={pathname === item.href ? 'page' : undefined}
                onClick={() => setMenuOpen(false)}
              >
                {item.label}
              </Link>
            ))}
            <Link
              href="/pricing"
              className="block bg-gradient-to-r from-gradientStart to-gradientEnd text-white px-4 py-2 rounded-lg text-center font-semibold"
              onClick={() => setMenuOpen(false)}
            >
              Get started
            </Link>
          </nav>
        </div>
      )}
      <main id="main-content">{children}</main>
      <footer className="bg-primary-dark text-white mt-16 py-10">
        <div className="max-w-7xl mx-auto px-4 grid grid-cols-2 md:grid-cols-5 gap-8">
          <div>
            <h5 className="font-semibold mb-3">Features</h5>
            <Link href="/features" className="block text-sm mb-1">All Features</Link>
            <Link href="/features/blog-ranking" className="block text-sm mb-1">Blog Ranking</Link>
            <Link href="/features/chatgpt-ranking" className="block text-sm mb-1">ChatGPT Ranking</Link>
            <Link href="/features/reddit-marketing" className="block text-sm mb-1">Reddit Marketing</Link>
            <Link href="/features/linkedin-marketing" className="block text-sm mb-1">LinkedIn Marketing</Link>
          </div>
          <div>
            <h5 className="font-semibold mb-3">Docs</h5>
            <Link href="/docs/getting-started" className="block text-sm mb-1">Getting Started</Link>
            <Link href="/docs/api-reference" className="block text-sm mb-1">API Reference</Link>
            <Link href="/docs/best-practices" className="block text-sm mb-1">Best Practices</Link>
          </div>
          <div>
            <h5 className="font-semibold mb-3">Resources</h5>
            <Link href="/resources" className="block text-sm mb-1">Resources</Link>
            <Link href="/pricing" className="block text-sm mb-1">Pricing</Link>
            <Link href="/blog" className="block text-sm mb-1">Blog</Link>
            <Link href="/managed" className="block text-sm mb-1">Managed Service</Link>
          </div>
          <div>
            <h5 className="font-semibold mb-3">Company</h5>
            <Link href="/company/careers" className="block text-sm mb-1">Careers</Link>
            <Link href="/company/about" className="block text-sm mb-1">About Us</Link>
            <Link href="/contact" className="block text-sm mb-1">Contact</Link>
          </div>
          <div>
            <h5 className="font-semibold mb-3">Legal</h5>
            <Link href="/legal/terms" className="block text-sm mb-1">Terms of Service</Link>
            <Link href="/legal/privacy" className="block text-sm mb-1">Privacy Policy</Link>
            <Link href="/legal/refund" className="block text-sm mb-1">Refund Policy</Link>
          </div>
        </div>
        <p className="text-center text-xs text-gray-300 mt-8">&copy; {new Date().getFullYear()} OGTool. All rights reserved.</p>
      </footer>
    </>
  );
}
