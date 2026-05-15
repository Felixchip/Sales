import React, { useState } from 'react';
import { useProduct } from '../contexts/ProductContext';

export default function ProductSwitcher() {
  const { products, activeProduct, switchProduct } = useProduct();
  const [isOpen, setIsOpen] = useState(false);

  if (!activeProduct) return null;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-slate-900/10"
      >
        <div className="flex h-5 w-5 items-center justify-center rounded bg-slate-900 text-[10px] text-white font-bold">
          {activeProduct.name.substring(0, 1).toUpperCase()}
        </div>
        <span>{activeProduct.name}</span>
        <svg
          className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-20"
            onClick={() => setIsOpen(false)}
          ></div>
          <div className="absolute right-0 mt-2 z-30 w-48 rounded-xl border border-slate-200 bg-white p-1 shadow-xl">
            <div className="px-3 py-2 text-[10px] uppercase tracking-widest text-slate-400">
              Switch Product
            </div>
            {products.map((product) => (
              <button
                key={product.id}
                onClick={() => {
                  switchProduct(product.id);
                  setIsOpen(false);
                }}
                className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  activeProduct.id === product.id
                    ? 'bg-slate-900 text-white'
                    : 'text-slate-700 hover:bg-slate-50'
                }`}
              >
                <div className={`flex h-5 w-5 items-center justify-center rounded text-[10px] font-bold ${
                  activeProduct.id === product.id ? 'bg-white/20' : 'bg-slate-100'
                }`}>
                  {product.name.substring(0, 1).toUpperCase()}
                </div>
                {product.name}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
