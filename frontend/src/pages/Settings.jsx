import { useState, useEffect } from 'react';
import Section from '../components/Section';
import Button from '../components/Button';
import Badge from '../components/Badge';
import { useToast } from '../components/ToastContainer';
import { useProduct } from '../contexts/ProductContext';
import { api } from '../api';

export default function Settings() {
  const toast = useToast();
  const { products, activeProduct, refreshProducts } = useProduct();
  const [editingProduct, setEditingProduct] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProduct, setNewProduct] = useState({
    name: '',
    description: '',
    value_prop: '',
    from_email: ''
  });

  useEffect(() => {
    if (activeProduct) {
      setEditingProduct({ ...activeProduct });
    }
  }, [activeProduct]);

  const handleSaveProduct = async () => {
    if (!editingProduct) return;
    setIsSaving(true);
    try {
      await api.createProduct(editingProduct);
      toast.success('Product updated successfully');
      refreshProducts();
    } catch (err) {
      toast.error(err.message || 'Failed to update product');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCreateProduct = async () => {
    if (!newProduct.name) {
      toast.error('Product name is required');
      return;
    }
    setIsSaving(true);
    try {
      await api.createProduct(newProduct);
      toast.success('Product created successfully');
      setShowCreateModal(false);
      setNewProduct({ name: '', description: '', value_prop: '', from_email: '' });
      refreshProducts();
    } catch (err) {
      toast.error(err.message || 'Failed to create product');
    } finally {
      setIsSaving(false);
    }
  };

  if (!editingProduct) return <div className="py-20 text-center">Loading settings...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Product Settings</h1>
          <p className="text-sm text-slate-600 mt-1">
            Configure branding, ICP criteria, and outreach defaults for {activeProduct.name}
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} variant="outline">
          + New Product
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sidebar: Product Info */}
        <div className="lg:col-span-1 space-y-6">
          <Section title="Active Product">
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Product ID</label>
                <div className="px-3 py-2 bg-slate-100 rounded-lg text-sm font-mono text-slate-600">
                  {editingProduct.id}
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Product Name</label>
                <input
                  type="text"
                  value={editingProduct.name}
                  onChange={(e) => setEditingProduct({ ...editingProduct, name: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900/10"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">From Email (Default)</label>
                <input
                  type="email"
                  value={editingProduct.from_email || ''}
                  onChange={(e) => setEditingProduct({ ...editingProduct, from_email: e.target.value })}
                  placeholder="e.g. sales@company.com"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900/10"
                />
              </div>
            </div>
          </Section>

          <Section title="All Products">
            <div className="space-y-2">
              {products.map(p => (
                <div key={p.id} className={`flex items-center justify-between p-2 rounded-lg border ${p.id === activeProduct.id ? 'border-slate-900 bg-slate-50' : 'border-slate-200'}`}>
                  <span className="text-sm font-medium">{p.name}</span>
                  {p.id === activeProduct.id && <Badge tone="green">Active</Badge>}
                </div>
              ))}
            </div>
          </Section>
        </div>

        {/* Main: Value Prop & ICP */}
        <div className="lg:col-span-2 space-y-6">
          <Section title="Branding & Messaging">
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">One-Sentence Description</label>
                <textarea
                  value={editingProduct.description || ''}
                  onChange={(e) => setEditingProduct({ ...editingProduct, description: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900/10"
                  placeholder="A tool for clear handoffs and fast catch-ups."
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Core Value Proposition</label>
                <textarea
                  value={editingProduct.value_prop || ''}
                  onChange={(e) => setEditingProduct({ ...editingProduct, value_prop: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900/10"
                  placeholder="We help teams scale efficiently without the communication noise."
                />
              </div>
            </div>
          </Section>

          <Section title="ICP Scoping (Keywords)">
            <div className="space-y-4">
              <p className="text-xs text-slate-500">
                These keywords are used to score signals. Higher scores mean better personalization.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Growth Triggers</label>
                  <div className="text-[10px] text-slate-400 mb-1">Comma separated: funding, hiring, launch</div>
                  <textarea
                    value={JSON.stringify(editingProduct.icp_config?.growth_triggers || {}, null, 2)}
                    onChange={(e) => {
                      try {
                        const val = JSON.parse(e.target.value);
                        setEditingProduct({
                          ...editingProduct,
                          icp_config: { ...editingProduct.icp_config, growth_triggers: val }
                        });
                      } catch (err) {}
                    }}
                    rows={6}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs font-mono focus:outline-none focus:ring-2 focus:ring-slate-900/10"
                  />
                </div>
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Industry Keywords</label>
                    <textarea
                      value={JSON.stringify(editingProduct.icp_config?.industry_keywords || {}, null, 2)}
                      onChange={(e) => {
                        try {
                          const val = JSON.parse(e.target.value);
                          setEditingProduct({
                            ...editingProduct,
                            icp_config: { ...editingProduct.icp_config, industry_keywords: val }
                          });
                        } catch (err) {}
                      }}
                      rows={6}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs font-mono focus:outline-none focus:ring-2 focus:ring-slate-900/10"
                    />
                  </div>
                </div>
              </div>
            </div>
          </Section>

          <div className="flex justify-end">
            <Button onClick={handleSaveProduct} disabled={isSaving} className="px-8">
              {isSaving ? 'Saving...' : 'Save Product Settings'}
            </Button>
          </div>
        </div>
      </div>

      {/* Create Product Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full mx-4 p-6">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">Create New Product</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Name</label>
                <input
                  type="text"
                  value={newProduct.name}
                  onChange={(e) => setNewProduct({ ...newProduct, name: e.target.value })}
                  placeholder="e.g. My SaaS Product"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Value Prop</label>
                <textarea
                  value={newProduct.value_prop}
                  onChange={(e) => setNewProduct({ ...newProduct, value_prop: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <Button onClick={handleCreateProduct} disabled={isSaving} className="flex-1">
                {isSaving ? 'Creating...' : 'Create'}
              </Button>
              <Button onClick={() => setShowCreateModal(false)} variant="outline" className="flex-1">
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
