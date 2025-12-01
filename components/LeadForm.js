import { useState } from 'react';
import CTAButton from './CTAButton';

export default function LeadForm({ title = 'Book a consultation', subtitle, id }) {
  const [status, setStatus] = useState('idle'); // idle | submitting | success | error
  const [error, setError] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    setStatus('submitting');
    setError('');
    const form = event.currentTarget;
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());
    try {
      const res = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        throw new Error('Submission failed');
      }
      setStatus('success');
      if (form) {
        form.reset();
      }
    } catch (err) {
      setStatus('error');
      setError(err.message || 'Something went wrong');
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 text-left" id={id}>
      <h3 className="text-2xl font-semibold text-primary-dark mb-2">{title}</h3>
      {subtitle && <p className="text-gray-700 mb-4">{subtitle}</p>}
      <form className="space-y-4" onSubmit={handleSubmit}>
        <div className="hidden" aria-hidden="true">
          <label htmlFor="website">Website</label>
          <input
            id="website"
            name="website"
            tabIndex="-1"
            autoComplete="off"
            className="opacity-0 h-px w-px"
          />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1" htmlFor="name">Name</label>
          <input className="w-full border border-gray-300 rounded-lg px-3 py-2" id="name" name="name" required />
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1" htmlFor="email">Work email</label>
            <input type="email" className="w-full border border-gray-300 rounded-lg px-3 py-2" id="email" name="email" required />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1" htmlFor="company">Company</label>
            <input className="w-full border border-gray-300 rounded-lg px-3 py-2" id="company" name="company" required />
          </div>
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1" htmlFor="message">What are you trying to achieve?</label>
          <textarea className="w-full border border-gray-300 rounded-lg px-3 py-2" id="message" name="message" rows="3" required />
        </div>
        <div className="flex items-center gap-3">
          <CTAButton type="submit" variant="primary" className="px-5" disabled={status === 'submitting'}>
            {status === 'submitting' ? 'Sending...' : 'Send request'}
          </CTAButton>
          <span className="text-sm" aria-live="polite">
            {status === 'success' && <span className="text-green-700">Thanks—check your email for next steps.</span>}
            {status === 'error' && <span className="text-red-600">{error}</span>}
          </span>
        </div>
      </form>
    </div>
  );
}
