import CTAButton from './CTAButton';

export default function Hero({ title, subtitle, primaryCta, secondaryCta }) {
  return (
    <section className="bg-gradient-to-b from-gradientStart to-gradientEnd text-white text-center py-20 px-4">
      <h1 className="text-4xl font-bold mb-4">{title}</h1>
      {subtitle && <p className="text-lg max-w-2xl mx-auto mb-6">{subtitle}</p>}
      <div className="flex justify-center gap-4 flex-wrap">
        {primaryCta && <CTAButton href={primaryCta.href} variant="inverse">{primaryCta.label}</CTAButton>}
        {secondaryCta && <CTAButton href={secondaryCta.href} variant="primary">{secondaryCta.label}</CTAButton>}
      </div>
    </section>
  );
}
