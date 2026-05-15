export default function Badge({ children, tone = "slate" }) {
  const toneClasses = {
    slate: "bg-slate-100 text-slate-700",
    green: "bg-green-100 text-green-700",
    blue: "bg-blue-100 text-blue-700",
    amber: "bg-amber-100 text-amber-700",
    violet: "bg-violet-100 text-violet-700",
    emerald: "bg-emerald-100 text-emerald-700",
  };

  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs ${toneClasses[tone] || toneClasses.slate}`}>
      {children}
    </span>
  );
}
