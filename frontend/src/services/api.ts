import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('token')
    }
    return Promise.reject(error)
  }
)

export default api

// Chat API
export const chatApi = {
  send: (data: { message: string; context?: any[]; use_rag?: boolean; model?: string }) =>
    api.post('/chat', data),

  getHistory: (params?: { limit?: number; offset?: number }) =>
    api.get('/chat/history', { params }),

  getModels: () => api.get('/chat/models'),

  importToKnowledge: (data: any) => api.post('/chat/import', data),
}

// Knowledge API
export const knowledgeApi = {
  listDocs: (params?: { category_id?: number; tags?: string[]; limit?: number; offset?: number }) =>
    api.get('/kb/docs', { params }),

  getDoc: (id: number) => api.get(`/kb/docs/${id}`),

  createDoc: (data: any) => api.post('/kb/docs', data),

  updateDoc: (id: number, data: any) => api.put(`/kb/docs/${id}`, data),

  deleteDoc: (id: number) => api.delete(`/kb/docs/${id}`),

  search: (data: { query: string; limit?: number; filters?: any }) =>
    api.post('/kb/search', data),

  getGraph: (params?: { entity_type?: string; entity_code?: string }) =>
    api.get('/kb/graph', { params }),
}

// Market API
export const marketApi = {
  getQuotes: (codes: string[]) => api.get('/market/quote', { params: { codes: codes.join(',') } }),

  getHistory: (params: { code: string; start_date?: string; end_date?: string; period?: string; limit?: number }) =>
    api.get('/market/history', { params }),

  getIndicators: (params: { code: string; period?: string }) =>
    api.get('/market/indicators', { params }),

  analyze: (data: { code: string; options?: any }) => api.post('/market/analyze', data),

  generateDailyReview: (data: { date: string }) => api.post('/market/review/daily', data),
}

// Portfolio API
export const portfolioApi = {
  getPortfolio: () => api.get('/portfolio'),

  addPosition: (data: any) => api.post('/portfolio', data),

  updatePosition: (id: number, data: any) => api.put(`/portfolio/${id}`, data),

  deletePosition: (id: number) => api.delete(`/portfolio/${id}`),

  getTransactions: (params?: { limit?: number }) =>
    api.get('/portfolio/transactions', { params }),
}

// Monitor API
export const monitorApi = {
  listAlerts: (params?: { active_only?: boolean }) =>
    api.get('/monitor/alerts', { params }),

  createAlert: (data: any) => api.post('/monitor/alerts', data),

  updateAlert: (id: number, data: any) => api.put(`/monitor/alerts/${id}`, data),

  deleteAlert: (id: number) => api.delete(`/monitor/alerts/${id}`),

  getHistory: (params?: { limit?: number }) =>
    api.get('/monitor/alerts/history', { params }),
}

// Strategy API
export const strategyApi = {
  listStrategies: (params?: { category?: string; status?: string }) =>
    api.get('/strategy', { params }),

  getStrategy: (id: number) => api.get(`/strategy/${id}`),

  createStrategy: (data: any) => api.post('/strategy', data),

  updateStrategy: (id: number, data: any) => api.put(`/strategy/${id}`, data),

  deleteStrategy: (id: number) => api.delete(`/strategy/${id}`),

  backtest: (id: number, data: any) => api.post(`/strategy/${id}/test`, data),

  getSignals: (params?: { code?: string }) => api.get('/strategy/signals', { params }),
}

// Review API
export const reviewApi = {
  getDailyReviews: (params?: { start_date?: string; end_date?: string; limit?: number }) =>
    api.get('/review/daily', { params }),

  getDailyReview: (review_date: string) =>
    api.get(`/review/daily/${review_date}`),

  createDailyReview: (data: { date: string; content?: string; summary?: string; market_overview?: string; watchlist_notes?: string }) =>
    api.post('/review/daily', data),

  getWeeklyReviews: (params?: { limit?: number }) =>
    api.get('/review/weekly', { params }),

  getCalendar: (params: { year: number; month: number }) =>
    api.get('/review/calendar', { params }),
}

// Config API
export const configApi = {
  getSystemSettings: () => api.get('/config/system'),

  updateSystemSettings: (data: any) => api.put('/config/system', data),

  getModels: (params?: { enabled_only?: boolean }) =>
    api.get('/models', { params }),

  createModel: (data: any) => api.post('/models', data),

  updateModel: (id: number, data: any) => api.put(`/models/${id}`, data),

  deleteModel: (id: number) => api.delete(`/models/${id}`),

  testModel: (id: number) => api.post(`/models/${id}/test`),
}
