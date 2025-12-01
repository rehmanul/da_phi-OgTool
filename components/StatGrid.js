export default function StatGrid({ title, items, columns = 'md:grid-cols-3', className = '', id }) {
  return (
    <section className={`py-16 px-4 ${className}`} id={id}>
      {title && <h2 className="text-3xl font-semibold text-center mb-8">{title}</h2>}
      <div className={`grid gap-6 ${columns} max-w-7xl mx-auto`}>
        {items.map((item) => (
          <div key={item.title} className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-primary-dark mb-2">{item.title}</h3>
            <p className="text-gray-600">{item.text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
