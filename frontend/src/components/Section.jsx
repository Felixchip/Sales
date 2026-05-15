export default function Section({ title, actions, children }) {
  return (
    <section className="mt-6">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-base font-semibold text-slate-900">{title}</h3>
        {actions && <div className="flex gap-2">{actions}</div>}
      </div>
      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        {children}
      </div>
    </section>
  );
}
