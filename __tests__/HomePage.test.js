import { render, screen } from '@testing-library/react';
import Home from '../pages/index';

describe('Home page', () => {
  it('renders hero copy and key CTAs', () => {
    render(<Home />);

    expect(screen.getByText(/Stop Missing Engaged Buyer Conversations/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Start Now/i })).toHaveAttribute('href', '#pricing');
    expect(screen.getByRole('link', { name: /See Managed/i })).toHaveAttribute('href', '/managed');
  });

  it('renders pricing plan CTAs with destinations', () => {
    render(<Home />);

    expect(screen.getByRole('link', { name: /Start self-serve/i })).toHaveAttribute(
      'href',
      '/contact#contact-form',
    );
    expect(screen.getByRole('link', { name: /Talk to sales/i })).toHaveAttribute(
      'href',
      '/contact#contact-form',
    );
    expect(screen.getByRole('link', { name: /Book consult/i })).toHaveAttribute(
      'href',
      '/managed#booking',
    );
  });
});
