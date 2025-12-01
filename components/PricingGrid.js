import CTAButton from './CTAButton';

export default function PricingGrid({ plans, title = 'Flexible Plans for All', subtitle, className = '', id }) {
  return (
    <section className={`py-16 px-4 ${className}`} id={id}>
      <div className="text-center mb-8">
        <h2 className="text-3xl font-semibold mb-2">{title}</h2>
        {subtitle && <p className="text-gray-600 max-w-2xl mx-auto">{subtitle}</p>}
      </div>
      <div className="flex flex-col md:flex-row justify-center gap-6 max-w-7xl mx-auto">
        {plans.map((plan) => (
            <div
              key={plan.name}
              className={`flex-1 max-w-xs bg-white rounded-lg shadow p-8 flex flex-col items-center ${
              plan.highlighted ? 'border-2 border-primary-dark' : ''
            }`}
          >
            <h4 className="text-xl font-semibold mb-2">{plan.name}</h4>
            <div className="text-3xl text-primary-dark font-bold mb-4">{plan.price}</div>
            <ul className="text-gray-600 space-y-2 mb-6">
              {plan.features.map((feature) => (
                <li key={feature}>{feature}</li>
              ))}
            </ul>
            <CTAButton href={plan.href} variant={plan.highlighted ? 'primary' : 'subtle'}>
              {plan.cta}
            </CTAButton>
          </div>
        ))}
      </div>
    </section>
  );
}
