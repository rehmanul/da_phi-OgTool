import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LeadForm from '../components/LeadForm';

describe('LeadForm', () => {
  const mockResponse = { ok: true, json: () => Promise.resolve({ status: 'ok' }) };

  beforeEach(() => {
    global.fetch = jest.fn(() => Promise.resolve(mockResponse));
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it('renders expected fields and copy', () => {
    render(<LeadForm title="Book time" subtitle="Tell us more" />);

    expect(screen.getByText('Book time')).toBeInTheDocument();
    expect(screen.getByText('Tell us more')).toBeInTheDocument();
    expect(screen.getByLabelText(/Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Work email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Company/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/What are you trying to achieve/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Send request/i })).toBeInTheDocument();
  });

  it('submits form data and shows success state', async () => {
    const user = userEvent.setup();
    render(<LeadForm />);

    await user.type(screen.getByLabelText(/Name/i), 'Ada Lovelace');
    await user.type(screen.getByLabelText(/Work email/i), 'ada@example.com');
    await user.type(screen.getByLabelText(/Company/i), 'Analytical Engines');
    await user.type(screen.getByLabelText(/What are you trying to achieve/i), 'Ship the demo');

    await user.click(screen.getByRole('button', { name: /Send request/i }));

    await screen.findByText(/Thanks—check your email/i);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        '/api/contact',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
        }),
      );
    });
  });
});
