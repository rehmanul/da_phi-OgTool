import { useState } from 'react';

export default function FaqAccordion({ items, title = 'Questions? Answers!' }) {
  const [openIndex, setOpenIndex] = useState(null);
  const toggle = (index) => setOpenIndex(openIndex === index ? null : index);

  return (
    <section className="py-16 px-4">
      <h2 className="text-3xl font-semibold text-center mb-8">{title}</h2>
      <div className="max-w-3xl mx-auto">
        {items.map((item, idx) => (
          <div key={item.q} className="mb-4 border-b border-gray-200 pb-3">
            <button
              onClick={() => toggle(idx)}
              className="w-full text-left font-semibold text-gray-800 flex justify-between items-center py-2"
              aria-expanded={openIndex === idx}
            >
              <span>{item.q}</span>
              <span aria-hidden="true">{openIndex === idx ? '▲' : '▼'}</span>
            </button>
            {openIndex === idx && <p className="text-gray-600 mt-2 px-2">{item.a}</p>}
          </div>
        ))}
      </div>
    </section>
  );
}
