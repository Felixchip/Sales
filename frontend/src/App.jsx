import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { ToastProvider } from './components/ToastContainer';
import { ProductProvider, useProduct } from './contexts/ProductContext';
import ProductSwitcher from './components/ProductSwitcher';
import Verify from './pages/Verify';
import Personalize from './pages/Personalize';
import Settings from './pages/Settings';

function NavButton({ to, children }) {
  const location = useLocation();
  const isActive = location.pathname === to;
  
  return (
    <Link
      to={to}
      className={`rounded-xl px-3 py-2 text-sm font-medium ${
        isActive ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
      }`}
    >
      {children}
    </Link>
  );
}

function Layout({ children }) {
  const { activeProduct } = useProduct();
  
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-900 text-white font-bold">
              {activeProduct ? activeProduct.name.substring(0, 1).toUpperCase() : "V"}
            </div>
            <div>
              <div className="text-sm uppercase tracking-widest text-slate-500">
                {activeProduct ? activeProduct.name : "Verify & Personalize"}
              </div>
              <div className="-mt-0.5 text-lg font-semibold text-slate-900">Outreach</div>
            </div>
          </div>
          
          <div className="flex items-center gap-6">
            <nav className="flex gap-2 border-r border-slate-200 pr-6 mr-6">
              <NavButton to="/">Personalize</NavButton>
              <NavButton to="/verify">Verify</NavButton>
              <NavButton to="/settings">Settings</NavButton>
            </nav>
            <ProductSwitcher />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        {children}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <ProductProvider>
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<Personalize />} />
              <Route path="/verify" element={<Verify />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </ProductProvider>
    </ToastProvider>
  );
}
