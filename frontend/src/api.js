const API_BASE = '/api';

async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
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
  // Verification
  verifyEmail: (email) => apiRequest('/verify', {
    method: 'POST',
    body: JSON.stringify({ email }),
  }),
  
  verifyBatch: (emails) => apiRequest('/verify/batch', {
    method: 'POST',
    body: JSON.stringify({ emails }),
  }),
  
  verifyBatchCSV: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch('/api/verify/batch', {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new Error(error.error || `API error: ${response.status}`);
    }
    return response.json();
  },
  
  getVerificationHistory: (limit = 50) => apiRequest(`/verify/history?limit=${limit}`),
  
  getVerificationStatus: (jobId) => apiRequest(`/verify/status/${jobId}`),
  
  saveEmail: (email, score, name = null) => apiRequest('/verify/save', {
    method: 'POST',
    body: JSON.stringify({ email, score, name }),
  }),
  
  getSavedEmails: (limit = 1000) => apiRequest(`/verify/saved?limit=${limit}`),
  
  deleteSavedEmail: (email) => apiRequest(`/verify/saved/${encodeURIComponent(email)}`, {
    method: 'DELETE',
  }),

  // Personalization
  ingestSignals: (signals) => apiRequest('/signals/ingest', {
    method: 'POST',
    body: JSON.stringify({ signals }),
  }),

  getSignalsByDomain: (domain, limit = 3) => apiRequest(`/signals/${domain}?limit=${limit}`),

  getAllSignals: (limit = 100) => apiRequest(`/signals?limit=${limit}`),

  renderPersonalization: (lead) => apiRequest('/personalize/render', {
    method: 'POST',
    body: JSON.stringify(lead),
  }),

  getTemplates: () => apiRequest('/templates'),

  createTemplate: (template) => apiRequest('/templates', {
    method: 'POST',
    body: JSON.stringify(template),
  }),

  purgeSignals: (days = 90) => apiRequest('/signals/purge', {
    method: 'POST',
    body: JSON.stringify({ days }),
  }),

  personalizeFromEmail: (email, name = null, signalId = null) => apiRequest('/personalize/from-email', {
    method: 'POST',
    body: JSON.stringify({ email, name, pinned_signal_id: signalId }),
  }),

  markSignalContacted: (signalId) => apiRequest(`/signals/${signalId}/contact`, {
    method: 'POST',
  }),

  getContactedSignals: (limit = 100) => apiRequest(`/signals/contacted?limit=${limit}`),

  // Prospects
  getProspects: (status = null, limit = 100) => {
    const endpoint = status ? `/prospects?status=${status}&limit=${limit}` : `/prospects?limit=${limit}`;
    return apiRequest(endpoint);
  },

  updateProspect: (domain, status, notes = null) => apiRequest(`/prospects/${domain}`, {
    method: 'PATCH',
    body: JSON.stringify({ status, notes }),
  }),

  discoverProspects: () => apiRequest('/prospects/discover', { method: 'POST' }),

  // Signal Collection Triggers
  collectPressSignals: (keywords = null, maxResults = 10) => apiRequest('/signals/press-releases', {
    method: 'POST',
    body: JSON.stringify({ keywords, max_results: maxResults }),
  }),

  collectHiringSignals: (keywords = null, maxResults = 10) => apiRequest('/signals/job-boards', {
    method: 'POST',
    body: JSON.stringify({ keywords, max_results: maxResults }),
  }),

  collectLaunchSignals: (keywords = null, maxResults = 10) => apiRequest('/signals/product-launches', {
    method: 'POST',
    body: JSON.stringify({ keywords, max_results: maxResults }),
  }),
};
