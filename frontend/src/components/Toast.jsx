import { useEffect } from 'react';

export default function Toast({ message, type = 'info', onClose }) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, 5000);
    
    return () => clearTimeout(timer);
  }, [onClose]);

  const styles = {
    success: 'bg-green-50 text-green-800 border-green-200',
    error: 'bg-red-50 text-red-800 border-red-200',
    info: 'bg-blue-50 text-blue-800 border-blue-200',
    warning: 'bg-amber-50 text-amber-800 border-amber-200',
  };

  const icons = {
    success: '✓',
    error: '✕',
    info: 'ⓘ',
    warning: '⚠',
  };

  return (
    <div className={`${styles[type]} border rounded-lg px-4 py-3 shadow-lg flex items-start gap-3 min-w-80 max-w-md animate-slide-in`}>
      <span className="text-lg font-semibold flex-shrink-0">{icons[type]}</span>
      <p className="flex-1 text-sm">{message}</p>
      <button 
        onClick={onClose}
        className="text-current opacity-50 hover:opacity-100 transition-opacity flex-shrink-0"
      >
        ✕
      </button>
    </div>
  );
}
