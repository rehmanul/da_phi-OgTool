import { render, screen, within } from '@testing-library/react';
import Layout from '../components/Layout';

jest.mock('next/router', () => ({
  useRouter: () => ({ pathname: '/' }),
}));

describe('Navigation', () => {
  it('renders primary navigation links', () => {
    render(
      <Layout>
        <div>Child</div>
      </Layout>,
    );

    const nav = screen.getByRole('navigation', { name: /primary/i });
    const links = [
      ['Self-Serve', '/'],
      ['Managed', '/managed'],
      ['Features', '/features'],
      ['Pricing', '/pricing'],
      ['Docs', '/docs'],
      ['Blog', '/blog'],
      ['Resources', '/resources'],
      ['Company', '/company'],
      ['Contact', '/contact'],
    ];

    links.forEach(([label, href]) => {
      expect(within(nav).getByRole('link', { name: label })).toHaveAttribute('href', href);
    });
  });
});
