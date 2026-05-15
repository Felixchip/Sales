import React, { createContext, useContext, useState, useEffect } from 'react';

const ProductContext = createContext();

export const useProduct = () => {
  const context = useContext(ProductContext);
  if (!context) {
    throw new Error('useProduct must be used within a ProductProvider');
  }
  return context;
};

export const ProductProvider = ({ children }) => {
  const [products, setProducts] = useState([]);
  const [activeProduct, setActiveProduct] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await fetch('/api/products');
      const data = await response.json();
      setProducts(data.products || []);
      
      // Load last active product from localStorage or default to EchoTray
      const savedProductId = localStorage.getItem('activeProductId');
      const found = data.products.find(p => p.id === savedProductId) || data.products.find(p => p.id === 'echotray') || data.products[0];
      
      if (found) {
        setActiveProduct(found);
      }
    } catch (error) {
      console.error('Failed to fetch products:', error);
    } finally {
      setLoading(false);
    }
  };

  const switchProduct = (productId) => {
    const product = products.find(p => p.id === productId);
    if (product) {
      setActiveProduct(product);
      localStorage.setItem('activeProductId', productId);
    }
  };

  const value = {
    products,
    activeProduct,
    switchProduct,
    refreshProducts: fetchProducts,
    loading
  };

  return (
    <ProductContext.Provider value={value}>
      {children}
    </ProductContext.Provider>
  );
};
