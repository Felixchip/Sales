const API_BASE = '/api';

async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  
  // Extract productId from options or use null
  const productId = options.productId;
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (productId) {
    headers['X-Product-Id'] = productId;
  }

  const config = {
    headers,
    ...options,
  };

  const response = await fetch(url, config);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || `API error: ${response.status}`);
  }
  
  return response.json();
}

export const api = {
  // Products
  getProducts: () => apiRequest('/products'),
  getProduct: (id) => apiRequest(`/products/${id}`),
  createProduct: (product) => apiRequest('/products', {
    method: 'POST',
    body: JSON.stringify(product),
  }),
  deleteProduct: (id) => apiRequest(`/products/${id}`, {
    method: 'DELETE',
  }),

  // Verification
  verifyEmail: (email) => apiRequest('/verify', {
    method: 'POST',
    body: JSON.stringify({ email }),
  }),
  
  verifyBatch: (emails) => apiRequest('/verify/batch', {
    method: 'POST',
    body: JSON.stringify({ emails }),
  }),
  
  getVerificationHistory: (limit = 50) => apiRequest(`/verify/history?limit=${limit}`),
  
  getVerificationStatus: (jobId) => apiRequest(`/verify/status/${jobId}`),
  
  // Personalization
  ingestSignals: (signals, productId) => apiRequest('/signals/ingest', {
    method: 'POST',
    productId,
    body: JSON.stringify({ signals }),
  }),

  getSignalsByDomain: (domain, productId, limit = 3) => apiRequest(`/signals/${domain}?limit=${limit}`, {
    productId
  }),

  getAllSignals: (productId, limit = 100) => apiRequest(`/signals?limit=${limit}`, {
    productId
  }),

  renderPersonalization: (lead, productId) => apiRequest('/personalize/render', {
    method: 'POST',
    productId,
    body: JSON.stringify(lead),
  }),

  getTemplates: (productId) => apiRequest('/templates', {
    productId
  }),

  createTemplate: (template, productId) => apiRequest('/templates', {
    method: 'POST',
    productId,
    body: JSON.stringify(template),
  }),

  personalizeFromEmail: (email, productId, name = null, signalId = null) => apiRequest('/personalize/from-email', {
    method: 'POST',
    productId,
    body: JSON.stringify({ email, name, pinned_signal_id: signalId }),
  }),

  markSignalContacted: (signalId) => apiRequest(`/signals/${signalId}/contact`, {
    method: 'POST',
  }),

  getContactedSignals: (productId, limit = 100) => apiRequest(`/signals/contacted?limit=${limit}`, {
    productId
  }),

  // Prospects
  getProspects: (productId, status = null, limit = 100) => {
    const endpoint = status ? `/prospects?status=${status}&limit=${limit}` : `/prospects?limit=${limit}`;
    return apiRequest(endpoint, { productId });
  },

  updateProspect: (domain, status, productId, notes = null) => apiRequest(`/prospects/${domain}`, {
    method: 'PATCH',
    productId,
    body: JSON.stringify({ status, notes }),
  }),

  discoverProspects: (productId) => apiRequest('/prospects/discover', { 
    method: 'POST',
    productId 
  }),

  // Signal Collection Triggers
  collectPressSignals: (productId, keywords = null, maxResults = 10) => apiRequest('/signals/press-releases', {
    method: 'POST',
    productId,
    body: JSON.stringify({ keywords, max_results: maxResults }),
  }),

  collectHiringSignals: (productId, keywords = null, maxResults = 10) => apiRequest('/signals/job-boards', {
    method: 'POST',
    productId,
    body: JSON.stringify({ keywords, max_results: maxResults }),
  }),

  collectLaunchSignals: (productId, keywords = null, maxResults = 10) => apiRequest('/signals/product-launches', {
    method: 'POST',
    productId,
    body: JSON.stringify({ keywords, max_results: maxResults }),
  }),
};
