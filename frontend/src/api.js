import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('mmtpl_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authApi = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  getMe: () => api.get('/auth/me'),
  getDemoUsers: () => api.get('/auth/demo-users'),
};

export const dashboardApi = {
  getStats: () => api.get('/dashboard/stats'),
};

export const materialsApi = {
  list: (params) => api.get('/materials', { params }),
  get: (itemId) => api.get(`/materials/${itemId}`),
  getLedger: (itemId) => api.get(`/materials/${itemId}/ledger`),
  getCategories: () => api.get('/materials/categories'),
  create: (data) => api.post('/materials', data),
  update: (itemId, data) => api.patch(`/materials/${itemId}`, data),
};

export const inwardApi = {
  list: (params) => api.get('/inward', { params }),
  getNextId: () => api.get('/inward/next-id'),
  create: (data) => api.post('/inward', data),
  verify: (receiptId, data) => api.post(`/inward/${receiptId}/verify`, data),
};

export const transactionsApi = {
  list: (params) => api.get('/transactions', { params }),
  getNextId: () => api.get('/transactions/next-id'),
  create: (data) => api.post('/transactions', data),
  verify: (txId, data) => api.post(`/transactions/${txId}/verify`, data),
};

export const contractorsApi = {
  list: () => api.get('/contractors'),
  getProfile: (code, params) => api.get(`/contractors/${code}`, { params }),
};

export const verificationApi = {
  getPending: (params) => api.get('/verification/pending', { params }),
  review: (entityType, entityId, data) => 
    api.post('/verification/review', data, { params: { entity_type: entityType, entity_id: entityId } }),
};

export const auditApi = {
  list: (params) => api.get('/audit', { params }),
};

export default api;
