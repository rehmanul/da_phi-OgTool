import Link from 'next/link';

const baseStyles = 'inline-flex items-center justify-center px-6 py-3 rounded-lg font-semibold transition shadow';
const variants = {
  primary: 'bg-gradient-to-r from-gradientStart to-gradientEnd text-white hover:shadow-lg',
  inverse: 'bg-white text-primary-dark hover:shadow-lg',
  subtle: 'bg-gray-100 text-primary-dark hover:bg-gray-200',
};

export default function CTAButton({ href, children, variant = 'primary', className = '', ...props }) {
  const styles = `${baseStyles} ${variants[variant] || variants.primary} ${className}`.trim();

  if (href) {
    return (
      <Link href={href} className={styles} {...props}>
        {children}
      </Link>
    );
  }

  return (
    <button className={styles} type="button" {...props}>
      {children}
    </button>
  );
}
