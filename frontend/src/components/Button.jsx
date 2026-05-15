export default function Button({ children, variant = "solid", size = "md", onClick, type = "button", disabled = false }) {
  const base = "rounded-xl font-medium transition active:scale-[.99] disabled:opacity-50 disabled:cursor-not-allowed";
  const pad = size === "sm" ? "px-3 py-1.5 text-sm" : size === "lg" ? "px-5 py-3" : "px-4 py-2";
  const styles =
    variant === "secondary"
      ? "bg-slate-100 text-slate-800 hover:bg-slate-200 border border-slate-200"
      : variant === "danger"
      ? "bg-red-600 text-white hover:bg-red-700"
      : variant === "ghost"
      ? "bg-transparent text-slate-700 hover:bg-slate-100 border border-slate-200"
      : "bg-slate-900 text-white hover:bg-black";
  
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${pad} ${styles}`}
    >
      {children}
    </button>
  );
}
